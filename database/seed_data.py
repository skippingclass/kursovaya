"""
Начальное заполнение базы данных (демо-данные колледжа «Astana Polytechnic»)
"""
from datetime import date
from sqlalchemy.orm import Session
from database.models import Role, User, Department, Discipline, Teacher, TeacherWorkload
from config import ROLE_ADMIN, ROLE_OPERATOR, ROLE_METHODIST
from services.passwords import hash_password


def seed_database(session: Session):
    # 1. Проверяем наличие ролей
    if session.query(Role).count() == 0:
        admin_role = Role(name=ROLE_ADMIN)
        operator_role = Role(name=ROLE_OPERATOR)
        methodist_role = Role(name=ROLE_METHODIST)
        session.add_all([admin_role, operator_role, methodist_role])
        session.commit()
    else:
        admin_role = session.query(Role).filter_by(name=ROLE_ADMIN).first()
        operator_role = session.query(Role).filter_by(name=ROLE_OPERATOR).first()
        methodist_role = session.query(Role).filter_by(name=ROLE_METHODIST).first()

    # 2. Пользователи
    if session.query(User).count() == 0:
        users = [
            User(username="admin", password_hash=hash_password("admin123"), role_id=admin_role.id),
            User(username="operator", password_hash=hash_password("operator123"), role_id=operator_role.id),
            User(username="methodist", password_hash=hash_password("methodist123"), role_id=methodist_role.id),
            User(username="zav_is", password_hash=hash_password("123456"), role_id=operator_role.id),
        ]
        session.add_all(users)
        session.commit()

    # 3. Кафедры
    if session.query(Department).count() == 0:
        dept_is = Department(name="Информационные системы и программирование", head_name="Султанова Алия Ергалиевна")
        dept_au = Department(name="Автоматизация и управление", head_name="Калиев Данияр Болатович")
        dept_st = Department(name="Строительство и архитектура", head_name="Омаров Нурлан Касымович")
        dept_ood = Department(name="Общеобразовательные дисциплины", head_name="Бекетова Гульнар Мухтаровна")
        dept_ek = Department(name="Экономика и учет", head_name="Мусина Зарина Толегеновна")
        session.add_all([dept_is, dept_au, dept_st, dept_ood, dept_ek])
        session.commit()

        # 4. Дисциплины
        disc_is1 = Discipline(code="ИС-101", name="Основы алгоритмизации и программирования", department_id=dept_is.id)
        disc_is2 = Discipline(code="ИС-203", name="Базы данных и СУБД PostgreSQL", department_id=dept_is.id)
        disc_is3 = Discipline(code="ИС-305", name="Разработка мобильных и веб-приложений", department_id=dept_is.id)
        disc_au1 = Discipline(code="АУ-102", name="Теория автоматического управления", department_id=dept_au.id)
        disc_au2 = Discipline(code="АУ-204", name="Микропроцессорные системы и датчики", department_id=dept_au.id)
        disc_st1 = Discipline(code="СТ-201", name="Архитектурное проектирование и BIM", department_id=dept_st.id)
        disc_ood1 = Discipline(code="ООД-01", name="Высшая математика", department_id=dept_ood.id)
        disc_ood2 = Discipline(code="ООД-02", name="Физика и электротехника", department_id=dept_ood.id)
        disc_ek1 = Discipline(code="ЭК-101", name="Бухгалтерский учет и налогообложение", department_id=dept_ek.id)

        session.add_all([disc_is1, disc_is2, disc_is3, disc_au1, disc_au2, disc_st1, disc_ood1, disc_ood2, disc_ek1])
        session.commit()

        # 5. Преподаватели
        t1 = Teacher(
            full_name="Ахметов Серик Канатович",
            birth_date=date(1982, 5, 14),
            phone="+7 (701) 234-56-78",
            email="s.akhmetov@polytech.kz",
            qualification="Педагог-исследователь",
            experience=16,
            department_id=dept_is.id,
            status="работает"
        )
        t2 = Teacher(
            full_name="Иванова Екатерина Сергеевна",
            birth_date=date(1988, 11, 23),
            phone="+7 (705) 345-67-89",
            email="e.ivanova@polytech.kz",
            qualification="Педагог-эксперт",
            experience=11,
            department_id=dept_is.id,
            status="работает"
        )
        t3 = Teacher(
            full_name="Касымов Бауыржан Аскарович",
            birth_date=date(1975, 3, 8),
            phone="+7 (777) 456-78-90",
            email="b.kassymov@polytech.kz",
            qualification="Высшая категория",
            experience=23,
            department_id=dept_au.id,
            status="работает"
        )
        t4 = Teacher(
            full_name="Смагулова Асем Маратовна",
            birth_date=date(1994, 9, 17),
            phone="+7 (771) 567-89-01",
            email="a.smagulova@polytech.kz",
            qualification="Педагог-модератор",
            experience=5,
            department_id=dept_is.id,
            status="работает"
        )
        t5 = Teacher(
            full_name="Жунусов Кайрат Темирланович",
            birth_date=date(1980, 1, 30),
            phone="+7 (702) 678-90-12",
            email="k.zhunussov@polytech.kz",
            qualification="Педагог-исследователь",
            experience=18,
            department_id=dept_st.id,
            status="работает"
        )
        t6 = Teacher(
            full_name="Петрова Ольга Дмитриевна",
            birth_date=date(1970, 7, 12),
            phone="+7 (707) 789-01-23",
            email="o.petrova@polytech.kz",
            qualification="Высшая категория",
            experience=28,
            department_id=dept_ood.id,
            status="работает"
        )
        t7 = Teacher(
            full_name="Нурланова Динара Сериковна",
            birth_date=date(1991, 12, 5),
            phone="+7 (747) 890-12-34",
            email="d.nurlanova@polytech.kz",
            qualification="Педагог-эксперт",
            experience=8,
            department_id=dept_ek.id,
            status="в отпуске"
        )
        session.add_all([t1, t2, t3, t4, t5, t6, t7])
        session.commit()

        # 6. Учебная нагрузка (TeacherWorkload)
        wl1 = TeacherWorkload(academic_year="2024-2025", hours_lecture=180, hours_practice=270, total_hours=450, teacher_id=t1.id, discipline_id=disc_is1.id)
        wl2 = TeacherWorkload(academic_year="2024-2025", hours_lecture=120, hours_practice=180, total_hours=300, teacher_id=t1.id, discipline_id=disc_is2.id)
        wl3 = TeacherWorkload(academic_year="2024-2025", hours_lecture=90, hours_practice=210, total_hours=300, teacher_id=t2.id, discipline_id=disc_is3.id)
        wl4 = TeacherWorkload(academic_year="2024-2025", hours_lecture=140, hours_practice=220, total_hours=360, teacher_id=t3.id, discipline_id=disc_au1.id)
        wl5 = TeacherWorkload(academic_year="2024-2025", hours_lecture=100, hours_practice=180, total_hours=280, teacher_id=t3.id, discipline_id=disc_au2.id)
        wl6 = TeacherWorkload(academic_year="2024-2025", hours_lecture=60, hours_practice=140, total_hours=200, teacher_id=t4.id, discipline_id=disc_is1.id)
        wl7 = TeacherWorkload(academic_year="2024-2025", hours_lecture=160, hours_practice=240, total_hours=400, teacher_id=t5.id, discipline_id=disc_st1.id)
        wl8 = TeacherWorkload(academic_year="2024-2025", hours_lecture=200, hours_practice=300, total_hours=500, teacher_id=t6.id, discipline_id=disc_ood1.id)
        wl9 = TeacherWorkload(academic_year="2024-2025", hours_lecture=120, hours_practice=180, total_hours=300, teacher_id=t7.id, discipline_id=disc_ek1.id)

        session.add_all([wl1, wl2, wl3, wl4, wl5, wl6, wl7, wl8, wl9])
        session.commit()
