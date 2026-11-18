"""
Сводная карточка преподавателя (Просмотр карточки преподавателя - Use Case)
Топ-монохромный дизайн в стиле TuneCloud.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QFrame, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from services.teacher_service import get_teacher_by_id
from services.workload_service import get_academic_years, semester_label
from ui.workload_tab import fill_table


class TeacherCardDialog(QDialog):
    def __init__(self, teacher_id: int, parent=None):
        super().__init__(parent)
        self.teacher_id = teacher_id
        self.setWindowTitle("Карточка преподавателя")
        self.resize(1050, 650)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(22, 22, 22, 22)

        # Шапка карточки (TuneCloud Profile header)
        header_card = QFrame()
        header_card.setObjectName("panelCard")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(18, 16, 18, 16)
        header_layout.setSpacing(8)

        self.lbl_name = QLabel()
        name_font = QFont()
        name_font.setPointSize(16)
        name_font.setBold(True)
        self.lbl_name.setFont(name_font)
        self.lbl_name.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(self.lbl_name)

        self.lbl_dept = QLabel()
        self.lbl_dept.setStyleSheet("font-size: 13px; color: #a1a1aa; font-weight: 500;")
        header_layout.addWidget(self.lbl_dept)

        # Монохромные бейджи
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(8)

        badge_style = "background-color: #16161b; color: #e4e4e7; border: 1px solid #27272a; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 11px;"

        self.badge_qual = QLabel()
        self.badge_qual.setStyleSheet(badge_style)
        badges_layout.addWidget(self.badge_qual)

        self.badge_exp = QLabel()
        self.badge_exp.setStyleSheet(badge_style)
        badges_layout.addWidget(self.badge_exp)

        self.badge_status = QLabel()
        self.badge_status.setStyleSheet(badge_style)
        badges_layout.addWidget(self.badge_status)

        badges_layout.addStretch()
        header_layout.addLayout(badges_layout)
        main_layout.addWidget(header_card)

        # Контакты и личные данные
        info_card = QFrame()
        info_card.setObjectName("panelCard")
        info_layout = QHBoxLayout(info_card)
        info_layout.setContentsMargins(16, 12, 16, 12)

        self.lbl_phone = QLabel()
        self.lbl_email = QLabel()
        self.lbl_birth = QLabel()

        info_layout.addWidget(self.lbl_phone)
        info_layout.addWidget(self.lbl_email)
        info_layout.addWidget(self.lbl_birth)
        main_layout.addWidget(info_card)

        # Таблица закрепленных дисциплин и учебной нагрузки
        workload_card = QFrame()
        workload_card.setObjectName("panelCard")
        wl_layout = QVBoxLayout(workload_card)
        wl_layout.setContentsMargins(16, 14, 16, 14)
        wl_layout.setSpacing(10)

        wl_title = QLabel("Закрепленные дисциплины и объем педагогической нагрузки")
        wl_title.setStyleSheet("font-weight: 700; color: #ffffff; font-size: 13px;")
        wl_layout.addWidget(wl_title)

        filters = QHBoxLayout()
        self.combo_year, self.combo_semester = QComboBox(), QComboBox()
        self.combo_year.addItem("Все годы", None)
        for year in get_academic_years():
            self.combo_year.addItem(year, year)
        for label, value in [("Все семестры", None), ("1", 1), ("2", 2), ("Не указан (архив)", 0)]:
            self.combo_semester.addItem(label, value)
        filters.addWidget(self.combo_year)
        filters.addWidget(self.combo_semester)
        wl_layout.addLayout(filters)
        self.combo_year.currentIndexChanged.connect(self.load_data)
        self.combo_semester.currentIndexChanged.connect(self.load_data)
        self.table_wl = QTableWidget()
        self.table_wl.setColumnCount(8)
        self.table_wl.setHorizontalHeaderLabels([
            "Учебный год", "Семестр", "Группа", "Дисциплина",
            "Теория", "Практика", "Всего", "Часов в неделю",
        ])
        self.table_wl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_wl.setAlternatingRowColors(True)
        self.table_wl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_wl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_wl.verticalHeader().setVisible(False)
        wl_layout.addWidget(self.table_wl)

        # Итоговая строка
        self.lbl_total_hours = QLabel()
        self.lbl_total_hours.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_total_hours.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff; padding: 4px;")
        wl_layout.addWidget(self.lbl_total_hours)

        main_layout.addWidget(workload_card)

        # Нижняя панель
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        btn_close = QPushButton("Закрыть")
        btn_close.setObjectName("btnSecondary")
        btn_close.clicked.connect(self.accept)
        bottom_layout.addWidget(btn_close)

        main_layout.addLayout(bottom_layout)

    def load_data(self):
        teacher = get_teacher_by_id(self.teacher_id)
        if not teacher:
            QMessageBox.warning(self, "Ошибка", "Преподаватель не найден!")
            self.reject()
            return

        self.lbl_name.setText(teacher.full_name)
        dept_name = teacher.department.name if teacher.department else "Кафедра не назначена"
        self.lbl_dept.setText(f"Кафедра: {dept_name}")

        self.badge_qual.setText(f"Категория: {teacher.qualification or 'Без категории'}")
        self.badge_exp.setText(f"Стаж: {teacher.experience or 0} лет")
        self.badge_status.setText(f"Статус: {teacher.status or 'работает'}")

        # Контакты
        self.lbl_phone.setText(f"<b style='color:#71717a;'>Телефон:</b> {teacher.phone or '-'}")
        self.lbl_email.setText(f"<b style='color:#71717a;'>E-mail:</b> {teacher.email or '-'}")
        bdate = teacher.birth_date.strftime("%d.%m.%Y") if teacher.birth_date else "-"
        self.lbl_birth.setText(f"<b style='color:#71717a;'>Дата рожд.:</b> {bdate}")

        year, semester = self.combo_year.currentData(), self.combo_semester.currentData()
        workloads = [w for w in teacher.workloads if (not year or w.academic_year == year)
                     and (semester is None or w.semester == semester)]
        fill_table(self.table_wl, ["Учебный год", "Семестр", "Группа", "Дисциплина", "Теория", "Практика", "Всего", "Часов в неделю"],
            [[w.academic_year, semester_label(w.semester), w.pool.group_name if w.pool else "", w.discipline.name,
              w.hours_lecture, w.hours_practice, w.total_hours, w.hours_per_week] for w in workloads])
        self.lbl_total_hours.setText(f"За выбранный период: теория {sum(w.hours_lecture for w in workloads)} ч.; "
            f"практика {sum(w.hours_practice for w in workloads)} ч.; всего {sum(w.total_hours for w in workloads)} ч.")
