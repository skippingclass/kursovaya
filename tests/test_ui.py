"""Запуск основных окон, маски и выборок Qt без рабочего дисплея."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
from pathlib import Path
from sqlalchemy import create_engine
from PyQt6.QtWidgets import QApplication
from database import connection
from services.auth_service import authenticate, logout
from services.workload_service import save_pool, add_workload


class UITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.previous = connection._engine
        connection._engine = create_engine(f"sqlite:///{self.folder.name}/test.db")
        connection.init_db()
        authenticate("admin", "admin123")
        self.widgets=[]

    def tearDown(self):
        for widget in self.widgets:
            widget.close()
        self.app.processEvents()
        connection._engine.dispose(); connection._engine=self.previous
        logout(); self.folder.cleanup()

    def test_main_window_all_tabs(self):
        from ui.main_window import MainWindow
        window=MainWindow(); self.widgets.append(window); window.show()
        for index in range(window.tabs.count()):
            window.tabs.setCurrentIndex(index); self.app.processEvents()
        self.assertEqual(window.tabs.count(),5)

    def test_dialogs_and_phone_mask(self):
        from ui.teacher_dialog import TeacherDialog
        from ui.workload_dialog import WorkloadDialog, PoolDialog
        from ui.teacher_card_dialog import TeacherCardDialog
        for dialog in [TeacherDialog(1),WorkloadDialog(1),PoolDialog(),TeacherCardDialog(1)]:
            self.widgets.append(dialog); dialog.show(); self.app.processEvents()
        teacher=self.widgets[0]
        teacher.input_phone.setText("+7 (701) 123-45-67")
        self.assertTrue(teacher.input_phone.hasAcceptableInput())
        teacher.input_phone.setText("+7 (701) 12")
        self.assertFalse(teacher.input_phone.hasAcceptableInput())
        self.assertTrue(teacher.input_last_name.text())

    def test_table_numbers_sort_numerically(self):
        from ui.workload_tab import make_table,fill_table
        from PyQt6.QtCore import Qt
        table=make_table(); self.widgets.append(table)
        fill_table(table,["Часы"],[[100],[9],[23]])
        table.sortItems(0,Qt.SortOrder.AscendingOrder)
        self.assertEqual([table.item(r,0).text() for r in range(3)],["9","23","100"])

    def test_report_filters_and_refresh_preserved(self):
        from ui.reports_tab import ReportsTab
        p=save_pool("2026-2027",2,"П-24-67Б",1,100,200,20)[2]
        add_workload("",1,1,50,100,pool_id=p)
        tab=ReportsTab(); self.widgets.append(tab)
        tab.combo_type.setCurrentIndex(1)
        tab.combo_year.setCurrentIndex(tab.combo_year.findData("2026-2027"))
        tab.combo_semester.setCurrentIndex(tab.combo_semester.findData(2))
        tab.combo_teacher.setCurrentIndex(tab.combo_teacher.findData(1))
        tab.load_filters(); tab.generate_report()
        self.assertEqual(tab.table.rowCount(),1)
        self.assertEqual(tab.combo_teacher.currentData(),1)
        self.assertEqual(tab.combo_year.currentData(),"2026-2027")

    def test_methodist_buttons_hidden(self):
        authenticate("methodist","methodist123")
        from ui.login_window import LoginWindow
        from ui.main_window import MainWindow
        from unittest.mock import patch
        window = MainWindow()
        login = LoginWindow()
        self.widgets.extend((window, login))
        self.assertFalse(window.db_menu.isEnabled())
        with patch("ui.login_window.DBSettingsDialog") as settings:
            login.open_db_settings()
            settings.assert_called_once_with(login, allow_backup=False)
        tab = window.tab_workload
        self.assertTrue(tab.btn_pool.isHidden())
        self.assertTrue(tab.btn_edit.isHidden())


if __name__ == '__main__': unittest.main()
