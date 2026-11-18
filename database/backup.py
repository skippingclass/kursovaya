"""Полные JSON-копии версии 2; восстановление одной транзакцией."""
import json
from datetime import date, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from sqlalchemy import Date, select, text
from database.connection import get_session
from database.models import Role, User, Department, Discipline, Teacher, WorkloadPool, TeacherWorkload
from database.migrations import migrate_records

TABLES = [("roles", Role), ("users", User), ("departments", Department),
          ("disciplines", Discipline), ("teachers", Teacher), ("pools", WorkloadPool),
          ("workloads", TeacherWorkload)]


def create_backup(filepath):
    target = Path(filepath)
    session = get_session()
    temporary = None
    try:
        if session.bind.dialect.name == "sqlite":
            session.execute(text("BEGIN"))
        elif session.bind.dialect.name == "postgresql":
            session.connection(execution_options={"isolation_level": "REPEATABLE READ"})
        data = {"version": 2, "created_at": datetime.now().isoformat()}
        for key, model in TABLES:
            data[key] = [{col.name: (value.isoformat() if isinstance(value, date) else value)
                          for col in model.__table__.columns
                          for value in [getattr(row, col.name)]} for row in session.query(model).all()]
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
        temporary.replace(target)
        return True, f"Резервная копия создана: {filepath}"
    except Exception as exc:
        return False, f"Ошибка создания копии: {exc}"
    finally:
        session.close()
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def restore_backup(filepath):
    session = get_session()
    try:
        with open(filepath, encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, dict):
            raise ValueError("Некорректная структура резервной копии.")
        version = data.get("version", 1)
        if version not in (1, 2):
            raise ValueError("Неподдерживаемая версия копии.")
        required = {key for key, _ in TABLES}
        if version == 1 and "pools" not in data:
            required.remove("pools")
        if any(not isinstance(data.get(key), list) for key in required):
            raise ValueError("Некорректная структура резервной копии.")
        for _, model in reversed(TABLES):
            session.query(model).delete(synchronize_session=False)
        for key, model in TABLES:
            columns = {col.name: col for col in model.__table__.columns}
            for item in data.get(key, []):
                values = {k: v for k, v in item.items() if k in columns}
                for k, col in columns.items():
                    if isinstance(col.type, Date) and values.get(k):
                        values[k] = date.fromisoformat(values[k])
                session.add(model(**values))
            session.flush()
        # SQLite может работать без проверки внешних ключей на уровне СУБД.
        for _, model in TABLES:
            for key in model.__table__.foreign_keys:
                column = key.parent
                broken = select(column).where(column.is_not(None), column.not_in(select(key.column))).limit(1)
                if session.execute(broken).first():
                    raise ValueError(f"В копии нарушена связь {column.table.name}.{column.name}.")
        for w in session.query(TeacherWorkload).all():
            if min(w.hours_lecture, w.hours_practice) < 0 or w.total_hours != w.hours_lecture + w.hours_practice:
                raise ValueError("Некорректные часы назначения.")
            if w.pool is not None:
                p = w.pool
                if (w.academic_year, w.semester, w.discipline_id) != (p.academic_year, p.semester, p.discipline_id):
                    raise ValueError("Назначение не соответствует общему плану.")
        for p in session.query(WorkloadPool).all():
            if p.available_lecture < 0 or p.available_practice < 0:
                raise ValueError("В копии назначено больше часов, чем предусмотрено планом.")
        if session.bind.dialect.name == "postgresql":
            for _, model in TABLES:
                name = model.__tablename__
                session.execute(text(f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), "
                                     f"COALESCE((SELECT MAX(id) FROM {name}), 1), "
                                     f"EXISTS(SELECT 1 FROM {name}))"))
        migrate_records(session)  # Один commit после всех проверок, включая конверсию старого формата.
        return True, "База данных восстановлена."
    except Exception as exc:
        session.rollback()
        return False, f"Ошибка восстановления: {exc}"
    finally:
        session.close()
