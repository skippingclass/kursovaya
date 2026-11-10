"""Форма преподавателя с раздельными ФИО и маской телефона."""
from datetime import date
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QDateEdit, QPushButton, QMessageBox, QFormLayout)
from PyQt6.QtCore import QDate, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from services.teacher_service import add_teacher, update_teacher, get_teacher_by_id, find_similar_teachers, validate_teacher_data
from services.department_service import get_departments


class TeacherDialog(QDialog):
    def __init__(self, teacher_id=None, parent=None):
        super().__init__(parent)
        self.teacher_id = teacher_id
        self.photo_path = None
        self.setWindowTitle("Редактирование преподавателя" if teacher_id else "Новый преподаватель")
        self.setMinimumWidth(590)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        form = QFormLayout()
        self.input_last_name, self.input_first_name, self.input_middle_name = QLineEdit(), QLineEdit(), QLineEdit()
        for field, label in ((self.input_last_name, "Фамилия *"), (self.input_first_name, "Имя *"),
                             (self.input_middle_name, "Отчество")):
            field.setMaxLength(100)
            field.setValidator(QRegularExpressionValidator(QRegularExpression("[\\p{L} '\u2019-]*"), self))
            form.addRow(label, field)
        self.combo_dept = QComboBox()
        for dept in get_departments():
            self.combo_dept.addItem(dept.name, dept.id)
        form.addRow("Кафедра *", self.combo_dept)
        self.combo_qual = QComboBox()
        self.combo_qual.addItems(["Педагог-исследователь", "Педагог-эксперт", "Педагог-модератор", "Высшая категория",
                                  "Первая категория", "Вторая категория", "Специалист"])
        form.addRow("Категория", self.combo_qual)
        self.spin_exp = QSpinBox()
        self.spin_exp.setRange(0, 70)
        form.addRow("Стаж в годах", self.spin_exp)
        self.date_birth = QDateEdit()
        self.date_birth.setCalendarPopup(True)
        self.date_birth.setDisplayFormat("dd.MM.yyyy")
        self.date_birth.setDateRange(QDate(1900, 1, 1), QDate.currentDate())
        self.date_birth.setSpecialValueText("Не указана")
        self.date_birth.setDate(self.date_birth.minimumDate())
        form.addRow("Дата рождения", self.date_birth)
        self.input_phone = QLineEdit()
        self.input_phone.setInputMask("+7 (999) 999-99-99;_")
        form.addRow("Телефон", self.input_phone)
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("name@example.kz")
        self.input_email.setMaxLength(100)
        form.addRow("Электронная почта", self.input_email)
        self.combo_status = QComboBox()
        self.combo_status.addItems(["работает", "в отпуске", "уволен"])
        form.addRow("Статус", self.combo_status)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Сохранить")
        save.setObjectName("btnPrimary")
        save.clicked.connect(self.on_save)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)
        if teacher_id:
            self.load_teacher_data()

    def load_teacher_data(self):
        teacher = get_teacher_by_id(self.teacher_id)
        if not teacher:
            return
        self.input_last_name.setText(teacher.last_name)
        self.input_first_name.setText(teacher.first_name)
        self.input_middle_name.setText(teacher.middle_name)
        self.combo_dept.setCurrentIndex(self.combo_dept.findData(teacher.department_id))
        self.combo_qual.setCurrentText(teacher.qualification or "Специалист")
        self.spin_exp.setValue(teacher.experience or 0)
        if teacher.birth_date:
            self.date_birth.setDate(QDate(teacher.birth_date.year, teacher.birth_date.month, teacher.birth_date.day))
        phone = teacher.phone or ""
        if phone.startswith("8"):
            phone = "+7" + phone[1:]
        self.input_phone.setText(phone)
        self.input_email.setText(teacher.email or "")
        self.combo_status.setCurrentText(teacher.status or "работает")
        self.photo_path = teacher.photo_path

    def on_save(self):
        qdate = self.date_birth.date()
        raw_phone = self.input_phone.text()
        phone = raw_phone if any(c.isdigit() for c in raw_phone[2:]) else ""
        if phone and not self.input_phone.hasAcceptableInput():
            QMessageBox.warning(self, "Проверка телефона", "Заполните номер телефона полностью или очистите поле.")
            return
        data = dict(last_name=self.input_last_name.text(), first_name=self.input_first_name.text(),
                    middle_name=self.input_middle_name.text(), department_id=self.combo_dept.currentData(),
                    qualification=self.combo_qual.currentText(), experience=self.spin_exp.value(),
                    birth_date=None if qdate == self.date_birth.minimumDate() else date(qdate.year(), qdate.month(), qdate.day()),
                    phone=phone, email=self.input_email.text(), status=self.combo_status.currentText(), photo_path=self.photo_path)
        valid, error = validate_teacher_data(data)
        if not valid:
            QMessageBox.warning(self, "Проверка данных", error)
            return
        matches = find_similar_teachers(data, self.teacher_id)
        allow_similar = False
        if matches and not any(m["exact"] for m in matches):
            names = "\n".join(m["full_name"] for m in matches)
            allow_similar = QMessageBox.question(self, "Похожая карточка",
                f"Возможно, в ФИО опечатка. Уже есть:\n{names}\n\nЭто другой человек?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes
            if not allow_similar:
                return
        if self.teacher_id:
            ok, message = update_teacher(self.teacher_id, data, allow_similar=allow_similar)
        else:
            ok, message, _ = add_teacher(data, allow_similar=allow_similar)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "Проверка данных", message)
