"""
Конфигурация приложения "Система учета преподавателей колледжа"
Высший колледж «Astana Polytechnic»
"""
import os
import json
from pathlib import Path

APP_NAME = "Система учета преподавателей"
COLLEGE_NAME = "Высший колледж «Astana Polytechnic»"
APP_VERSION = "2.1.0"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = BASE_DIR / "settings.json"

# Создаем директорию для данных, если ее нет
DATA_DIR.mkdir(exist_ok=True)

# Роли пользователей
ROLE_ADMIN = "Администратор"
ROLE_OPERATOR = "Заведующий кафедрой"  # Зав. кафедрой / Отдел кадров
ROLE_METHODIST = "Методист"            # Руководство / Методист (только чтение)

ROLES_LIST = [ROLE_ADMIN, ROLE_OPERATOR, ROLE_METHODIST]

# Стандартные настройки подключения
DEFAULT_CONFIG = {
    "db_type": "sqlite",  # "sqlite" или "postgresql"
    "pg_host": "localhost",
    "pg_port": 5432,
    "pg_database": "college_teachers",
    "pg_user": "postgres",
    "pg_password": "",
    "sqlite_path": str(DATA_DIR / "college_teachers.db")
}

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                return config
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def get_database_url() -> str:
    override = os.environ.get("COLLEGE_DB_URL")
    if override:
        return override
    cfg = load_config()
    if cfg.get("db_type") == "postgresql":
        host = cfg.get("pg_host", "localhost")
        port = cfg.get("pg_port", 5432)
        dbname = cfg.get("pg_database", "college_teachers")
        user = cfg.get("pg_user", "postgres")
        pwd = cfg.get("pg_password", "")
        if pwd:
            return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{dbname}"
        return f"postgresql+psycopg2://{user}@{host}:{port}/{dbname}"
    else:
        # SQLite
        sqlite_path = cfg.get("sqlite_path", str(DATA_DIR / "college_teachers.db"))
        return f"sqlite:///{sqlite_path}"
