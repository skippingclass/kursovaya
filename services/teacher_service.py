"""Карточки преподавателей, проверка похожих записей, поиск и сортировка."""
import logging
import re
import unicodedata
from datetime import date
from difflib import SequenceMatcher
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from database.connection import get_session
from database.models import Teacher, TeacherWorkload, Department

LOG = logging.getLogger(__name__)


def normalize_name(value):
    return " ".join(unicodedata.normalize("NFKC", value or "").casefold().replace("ё", "е").split())


def _prepare(data):
    result = dict(data)
    if "last_name" not in result:
        parts = (result.get("full_name") or "").split(maxsplit=2)
        result.update(last_name=parts[0] if parts else "", first_name=parts[1] if len(parts) > 1 else "",
                      middle_name=parts[2] if len(parts) > 2 else "")
    for key in ("last_name", "first_name", "middle_name", "phone", "email", "qualification"):
        result[key] = " ".join((result.get(key) or "").split())
    result["full_name"] = " ".join(result[k] for k in ("last_name", "first_name", "middle_name") if result[k])
    return result


def get_teachers(search_text=None, department_id=None, qualification=None, status=None,
                 min_exp=None, max_exp=None, sort_by="full_name", descending=False,
                 academic_year=None, rate_filter=None):
    session = get_session()
    try:
        query = session.query(Teacher).options(joinedload(Teacher.department), joinedload(Teacher.workloads))
        if department_id:
            query = query.filter(Teacher.department_id == department_id)
        if qualification and qualification != "Все категории":
            query = query.filter(Teacher.qualification == qualification)
        if status and status != "Все статусы":
            query = query.filter(Teacher.status == status)
        if min_exp is not None:
            query = query.filter(Teacher.experience >= min_exp)
        if max_exp is not None:
            query = query.filter(Teacher.experience <= max_exp)
        teachers = query.all()
        # SQLite LOWER не обрабатывает кириллицу: casefold одинаков для обеих СУБД.
        if search_text:
            needle = normalize_name(search_text)
            teachers = [t for t in teachers if needle in normalize_name(f"{t.full_name} {t.phone or ''} {t.email or ''}")]
        for teacher in teachers:
            teacher.period_hours = sum(w.total_hours for w in teacher.workloads
                                       if not academic_year or w.academic_year == academic_year)
        compare = {"below": lambda h: h < 720, "equal": lambda h: h == 720, "above": lambda h: h > 720}
        if rate_filter in compare:
            teachers = [t for t in teachers if compare[rate_filter](t.period_hours)]
        keys = {"full_name": lambda t: normalize_name(t.full_name), "experience": lambda t: t.experience or 0,
                "total_hours": lambda t: t.period_hours,
                "department": lambda t: normalize_name(t.department.name if t.department else "")}
        teachers.sort(key=lambda t: (normalize_name(t.full_name), t.id))
        teachers.sort(key=keys.get(sort_by, keys["full_name"]), reverse=descending)
        return teachers
    finally:
        session.close()


def get_teacher_by_id(teacher_id):
    session = get_session()
    try:
        return session.query(Teacher).options(joinedload(Teacher.department),
            joinedload(Teacher.workloads).joinedload(TeacherWorkload.discipline),
            joinedload(Teacher.workloads).joinedload(TeacherWorkload.pool)).filter_by(id=teacher_id).first()
    finally:
        session.close()


