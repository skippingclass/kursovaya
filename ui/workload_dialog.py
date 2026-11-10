"""Редактирование общего плана и назначение часов из его остатка."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QPushButton, QMessageBox, QLineEdit)
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from services.teacher_service import get_teachers
from services.department_service import get_disciplines
from services.workload_service import (get_pools, get_academic_years, get_workloads,
    save_pool, add_workload, update_workload, semester_label)


def year_combo():
    combo = QComboBox()
    combo.setEditable(True)
    combo.addItems(get_academic_years())
    from datetime import date
    y = date.today().year - (date.today().month < 9)
    combo.setCurrentText(f"{y}-{y+1}")
    combo.lineEdit().setInputMask("9999-9999;_")
    return combo


def buttons(dialog, layout):
    row = QHBoxLayout()
    row.addStretch()
    cancel, save = QPushButton("Отмена"), QPushButton("Сохранить")
    cancel.clicked.connect(dialog.reject)
    save.setObjectName("btnPrimary")
    save.clicked.connect(dialog.on_save)
    row.addWidget(cancel)
    row.addWidget(save)
    layout.addLayout(row)


class PoolDialog(QDialog):
    def __init__(self, pool_id=None, parent=None):
        super().__init__(parent)
        self.pool_id = pool_id
        self.setWindowTitle("Общий план учебной нагрузки")
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(QLabel("Общий план учебной нагрузки"))
        form = QFormLayout()
        self.combo_year = year_combo()
        self.combo_semester = QComboBox()
        self.combo_semester.addItem("1", 1)
        self.combo_semester.addItem("2", 2)
        self.input_group = QLineEdit()
        self.input_group.setMaxLength(100)
        self.input_group.setPlaceholderText("П-24-67Б")
        self.combo_disc = QComboBox()
        for d in get_disciplines():
            self.combo_disc.addItem(f"[{d.code}] {d.name}", d.id)
        self.spin_lec, self.spin_prac, self.spin_weeks = QSpinBox(), QSpinBox(), QSpinBox()
        self.spin_lec.setRange(0, 10000)
        self.spin_prac.setRange(0, 10000)
        self.spin_weeks.setRange(1, 52)
        self.spin_weeks.setValue(18)
        for label, field in (("Учебный год *", self.combo_year), ("Семестр *", self.combo_semester),
                ("Учебная группа *", self.input_group), ("Дисциплина *", self.combo_disc),
                ("Теория в плане, ч.", self.spin_lec), ("Практика в плане, ч.", self.spin_prac),
                ("Учебных недель в семестре", self.spin_weeks)):
            form.addRow(label, field)
        layout.addLayout(form)
        note = QLabel("Объем задается для группы за семестр. Из него назначаются часы преподавателям.")
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons(self, layout)
        if pool_id:
            pool = next(p for p in get_pools() if p.id == pool_id)
            self.combo_year.setCurrentText(pool.academic_year)
            self.combo_semester.setCurrentIndex(self.combo_semester.findData(pool.semester))
            self.input_group.setText(pool.group_name)
            self.combo_disc.setCurrentIndex(self.combo_disc.findData(pool.discipline_id))
            self.spin_lec.setValue(pool.hours_lecture)
            self.spin_prac.setValue(pool.hours_practice)
            self.spin_weeks.setValue(pool.weeks)

    def on_save(self):
        ok, message, _ = save_pool(self.combo_year.currentText(), self.combo_semester.currentData(),
            self.input_group.text(), self.combo_disc.currentData(), self.spin_lec.value(),
            self.spin_prac.value(), self.spin_weeks.value(), self.pool_id)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "Проверка общего плана", message)


class WorkloadDialog(QDialog):
    def __init__(self, workload_id=None, parent=None, pool_id=None):
        super().__init__(parent)
        self.workload_id = workload_id
        self.target = next((w for w in get_workloads() if w.id == workload_id), None)
        self.pools = get_pools()
        self.setWindowTitle("Редактирование назначения" if workload_id else "Назначение часов из общего плана")
        self.setMinimumWidth(730)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(QLabel("Назначение часов преподавателю"))
        form = QFormLayout()
        self.combo_year = year_combo()
        self.combo_semester = QComboBox()
        self.combo_semester.addItem("Все семестры", None)
        self.combo_semester.addItem("1", 1)
        self.combo_semester.addItem("2", 2)
        self.combo_semester.addItem("Не указан (архив)", 0)
        self.combo_pool, self.combo_teacher = QComboBox(), QComboBox()
        for teacher in get_teachers():
            if teacher.status != "уволен" or (self.target and self.target.teacher_id == teacher.id):
                self.combo_teacher.addItem(teacher.full_name, teacher.id)
        self.spin_lec, self.spin_prac = QSpinBox(), QSpinBox()
        for spin in (self.spin_lec, self.spin_prac):
            spin.setRange(0, 10000)
        self.lbl_available, self.lbl_total, self.lbl_weekly = QLabel(), QLabel(), QLabel()
        for label, field in (("Учебный год", self.combo_year), ("Семестр", self.combo_semester),
                ("Строка общего плана *", self.combo_pool), ("Преподаватель *", self.combo_teacher),
                ("Доступно для назначения", self.lbl_available), ("Теория, ч.", self.spin_lec),
                ("Практика, ч.", self.spin_prac), ("Всего часов", self.lbl_total),
                ("Среднее количество часов в неделю", self.lbl_weekly)):
            form.addRow(label, field)
        layout.addLayout(form)
        buttons(self, layout)
        self.combo_year.currentTextChanged.connect(self.load_pools)
        self.combo_semester.currentIndexChanged.connect(self.load_pools)
        self.combo_pool.currentIndexChanged.connect(self.update_available)
        self.spin_lec.valueChanged.connect(self.update_total_hours)
        self.spin_prac.valueChanged.connect(self.update_total_hours)
        if self.target:
            self.combo_year.setCurrentText(self.target.academic_year)
            self.combo_semester.setCurrentIndex(self.combo_semester.findData(self.target.semester))
        self.load_pools()
        chosen = self.target.pool_id if self.target else pool_id
        if chosen:
            pool = next((p for p in self.pools if p.id == chosen), None)
            if pool:
                self.combo_year.setCurrentText(pool.academic_year)
                self.combo_semester.setCurrentIndex(self.combo_semester.findData(pool.semester))
                self.load_pools()
                self.combo_pool.setCurrentIndex(self.combo_pool.findData(chosen))
        if self.target:
            self.combo_teacher.setCurrentIndex(self.combo_teacher.findData(self.target.teacher_id))
            self.spin_lec.setValue(self.target.hours_lecture)
            self.spin_prac.setValue(self.target.hours_practice)
        self.update_available()

    def load_pools(self):
        selected = self.combo_pool.currentData()
        self.combo_pool.blockSignals(True)
        self.combo_pool.clear()
        sem = self.combo_semester.currentData()
        for pool in self.pools:
            if pool.academic_year == self.combo_year.currentText() and (sem is None or pool.semester == sem):
                self.combo_pool.addItem(f"{pool.group_name} · {pool.discipline.name} · сем. {semester_label(pool.semester)}", pool.id)
        if self.combo_pool.findData(selected) >= 0:
            self.combo_pool.setCurrentIndex(self.combo_pool.findData(selected))
        self.combo_pool.blockSignals(False)
        self.update_available()

    def update_available(self):
        pool = next((p for p in self.pools if p.id == self.combo_pool.currentData()), None)
        if pool:
            old_l = self.target.hours_lecture if self.target and self.target.pool_id == pool.id else 0
            old_p = self.target.hours_practice if self.target and self.target.pool_id == pool.id else 0
            self.lbl_available.setText(f"теория {pool.available_lecture + old_l} ч.; практика {pool.available_practice + old_p} ч.")
        else:
            self.lbl_available.setText("Сначала добавьте строку общего плана за выбранный период.")
        self.update_total_hours()

    def update_total_hours(self):
        total = self.spin_lec.value() + self.spin_prac.value()
        self.lbl_total.setText(str(total))
        pool = next((p for p in self.pools if p.id == self.combo_pool.currentData()), None)
        self.lbl_weekly.setText(f"{total / pool.weeks:.2f} ч. ({pool.weeks} учебных недель)" if pool else "—")

    def on_save(self):
        pool = next((p for p in self.pools if p.id == self.combo_pool.currentData()), None)
        if not pool:
            QMessageBox.warning(self, "Общий план", "Выберите строку общего плана нагрузки.")
            return
        args = (pool.academic_year, self.combo_teacher.currentData(), pool.discipline_id,
                self.spin_lec.value(), self.spin_prac.value())
        if self.workload_id:
            ok, message = update_workload(self.workload_id, *args, pool_id=pool.id)
        else:
            ok, message, _ = add_workload(*args, pool_id=pool.id)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "Назначение нагрузки", message)
