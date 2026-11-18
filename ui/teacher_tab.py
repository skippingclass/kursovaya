"""
Вкладка управления преподавателями (TeacherModule, SearchModule)
Топ-монохромный дизайн в стиле TuneCloud.
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from services.teacher_service import get_teachers, delete_teacher
from services.department_service import get_departments
from services.auth_service import is_operator
from services.report_service import export_teachers_to_excel, export_teachers_to_pdf
from ui.teacher_dialog import TeacherDialog
from ui.teacher_card_dialog import TeacherCardDialog
from services.workload_service import get_academic_years
from datetime import date


class TeacherTab(QWidget):
    status_updated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_filters()
        self.refresh_table()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # 1. Панель поиска и фильтрации (TuneCloud card)
        filter_frame = QFrame()
        filter_frame.setObjectName("panelCard")
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(14, 12, 14, 12)
        filter_layout.setSpacing(10)

        # Верхняя строка: Поиск по тексту + кнопка сброса
        search_row = QHBoxLayout()
        search_row.setSpacing(10)

        search_lbl = QLabel("Поиск:")
        search_lbl.setStyleSheet("font-weight: 700; color: #ffffff;")
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Поиск по ФИО, телефону или e-mail преподавателя...")
        self.input_search.setClearButtonEnabled(True)
        self.input_search.textChanged.connect(self.refresh_table)
        search_row.addWidget(search_lbl)
        search_row.addWidget(self.input_search, 3)

        btn_reset = QPushButton("Сбросить")
        btn_reset.setObjectName("btnSecondary")
        btn_reset.clicked.connect(self.reset_filters)
        search_row.addWidget(btn_reset)

        filter_layout.addLayout(search_row)

        # Нижняя строка: Фильтры
        filters_row = QHBoxLayout()
        filters_row.setSpacing(10)

        # Кафедра
        filters_row.addWidget(QLabel("Кафедра:"))
        self.combo_dept = QComboBox()
        self.combo_dept.currentIndexChanged.connect(self.refresh_table)
        filters_row.addWidget(self.combo_dept, 2)

        # Категория
        filters_row.addWidget(QLabel("Категория:"))
        self.combo_qual = QComboBox()
        self.combo_qual.addItems([
            "Все категории",
            "Педагог-исследователь",
            "Педагог-эксперт",
            "Педагог-модератор",
            "Высшая категория",
            "Первая категория",
            "Вторая категория",
            "Специалист"
        ])
        self.combo_qual.currentIndexChanged.connect(self.refresh_table)
        filters_row.addWidget(self.combo_qual, 1)

        # Статус
        filters_row.addWidget(QLabel("Статус:"))
        self.combo_status = QComboBox()
        self.combo_status.addItems(["Все статусы", "работает", "в отпуске", "уволен"])
        self.combo_status.currentIndexChanged.connect(self.refresh_table)
        filters_row.addWidget(self.combo_status, 1)

        # Стаж
        filters_row.addWidget(QLabel("Стаж от:"))
        self.spin_min_exp = QSpinBox()
        self.spin_min_exp.setRange(0, 70)
        self.spin_min_exp.setValue(0)
        self.spin_min_exp.valueChanged.connect(self.refresh_table)
        filters_row.addWidget(self.spin_min_exp)

        filters_row.addWidget(QLabel("до:"))
        self.spin_max_exp = QSpinBox()
        self.spin_max_exp.setRange(0, 70)
        self.spin_max_exp.setValue(70)
        self.spin_max_exp.valueChanged.connect(self.refresh_table)
        filters_row.addWidget(self.spin_max_exp)

        filter_layout.addLayout(filters_row)
        sort_row = QHBoxLayout()
        self.combo_year = QComboBox()
        self.combo_year.addItems(get_academic_years())
        current = date.today().year - (date.today().month < 9)
        self.combo_year.setCurrentText(f"{current}-{current+1}")
        self.combo_rate = QComboBox()
        for label, value in [("Любая нагрузка", None), ("Меньше ставки (< 720 ч.)", "below"),
                             ("Ровно ставка (720 ч.)", "equal"), ("Больше ставки (> 720 ч.)", "above")]:
            self.combo_rate.addItem(label, value)
        self.combo_sort = QComboBox()
        for label, value in [("ФИО", "full_name"), ("Стаж", "experience"), ("Часы за год", "total_hours"), ("Кафедра", "department")]:
            self.combo_sort.addItem(label, value)
        self.combo_direction = QComboBox()
        self.combo_direction.addItem("По возрастанию", False)
        self.combo_direction.addItem("По убыванию", True)
        for label, combo in [("Нагрузка за год", self.combo_year), ("Ставка", self.combo_rate),
                             ("Сортировать по", self.combo_sort), ("Порядок", self.combo_direction)]:
            sort_row.addWidget(QLabel(label))
            sort_row.addWidget(combo, 1)
            combo.currentIndexChanged.connect(self.refresh_table)
        filter_layout.addLayout(sort_row)
        main_layout.addWidget(filter_frame)

        # 2. Панель действий (Монохромные кнопки)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.btn_add = QPushButton("➕ Добавить преподавателя")
        self.btn_add.setObjectName("btnPrimary")
        self.btn_add.clicked.connect(self.on_add_teacher)
        actions_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton("✏ Редактировать")
        self.btn_edit.clicked.connect(self.on_edit_teacher)
        actions_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("🗑 Удалить")
        self.btn_delete.setObjectName("btnDanger")
        self.btn_delete.clicked.connect(self.on_delete_teacher)
        actions_layout.addWidget(self.btn_delete)

        self.btn_card = QPushButton("👤 Карточка")
        self.btn_card.clicked.connect(self.on_view_card)
        actions_layout.addWidget(self.btn_card)

        actions_layout.addStretch()

        btn_excel = QPushButton("📊 Excel (.xlsx)")
        btn_excel.setObjectName("btnSecondary")
        btn_excel.clicked.connect(self.on_export_excel)
        actions_layout.addWidget(btn_excel)

        btn_pdf = QPushButton("📄 PDF (.pdf)")
        btn_pdf.setObjectName("btnSecondary")
        btn_pdf.clicked.connect(self.on_export_pdf)
        actions_layout.addWidget(btn_pdf)

        main_layout.addLayout(actions_layout)

        # 3. Таблица преподавателей
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        headers = ["ID", "ФИО преподавателя", "Кафедра / Отделение", "Квалификация", "Стаж", "Телефон", "E-mail", "Статус", "Часы за выбранный год"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.on_view_card)
        main_layout.addWidget(self.table)

        self.apply_role_permissions()

    def apply_role_permissions(self):
        can_edit = is_operator()
        self.btn_add.setVisible(can_edit)
        self.btn_edit.setVisible(can_edit)
        self.btn_delete.setVisible(can_edit)

    def load_filters(self):
        selected_department = self.combo_dept.currentData()
        selected_year = self.combo_year.currentText()
        self.combo_year.blockSignals(True)
        self.combo_year.clear()
        self.combo_year.addItems(get_academic_years())
        self.combo_year.setCurrentText(selected_year)
        self.combo_year.blockSignals(False)
        self.combo_dept.blockSignals(True)
        self.combo_dept.clear()
        self.combo_dept.addItem("Все кафедры", 0)
        departments = get_departments()
        for dept in departments:
            self.combo_dept.addItem(dept.name, dept.id)
        self.combo_dept.setCurrentIndex(max(0, self.combo_dept.findData(selected_department)))
        self.combo_dept.blockSignals(False)

    def reset_filters(self):
        self.input_search.clear()
        self.combo_dept.setCurrentIndex(0)
        self.combo_qual.setCurrentIndex(0)
        self.combo_status.setCurrentIndex(0)
        self.spin_min_exp.setValue(0)
        self.spin_max_exp.setValue(70)
        self.combo_rate.setCurrentIndex(0)
        self.combo_sort.setCurrentIndex(0)
        self.combo_direction.setCurrentIndex(0)
        self.refresh_table()

    def get_selected_teacher_id(self) -> Optional[int]:
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        id_item = self.table.item(row, 0)
        if id_item:
            return int(id_item.text())
        return None

    def refresh_table(self):
        search_text = self.input_search.text().strip()
        dept_id = self.combo_dept.currentData()
        qualification = self.combo_qual.currentText()
        status = self.combo_status.currentText()
        min_exp = self.spin_min_exp.value()
        max_exp = self.spin_max_exp.value()

        teachers = get_teachers(
            search_text=search_text,
            department_id=dept_id,
            qualification=qualification,
            status=status,
            min_exp=min_exp,
            max_exp=max_exp,
            sort_by=self.combo_sort.currentData(),
            descending=self.combo_direction.currentData(),
            academic_year=self.combo_year.currentText(),
            rate_filter=self.combo_rate.currentData()
        )

        self.table.setRowCount(len(teachers))
        for row, t in enumerate(teachers):
            self.table.setItem(row, 0, QTableWidgetItem(str(t.id)))
            self.table.setItem(row, 1, QTableWidgetItem(t.full_name))
            dept_name = t.department.name if t.department else "-"
            self.table.setItem(row, 2, QTableWidgetItem(dept_name))
            self.table.setItem(row, 3, QTableWidgetItem(t.qualification or "-"))

            exp_item = QTableWidgetItem(f"{t.experience} лет")
            exp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, exp_item)

            self.table.setItem(row, 5, QTableWidgetItem(t.phone or "-"))
            self.table.setItem(row, 6, QTableWidgetItem(t.email or "-"))

            st_item = QTableWidgetItem(t.status or "работает")
            st_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, st_item)

            hrs_item = QTableWidgetItem(str(t.period_hours))
            hrs_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 8, hrs_item)

        for row in range(self.table.rowCount()):
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                item.setToolTip(item.text())
        self.status_updated.emit(f"Отображено преподавателей: {len(teachers)}")

    def on_add_teacher(self):
        dlg = TeacherDialog(parent=self)
        if dlg.exec():
            self.refresh_table()

    def on_edit_teacher(self):
        tid = self.get_selected_teacher_id()
        if not tid:
            QMessageBox.information(self, "Выбор преподавателя", "Пожалуйста, выберите преподавателя в таблице для редактирования!")
            return
        dlg = TeacherDialog(teacher_id=tid, parent=self)
        if dlg.exec():
            self.refresh_table()

    def on_delete_teacher(self):
        tid = self.get_selected_teacher_id()
        if not tid:
            QMessageBox.information(self, "Выбор преподавателя", "Пожалуйста, выберите преподавателя в таблице для удаления!")
            return

        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы действительно хотите удалить выбранного преподавателя и всю связанную учебную нагрузку?\nДействие необратимо!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            ok, msg = delete_teacher(tid)
            if ok:
                QMessageBox.information(self, "Успех", msg)
                self.refresh_table()
            else:
                QMessageBox.critical(self, "Ошибка удаления", msg)

    def on_view_card(self):
        tid = self.get_selected_teacher_id()
        if not tid:
            QMessageBox.information(self, "Выбор преподавателя", "Пожалуйста, выберите преподавателя в таблице для просмотра карточки!")
            return
        dlg = TeacherCardDialog(teacher_id=tid, parent=self)
        dlg.exec()

    def on_export_excel(self):
        dept_id = self.combo_dept.currentData()
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт списка преподавателей в Excel",
            "prepodavateli_astana_polytech.xlsx",
            "Excel файлы (*.xlsx)"
        )
        if filepath:
            ok, msg = export_teachers_to_excel(filepath, **self.export_filters())
            if ok:
                QMessageBox.information(self, "Экспорт в Excel", msg)
            else:
                QMessageBox.critical(self, "Ошибка экспорта", msg)

    def on_export_pdf(self):
        dept_id = self.combo_dept.currentData()
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт списка преподавателей в PDF",
            "prepodavateli_astana_polytech.pdf",
            "PDF файлы (*.pdf)"
        )
        if filepath:
            ok, msg = export_teachers_to_pdf(filepath, **self.export_filters())
            if ok:
                QMessageBox.information(self, "Экспорт в PDF", msg)
            else:
                QMessageBox.critical(self, "Ошибка экспорта", msg)

    def export_filters(self):
        return dict(department_id=self.combo_dept.currentData(), search_text=self.input_search.text(),
            qualification=self.combo_qual.currentText(), status=self.combo_status.currentText(),
            min_exp=self.spin_min_exp.value(), max_exp=self.spin_max_exp.value(),
            sort_by=self.combo_sort.currentData(), descending=self.combo_direction.currentData(),
            academic_year=self.combo_year.currentText(), rate_filter=self.combo_rate.currentData())
