"""
Вкладка учета и распределения учебной нагрузки (LoadModule)
Топ-монохромный дизайн в стиле TuneCloud.
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from services.workload_service import get_workloads, delete_workload, get_academic_years
from services.department_service import get_departments
from services.teacher_service import get_teachers
from services.auth_service import is_operator
from services.report_service import export_workload_to_excel
from ui.workload_dialog import WorkloadDialog


class WorkloadTab(QWidget):
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

        # 1. Панель фильтров (TuneCloud card)
        filter_frame = QFrame()
        filter_frame.setObjectName("panelCard")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(14, 12, 14, 12)
        filter_layout.setSpacing(12)

        # Учебный год
        filter_layout.addWidget(QLabel("Учебный год:"))
        self.combo_year = QComboBox()
        self.combo_year.currentIndexChanged.connect(self.refresh_table)
        filter_layout.addWidget(self.combo_year, 1)

        # Кафедра
        filter_layout.addWidget(QLabel("Кафедра:"))
        self.combo_dept = QComboBox()
        self.combo_dept.currentIndexChanged.connect(self.on_department_changed)
        filter_layout.addWidget(self.combo_dept, 2)

        # Преподаватель
        filter_layout.addWidget(QLabel("Преподаватель:"))
        self.combo_teacher = QComboBox()
        self.combo_teacher.currentIndexChanged.connect(self.refresh_table)
        filter_layout.addWidget(self.combo_teacher, 2)

        btn_reset = QPushButton("Сбросить")
        btn_reset.setObjectName("btnSecondary")
        btn_reset.clicked.connect(self.reset_filters)
        filter_layout.addWidget(btn_reset)

        main_layout.addWidget(filter_frame)

        # 2. Панель действий
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.btn_add = QPushButton("➕ Назначить нагрузку")
        self.btn_add.setObjectName("btnPrimary")
        self.btn_add.clicked.connect(self.on_add_workload)
        actions_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton("✏ Редактировать")
        self.btn_edit.clicked.connect(self.on_edit_workload)
        actions_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("🗑 Удалить")
        self.btn_delete.setObjectName("btnDanger")
        self.btn_delete.clicked.connect(self.on_delete_workload)
        actions_layout.addWidget(self.btn_delete)

        actions_layout.addStretch()

        btn_excel = QPushButton("📊 Экспорт ведомости в Excel")
        btn_excel.setObjectName("btnSecondary")
        btn_excel.clicked.connect(self.on_export_excel)
        actions_layout.addWidget(btn_excel)

        main_layout.addLayout(actions_layout)

        # 3. Таблица нагрузки
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        headers = ["ID", "Учебный год", "Преподаватель", "Кафедра", "Код", "Дисциплина", "Лекции (ч)", "Практики (ч)", "Всего (ч)"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.on_edit_workload)
        main_layout.addWidget(self.table)

        # 4. Итоговая панель часов (TuneCloud status pill)
        summary_frame = QFrame()
        summary_frame.setObjectName("panelCard")
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(14, 8, 14, 8)
        self.lbl_summary = QLabel()
        self.lbl_summary.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 13px;")
        summary_layout.addWidget(self.lbl_summary)
        main_layout.addWidget(summary_frame)

        self.apply_role_permissions()

    def apply_role_permissions(self):
        can_edit = is_operator()
        self.btn_add.setVisible(can_edit)
        self.btn_edit.setVisible(can_edit)
        self.btn_delete.setVisible(can_edit)

    def load_filters(self):
        self.combo_year.blockSignals(True)
        self.combo_year.clear()
        self.combo_year.addItem("Все годы")
        years = get_academic_years()
        self.combo_year.addItems(years)
        self.combo_year.blockSignals(False)

        self.combo_dept.blockSignals(True)
        self.combo_dept.clear()
        self.combo_dept.addItem("Все кафедры", 0)
        departments = get_departments()
        for d in departments:
            self.combo_dept.addItem(d.name, d.id)
        self.combo_dept.blockSignals(False)

        self.load_teachers_combo()

    def load_teachers_combo(self):
        self.combo_teacher.blockSignals(True)
        self.combo_teacher.clear()
        self.combo_teacher.addItem("Все преподаватели", 0)
        dept_id = self.combo_dept.currentData()
        teachers = get_teachers(department_id=dept_id)
        for t in teachers:
            self.combo_teacher.addItem(t.full_name, t.id)
        self.combo_teacher.blockSignals(False)

    def on_department_changed(self):
        self.load_teachers_combo()
        self.refresh_table()

    def reset_filters(self):
        self.combo_year.setCurrentIndex(0)
        self.combo_dept.setCurrentIndex(0)
        self.load_teachers_combo()
        self.combo_teacher.setCurrentIndex(0)
        self.refresh_table()

    def get_selected_workload_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        row = items[0].row()
        return int(self.table.item(row, 0).text())

    def refresh_table(self):
        year = self.combo_year.currentText()
        if year == "Все годы":
            year = None

        dept_id = self.combo_dept.currentData()
        teacher_id = self.combo_teacher.currentData()

        workloads = get_workloads(
            academic_year=year,
            teacher_id=teacher_id,
            department_id=dept_id
        )

        self.table.setRowCount(len(workloads))
        tot_lec = 0
        tot_prac = 0
        tot_all = 0

        for row, w in enumerate(workloads):
            self.table.setItem(row, 0, QTableWidgetItem(str(w.id)))
            self.table.setItem(row, 1, QTableWidgetItem(w.academic_year))

            t_name = w.teacher.full_name if w.teacher else "-"
            self.table.setItem(row, 2, QTableWidgetItem(t_name))

            d_name = w.teacher.department.name if w.teacher and w.teacher.department else "-"
            self.table.setItem(row, 3, QTableWidgetItem(d_name))

            code = w.discipline.code if w.discipline else "-"
            self.table.setItem(row, 4, QTableWidgetItem(code))

            disc = w.discipline.name if w.discipline else "-"
            self.table.setItem(row, 5, QTableWidgetItem(disc))

            l_item = QTableWidgetItem(str(w.hours_lecture))
            l_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, l_item)

            p_item = QTableWidgetItem(str(w.hours_practice))
            p_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, p_item)

            t_item = QTableWidgetItem(str(w.total_hours))
            t_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 8, t_item)

            tot_lec += w.hours_lecture
            tot_prac += w.hours_practice
            tot_all += w.total_hours

        self.lbl_summary.setText(
            f"Итог:  Записей: {len(workloads)}  |  Лекции: {tot_lec} ч.  |  Практики: {tot_prac} ч.  |  СУММАРНАЯ НАГРУЗКА: {tot_all} ч."
        )
        self.status_updated.emit(f"Отображено записей нагрузки: {len(workloads)}")

    def on_add_workload(self):
        dlg = WorkloadDialog(parent=self)
        if dlg.exec():
            self.load_filters()
            self.refresh_table()

    def on_edit_workload(self):
        wid = self.get_selected_workload_id()
        if not wid:
            QMessageBox.information(self, "Выбор нагрузки", "Выберите строку с учебной нагрузкой для редактирования!")
            return
        dlg = WorkloadDialog(workload_id=wid, parent=self)
        if dlg.exec():
            self.refresh_table()

    def on_delete_workload(self):
        wid = self.get_selected_workload_id()
        if not wid:
            QMessageBox.information(self, "Выбор нагрузки", "Выберите строку с учебной нагрузкой для удаления!")
            return

        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы действительно хотите удалить эту запись об учебной нагрузке?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            ok, msg = delete_workload(wid)
            if ok:
                QMessageBox.information(self, "Успех", msg)
                self.refresh_table()
            else:
                QMessageBox.critical(self, "Ошибка удаления", msg)

    def on_export_excel(self):
        year = self.combo_year.currentText()
        if year == "Все годы":
            year = None
        dept_id = self.combo_dept.currentData()

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт ведомости нагрузки в Excel",
            "vedomost_nagruzki_polytech.xlsx",
            "Excel файлы (*.xlsx)"
        )
        if filepath:
            ok, msg = export_workload_to_excel(filepath, academic_year=year, department_id=dept_id)
            if ok:
                QMessageBox.information(self, "Экспорт в Excel", msg)
            else:
                QMessageBox.critical(self, "Ошибка экспорта", msg)
