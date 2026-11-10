"""Полные JSON-копии версии 2; восстановление одной транзакцией."""
import json
from datetime import date, datetime
from sqlalchemy import Date, Integer, text
from database.connection import get_session
from database.models import Role, User, Department, Discipline, Teacher, WorkloadPool, TeacherWorkload
from database.migrations import migrate_records

TABLES = [("roles", Role), ("users", User), ("departments", Department),
          ("disciplines", Discipline), ("teachers", Teacher), ("pools", WorkloadPool),
          ("workloads", TeacherWorkload)]


def create_backup(filepath):
    session = get_session()
    try:
        data = {"version": 2, "created_at": datetime.now().isoformat()}
        for key, model in TABLES:
            data[key] = [{col.name: (value.isoformat() if isinstance(value, date) else value)
                          for col in model.__table__.columns
                          for value in [getattr(row, col.name)]} for row in session.query(model).all()]
        with open(filepath, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
        return True, f"Резервная копия создана: {filepath}"
    except Exception as exc:
        return False, f"Ошибка создания копии: {exc}"
    finally:
        session.close()


def restore_backup(filepath):
    session = get_session()
    try:
        with open(filepath, encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, dict) or any(not isinstance(data.get(key), list)
                                              for key, _ in TABLES if key != "pools"):
            raise ValueError("Некорректная структура резервной копии.")
        if data.get("version", 1) not in (1, 2):
            raise ValueError("Неподдерживаемая версия копии.")
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
        # Проверяем ссылки и остатки также на SQLite с отключенными внешними ключами.
        for w in session.query(TeacherWorkload).all():
            if not session.get(Teacher, w.teacher_id) or not session.get(Discipline, w.discipline_id):
                raise ValueError("Нарушены связи назначения.")
            if min(w.hours_lecture, w.hours_practice) < 0 or w.total_hours != w.hours_lecture + w.hours_practice:
                raise ValueError("Некорректные часы назначения.")
            if w.pool_id:
                p = session.get(WorkloadPool, w.pool_id)
                if not p or (w.academic_year, w.semester, w.discipline_id) != (p.academic_year, p.semester, p.discipline_id):
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
