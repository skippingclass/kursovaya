"""
Управление подключением к базе данных (SQLAlchemy)
Поддерживает PostgreSQL и SQLite (автономный режим)
"""
from typing import Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from config import get_database_url
from database.models import Base

_engine = None
_SessionLocal = None


def get_engine(db_url: str = None):
    global _engine
    if db_url is not None:
        return create_engine(db_url, echo=False)
    if _engine is None:
        url = get_database_url()
        _engine = create_engine(url, echo=False)
    return _engine


def get_session(db_url: str = None) -> Session:
    global _SessionLocal
    engine = get_engine(db_url)
    session_cls = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_cls()


def test_connection(db_url: str) -> Tuple[bool, str]:
    """Проверка подключения к указанной БД"""
    try:
        temp_engine = create_engine(db_url, connect_args={"connect_timeout": 3} if "postgresql" in db_url else {})
        with temp_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Подключение успешно установлено!"
    except Exception as e:
        return False, str(e)


def init_db(db_url: str = None):
    """Инициализация базы данных: создание таблиц и заполнение начальными данными"""
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)

    # Проверяем, есть ли роли и начальные данные
    from database.seed_data import seed_database
    session = get_session(db_url)
    try:
        seed_database(session)
    finally:
        session.close()


def reset_engine():
    """Сброс кэшированного движка при смене настроек подключения"""
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