def validate_teacher_data(data):
    data = _prepare(data)
    for key, label in (("last_name", "Фамилия"), ("first_name", "Имя")):
        if not data[key]:
            return False, f"Поле «{label}» обязательно."
    for key in ("last_name", "first_name", "middle_name"):
        value = data[key]
        if len(value) > 100 or (value and not all(c.isalpha() or c in " -'’" for c in value)):
            return False, "В ФИО допустимы буквы, пробел, дефис и апостроф; до 100 символов в поле."
    if len(data["full_name"]) > 200:
        return False, "Суммарная длина ФИО не должна превышать 200 символов."
    try:
        if int(data.get("department_id") or 0) <= 0:
            return False, "Выберите кафедру."
        if not 0 <= int(data.get("experience", 0)) <= 70:
            return False, "Стаж должен быть от 0 до 70 лет."
    except (ValueError, TypeError):
        return False, "Стаж и идентификатор кафедры должны быть целыми числами."
    if data["email"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", data["email"]):
        return False, "Укажите почту в формате name@example.kz."
    digits = re.sub(r"\D", "", data["phone"])
    if data["phone"] and (len(digits) != 11 or digits[0] not in "78"):
        return False, "Телефон должен содержать 11 цифр и начинаться с +7 или 8."
    birth = data.get("birth_date")
    if birth and (not isinstance(birth, date) or birth > date.today()):
        return False, "Дата рождения не может быть в будущем."
    return True, None


def _duplicates(session, data, exclude_id=None):
    matches = []
    name = normalize_name(data["full_name"])
    phone = re.sub(r"\D", "", data["phone"])
    phone = "7" + phone[1:] if phone else ""
    for teacher in session.query(Teacher).all():
        if teacher.id == exclude_id:
            continue
        candidate = normalize_name(teacher.full_name)
        contact = re.sub(r"\D", "", teacher.phone or "")
        contact = "7" + contact[1:] if contact else ""
        same_contact = (phone and phone == contact) or (data["email"] and data["email"].casefold() == (teacher.email or "").casefold())
        if candidate == name or same_contact:
            matches.append((teacher, True))
        elif SequenceMatcher(None, candidate, name).ratio() >= 0.88:
            matches.append((teacher, False))
    return matches


def find_similar_teachers(data, exclude_id=None):
    session = get_session()
    try:
        return [{"id": t.id, "full_name": t.full_name, "exact": exact} for t, exact in _duplicates(session, _prepare(data), exclude_id)]
    finally:
        session.close()


def _save_teacher(data, teacher_id=None, allow_similar=False):
    data = _prepare(data)
    valid, error = validate_teacher_data(data)
    if not valid:
        return False, error, None
    session = get_session()
    try:
        dialect = session.bind.dialect.name
        if dialect == "sqlite":
            session.execute(text("BEGIN IMMEDIATE"))
        elif dialect == "postgresql":
            session.execute(text("LOCK TABLE teachers IN SHARE ROW EXCLUSIVE MODE"))
        if not session.get(Department, data["department_id"]):
            return False, "Кафедра не найдена.", None
        matches = _duplicates(session, data, teacher_id)
        if any(exact for _, exact in matches):
            return False, "Преподаватель с таким ФИО, телефоном или почтой уже существует.", None
        if matches and not allow_similar:
            return False, "Найдена похожая карточка: " + ", ".join(t.full_name for t, _ in matches) + ". Проверьте опечатку.", None
        teacher = session.get(Teacher, teacher_id) if teacher_id else Teacher()
        if teacher is None:
            return False, "Преподаватель не найден.", None
        for key in ("full_name", "last_name", "first_name", "middle_name", "birth_date", "phone", "email",
                    "qualification", "experience", "department_id", "status", "photo_path"):
            if key in data:
                setattr(teacher, key, data[key])
        session.add(teacher)
        session.commit()
        return True, "Карточка преподавателя сохранена.", teacher.id
    except Exception:
        session.rollback()
        LOG.exception("Could not save teacher")
        return False, "Не удалось сохранить карточку.", None
    finally:
        session.close()


def add_teacher(data, allow_similar=False):
    return _save_teacher(data, allow_similar=allow_similar)


def update_teacher(teacher_id, data, allow_similar=False):
    ok, message, _ = _save_teacher(data, teacher_id, allow_similar)
    return ok, message


def delete_teacher(teacher_id):
    session = get_session()
    try:
        teacher = session.get(Teacher, teacher_id)
        if not teacher:
            return False, "Преподаватель не найден."
        session.delete(teacher)
        session.commit()
        return True, "Карточка удалена. Назначенные часы возвращены в общий план."
    except Exception:
        session.rollback()
        LOG.exception("Could not delete teacher")
        return False, "Не удалось удалить карточку."
    finally:
        session.close()
