"""
Сервис учета и распределения педагогической нагрузки (LoadModule)
Расчет часов, закрепление дисциплин за преподавателями.
"""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import joinedload
from database.connection import get_session
from database.models import TeacherWorkload, Teacher, Discipline, Department


def get_workloads(
    academic_year: Optional[str] = None,
    teacher_id: Optional[int] = None,
    department_id: Optional[int] = None
) -> List[TeacherWorkload]:
    session = get_session()
    try:
        query = session.query(TeacherWorkload).options(
            joinedload(TeacherWorkload.teacher).joinedload(Teacher.department),
            joinedload(TeacherWorkload.discipline)
        )

        if academic_year and academic_year != "Все годы":
            query = query.filter(TeacherWorkload.academic_year == academic_year)

        if teacher_id and teacher_id > 0:
            query = query.filter(TeacherWorkload.teacher_id == teacher_id)

        if department_id and department_id > 0:
            query = query.join(TeacherWorkload.teacher).filter(Teacher.department_id == department_id)

        query = query.order_by(TeacherWorkload.academic_year.desc(), TeacherWorkload.id.desc())
        return query.all()
    finally:
        session.close()


def get_academic_years() -> List[str]:
    """Список всех учебных годов в базе данных"""
    session = get_session()
    try:
        res = session.query(TeacherWorkload.academic_year).distinct().all()
        years = [r[0] for r in res if r[0]]
        # Если пусто или нет актуальных, добавим текущие годы
        defaults = ["2023-2024", "2024-2025", "2025-2026", "2026-2027"]
        combined = sorted(list(set(years + defaults)), reverse=True)
        return combined
    finally:
        session.close()


def add_workload(
    academic_year: str,
    teacher_id: int,
    discipline_id: int,
    hours_lecture: int,
    hours_practice: int
) -> Tuple[bool, str, Optional[int]]:
    if not academic_year or not academic_year.strip():
        return False, "Укажите учебный год!", None
    if not teacher_id or teacher_id <= 0:
        return False, "Выберите преподавателя!", None
    if not discipline_id or discipline_id <= 0:
        return False, "Выберите дисциплину!", None

    try:
        hl = int(hours_lecture)
        hp = int(hours_practice)
        if hl < 0 or hp < 0:
            return False, "Часы нагрузки не могут быть отрицательными!", None
        total = hl + hp
        if total <= 0:
            return False, "Суммарная нагрузка должна быть больше 0 часов!", None
    except ValueError:
        return False, "Часы должны быть целыми неотрицательными числами!", None

    session = get_session()
    try:
        # Проверим, нет ли дубликата нагрузки для этого преподавателя, дисциплины и года
        existing = session.query(TeacherWorkload).filter(
            TeacherWorkload.academic_year == academic_year.strip(),
            TeacherWorkload.teacher_id == teacher_id,
            TeacherWorkload.discipline_id == discipline_id
        ).first()
        if existing:
            return False, "Для данного преподавателя уже назначена нагрузка по этой дисциплине в указанном учебном году!", None

        wl = TeacherWorkload(
            academic_year=academic_year.strip(),
            teacher_id=teacher_id,
            discipline_id=discipline_id,
            hours_lecture=hl,
            hours_practice=hp,
            total_hours=total
        )
        session.add(wl)
        session.commit()
        return True, "Учебная нагрузка успешно добавлена!", wl.id
    except Exception as e:
        session.rollback()
        return False, f"Ошибка добавления нагрузки: {e}", None
    finally:
        session.close()


def update_workload(
    workload_id: int,
    academic_year: str,
    teacher_id: int,
    discipline_id: int,
    hours_lecture: int,
    hours_practice: int
) -> Tuple[bool, str]:
    if not academic_year or not academic_year.strip():
        return False, "Укажите учебный год!"
    if not teacher_id or teacher_id <= 0:
        return False, "Выберите преподавателя!"
    if not discipline_id or discipline_id <= 0:
        return False, "Выберите дисциплину!"

    try:
        hl = int(hours_lecture)
        hp = int(hours_practice)
        if hl < 0 or hp < 0:
            return False, "Часы нагрузки не могут быть отрицательными!"
        total = hl + hp
        if total <= 0:
            return False, "Суммарная нагрузка должна быть больше 0 часов!"
    except ValueError:
        return False, "Часы должны быть целыми неотрицательными числами!"

    session = get_session()
    try:
        wl = session.query(TeacherWorkload).filter(TeacherWorkload.id == workload_id).first()
        if not wl:
            return False, "Запись о нагрузке не найдена!"

        # Проверка дубликата при изменении
        dup = session.query(TeacherWorkload).filter(
            TeacherWorkload.id != workload_id,
            TeacherWorkload.academic_year == academic_year.strip(),
            TeacherWorkload.teacher_id == teacher_id,
            TeacherWorkload.discipline_id == discipline_id
        ).first()
        if dup:
            return False, "Такая нагрузка уже существует для выбранного преподавателя и дисциплины!"

        wl.academic_year = academic_year.strip()
        wl.teacher_id = teacher_id
        wl.discipline_id = discipline_id
        wl.hours_lecture = hl
        wl.hours_practice = hp
        wl.total_hours = total

        session.commit()
        return True, "Нагрузка успешно обновлена!"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка обновления нагрузки: {e}"
    finally:
        session.close()


def delete_workload(workload_id: int) -> Tuple[bool, str]:
    session = get_session()
    try:
        wl = session.query(TeacherWorkload).filter(TeacherWorkload.id == workload_id).first()
        if not wl:
            return False, "Запись о нагрузке не найдена!"
        session.delete(wl)
        session.commit()
        return True, "Запись о нагрузке успешно удалена!"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка удаления нагрузки: {e}"
    finally:
        session.close()
