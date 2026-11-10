"""
SQLAlchemy ORM модели базы данных.
Полностью соответствует ER-диаграмме проекта:
Roles, Users, Departments, Teachers, Disciplines, TeacherWorkload.
"""
from datetime import date
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Date, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Role(Base):
    """Таблица Roles (Справочник ролей пользователей)"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

    users = relationship("User", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"


class User(Base):
    """Таблица Users (Учетные записи сотрудников)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    role = relationship("Role", back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role_id={self.role_id})>"


class Department(Base):
    """Таблица Departments (Кафедры и отделения колледжа)"""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    head_name = Column(String(200), nullable=True)

    teachers = relationship("Teacher", back_populates="department", cascade="all, delete-orphan")
    disciplines = relationship("Discipline", back_populates="department", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}', head='{self.head_name}')>"


class Teacher(Base):
    """Таблица Teachers (Личные данные преподавателей)"""
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(200), nullable=False)
    birth_date = Column(Date, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    qualification = Column(String(100), nullable=True)  # Высшая категория, Педагог-эксперт и т.д.
    experience = Column(Integer, default=0)              # Стаж работы в годах
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    status = Column(String(50), default="работает")     # работает, в отпуске, уволен
    photo_path = Column(String(300), nullable=True)

    department = relationship("Department", back_populates="teachers")
    workloads = relationship("TeacherWorkload", back_populates="teacher", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Teacher(id={self.id}, name='{self.full_name}', dept_id={self.department_id})>"

    @property
    def total_hours(self) -> int:
        return sum(w.total_hours for w in self.workloads) if self.workloads else 0


class Discipline(Base):
    """Таблица Disciplines (Учебные дисциплины)"""
    __tablename__ = "disciplines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    department = relationship("Department", back_populates="disciplines")
    workloads = relationship("TeacherWorkload", back_populates="discipline", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Discipline(id={self.id}, code='{self.code}', name='{self.name}')>"


class TeacherWorkload(Base):
    """Таблица TeacherWorkload (Распределение учебной нагрузки)"""
    __tablename__ = "teacher_workload"

    id = Column(Integer, primary_key=True, autoincrement=True)
    academic_year = Column(String(20), nullable=False)  # 2024-2025
    hours_lecture = Column(Integer, default=0)
    hours_practice = Column(Integer, default=0)
    total_hours = Column(Integer, default=0)

    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False)

    teacher = relationship("Teacher", back_populates="workloads")
    discipline = relationship("Discipline", back_populates="workloads")

    def __repr__(self):
        return f"<TeacherWorkload(id={self.id}, teacher_id={self.teacher_id}, disc_id={self.discipline_id}, total={self.total_hours})>"
