"""
Диалоговое окно добавления / редактирования преподавателя (TeacherDialog)
Топ-монохромный дизайн в стиле TuneCloud.
"""
from datetime import date
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QDateEdit, QPushButton, QMessageBox,
    QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QDate
from services.department_service import get_departments
from services.teacher_service import add_teacher, update_teacher, get_teacher_by_id


class TeacherDialog(QDialog):
    def __init__(self, teacher_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.teacher_id = teacher_id
        is_edit = teacher_id is not None
        self.setWindowTitle("Редактирование личного дела" if is_edit else "Добавление преподавателя")
        self.setFixedWidth(560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.departments = get_departments()
        self.photo_path = None

        self.init_ui()
        if is_edit:
            self.load_teacher_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title_lbl = QLabel("Редактирование преподавателя" if self.teacher_id else "Новый преподаватель")
        title_lbl.setStyleSheet("font-size: 17px; font-weight: 700; color: #ffffff;")
        layout.addWidget(title_lbl)

        card = QFrame()
        card.setObjectName("panelCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)

        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        grid.setHorizontalSpacing(14)

        # 1. ФИО
        grid.addWidget(QLabel("ФИО преподавателя: *"), 0, 0)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Фамилия Имя Отчество...")
        grid.addWidget(self.input_name, 0, 1)

        # 2. Кафедра
        grid.addWidget(QLabel("Кафедра / Отделение: *"), 1, 0)
        self.combo_dept = QComboBox()
        for dept in self.departments:
            self.combo_dept.addItem(dept.name, dept.id)
        grid.addWidget(self.combo_dept, 1, 1)

        # 3. Квалификация
        grid.addWidget(QLabel("Категория:"), 2, 0)
        self.combo_qual = QComboBox()
        categories = [
            "Педагог-исследователь",
            "Педагог-эксперт",
            "Педагог-модератор",
            "Высшая категория",
            "Первая категория",
            "Вторая категория",
            "Специалист"
        ]
        self.combo_qual.addItems(categories)
        grid.addWidget(self.combo_qual, 2, 1)

        # 4. Стаж работы
        grid.addWidget(QLabel("Стаж работы (лет):"), 3, 0)
        self.spin_exp = QSpinBox()
        self.spin_exp.setRange(0, 70)
        self.spin_exp.setValue(5)
        grid.addWidget(self.spin_exp, 3, 1)

        # 5. Дата рождения
        grid.addWidget(QLabel("Дата рождения:"), 4, 0)
        self.date_birth = QDateEdit()
        self.date_birth.setCalendarPopup(True)
        self.date_birth.setDisplayFormat("dd.MM.yyyy")
        self.date_birth.setDate(QDate(1985, 1, 1))
        grid.addWidget(self.date_birth, 4, 1)

        # 6. Телефон
        grid.addWidget(QLabel("Номер телефона:"), 5, 0)
        self.input_phone = QLineEdit()
        self.input_phone.setPlaceholderText("+7 (7xx) xxx-xx-xx")
        grid.addWidget(self.input_phone, 5, 1)

        # 7. E-mail
        grid.addWidget(QLabel("Электронная почта:"), 6, 0)
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("name@polytech.kz")
        grid.addWidget(self.input_email, 6, 1)

        # 8. Статус
        grid.addWidget(QLabel("Текущий статус:"), 7, 0)
        self.combo_status = QComboBox()
        self.combo_status.addItems(["работает", "в отпуске", "уволен"])
        grid.addWidget(self.combo_status, 7, 1)

        card_layout.addLayout(grid)
        layout.addWidget(card)

        # Нижние кнопки управления
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

    def load_teacher_data(self):
        teacher = get_teacher_by_id(self.teacher_id)
        if not teacher:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить данные преподавателя!")
            self.reject()
            return

        self.input_name.setText(teacher.full_name)
        idx = self.combo_dept.findData(teacher.department_id)
        if idx >= 0:
            self.combo_dept.setCurrentIndex(idx)

        idx_q = self.combo_qual.findText(teacher.qualification)
        if idx_q >= 0:
            self.combo_qual.setCurrentIndex(idx_q)

        self.spin_exp.setValue(teacher.experience or 0)

        if teacher.birth_date:
            b = teacher.birth_date
            self.date_birth.setDate(QDate(b.year, b.month, b.day))

        self.input_phone.setText(teacher.phone or "")
        self.input_email.setText(teacher.email or "")

        idx_s = self.combo_status.findText(teacher.status or "работает")
        if idx_s >= 0:
            self.combo_status.setCurrentIndex(idx_s)

        self.photo_path = teacher.photo_path

    def on_save(self):
        name = self.input_name.text().strip()
        dept_id = self.combo_dept.currentData()
        qual = self.combo_qual.currentText()
        exp = self.spin_exp.value()
        qdate = self.date_birth.date()
        birth_d = date(qdate.year(), qdate.month(), qdate.day())
        phone = self.input_phone.text().strip()
        email = self.input_email.text().strip()
        status = self.combo_status.currentText()

        data = {
            "full_name": name,
            "department_id": dept_id,
            "qualification": qual,
            "experience": exp,
            "birth_date": birth_d,
            "phone": phone,
            "email": email,
            "status": status,
            "photo_path": self.photo_path
        }

        if self.teacher_id:
            ok, msg = update_teacher(self.teacher_id, data)
        else:
            ok, msg, _ = add_teacher(data)

        if ok:
            QMessageBox.information(self, "Успех", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка валидации", msg)
