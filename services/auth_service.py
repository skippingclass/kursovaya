"""
Сервис аутентификации и авторизации (AuthModule)
Учетные записи используются автономным приложением и HTTP API.
"""
from typing import Optional, Dict, Any, Tuple
from database.connection import get_session
from database.models import User
from config import ROLE_ADMIN, ROLE_OPERATOR, ROLE_METHODIST
from services.passwords import hash_password, verify_password

_current_user: Optional[Dict[str, Any]] = None


def user_info(user):
    return {"id": user.id, "username": user.username, "role_id": user.role_id,
            "role_name": user.role.name if user.role else "Неизвестно"}


def session_key(user):
    return user.username, user.password_hash


def verify_credentials(username, password):
    with get_session() as session:
        user = session.query(User).filter_by(username=username.strip()).first()
        if user is None or not verify_password(password, user.password_hash):
            return None
        if not user.password_hash.startswith("scrypt$"):
            old_hash = user.password_hash
            updated = session.query(User).filter_by(id=user.id, password_hash=old_hash).update(
                {User.password_hash: hash_password(password)}, synchronize_session=False)
            session.commit()
            if not updated:
                user = session.query(User).filter_by(username=username.strip()).first()
                if user is None or not verify_password(password, user.password_hash):
                    return None
        return user_info(user), session_key(user)


def authenticate(username: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Set the active account for the standalone desktop application."""
    global _current_user

    if not username or not password:
        return False, "Логин и пароль обязательны для заполнения!", None

    try:
        credentials = verify_credentials(username, password)
        if credentials is None:
            return False, "Неверное имя пользователя или пароль!", None
        _current_user, _ = credentials
        return True, None, _current_user

    except Exception as e:
        return False, f"Ошибка подключения к базе данных:\n{e}", None


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
