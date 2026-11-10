"""Параметры отчетов и экспорт точно той же выборки."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                            QPushButton, QMessageBox, QFileDialog)
from PyQt6.QtCore import pyqtSignal
from services.department_service import get_departments
from services.teacher_service import get_teachers
from services.workload_service import get_academic_years
from services.report_service import (get_teachers_report_data, get_workload_report_data,
    get_stats_report_data, STAFF_HEADERS, STAFF_KEYS, WORKLOAD_HEADERS, WORKLOAD_KEYS, STATS_HEADERS,
    export_teachers_to_excel, export_workload_to_excel, export_teachers_to_pdf, export_workload_to_pdf, export_stats)
from ui.workload_tab import fill_table, make_table


class ReportsTab(QWidget):
    status_updated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Кадровый состав", "Распределение учебной нагрузки", "Статистика по категориям"])
        self.combo_dept, self.combo_year = QComboBox(), QComboBox()
        for label, combo in (("Отчет", self.combo_type), ("Кафедра", self.combo_dept), ("Учебный год", self.combo_year)):
            row.addWidget(QLabel(label))
            row.addWidget(combo, 1)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.combo_semester, self.combo_teacher = QComboBox(), QComboBox()
        for label, value in [("Все семестры", None), ("1", 1), ("2", 2), ("Не указан (архив)", 0)]:
            self.combo_semester.addItem(label, value)
        self.lbl_semester, self.lbl_teacher = QLabel("Семестр"), QLabel("Преподаватель")
        row.addWidget(self.lbl_semester)
        row.addWidget(self.combo_semester)
        row.addWidget(self.lbl_teacher)
        row.addWidget(self.combo_teacher, 1)
        layout.addLayout(row)
        self.lbl_report_title = QLabel()
        layout.addWidget(self.lbl_report_title)
        self.table = make_table()
        layout.addWidget(self.table)
        row = QHBoxLayout()
        for title, callback in (("Сформировать", self.generate_report), ("Экспорт в Excel", self.export_excel), ("Экспорт в PDF", self.export_pdf)):
            button = QPushButton(title)
            button.clicked.connect(callback)
            row.addWidget(button)
        layout.addLayout(row)
        self.load_filters()
        self.combo_type.currentIndexChanged.connect(self.on_report_type_changed)
        self.combo_dept.currentIndexChanged.connect(self.on_department_changed)
        for combo in (self.combo_year, self.combo_semester, self.combo_teacher):
            combo.currentIndexChanged.connect(self.generate_report)
        self.on_report_type_changed()

    def load_filters(self):
        for combo, entries in ((self.combo_dept, [("Все кафедры", 0)] + [(d.name, d.id) for d in get_departments()]),
                              (self.combo_year, [("Все годы", None)] + [(y, y) for y in get_academic_years()])):
            chosen = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for label, value in entries:
                combo.addItem(label, value)
            combo.setCurrentIndex(max(0, combo.findData(chosen)))
            combo.blockSignals(False)
        self.load_teachers()

    def load_teachers(self):
        selected = self.combo_teacher.currentData()
        self.combo_teacher.blockSignals(True)
        self.combo_teacher.clear()
        self.combo_teacher.addItem("Все преподаватели", 0)
        for t in get_teachers(department_id=self.combo_dept.currentData()):
            self.combo_teacher.addItem(t.full_name, t.id)
        self.combo_teacher.setCurrentIndex(max(0, self.combo_teacher.findData(selected)))
        self.combo_teacher.blockSignals(False)

    def on_department_changed(self):
        self.load_teachers()
        self.generate_report()

    def on_report_type_changed(self):
        show = self.combo_type.currentIndex() == 1
        for widget in (self.lbl_semester, self.combo_semester, self.lbl_teacher, self.combo_teacher):
            widget.setVisible(show)
        self.generate_report()

    def filters(self):
        result = dict(department_id=self.combo_dept.currentData(), academic_year=self.combo_year.currentData())
        if self.combo_type.currentIndex() == 1:
            result.update(semester=self.combo_semester.currentData(), teacher_id=self.combo_teacher.currentData())
        return result

    def generate_report(self):
        idx = self.combo_type.currentIndex()
        if idx == 0:
            data = get_teachers_report_data(**self.filters())
            headers, rows = STAFF_HEADERS, [[d[k] for k in STAFF_KEYS] for d in data]
        elif idx == 1:
            data = get_workload_report_data(**self.filters())
            headers, rows = WORKLOAD_HEADERS, [[d[k] for k in WORKLOAD_KEYS] for d in data]
        else:
            headers, rows = STATS_HEADERS, get_stats_report_data(**self.filters())
        fill_table(self.table, headers, rows)
        self.lbl_report_title.setText(f"{self.combo_type.currentText()} · {self.combo_year.currentText()}" +
            (f" · семестр {self.combo_semester.currentText()}" if idx == 1 else ""))
        self.status_updated.emit(f"Строк в отчете: {len(rows)}")

    def export_excel(self):
        self.export(False)

    def export_pdf(self):
        self.export(True)

    def export(self, pdf):
        extension = "pdf" if pdf else "xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить отчет", f"otchet.{extension}", f"Отчет (*.{extension})")
        if not path:
            return
        idx = self.combo_type.currentIndex()
        if idx == 2:
            ok, message = export_stats(path, **self.filters(), pdf=pdf)
        else:
            action = ([export_teachers_to_pdf, export_workload_to_pdf] if pdf else
                      [export_teachers_to_excel, export_workload_to_excel])[idx]
            ok, message = action(path, **self.filters())
        (QMessageBox.information if ok else QMessageBox.warning)(self, "Экспорт отчета", message)
