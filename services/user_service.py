"""
Сервис управления пользователями системы (Администратор)
"""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import joinedload
from database.connection import get_session
from database.models import User, Role
from services.auth_service import get_current_user
from services.passwords import hash_password


def get_users() -> List[User]:
    session = get_session()
    try:
        return session.query(User).options(joinedload(User.role)).order_by(User.id.asc()).all()
    finally:
        session.close()


def get_roles() -> List[Role]:
    session = get_session()
    try:
        return session.query(Role).order_by(Role.id.asc()).all()
    finally:
        session.close()


def add_user(username: str, password: str, role_id: int) -> Tuple[bool, str, Optional[int]]:
    if not username or not username.strip():
        return False, "Логин обязателен для заполнения!", None
    if len(username.strip()) < 3:
        return False, "Логин должен быть не короче 3 символов!", None
    if not password or len(password) < 4:
        return False, "Пароль должен содержать не менее 4 символов!", None
    if not role_id or role_id <= 0:
        return False, "Выберите роль для пользователя!", None

    session = get_session()
    try:
        existing = session.query(User).filter(User.username == username.strip()).first()
        if existing:
            return False, f"Пользователь с логином '{username.strip()}' уже существует!", None

        user = User(
            username=username.strip(),
            password_hash=hash_password(password),
            role_id=role_id
        )
        session.add(user)
        session.commit()
        return True, "Пользователь успешно создан!", user.id
    except Exception as e:
        session.rollback()
        return False, f"Ошибка создания пользователя: {e}", None
    finally:
        session.close()


def update_user(user_id: int, username: str, role_id: int, new_password: Optional[str] = None) -> Tuple[bool, str]:
    if not username or not username.strip():
        return False, "Логин обязателен для заполнения!"
    if len(username.strip()) < 3:
        return False, "Логин должен быть не короче 3 символов!"
    if not role_id or role_id <= 0:
        return False, "Выберите роль для пользователя!"

    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "Пользователь не найден!"

        dup = session.query(User).filter(User.username == username.strip(), User.id != user_id).first()
        if dup:
            return False, f"Логин '{username.strip()}' уже занят другим пользователем!"

        user.username = username.strip()
        user.role_id = role_id
        if new_password and new_password.strip():
            if len(new_password) < 4:
                return False, "Новый пароль должен содержать не менее 4 символов!"
            user.password_hash = hash_password(new_password)

        session.commit()
        return True, "Данные пользователя успешно обновлены!"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка обновления пользователя: {e}"
    finally:
        session.close()


def delete_user(user_id: int) -> Tuple[bool, str]:
    curr = get_current_user()
    if curr and curr.get("id") == user_id:
        return False, "Вы не можете удалить свою собственную учетную запись!"

    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "Пользователь не найден!"

        # Не даем удалить последнего администратора
        role = session.query(Role).filter(Role.id == user.role_id).first()
        if role and role.name == "Администратор":
            admin_count = session.query(User).filter(User.role_id == role.id).count()
            if admin_count <= 1:
                return False, "Нельзя удалить единственного администратора системы!"

        session.delete(user)
        session.commit()
        return True, "Пользователь успешно удален!"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка удаления пользователя: {e}"
    finally:
        session.close()
