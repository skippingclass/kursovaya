"""
Диалоговое окно добавления / редактирования учебной нагрузки (WorkloadDialog)
Топ-монохромный дизайн в стиле TuneCloud.
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QPushButton, QMessageBox, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt
from services.teacher_service import get_teachers
from services.department_service import get_disciplines
from services.workload_service import add_workload, update_workload, get_academic_years, get_workloads


class WorkloadDialog(QDialog):
    def __init__(self, workload_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.workload_id = workload_id
        is_edit = workload_id is not None
        self.setWindowTitle("Редактирование нагрузки" if is_edit else "Назначение нагрузки")
        self.setFixedWidth(540)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.teachers = get_teachers()
        self.disciplines = get_disciplines()

        self.init_ui()
        if is_edit:
            self.load_workload_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title_lbl = QLabel("Редактирование нагрузки" if self.workload_id else "Назначение учебных часов")
        title_lbl.setStyleSheet("font-size: 17px; font-weight: 700; color: #ffffff;")
        layout.addWidget(title_lbl)

        card = QFrame()
        card.setObjectName("panelCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)

        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        grid.setHorizontalSpacing(14)

        # 1. Учебный год
        grid.addWidget(QLabel("Учебный год: *"), 0, 0)
        self.combo_year = QComboBox()
        self.combo_year.setEditable(True)
        years = get_academic_years()
        self.combo_year.addItems(years)
        grid.addWidget(self.combo_year, 0, 1)

        # 2. Преподаватель
        grid.addWidget(QLabel("Преподаватель: *"), 1, 0)
        self.combo_teacher = QComboBox()
        for t in self.teachers:
            dept_name = t.department.name if t.department else ""
            self.combo_teacher.addItem(f"{t.full_name} ({dept_name})", t.id)
        grid.addWidget(self.combo_teacher, 1, 1)

        # 3. Дисциплина
        grid.addWidget(QLabel("Учебная дисциплина: *"), 2, 0)
        self.combo_disc = QComboBox()
        for d in self.disciplines:
            self.combo_disc.addItem(f"[{d.code}] {d.name}", d.id)
        grid.addWidget(self.combo_disc, 2, 1)

        # 4. Часы лекций
        grid.addWidget(QLabel("Часы лекций:"), 3, 0)
        self.spin_lec = QSpinBox()
        self.spin_lec.setRange(0, 1500)
        self.spin_lec.setValue(90)
        self.spin_lec.valueChanged.connect(self.update_total_hours)
        grid.addWidget(self.spin_lec, 3, 1)

        # 5. Часы практик
        grid.addWidget(QLabel("Часы практик / лаб:"), 4, 0)
        self.spin_prac = QSpinBox()
        self.spin_prac.setRange(0, 1500)
        self.spin_prac.setValue(120)
        self.spin_prac.valueChanged.connect(self.update_total_hours)
        grid.addWidget(self.spin_prac, 4, 1)

        # 6. Всего часов
        grid.addWidget(QLabel("Итоговый объем нагрузки:"), 5, 0)
        self.lbl_total = QLabel("210 ч.")
        self.lbl_total.setStyleSheet("font-weight: 700; font-size: 15px; color: #ffffff;")
        grid.addWidget(self.lbl_total, 5, 1)

        card_layout.addLayout(grid)
        layout.addWidget(card)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Отмена")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Сохранить")
        btn_save.setObjectName("btnPrimary")
        btn_save.setMinimumWidth(120)
        btn_save.clicked.connect(self.on_save)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def update_total_hours(self):
        tot = self.spin_lec.value() + self.spin_prac.value()
        self.lbl_total.setText(f"{tot} ч.")

    def load_workload_data(self):
        workloads = get_workloads()
        target = next((w for w in workloads if w.id == self.workload_id), None)
        if not target:
            QMessageBox.warning(self, "Ошибка", "Запись о нагрузке не найдена!")
            self.reject()
            return

        idx_y = self.combo_year.findText(target.academic_year)
        if idx_y >= 0:
            self.combo_year.setCurrentIndex(idx_y)
        else:
            self.combo_year.setEditText(target.academic_year)

        idx_t = self.combo_teacher.findData(target.teacher_id)
        if idx_t >= 0:
            self.combo_teacher.setCurrentIndex(idx_t)

        idx_d = self.combo_disc.findData(target.discipline_id)
        if idx_d >= 0:
            self.combo_disc.setCurrentIndex(idx_d)

        self.spin_lec.setValue(target.hours_lecture or 0)
        self.spin_prac.setValue(target.hours_practice or 0)
        self.update_total_hours()

    def on_save(self):
        year = self.combo_year.currentText().strip()
        teacher_id = self.combo_teacher.currentData()
        discipline_id = self.combo_disc.currentData()
        hl = self.spin_lec.value()
        hp = self.spin_prac.value()

        if self.workload_id:
            ok, msg = update_workload(self.workload_id, year, teacher_id, discipline_id, hl, hp)
        else:
            ok, msg, _ = add_workload(year, teacher_id, discipline_id, hl, hp)

        if ok:
            QMessageBox.information(self, "Успех", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", msg)
