"""
Модуль резервного копирования и восстановления базы данных (Use Case: Резервное копирование БД)
"""
import json
from datetime import datetime
from typing import Tuple
from database.connection import get_session
from database.models import Role, User, Department, Discipline, Teacher, TeacherWorkload


def create_backup(filepath: str) -> Tuple[bool, str]:
    """Экспорт всех таблиц БД в структурированный файл резервной копии JSON"""
    session = get_session()
    try:
        backup_data = {
            "created_at": datetime.now().isoformat(),
            "roles": [],
            "users": [],
            "departments": [],
            "disciplines": [],
            "teachers": [],
            "workloads": []
        }

        for r in session.query(Role).all():
            backup_data["roles"].append({"id": r.id, "name": r.name})

        for u in session.query(User).all():
            backup_data["users"].append({
                "id": u.id,
                "username": u.username,
                "password_hash": u.password_hash,
                "role_id": u.role_id
            })

        for d in session.query(Department).all():
            backup_data["departments"].append({
                "id": d.id,
                "name": d.name,
                "head_name": d.head_name
            })

        for disc in session.query(Discipline).all():
            backup_data["disciplines"].append({
                "id": disc.id,
                "code": disc.code,
                "name": disc.name,
                "department_id": disc.department_id
            })

        for t in session.query(Teacher).all():
            backup_data["teachers"].append({
                "id": t.id,
                "full_name": t.full_name,
                "birth_date": t.birth_date.isoformat() if t.birth_date else None,
                "phone": t.phone,
                "email": t.email,
                "qualification": t.qualification,
                "experience": t.experience,
                "department_id": t.department_id,
                "status": t.status,
                "photo_path": t.photo_path
            })

        for w in session.query(TeacherWorkload).all():
            backup_data["workloads"].append({
                "id": w.id,
                "academic_year": w.academic_year,
                "hours_lecture": w.hours_lecture,
                "hours_practice": w.hours_practice,
                "total_hours": w.total_hours,
                "teacher_id": w.teacher_id,
                "discipline_id": w.discipline_id
            })

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        return True, f"Резервная копия успешно создана:\n{filepath}"
    except Exception as e:
        return False, f"Ошибка создания резервной копии: {e}"
    finally:
        session.close()


def restore_backup(filepath: str) -> Tuple[bool, str]:
    """Восстановление базы данных из резервной копии"""
    session = get_session()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Очищаем таблицы в обратном порядке внешних ключей
        session.query(TeacherWorkload).delete()
        session.query(Teacher).delete()
        session.query(Discipline).delete()
        session.query(Department).delete()
        session.query(User).delete()
        session.query(Role).delete()
        session.commit()

        # Восстанавливаем роли
        for r_data in data.get("roles", []):
            session.add(Role(id=r_data["id"], name=r_data["name"]))
        session.commit()

        # Восстанавливаем пользователей
        for u_data in data.get("users", []):
            session.add(User(
                id=u_data["id"],
                username=u_data["username"],
                password_hash=u_data["password_hash"],
                role_id=u_data["role_id"]
            ))
        session.commit()

        # Восстанавливаем кафедры
        for d_data in data.get("departments", []):
            session.add(Department(
                id=d_data["id"],
                name=d_data["name"],
                head_name=d_data.get("head_name")
            ))
        session.commit()

        # Восстанавливаем дисциплины
        for disc_data in data.get("disciplines", []):
            session.add(Discipline(
                id=disc_data["id"],
                code=disc_data["code"],
                name=disc_data["name"],
                department_id=disc_data["department_id"]
            ))
        session.commit()

        # Восстанавливаем преподавателей
        from datetime import date
        for t_data in data.get("teachers", []):
            bdate = date.fromisoformat(t_data["birth_date"]) if t_data.get("birth_date") else None
            session.add(Teacher(
                id=t_data["id"],
                full_name=t_data["full_name"],
                birth_date=bdate,
                phone=t_data.get("phone"),
                email=t_data.get("email"),
                qualification=t_data.get("qualification"),
                experience=t_data.get("experience", 0),
                department_id=t_data["department_id"],
                status=t_data.get("status", "работает"),
                photo_path=t_data.get("photo_path")
            ))
        session.commit()

        # Восстанавливаем нагрузки
        for w_data in data.get("workloads", []):
            session.add(TeacherWorkload(
                id=w_data["id"],
                academic_year=w_data["academic_year"],
                hours_lecture=w_data.get("hours_lecture", 0),
                hours_practice=w_data.get("hours_practice", 0),
                total_hours=w_data.get("total_hours", 0),
                teacher_id=w_data["teacher_id"],
                discipline_id=w_data["discipline_id"]
            ))
        session.commit()

        return True, "База данных успешно восстановлена из резервной копии!"
    except Exception as e:
        session.rollback()
        return False, f"Ошибка восстановления базы данных: {e}"
    finally:
        session.close()
