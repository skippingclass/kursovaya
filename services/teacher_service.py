"""
Сервис управления кадрами и преподавателями (TeacherModule, SearchModule)
CRUD операции, расширенный многокритериальный поиск и фильтрация.
"""
from datetime import date
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
from database.connection import get_session
from database.models import Teacher, Department, TeacherWorkload


def get_teachers(
    search_text: Optional[str] = None,
    department_id: Optional[int] = None,
    qualification: Optional[str] = None,
    status: Optional[str] = None,
    min_exp: Optional[int] = None,
    max_exp: Optional[int] = None
) -> List[Teacher]:
    """
    Алгоритм поиска и фильтрации преподавателей (Раздел 6.2):
    Многокритериальная фильтрация по ФИО, кафедре, категории, статусу и стажу.
    """
    session = get_session()
    try:
        query = session.query(Teacher).options(
            joinedload(Teacher.department),
            joinedload(Teacher.workloads)
        )

        # Контекстный поиск по ФИО, телефону или email
        if search_text:
            st = f"%{search_text.strip().lower()}%"
            query = query.filter(
                or_(
                    Teacher.full_name.ilike(st),
                    Teacher.phone.ilike(st),
                    Teacher.email.ilike(st)
                )
            )

        # Фильтр по кафедре
        if department_id and department_id > 0:
            query = query.filter(Teacher.department_id == department_id)

        # Фильтр по категории
        if qualification and qualification != "Все категории":
            query = query.filter(Teacher.qualification == qualification)

        # Фильтр по статусу
        if status and status != "Все статусы":
            query = query.filter(Teacher.status == status)

        # Фильтр по стажу работы
        if min_exp is not None and min_exp >= 0:
            query = query.filter(Teacher.experience >= min_exp)
        if max_exp is not None and max_exp >= 0:
            query = query.filter(Teacher.experience <= max_exp)

        # Сортировка по ФИО
        query = query.order_by(Teacher.full_name.asc())
        return query.all()
    finally:
        session.close()


def get_teacher_by_id(teacher_id: int) -> Optional[Teacher]:
    """Получение подробных данных преподавателя по ID с привязкой кафедры и нагрузок"""
    session = get_session()
    try:
        return session.query(Teacher).options(
            joinedload(Teacher.department),
            joinedload(Teacher.workloads).joinedload(TeacherWorkload.discipline)
        ).filter(Teacher.id == teacher_id).first()
    finally:
        session.close()


def validate_teacher_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Валидация полей карточки преподавателя"""
    full_name = data.get("full_name", "").strip()
    if not full_name:
        return False, "Поле 'ФИО' обязательно для заполнения!"
    if len(full_name) < 3:
        return False, "ФИО должно содержать не менее 3 символов!"

    dept_id = data.get("department_id")
    if not dept_id or dept_id <= 0:
        return False, "Необходимо выбрать кафедру/отделение!"

    experience = data.get("experience", 0)
    try:
        exp = int(experience)
        if exp < 0 or exp > 70:
            return False, "Стаж работы должен быть в диапазоне от 0 до 70 лет!"
    except ValueError:
        return False, "Стаж работы должен быть целым числом!"

    email = data.get("email", "").strip()
    if email and ("@" not in email or "." not in email):
        return False, "Некорректный формат адреса электронной почты (example@mail.kz)!"

    return True, None


def add_teacher(data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
    """Добавление новой карточки преподавателя"""
    valid, err = validate_teacher_data(data)
    if not valid:
        return False, err, None

    session = get_session()
    try:
        teacher = Teacher(
            full_name=data["full_name"].strip(),
            birth_date=data.get("birth_date"),
            phone=data.get("phone", "").strip(),
            email=data.get("email", "").strip(),
            qualification=data.get("qualification", "").strip(),
            experience=int(data.get("experience", 0)),
            department_id=int(data["department_id"]),
            status=data.get("status", "работает"),
            photo_path=data.get("photo_path")
        )
        session.add(teacher)
        session.commit()
        teacher_id = teacher.id
        return True, "Преподаватель успешно добавлен!", teacher_id
    except Exception as e:
        session.rollback()
        return False, f"Ошибка добавления: {e}", None
    finally:
        session.close()


def update_teacher(teacher_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
    """Редактирование данных преподавателя"""
    valid, err = validate_teacher_data(data)
    if not valid:
        return False, err

    session = get_session()
    try:
        teacher = session.query(Teacher).filter(Teacher.id == teacher_id).first()
        if not teacher:
            return False, "Преподаватель не найден!"

        teacher.full_name = data["full_name"].strip()
        teacher.birth_date = data.get("birth_date")
        teacher.phone = data.get("phone", "").strip()
        teacher.email = data.get("email", "").strip()
        teacher.qualification = data.get("qualification", "").strip()
        teacher.experience = int(data.get("experience", 0))
        teacher.department_id = int(data["department_id"])
        teacher.status = data.get("status", "работает")
        if "photo_path" in data:
            teacher.photo_path = data["photo_path"]

        session.commit()
        return True, "Данные преподавателя успешно обновлены!"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка обновления: {e}"
    finally:
        session.close()


def delete_teacher(teacher_id: int) -> Tuple[bool, str]:
    """Удаление карточки преподавателя и связанных нагрузок"""
    session = get_session()
    try:
        teacher = session.query(Teacher).filter(Teacher.id == teacher_id).first()
        if not teacher:
            return False, "Преподаватель не найден!"

        name = teacher.full_name
        session.delete(teacher)
        session.commit()
        return True, f"Преподаватель '{name}' успешно удален!"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка удаления: {e}"
    finally:
        session.close()
