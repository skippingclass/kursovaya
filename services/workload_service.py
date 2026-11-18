"""План учебной нагрузки и распределение часов из общего пула."""
import logging
import re
from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from database.connection import get_session
from database.models import TeacherWorkload, WorkloadPool, Teacher, Discipline

RATE_HOURS = 720
LOG = logging.getLogger(__name__)


def semester_label(value):
    return str(value) if value in (1, 2) else "Не указан"


def get_workloads(academic_year=None, teacher_id=None, department_id=None, semester=None):
    session = get_session()
    try:
        query = session.query(TeacherWorkload).options(
            joinedload(TeacherWorkload.teacher).joinedload(Teacher.department),
            joinedload(TeacherWorkload.discipline), joinedload(TeacherWorkload.pool))
        if academic_year and academic_year != "Все годы":
            query = query.filter(TeacherWorkload.academic_year == academic_year)
        if teacher_id:
            query = query.filter(TeacherWorkload.teacher_id == teacher_id)
        if department_id:
            query = query.join(TeacherWorkload.teacher).filter(Teacher.department_id == department_id)
        if semester is not None:
            query = query.filter(TeacherWorkload.semester == semester)
        return query.order_by(TeacherWorkload.academic_year.desc(), TeacherWorkload.semester,
                              TeacherWorkload.id).all()
    finally:
        session.close()


def get_pools(academic_year=None, semester=None, department_id=None):
    session = get_session()
    try:
        query = session.query(WorkloadPool).options(joinedload(WorkloadPool.discipline),
                                                   joinedload(WorkloadPool.workloads))
        if academic_year and academic_year != "Все годы":
            query = query.filter(WorkloadPool.academic_year == academic_year)
        if semester is not None:
            query = query.filter(WorkloadPool.semester == semester)
        if department_id:
            query = query.join(WorkloadPool.discipline).filter(Discipline.department_id == department_id)
        return query.order_by(WorkloadPool.academic_year.desc(), WorkloadPool.semester,
                              WorkloadPool.group_name, WorkloadPool.id).all()
    finally:
        session.close()


def get_academic_years():
    session = get_session()
    try:
        years = {r[0] for r in session.query(TeacherWorkload.academic_year).distinct()}
        years.update(r[0] for r in session.query(WorkloadPool.academic_year).distinct())
        current = date.today().year - (date.today().month < 9)
        years.update(f"{y}-{y+1}" for y in range(current-2, current+3))
        return sorted(years, reverse=True)
    finally:
        session.close()


def _hours(lecture, practice):
    try:
        hl, hp = int(lecture), int(practice)
        if hl != float(lecture) or hp != float(practice) or min(hl, hp) < 0 or hl + hp <= 0:
            raise ValueError
        return hl, hp
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Укажите целые неотрицательные часы; сумма должна быть больше нуля.")


def _write_lock(session):
    # SQLite не поддерживает FOR UPDATE; резервируем запись до чтения остатка.
    if session.bind.dialect.name == "sqlite":
        session.execute(text("BEGIN IMMEDIATE"))


def save_pool(academic_year, semester, group_name, discipline_id, hours_lecture,
              hours_practice, weeks=18, pool_id=None):
    session = get_session()
    try:
        if not re.fullmatch(r"\d{4}-\d{4}", academic_year.strip()):
            raise ValueError("Учебный год вводится в формате 2026-2027.")
        start, end = map(int, academic_year.split("-"))
        if end != start + 1:
            raise ValueError("Учебный год должен охватывать два последовательных года.")
        if semester not in (1, 2) or not group_name.strip() or len(group_name.strip()) > 100:
            raise ValueError("Выберите семестр 1 или 2 и укажите группу (до 100 символов).")
        hl, hp = _hours(hours_lecture, hours_practice)
        if not 1 <= int(weeks) <= 52:
            raise ValueError("Количество учебных недель должно быть от 1 до 52.")
        _write_lock(session)
        pool = session.query(WorkloadPool).filter_by(id=pool_id).with_for_update().first() if pool_id else None
        if pool_id and not pool:
            raise ValueError("Строка общего плана не найдена.")
        if not session.get(Discipline, discipline_id):
            raise ValueError("Выберите существующую дисциплину.")
        duplicate = session.query(WorkloadPool).filter_by(
            academic_year=academic_year.strip(), semester=semester,
            group_name=group_name.strip().upper(), discipline_id=discipline_id)
        if pool_id:
            duplicate = duplicate.filter(WorkloadPool.id != pool_id)
        if duplicate.first():
            raise ValueError("План для этой группы, дисциплины и семестра уже существует.")
        if pool:
            if hl < sum(w.hours_lecture for w in pool.workloads) or hp < sum(w.hours_practice for w in pool.workloads):
                raise ValueError("План нельзя уменьшить ниже уже назначенных часов теории или практики.")
            if pool.workloads and discipline_id != pool.discipline_id:
                raise ValueError("Сначала отмените назначения, чтобы изменить дисциплину плана.")
        else:
            pool = WorkloadPool()
            session.add(pool)
        pool.academic_year, pool.semester = academic_year.strip(), semester
        pool.group_name, pool.discipline_id = group_name.strip().upper(), discipline_id
        pool.hours_lecture, pool.hours_practice, pool.weeks = hl, hp, int(weeks)
        for w in pool.workloads:
            w.academic_year, w.semester, w.discipline_id = pool.academic_year, semester, discipline_id
        session.commit()
        return True, "Общий план сохранен.", pool.id
    except (ValueError, TypeError, AttributeError) as exc:
        session.rollback()
        return False, str(exc), None
    except Exception:
        session.rollback()
        LOG.exception("Could not save workload plan")
        return False, "Не удалось сохранить план.", None
    finally:
        session.close()


