"""Идемпотентное обновление версии 1 без потери исходных назначений."""
from sqlalchemy import inspect, text
from database.models import Teacher, TeacherWorkload, WorkloadPool


def migrate_schema(engine):
    columns = {
        "teachers": {"last_name": "VARCHAR(100) NOT NULL DEFAULT ''",
                     "first_name": "VARCHAR(100) NOT NULL DEFAULT ''",
                     "middle_name": "VARCHAR(100) NOT NULL DEFAULT ''"},
        "teacher_workload": {"semester": "INTEGER NOT NULL DEFAULT 0",
                             "pool_id": "INTEGER REFERENCES workload_pools(id)"},
    }
    with engine.begin() as conn:
        for table, additions in columns.items():
            existing = {c["name"] for c in inspect(conn).get_columns(table)}
            for name, definition in additions.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_assignment_pool_teacher "
                          "ON teacher_workload (pool_id, teacher_id)"))


def migrate_records(session):
    for teacher in session.query(Teacher).all():
        if not teacher.last_name:
            parts = teacher.full_name.split(maxsplit=2)
            teacher.last_name = parts[0] if parts else ""
            teacher.first_name = parts[1] if len(parts) > 1 else ""
            teacher.middle_name = parts[2] if len(parts) > 2 else ""
    for workload in session.query(TeacherWorkload).filter_by(pool_id=None).all():
        workload.hours_lecture = workload.hours_lecture or 0
        workload.hours_practice = workload.hours_practice or 0
        # Группа и семестр старой версии неизвестны; не выдаем предположение за факт.
        pool = WorkloadPool(academic_year=workload.academic_year, semester=0,
                            group_name=f"Не указана (архив №{workload.id})",
                            discipline_id=workload.discipline_id,
                            hours_lecture=workload.hours_lecture or 0,
                            hours_practice=workload.hours_practice or 0, weeks=18)
        session.add(pool)
        session.flush()
        workload.pool_id = pool.id
        workload.semester = 0
        workload.total_hours = (workload.hours_lecture or 0) + (workload.hours_practice or 0)
    session.commit()
