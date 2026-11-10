"""
Сервис управления кафедрами и дисциплинами
"""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import joinedload
from database.connection import get_session
from database.models import Department, Discipline, Teacher, WorkloadPool


# --- КАФЕДРЫ ---

def get_departments() -> List[Department]:
    session = get_session()
    try:
        return session.query(Department).order_by(Department.name.asc()).all()
    finally:
        session.close()


def get_department_by_id(dept_id: int) -> Optional[Department]:
    session = get_session()
    try:
        return session.query(Department).filter(Department.id == dept_id).first()
    finally:
        session.close()


def add_department(name: str, head_name: str = "") -> Tuple[bool, str, Optional[int]]:
    if not name or not name.strip():
        return False, "Название кафедры обязательно!", None

    session = get_session()
    try:
        dept = Department(name=name.strip(), head_name=head_name.strip() if head_name else None)
        session.add(dept)
        session.commit()
        return True, "Кафедра успешно добавлена!", dept.id
    except Exception as e:
        session.rollback()
        return False, f"Ошибка добавления кафедры: {e}", None
    finally:
        session.close()


def update_department(dept_id: int, name: str, head_name: str = "") -> Tuple[bool, str]:
    if not name or not name.strip():
        return False, "Название кафедры обязательно!"

    session = get_session()
    try:
        dept = session.query(Department).filter(Department.id == dept_id).first()
        if not dept:
            return False, "Кафедра не найдена!"
        dept.name = name.strip()
        dept.head_name = head_name.strip() if head_name else None
        session.commit()
        return True, "Данные кафедры успешно обновлены!"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка обновления кафедры: {e}"
    finally:
        session.close()


def delete_department(dept_id: int) -> Tuple[bool, str]:
    session = get_session()
    try:
        dept = session.query(Department).filter(Department.id == dept_id).first()
        if not dept:
            return False, "Кафедра не найдена!"
        name = dept.name
        if dept.teachers or dept.disciplines:
            return False, "Сначала перенесите преподавателей и удалите дисциплины кафедры."
        session.delete(dept)
        session.commit()
        return True, f"Кафедра '{name}' успешно удалена!"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка удаления: {e}"
    finally:
        session.close()


# --- ДИСЦИПЛИНЫ ---

def get_disciplines(department_id: Optional[int] = None) -> List[Discipline]:
    session = get_session()
    try:
        query = session.query(Discipline).options(joinedload(Discipline.department))
        if department_id and department_id > 0:
            query = query.filter(Discipline.department_id == department_id)
        return query.order_by(Discipline.code.asc(), Discipline.name.asc()).all()
    finally:
        session.close()


def add_discipline(code: str, name: str, department_id: int) -> Tuple[bool, str, Optional[int]]:
    if not code or not code.strip():
        return False, "Код дисциплины обязателен!", None
    if not name or not name.strip():
        return False, "Название дисциплины обязательно!", None
    if not department_id or department_id <= 0:
        return False, "Выберите кафедру для дисциплины!", None

    session = get_session()
    try:
        disc = Discipline(code=code.strip(), name=name.strip(), department_id=department_id)
        session.add(disc)
        session.commit()
        return True, "Дисциплина успешно добавлена!", disc.id
    except Exception as e:
        session.rollback()
        return False, f"Ошибка добавления дисциплины: {e}", None
    finally:
        session.close()


def update_discipline(disc_id: int, code: str, name: str, department_id: int) -> Tuple[bool, str]:
    if not code or not code.strip():
        return False, "Код дисциплины обязателен!"
    if not name or not name.strip():
        return False, "Название дисциплины обязательно!"

    session = get_session()
    try:
        disc = session.query(Discipline).filter(Discipline.id == disc_id).first()
        if not disc:
            return False, "Дисциплина не найдена!"
        disc.code = code.strip()
        disc.name = name.strip()
        disc.department_id = department_id
        session.commit()
        return True, "Дисциплина успешно обновлена!"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка обновления: {e}"
    finally:
        session.close()


def delete_discipline(disc_id: int) -> Tuple[bool, str]:
    session = get_session()
    try:
        disc = session.query(Discipline).filter(Discipline.id == disc_id).first()
        if not disc:
            return False, "Дисциплина не найдена!"
        name = disc.name
        if disc.workloads or disc.pools:
            return False, "Дисциплина используется в общем плане или назначениях нагрузки."
        session.delete(disc)
        session.commit()
        return True, f"Дисциплина '{name}' успешно удалена!"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка удаления: {e}"
    finally:
        session.close()