def delete_pool(pool_id):
    session = get_session()
    try:
        _write_lock(session)
        pool = session.query(WorkloadPool).filter_by(id=pool_id).with_for_update().first()
        if not pool:
            return False, "Строка плана не найдена."
        if pool.workloads:
            return False, "Сначала отмените назначения преподавателям из этой строки плана."
        session.delete(pool)
        session.commit()
        return True, "Строка общего плана удалена."
    except Exception:
        session.rollback()
        LOG.exception("Could not delete workload plan")
        return False, "Не удалось удалить план."
    finally:
        session.close()


def _save_assignment(teacher_id, pool_id, lecture, practice, workload_id=None):
    session = get_session()
    try:
        hl, hp = _hours(lecture, practice)
        _write_lock(session)
        assignment = session.get(TeacherWorkload, workload_id) if workload_id else None
        if workload_id and not assignment:
            raise ValueError("Назначение не найдено.")
        # Один порядок захвата блокировок при переносе между двумя пулами.
        pool_ids = sorted({i for i in (pool_id, assignment.pool_id if assignment else None) if i})
        pools = session.query(WorkloadPool).filter(WorkloadPool.id.in_(pool_ids)).order_by(WorkloadPool.id).with_for_update().all()
        pool = next((p for p in pools if p.id == pool_id), None)
        if not pool:
            raise ValueError("Выберите строку общего плана нагрузки.")
        teacher = session.get(Teacher, teacher_id)
        if not teacher or teacher.status == "уволен":
            raise ValueError("Выберите действующего преподавателя.")
        others = session.query(TeacherWorkload).filter_by(pool_id=pool.id).all()
        others = [w for w in others if w.id != workload_id]
        if any(w.teacher_id == teacher_id for w in others):
            raise ValueError("У преподавателя уже есть назначение из этой строки плана. Отредактируйте его.")
        free_l = pool.hours_lecture - sum(w.hours_lecture for w in others)
        free_p = pool.hours_practice - sum(w.hours_practice for w in others)
        if hl > free_l or hp > free_p:
            raise ValueError(f"Недостаточно часов в общем плане. Доступно: теория {free_l} ч., практика {free_p} ч.")
        if not assignment:
            assignment = TeacherWorkload()
            session.add(assignment)
        assignment.teacher_id, assignment.pool_id = teacher_id, pool.id
        assignment.discipline_id, assignment.academic_year = pool.discipline_id, pool.academic_year
        assignment.semester = pool.semester
        assignment.hours_lecture, assignment.hours_practice, assignment.total_hours = hl, hp, hl + hp
        session.commit()
        return True, "Назначение сохранено; остаток общего плана пересчитан.", assignment.id
    except ValueError as exc:
        session.rollback()
        return False, str(exc), None
    except Exception:
        session.rollback()
        LOG.exception("Could not save assignment")
        return False, "Не удалось сохранить назначение.", None
    finally:
        session.close()


def add_workload(academic_year, teacher_id, discipline_id, hours_lecture, hours_practice,
                 semester=None, pool_id=None):
    return _save_assignment(teacher_id, pool_id, hours_lecture, hours_practice)


def update_workload(workload_id, academic_year, teacher_id, discipline_id,
                    hours_lecture, hours_practice, semester=None, pool_id=None):
    ok, msg, _ = _save_assignment(teacher_id, pool_id, hours_lecture, hours_practice, workload_id)
    return ok, msg


def delete_workload(workload_id):
    session = get_session()
    try:
        _write_lock(session)
        workload = session.get(TeacherWorkload, workload_id)
        if not workload:
            return False, "Назначение не найдено."
        session.query(WorkloadPool).filter_by(id=workload.pool_id).with_for_update().first()
        session.delete(workload)
        session.commit()
        return True, "Назначение отменено. Часы возвращены в общий план."
    except Exception:
        session.rollback()
        LOG.exception("Could not delete assignment")
        return False, "Не удалось отменить назначение."
    finally:
        session.close()
