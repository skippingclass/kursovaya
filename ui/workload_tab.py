"""Общий план → назначения преподавателям с едиными фильтрами."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from services.workload_service import get_workloads, delete_workload, get_academic_years, get_pools, delete_pool, semester_label
from services.department_service import get_departments
from services.teacher_service import get_teachers
from services.auth_service import is_operator
from services.report_service import export_workload_to_excel
from ui.workload_dialog import WorkloadDialog, PoolDialog


def fill_table(table, headers, rows):
    table.setSortingEnabled(False)
    table.clear()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            item = QTableWidgetItem()
            item.setData(Qt.ItemDataRole.DisplayRole, value if value is not None else "")
            table.setItem(r, c, item)
    table.setSortingEnabled(True)
    table.resizeColumnsToContents()
    table.horizontalHeader().setStretchLastSection(True)


def make_table():
    table = QTableWidget()
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    return table


class WorkloadTab(QWidget):
    status_updated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        filters = QHBoxLayout()
        self.combo_year, self.combo_semester, self.combo_dept, self.combo_teacher = [QComboBox() for _ in range(4)]
        self.combo_semester.addItem("Все семестры", None)
        self.combo_semester.addItem("1", 1)
        self.combo_semester.addItem("2", 2)
        self.combo_semester.addItem("Не указан (архив)", 0)
        for label, combo in (("Учебный год", self.combo_year), ("Семестр", self.combo_semester),
                             ("Кафедра", self.combo_dept)):
            filters.addWidget(QLabel(label))
            filters.addWidget(combo, 1)
        reset = QPushButton("Сбросить")
        reset.clicked.connect(self.reset_filters)
        filters.addWidget(reset)
        layout.addLayout(filters)
        teacher_row = QHBoxLayout()
        teacher_row.addWidget(QLabel("Назначения преподавателя"))
        teacher_row.addWidget(self.combo_teacher, 1)
        export = QPushButton("Экспорт назначений в Excel")
        export.clicked.connect(self.on_export_excel)
        teacher_row.addWidget(export)
        layout.addLayout(teacher_row)
        self.pages = QTabWidget()
        self.pool_table, self.table = make_table(), make_table()
        self.pages.addTab(self.pool_table, "Общий план часов")
        self.pages.addTab(self.table, "Назначения преподавателям")
        layout.addWidget(self.pages)
        actions = QHBoxLayout()
        self.btn_pool = QPushButton("Добавить в общий план")
        self.btn_pool.clicked.connect(self.on_add_pool)
        self.btn_add = QPushButton("Назначить преподавателю")
        self.btn_add.setObjectName("btnPrimary")
        self.btn_add.clicked.connect(self.on_add_workload)
        self.btn_edit = QPushButton("Редактировать")
        self.btn_edit.clicked.connect(self.on_edit_workload)
        self.btn_delete = QPushButton("Удалить / вернуть часы")
        self.btn_delete.clicked.connect(self.on_delete_workload)
        for button in (self.btn_pool, self.btn_add, self.btn_edit, self.btn_delete):
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.lbl_summary = QLabel()
        self.lbl_summary.setWordWrap(True)
        layout.addWidget(self.lbl_summary)
        self.combo_year.currentIndexChanged.connect(self.refresh_table)
        self.combo_semester.currentIndexChanged.connect(self.refresh_table)
        self.combo_dept.currentIndexChanged.connect(self.on_department_changed)
        self.combo_teacher.currentIndexChanged.connect(self.refresh_table)
        self.pool_table.doubleClicked.connect(self.on_edit_workload)
        self.table.doubleClicked.connect(self.on_edit_workload)
        self.load_filters()
        self.refresh_table()
        self.apply_role_permissions()

    def apply_role_permissions(self):
        for button in (self.btn_pool, self.btn_add, self.btn_edit, self.btn_delete):
            button.setVisible(is_operator())

    def load_filters(self):
        for combo, entries in ((self.combo_year, [("Все годы", None)] + [(y, y) for y in get_academic_years()]),
                (self.combo_dept, [("Все кафедры", 0)] + [(d.name, d.id) for d in get_departments()])):
            selected = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for label, value in entries:
                combo.addItem(label, value)
            combo.setCurrentIndex(max(0, combo.findData(selected)))
            combo.blockSignals(False)
        self.load_teachers_combo()

    def load_teachers_combo(self):
        selected = self.combo_teacher.currentData()
        self.combo_teacher.blockSignals(True)
        self.combo_teacher.clear()
        self.combo_teacher.addItem("Все преподаватели", 0)
        for t in get_teachers(department_id=self.combo_dept.currentData()):
            self.combo_teacher.addItem(t.full_name, t.id)
        self.combo_teacher.setCurrentIndex(max(0, self.combo_teacher.findData(selected)))
        self.combo_teacher.blockSignals(False)

    def on_department_changed(self):
        self.load_teachers_combo()
        self.refresh_table()

    def reset_filters(self):
        for combo in (self.combo_year, self.combo_semester, self.combo_dept, self.combo_teacher):
            combo.setCurrentIndex(0)
        self.refresh_table()

    def selected_id(self, table):
        return int(table.item(table.currentRow(), 0).text()) if table.currentRow() >= 0 else None

    def get_selected_workload_id(self):
        return self.selected_id(self.table)

    def refresh_table(self):
        year, semester, dept = self.combo_year.currentData(), self.combo_semester.currentData(), self.combo_dept.currentData()
        pools = get_pools(year, semester, dept)
        assignments = get_workloads(year, self.combo_teacher.currentData(), dept, semester)
        fill_table(self.pool_table, ["ID", "Учебный год", "Семестр", "Группа", "Дисциплина", "Недель",
                "План теории", "План практики", "Всего", "Свободно теории", "Свободно практики"],
            [[p.id, p.academic_year, semester_label(p.semester), p.group_name, p.discipline.name, p.weeks,
              p.hours_lecture, p.hours_practice, p.total_hours, p.available_lecture, p.available_practice] for p in pools])
        fill_table(self.table, ["ID", "Учебный год", "Семестр", "Группа", "Преподаватель", "Кафедра", "Дисциплина",
                "Теория", "Практика", "Всего", "Часов в неделю"],
            [[w.id, w.academic_year, semester_label(w.semester), w.pool.group_name if w.pool else "",
              w.teacher.full_name, w.teacher.department.name, w.discipline.name,
              w.hours_lecture, w.hours_practice, w.total_hours, w.hours_per_week] for w in assignments])
        free_l, free_p = sum(p.available_lecture for p in pools), sum(p.available_practice for p in pools)
        self.lbl_summary.setText(f"Общий план: {sum(p.total_hours for p in pools)} ч. · Свободно: теория {free_l}, практика {free_p} ч.\n"
            f"Выбранные назначения: теория {sum(w.hours_lecture for w in assignments)}, практика {sum(w.hours_practice for w in assignments)}, "
            f"всего {sum(w.total_hours for w in assignments)} ч. · Ставка: 720 ч. в год")
        self.status_updated.emit(f"Строк плана: {len(pools)}; назначений: {len(assignments)}")

    def on_add_pool(self):
        if is_operator() and PoolDialog(parent=self).exec():
            self.load_filters()
            self.refresh_table()

    def on_add_workload(self):
        if not is_operator():
            return
        pool_id = self.selected_id(self.pool_table) if self.pages.currentIndex() == 0 else None
        if WorkloadDialog(parent=self, pool_id=pool_id).exec():
            self.pages.setCurrentIndex(1)
            self.refresh_table()

    def on_edit_workload(self):
        if not is_operator():
            return
        is_pool = self.pages.currentIndex() == 0
        selected = self.selected_id(self.pool_table if is_pool else self.table)
        if not selected:
            QMessageBox.information(self, "Выбор строки", "Выберите строку для редактирования.")
            return
        dialog = PoolDialog(selected, self) if is_pool else WorkloadDialog(selected, self)
        if dialog.exec():
            self.load_filters()
            self.refresh_table()

    def on_delete_workload(self):
        if not is_operator():
            return
        is_pool = self.pages.currentIndex() == 0
        selected = self.selected_id(self.pool_table if is_pool else self.table)
        if not selected:
            QMessageBox.information(self, "Выбор строки", "Выберите строку.")
            return
        message = "Удалить строку общего плана?" if is_pool else "Отменить назначение и вернуть часы в общий план?"
        if QMessageBox.question(self, "Подтверждение", message) == QMessageBox.StandardButton.Yes:
            ok, message = delete_pool(selected) if is_pool else delete_workload(selected)
            if not ok:
                QMessageBox.warning(self, "Удаление", message)
            self.refresh_table()

    def on_export_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт назначений", "nagruzka.xlsx", "Excel (*.xlsx)")
        if path:
            ok, message = export_workload_to_excel(path, academic_year=self.combo_year.currentData(),
                semester=self.combo_semester.currentData(), department_id=self.combo_dept.currentData(),
                teacher_id=self.combo_teacher.currentData())
            (QMessageBox.information if ok else QMessageBox.warning)(self, "Экспорт", message)
