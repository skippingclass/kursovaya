"""
Вкладка формирования и экспорта отчетов (ReportModule)
Топ-монохромный дизайн в стиле TuneCloud.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from services.department_service import get_departments
from services.workload_service import get_academic_years
from services.report_service import (
    get_teachers_report_data, get_workload_report_data,
    export_teachers_to_excel, export_workload_to_excel,
    export_teachers_to_pdf, export_workload_to_pdf
)


class ReportsTab(QWidget):
    status_updated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_filters()
        self.generate_report()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Панель параметров отчета (TuneCloud card)
        param_frame = QFrame()
        param_frame.setObjectName("panelCard")
        param_layout = QHBoxLayout(param_frame)
        param_layout.setContentsMargins(14, 12, 14, 12)
        param_layout.setSpacing(12)

        # Выбор типа отчета
        param_layout.addWidget(QLabel("Тип отчета:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems([
            "1. Отчет по кадровому составу преподавателей",
            "2. Ведомость распределения учебной нагрузки",
            "3. Сводная статистика по квалификационным категориям"
        ])
        self.combo_type.currentIndexChanged.connect(self.on_report_type_changed)
        param_layout.addWidget(self.combo_type, 2)

        # Фильтр по кафедре
        self.lbl_dept = QLabel("Кафедра:")
        self.combo_dept = QComboBox()
        param_layout.addWidget(self.lbl_dept)
        param_layout.addWidget(self.combo_dept, 2)

        # Фильтр по учебному году
        self.lbl_year = QLabel("Учебный год:")
        self.combo_year = QComboBox()
        param_layout.addWidget(self.lbl_year)
        param_layout.addWidget(self.combo_year, 1)

        # Кнопка сформировать
        btn_generate = QPushButton("🔄 Сформировать")
        btn_generate.setObjectName("btnPrimary")
        btn_generate.clicked.connect(self.generate_report)
        param_layout.addWidget(btn_generate)

        layout.addWidget(param_frame)

        # Панель экспорта
        export_layout = QHBoxLayout()
        self.lbl_report_title = QLabel()
        self.lbl_report_title.setStyleSheet("font-weight: 700; font-size: 14px; color: #ffffff;")
        export_layout.addWidget(self.lbl_report_title)
        export_layout.addStretch()

        btn_excel = QPushButton("📊 Экспорт в Excel (.xlsx)")
        btn_excel.setObjectName("btnSecondary")
        btn_excel.clicked.connect(self.export_excel)
        export_layout.addWidget(btn_excel)

        btn_pdf = QPushButton("📄 Экспорт в PDF (.pdf)")
        btn_pdf.setObjectName("btnSecondary")
        btn_pdf.clicked.connect(self.export_pdf)
        export_layout.addWidget(btn_pdf)

        layout.addLayout(export_layout)

        # Таблица предпросмотра отчета
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.on_report_type_changed()

    def load_filters(self):
        self.combo_dept.blockSignals(True)
        self.combo_dept.clear()
        self.combo_dept.addItem("Все кафедры", 0)
        departments = get_departments()
        for d in departments:
            self.combo_dept.addItem(d.name, d.id)
        self.combo_dept.blockSignals(False)

        self.combo_year.blockSignals(True)
        self.combo_year.clear()
        self.combo_year.addItem("Все годы")
        years = get_academic_years()
        self.combo_year.addItems(years)
        self.combo_year.blockSignals(False)

    def on_report_type_changed(self):
        idx = self.combo_type.currentIndex()
        if idx == 0:
            self.lbl_dept.setVisible(True)
            self.combo_dept.setVisible(True)
            self.lbl_year.setVisible(False)
            self.combo_year.setVisible(False)
        elif idx == 1:
            self.lbl_dept.setVisible(True)
            self.combo_dept.setVisible(True)
            self.lbl_year.setVisible(True)
            self.combo_year.setVisible(True)
        else:
            self.lbl_dept.setVisible(False)
            self.combo_dept.setVisible(False)
            self.lbl_year.setVisible(False)
            self.combo_year.setVisible(False)

        self.generate_report()

    def generate_report(self):
        idx = self.combo_type.currentIndex()
        dept_id = self.combo_dept.currentData()
        year = self.combo_year.currentText()
        if year == "Все годы":
            year = None

        if idx == 0:
            self.generate_teachers_report(dept_id)
        elif idx == 1:
            self.generate_workload_report(year, dept_id)
        else:
            self.generate_stats_report()

    def generate_teachers_report(self, dept_id: int):
        self.lbl_report_title.setText("Отчет по кадровому составу преподавателей колледжа")
        data = get_teachers_report_data(dept_id)

        headers = ["№", "ФИО преподавателя", "Кафедра / Отделение", "Квалификация", "Стаж", "Телефон", "E-mail", "Статус", "Всего часов"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(item["num"])))
            self.table.setItem(row, 1, QTableWidgetItem(item["full_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["department"]))
            self.table.setItem(row, 3, QTableWidgetItem(item["qualification"]))

            exp_item = QTableWidgetItem(item["experience"])
            exp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, exp_item)

            self.table.setItem(row, 5, QTableWidgetItem(item["phone"]))
            self.table.setItem(row, 6, QTableWidgetItem(item["email"]))

            st_item = QTableWidgetItem(item["status"])
            st_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, st_item)

            hrs_item = QTableWidgetItem(str(item["total_hours"]))
            hrs_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 8, hrs_item)

        self.status_updated.emit(f"Сформирован отчет по преподавателям: {len(data)} записей")

    def generate_workload_report(self, year: str, dept_id: int):
        year_str = f" за {year} уч. год" if year else ""
        self.lbl_report_title.setText(f"Ведомость распределения учебной нагрузки{year_str}")
        data = get_workload_report_data(year, dept_id)

        headers = ["№", "Учебный год", "Преподаватель", "Кафедра", "Код", "Дисциплина", "Лекции (ч)", "Практики (ч)", "Всего (ч)"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(item["num"])))
            self.table.setItem(row, 1, QTableWidgetItem(item["academic_year"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["teacher"]))
            self.table.setItem(row, 3, QTableWidgetItem(item["department"]))
            self.table.setItem(row, 4, QTableWidgetItem(item["discipline_code"]))
            self.table.setItem(row, 5, QTableWidgetItem(item["discipline_name"]))

            lec = QTableWidgetItem(str(item["hours_lecture"]))
            lec.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, lec)

            prac = QTableWidgetItem(str(item["hours_practice"]))
            prac.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, prac)

            tot = QTableWidgetItem(str(item["total_hours"]))
            tot.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 8, tot)

        self.status_updated.emit(f"Сформирована ведомость нагрузки: {len(data)} записей")

    def generate_stats_report(self):
        self.lbl_report_title.setText("Сводная статистика по кафедрам и квалификационным категориям")
        from services.teacher_service import get_teachers
        teachers = get_teachers()
        departments = get_departments()

        headers = ["Кафедра", "Всего преп.", "Исследователи", "Эксперты", "Модераторы", "Высшая кат.", "Первая/Вторая", "Специалисты", "Суммарная нагрузка (ч)"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        self.table.setRowCount(len(departments) + 1)

        total_teachers = 0
        total_hours_all = 0

        for row, d in enumerate(departments):
            dept_teachers = [t for t in teachers if t.department_id == d.id]
            cnt = len(dept_teachers)
            total_teachers += cnt

            issled = sum(1 for t in dept_teachers if t.qualification == "Педагог-исследователь")
            expert = sum(1 for t in dept_teachers if t.qualification == "Педагог-эксперт")
            moder = sum(1 for t in dept_teachers if t.qualification == "Педагог-модератор")
            vyssh = sum(1 for t in dept_teachers if t.qualification == "Высшая категория")
            perv_vtor = sum(1 for t in dept_teachers if t.qualification in ("Первая категория", "Вторая категория"))
            spec = sum(1 for t in dept_teachers if t.qualification == "Специалист" or not t.qualification)
            hrs = sum(t.total_hours for t in dept_teachers)
            total_hours_all += hrs

            self.table.setItem(row, 0, QTableWidgetItem(d.name))
            self.table.setItem(row, 1, QTableWidgetItem(str(cnt)))
            self.table.setItem(row, 2, QTableWidgetItem(str(issled)))
            self.table.setItem(row, 3, QTableWidgetItem(str(expert)))
            self.table.setItem(row, 4, QTableWidgetItem(str(moder)))
            self.table.setItem(row, 5, QTableWidgetItem(str(vyssh)))
            self.table.setItem(row, 6, QTableWidgetItem(str(perv_vtor)))
            self.table.setItem(row, 7, QTableWidgetItem(str(spec)))
            self.table.setItem(row, 8, QTableWidgetItem(str(hrs)))

            for col in range(1, 9):
                it = self.table.item(row, col)
                if it:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Итоговая строка
        last_row = len(departments)
        itog_item = QTableWidgetItem("ИТОГО ПО КОЛЛЕДЖУ:")
        self.table.setItem(last_row, 0, itog_item)

        t_cnt_item = QTableWidgetItem(str(total_teachers))
        t_cnt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(last_row, 1, t_cnt_item)

        for col in range(2, 8):
            s = sum(int(self.table.item(r, col).text()) for r in range(len(departments)))
            it = QTableWidgetItem(str(s))
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(last_row, col, it)

        h_all_item = QTableWidgetItem(str(total_hours_all))
        h_all_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(last_row, 8, h_all_item)

        self.status_updated.emit("Сформирована сводная статистика по колледжу")

    def export_excel(self):
        idx = self.combo_type.currentIndex()
        dept_id = self.combo_dept.currentData()
        year = self.combo_year.currentText()
        if year == "Все годы":
            year = None

        if idx == 0:
            filepath, _ = QFileDialog.getSaveFileName(self, "Экспорт в Excel", "kadry_otchet.xlsx", "Excel (*.xlsx)")
            if filepath:
                ok, msg = export_teachers_to_excel(filepath, department_id=dept_id)
                if ok:
                    QMessageBox.information(self, "Успех", msg)
                else:
                    QMessageBox.critical(self, "Ошибка", msg)
        elif idx == 1:
            filepath, _ = QFileDialog.getSaveFileName(self, "Экспорт в Excel", "nagruzka_otchet.xlsx", "Excel (*.xlsx)")
            if filepath:
                ok, msg = export_workload_to_excel(filepath, academic_year=year, department_id=dept_id)
                if ok:
                    QMessageBox.information(self, "Успех", msg)
                else:
                    QMessageBox.critical(self, "Ошибка", msg)
        else:
            filepath, _ = QFileDialog.getSaveFileName(self, "Экспорт в Excel", "statistika_otchet.xlsx", "Excel (*.xlsx)")
            if filepath:
                ok, msg = export_teachers_to_excel(filepath)
                if ok:
                    QMessageBox.information(self, "Успех", msg)
                else:
                    QMessageBox.critical(self, "Ошибка", msg)

    def export_pdf(self):
        idx = self.combo_type.currentIndex()
        dept_id = self.combo_dept.currentData()
        year = self.combo_year.currentText()
        if year == "Все годы":
            year = None

        if idx == 1:
            filepath, _ = QFileDialog.getSaveFileName(self, "Экспорт ведомости в PDF", "nagruzka_otchet.pdf", "PDF (*.pdf)")
            if filepath:
                ok, msg = export_workload_to_pdf(filepath, academic_year=year, department_id=dept_id)
                if ok:
                    QMessageBox.information(self, "Успех", msg)
                else:
                    QMessageBox.critical(self, "Ошибка", msg)
        else:
            filepath, _ = QFileDialog.getSaveFileName(self, "Экспорт в PDF", "kadry_otchet.pdf", "PDF (*.pdf)")
            if filepath:
                ok, msg = export_teachers_to_pdf(filepath, department_id=dept_id)
                if ok:
                    QMessageBox.information(self, "Успех", msg)
                else:
                    QMessageBox.critical(self, "Ошибка", msg)
