"""Проверки бизнес-сценариев на временных БД; рабочая база не изменяется."""
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import database.connection as connection
from database.models import Base, Department, Discipline, Teacher, TeacherWorkload, WorkloadPool
from services.teacher_service import add_teacher, update_teacher, get_teachers, get_teacher_by_id, delete_teacher
from services.workload_service import (save_pool, get_pools, add_workload, update_workload, delete_workload,
                                      get_workloads, delete_pool)
from database.backup import create_backup, restore_backup


class SystemTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.previous = connection._engine
        connection._engine = create_engine(f"sqlite:///{self.root / 'test.db'}")
        Base.metadata.create_all(connection._engine)
        with Session(connection._engine) as s:
            s.add(Department(id=1, name="Программирование"))
            s.flush()
            s.add(Discipline(id=1, name="Алгоритмизация", code="ИС-1", department_id=1))
            s.commit()
        self.t1 = self.teacher("Евполов", "Владислав", "Игоревич", experience=9)
        self.t2 = self.teacher("Петрова", "Мария", "Олеговна", experience=23)

    def tearDown(self):
        connection._engine.dispose()
        connection._engine = self.previous
        self.folder.cleanup()

    def teacher(self, last, first, middle="", **extra):
        result = add_teacher(dict(last_name=last, first_name=first, middle_name=middle, department_id=1, **extra))
        self.assertTrue(result[0], result[1])
        return result[2]

    def pool(self, group="П-24-67Б", semester=1, lecture=400, practice=600, year="2026-2027"):
        result = save_pool(year, semester, group, 1, lecture, practice, 20)
        self.assertTrue(result[0], result[1])
        return result[2]

    def assign(self, pool, teacher=None, lecture=50, practice=100):
        result = add_workload("", teacher or self.t1, 1, lecture, practice, pool_id=pool)
        self.assertTrue(result[0], result[1])
        return result[2]

    def test_separate_names(self):
        teacher = get_teacher_by_id(self.t1)
        self.assertEqual((teacher.last_name, teacher.first_name, teacher.middle_name), ("Евполов", "Владислав", "Игоревич"))
        self.assertEqual(teacher.full_name, "Евполов Владислав Игоревич")

    def test_normalized_exact_duplicate(self):
        ok, _, _ = add_teacher(dict(full_name="  ЕВПОЛОВ   Владислав Игоревич ", department_id=1))
        self.assertFalse(ok)

    def test_typo_requires_explicit_override(self):
        data = dict(full_name="Евпалов Владислав Игоревич", department_id=1)
        self.assertFalse(add_teacher(data)[0])
        self.assertTrue(add_teacher(data, allow_similar=True)[0])

    def test_contact_duplicate(self):
        t = self.teacher("Сидоров", "Олег", phone="+7 (701) 123-45-67", email="oleg@test.kz")
        self.assertFalse(add_teacher(dict(full_name="Смирнов Антон", department_id=1, phone="87011234567"))[0])
        self.assertFalse(add_teacher(dict(full_name="Ким Сергей", department_id=1, email="OLEG@test.kz"))[0])

    def test_teacher_validation(self):
        for extra in [dict(first_name=""), dict(email="bad@"), dict(phone="123"), dict(last_name="Тест123"), dict(experience=71)]:
            data = dict(last_name="Ковалев", first_name="Антон", department_id=1)
            data.update(extra)
            self.assertFalse(add_teacher(data)[0], data)

    def test_update_own_card_not_duplicate(self):
        self.assertTrue(update_teacher(self.t1, dict(last_name="Евполов", first_name="Владислав", middle_name="Игоревич", department_id=1))[0])

    def test_cyrillic_search(self):
        self.assertEqual([t.id for t in get_teachers(search_text="ЕВПОЛОВ")], [self.t1])

    def test_numeric_sort(self):
        self.teacher("Ким", "Антон", experience=10)
        rows = get_teachers(sort_by="experience")
        self.assertEqual([t.experience for t in rows], [9, 10, 23])
        self.assertEqual([t.experience for t in get_teachers(sort_by="experience", descending=True)], [23, 10, 9])

    def test_pool_validation_and_duplicate(self):
        self.pool()
        self.assertFalse(save_pool("2026-2027", 1, "п-24-67б", 1, 5, 5)[0])
        for year, sem, l, p in [("2026-2028",1,5,5),("bad",1,5,5),("2026-2027",0,5,5),("2026-2027",1,-1,5),("2026-2027",1,0,0)]:
            self.assertFalse(save_pool(year, sem, "Г-1", 1, l, p)[0])

    def test_remaining_by_type_and_week(self):
        p = self.pool()
        self.assign(p)
        pool = get_pools()[0]
        self.assertEqual((pool.available_lecture, pool.available_practice), (350, 500))
        self.assertEqual(get_workloads()[0].hours_per_week, 7.5)

    def test_overallocation_rejected(self):
        p = self.pool(lecture=60, practice=100)
        self.assign(p)
        self.assertFalse(add_workload("",self.t2,1,11,0,pool_id=p)[0])
        self.assertFalse(add_workload("",self.t2,1,0,1,pool_id=p)[0])
        self.assertEqual(len(get_workloads()),1)

    def test_missing_pool_rejected(self):
        self.assertFalse(add_workload("2026-2027", self.t1, 1, 10, 10)[0])

    def test_duplicate_assignment_and_multiple_groups(self):
        p = self.pool()
        self.assign(p)
        self.assertFalse(add_workload("",self.t1,1,10,10,pool_id=p)[0])
        p2 = self.pool(group="П-25-67Б")
        self.assign(p2)
        self.assertEqual(len(get_workloads(teacher_id=self.t1)),2)

    def test_reduction_returns_hours(self):
        p = self.pool()
        w = self.assign(p)
        self.assertTrue(update_workload(w,"",self.t1,1,20,30,pool_id=p)[0])
        self.assertEqual((get_pools()[0].available_lecture,get_pools()[0].available_practice),(380,570))

    def test_failed_edit_keeps_both_balances(self):
        p, p2 = self.pool(), self.pool(group="Г-2",lecture=5,practice=5)
        w = self.assign(p)
        self.assertFalse(update_workload(w,"",self.t1,1,20,30,pool_id=p2)[0])
        pools = {x.id:x for x in get_pools()}
        self.assertEqual((pools[p].available_lecture,pools[p2].available_lecture),(350,5))
        self.assertEqual(get_workloads()[0].pool_id,p)

    def test_transfer_between_pools(self):
        p, p2 = self.pool(), self.pool(group="Г-2",semester=2)
        w = self.assign(p)
        self.assertTrue(update_workload(w,"",self.t2,1,50,100,pool_id=p2)[0])
        pools = {x.id:x for x in get_pools()}
        self.assertEqual((pools[p].available_lecture,pools[p2].available_lecture),(400,350))
        self.assertEqual(get_workloads()[0].semester,2)

    def test_delete_assignment_returns_hours(self):
        p = self.pool()
        self.assertTrue(delete_workload(self.assign(p))[0])
        self.assertEqual(get_pools()[0].available_practice,600)

    def test_delete_teacher_returns_hours(self):
        p = self.pool()
        self.assign(p)
        self.assertTrue(delete_teacher(self.t1)[0])
        self.assertEqual(get_pools()[0].available_lecture,400)

    def test_plan_cannot_shrink_below_assignments(self):
        p = self.pool()
        self.assign(p)
        self.assertFalse(save_pool("2026-2027",1,"П-24-67Б",1,49,600,20,p)[0])
        self.assertFalse(delete_pool(p)[0])
        self.assertTrue(save_pool("2026-2027",2,"П-24-67Б",1,100,200,10,p)[0])
        w = get_workloads()[0]
        self.assertEqual((w.semester,w.hours_per_week),(2,15))

    def test_rate_is_per_year_and_720_boundary(self):
        p = self.pool(lecture=1000,practice=1000)
        self.assign(p,self.t1,360,360)
        self.assign(p,self.t2,360,361)
        p2=self.pool(year="2025-2026")
        self.assign(p2,self.t1,200,200)
        self.assertEqual([t.id for t in get_teachers(academic_year="2026-2027",rate_filter="equal")],[self.t1])
        self.assertEqual([t.id for t in get_teachers(academic_year="2026-2027",rate_filter="above")],[self.t2])
        self.assertEqual(len(get_teachers(academic_year="2024-2025",rate_filter="below")),2)

    def test_filters_semester_teacher(self):
        p1,p2=self.pool(),self.pool(semester=2)
        self.assign(p1,self.t1); self.assign(p2,self.t2)
        from services.report_service import get_workload_report_data
        rows=get_workload_report_data("2026-2027",1,2,self.t2)
        self.assertEqual(len(rows),1)
        self.assertEqual((rows[0]["semester"],rows[0]["teacher"]),("2","Петрова Мария Олеговна"))

    def test_backup_round_trip_and_atomic_rollback(self):
        p = self.pool(); self.assign(p)
        file=self.root/'backup.json'
        self.assertTrue(create_backup(file)[0])
        self.assertTrue(restore_backup(file)[0])
        self.assertEqual(get_pools()[0].available_lecture,350)
        data=json.loads(file.read_text()); data['workloads'][0]['teacher_id']=9999
        file.write_text(json.dumps(data))
        self.assertFalse(restore_backup(file)[0])
        self.assertEqual(len(get_workloads()),1)
        self.assertEqual(get_pools()[0].available_lecture,350)

    def test_legacy_backup_preserved(self):
        p=self.pool(); self.assign(p)
        file=self.root/'backup.json'; create_backup(file)
        data=json.loads(file.read_text()); data.pop('pools'); data.pop('version')
        for w in data['workloads']:
            w.pop('pool_id'); w.pop('semester')
        for t in data['teachers']:
            for k in ['last_name','first_name','middle_name']: t.pop(k)
        file.write_text(json.dumps(data))
        self.assertTrue(restore_backup(file)[0])
        self.assertEqual(get_workloads()[0].semester,0)
        self.assertEqual(get_pools()[0].available_lecture,0)
        self.assertEqual(get_teacher_by_id(self.t1).last_name,'Евполов')

    def test_concurrent_capacity(self):
        p=self.pool(lecture=50,practice=100)
        def allocate(t): return add_workload("",t,1,50,100,pool_id=p)[0]
        with ThreadPoolExecutor(max_workers=2) as executor:
            results=list(executor.map(allocate,[self.t1,self.t2]))
        self.assertEqual(sum(results),1)
        self.assertEqual(get_pools()[0].available_lecture,0)

    def test_excel_pdf_export_matches_filters(self):
        from services.report_service import export_workload_to_excel,export_workload_to_pdf
        from openpyxl import load_workbook
        from pypdf import PdfReader
        p=self.pool(semester=2); self.assign(p,self.t2)
        self.assign(self.pool(),self.t1)
        xlsx,pdf=self.root/'report.xlsx',self.root/'report.pdf'
        kwargs=dict(academic_year="2026-2027",semester=2,teacher_id=self.t2)
        self.assertTrue(export_workload_to_excel(xlsx,**kwargs)[0])
        ws=load_workbook(xlsx).active
        self.assertEqual([ws.cell(6,c).value for c in [2,3,4,5,11,12]],['2026-2027','2','П-24-67Б','Петрова Мария Олеговна',150,7.5])
        self.assertEqual(ws.cell(7,11).value,150)
        result=export_workload_to_pdf(pdf,**kwargs)
        self.assertTrue(result[0],result[1])
        text=' '.join(page.extract_text() for page in PdfReader(pdf).pages)
        self.assertIn('Петрова',text); self.assertNotIn('Евполов',text); self.assertIn('2026-2027',text)

    def test_existing_database_migration_is_idempotent(self):
        copy = self.root / "legacy.db"
        connection._engine.dispose()
        connection._engine = create_engine(f"sqlite:///{copy}")
        legacy_tables = {"teachers", "teacher_workload", "workload_pools"}
        Base.metadata.create_all(connection._engine, tables=[
            table for table in Base.metadata.sorted_tables if table.name not in legacy_tables])
        with sqlite3.connect(copy) as db:
            db.executescript("""
                CREATE TABLE teachers (
                    id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, birth_date DATE, phone TEXT,
                    email TEXT, qualification TEXT, experience INTEGER, department_id INTEGER NOT NULL,
                    status TEXT, photo_path TEXT
                );
                CREATE TABLE teacher_workload (
                    id INTEGER PRIMARY KEY, academic_year TEXT NOT NULL, hours_lecture INTEGER,
                    hours_practice INTEGER, total_hours INTEGER, teacher_id INTEGER NOT NULL,
                    discipline_id INTEGER NOT NULL
                );
                INSERT INTO departments (id, name) VALUES (1, 'Информатика');
                INSERT INTO disciplines (id, code, name, department_id) VALUES (1, 'ИС-1', 'Базы данных', 1);
                INSERT INTO teachers (id, full_name, department_id) VALUES (7, 'Иванова Анна Олеговна', 1);
                INSERT INTO teacher_workload VALUES (11, '2025-2026', 20, 30, 50, 7, 1);
            """)
            before = db.execute("SELECT id, full_name FROM teachers ORDER BY id").fetchall()
            hours = db.execute("SELECT id, total_hours FROM teacher_workload ORDER BY id").fetchall()
        connection.init_db()
        connection.init_db()
        self.assertEqual([(t.id,t.full_name) for t in sorted(get_teachers(),key=lambda t:t.id)],before)
        self.assertEqual([(w.id,w.total_hours) for w in sorted(get_workloads(),key=lambda w:w.id)],hours)
        self.assertEqual(len(get_pools()),len(hours))
        self.assertTrue(copy.with_name(copy.name+'.before-v2.bak').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
