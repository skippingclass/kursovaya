"""
Сервис аутентификации и авторизации (AuthModule)
Реализует блок-схему алгоритма авторизации (Раздел 6.3)
"""
import hashlib
from typing import Optional, Dict, Any, Tuple
from database.connection import get_session
from database.models import User, Role
from config import ROLE_ADMIN, ROLE_OPERATOR, ROLE_METHODIST

_current_user: Optional[Dict[str, Any]] = None


def hash_password(password: str) -> str:
    """Хэширование пароля SHA-256"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def authenticate(username: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Алгоритм авторизации пользователя (Блок-схема 6.3):
    1. Ввод логина и пароля
    2. Хэширование пароля (SHA-256)
    3. Запрос к БД (таблица Users)
    4. Пользователь найден и пароль верен?
       - Да: Получение роли (role_id, role.name), открытие MainWindow
       - Нет: Сообщение об ошибке
    """
    global _current_user

    if not username or not password:
        return False, "Логин и пароль обязательны для заполнения!", None

    session = get_session()
    try:
        pw_hash = hash_password(password)
        user = session.query(User).filter(
            User.username == username.strip(),
            User.password_hash == pw_hash
        ).first()

        if user is None:
            return False, "Неверное имя пользователя или пароль!", None

        role = session.query(Role).filter(Role.id == user.role_id).first()
        role_name = role.name if role else "Неизвестно"

        _current_user = {
            "id": user.id,
            "username": user.username,
            "role_id": user.role_id,
            "role_name": role_name
        }
        return True, None, _current_user

    except Exception as e:
        return False, f"Ошибка подключения к базе данных:\n{e}", None
    finally:
        session.close()


def logout():
    """Выход из системы"""
    global _current_user
    _current_user = None


def get_current_user() -> Optional[Dict[str, Any]]:
    """Текущий авторизованный пользователь"""
    return _current_user


def is_admin() -> bool:
    """Проверка прав системного администратора"""
    u = get_current_user()
    return u is not None and u.get("role_name") == ROLE_ADMIN


def is_operator() -> bool:
    """Проверка прав оператора (Заведующий кафедрой / Отдел кадров)"""
    u = get_current_user()
    return u is not None and u.get("role_name") in (ROLE_ADMIN, ROLE_OPERATOR)


def is_read_only() -> bool:
    """Проверка прав только на чтение (Методист / Руководство)"""
    u = get_current_user()
    return u is not None and u.get("role_name") == ROLE_METHODIST
