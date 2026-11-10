"""
Вкладка управления кафедрами и дисциплинами
Топ-монохромный дизайн в стиле TuneCloud.
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QSplitter, QGroupBox, QComboBox, QDialog, QGridLayout,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from services.department_service import (
    get_departments, add_department, update_department, delete_department,
    get_disciplines, add_discipline, update_discipline, delete_discipline
)
from services.auth_service import is_operator


# --- ДИАЛОГ КАФЕДРЫ ---
class DepartmentDialog(QDialog):
    def __init__(self, dept_id: Optional[int] = None, name: str = "", head: str = "", parent=None):
        super().__init__(parent)
        self.dept_id = dept_id
        self.setWindowTitle("Редактирование кафедры" if dept_id else "Добавление кафедры")
        self.setFixedWidth(480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Редактирование кафедры" if dept_id else "Новая кафедра")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("panelCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)

        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        grid.setHorizontalSpacing(12)

        grid.addWidget(QLabel("Название кафедры: *"), 0, 0)
        self.input_name = QLineEdit(name)
        self.input_name.setPlaceholderText("Например: Информационные системы...")
        grid.addWidget(self.input_name, 0, 1)

        grid.addWidget(QLabel("Заведующий:"), 1, 0)
        self.input_head = QLineEdit(head)
        self.input_head.setPlaceholderText("ФИО заведующего кафедрой...")
        grid.addWidget(self.input_head, 1, 1)

        card_layout.addLayout(grid)
        layout.addWidget(card)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Сохранить")
        btn_save.setObjectName("btnPrimary")
        btn_save.setMinimumWidth(110)
        btn_save.clicked.connect(self.on_save)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def on_save(self):
        name = self.input_name.text().strip()
        head = self.input_head.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название кафедры обязательно!")
            return

        if self.dept_id:
            ok, msg = update_department(self.dept_id, name, head)
        else:
            ok, msg, _ = add_department(name, head)

        if ok:
            QMessageBox.information(self, "Успех", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", msg)


# --- ДИАЛОГ ДИСЦИПЛИНЫ ---
class DisciplineDialog(QDialog):
    def __init__(self, disc_id: Optional[int] = None, code: str = "", name: str = "", dept_id: int = None, parent=None):
        super().__init__(parent)
        self.disc_id = disc_id
        self.setWindowTitle("Редактирование дисциплины" if disc_id else "Добавление дисциплины")
        self.setFixedWidth(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Редактирование дисциплины" if disc_id else "Новая дисциплина")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("panelCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)

        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        grid.setHorizontalSpacing(12)

        grid.addWidget(QLabel("Код дисциплины: *"), 0, 0)
        self.input_code = QLineEdit(code)
        self.input_code.setPlaceholderText("Например: ИС-101...")
        grid.addWidget(self.input_code, 0, 1)

        grid.addWidget(QLabel("Название дисциплины: *"), 1, 0)
        self.input_name = QLineEdit(name)
        self.input_name.setPlaceholderText("Например: Базы данных...")
        grid.addWidget(self.input_name, 1, 1)

        grid.addWidget(QLabel("Кафедра: *"), 2, 0)
        self.combo_dept = QComboBox()
        departments = get_departments()
        for d in departments:
            self.combo_dept.addItem(d.name, d.id)
        if dept_id:
            idx = self.combo_dept.findData(dept_id)
            if idx >= 0:
                self.combo_dept.setCurrentIndex(idx)
        grid.addWidget(self.combo_dept, 2, 1)

        card_layout.addLayout(grid)
        layout.addWidget(card)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Сохранить")
        btn_save.setObjectName("btnPrimary")
        btn_save.setMinimumWidth(110)
        btn_save.clicked.connect(self.on_save)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def on_save(self):
        code = self.input_code.text().strip()
        name = self.input_name.text().strip()
        dept_id = self.combo_dept.currentData()

        if self.disc_id:
            ok, msg = update_discipline(self.disc_id, code, name, dept_id)
        else:
            ok, msg, _ = add_discipline(code, name, dept_id)

        if ok:
            QMessageBox.information(self, "Успех", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", msg)


# --- ОСНОВНАЯ ВКЛАДКА ---
class DepartmentsTab(QWidget):
    status_updated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.refresh_departments()
        self.refresh_disciplines()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 1. Секция Кафедры
        dept_box = QGroupBox("Кафедры колледжа")
        dept_layout = QVBoxLayout(dept_box)
        dept_layout.setSpacing(10)

        dept_btns = QHBoxLayout()
        self.btn_add_dept = QPushButton("➕ Добавить")
        self.btn_add_dept.setObjectName("btnPrimary")
        self.btn_add_dept.clicked.connect(self.on_add_department)
        dept_btns.addWidget(self.btn_add_dept)

        self.btn_edit_dept = QPushButton("✏ Редактировать")
        self.btn_edit_dept.clicked.connect(self.on_edit_department)
        dept_btns.addWidget(self.btn_edit_dept)

        self.btn_del_dept = QPushButton("🗑 Удалить")
        self.btn_del_dept.setObjectName("btnDanger")
        self.btn_del_dept.clicked.connect(self.on_delete_department)
        dept_btns.addWidget(self.btn_del_dept)
        dept_layout.addLayout(dept_btns)

        self.table_depts = QTableWidget()
        self.table_depts.setColumnCount(3)
        self.table_depts.setHorizontalHeaderLabels(["ID", "Название кафедры", "Заведующий кафедрой"])
        self.table_depts.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_depts.setAlternatingRowColors(True)
        self.table_depts.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_depts.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_depts.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_depts.verticalHeader().setVisible(False)
        self.table_depts.itemSelectionChanged.connect(self.on_dept_selected)
        dept_layout.addWidget(self.table_depts)

        splitter.addWidget(dept_box)

        # 2. Секция Дисциплины
        disc_box = QGroupBox("Учебные дисциплины")
        disc_layout = QVBoxLayout(disc_box)
        disc_layout.setSpacing(10)

        disc_top = QHBoxLayout()
        disc_top.addWidget(QLabel("Кафедра:"))
        self.combo_dept_filter = QComboBox()
        self.combo_dept_filter.currentIndexChanged.connect(self.refresh_disciplines)
        disc_top.addWidget(self.combo_dept_filter, 1)
        disc_layout.addLayout(disc_top)

        disc_btns = QHBoxLayout()
        self.btn_add_disc = QPushButton("➕ Добавить")
        self.btn_add_disc.setObjectName("btnPrimary")
        self.btn_add_disc.clicked.connect(self.on_add_discipline)
        disc_btns.addWidget(self.btn_add_disc)

        self.btn_edit_disc = QPushButton("✏ Редактировать")
        self.btn_edit_disc.clicked.connect(self.on_edit_discipline)
        disc_btns.addWidget(self.btn_edit_disc)

        self.btn_del_disc = QPushButton("🗑 Удалить")
        self.btn_del_disc.setObjectName("btnDanger")
        self.btn_del_disc.clicked.connect(self.on_delete_discipline)
        disc_btns.addWidget(self.btn_del_disc)
        disc_layout.addLayout(disc_btns)

        self.table_disc = QTableWidget()
        self.table_disc.setColumnCount(4)
        self.table_disc.setHorizontalHeaderLabels(["ID", "Код", "Название дисциплины", "Кафедра"])
        self.table_disc.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_disc.setAlternatingRowColors(True)
        self.table_disc.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_disc.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_disc.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_disc.verticalHeader().setVisible(False)
        disc_layout.addWidget(self.table_disc)

        splitter.addWidget(disc_box)
        main_layout.addWidget(splitter)

        self.apply_role_permissions()

    def apply_role_permissions(self):
        can_edit = is_operator()
        self.btn_add_dept.setVisible(can_edit)
        self.btn_edit_dept.setVisible(can_edit)
        self.btn_del_dept.setVisible(can_edit)
        self.btn_add_disc.setVisible(can_edit)
        self.btn_edit_disc.setVisible(can_edit)
        self.btn_del_disc.setVisible(can_edit)

    def refresh_departments(self):
        depts = get_departments()
        self.table_depts.setRowCount(len(depts))
        for row, d in enumerate(depts):
            self.table_depts.setItem(row, 0, QTableWidgetItem(str(d.id)))
            self.table_depts.setItem(row, 1, QTableWidgetItem(d.name))
            self.table_depts.setItem(row, 2, QTableWidgetItem(d.head_name or "-"))

        self.combo_dept_filter.blockSignals(True)
        curr = self.combo_dept_filter.currentData()
        self.combo_dept_filter.clear()
        self.combo_dept_filter.addItem("Все кафедры", 0)
        for d in depts:
            self.combo_dept_filter.addItem(d.name, d.id)
        if curr:
            idx = self.combo_dept_filter.findData(curr)
            if idx >= 0:
                self.combo_dept_filter.setCurrentIndex(idx)
        self.combo_dept_filter.blockSignals(False)

    def refresh_disciplines(self):
        dept_id = self.combo_dept_filter.currentData()
        disciplines = get_disciplines(department_id=dept_id)
        self.table_disc.setRowCount(len(disciplines))
        for row, disc in enumerate(disciplines):
            self.table_disc.setItem(row, 0, QTableWidgetItem(str(disc.id)))
            self.table_disc.setItem(row, 1, QTableWidgetItem(disc.code))
            self.table_disc.setItem(row, 2, QTableWidgetItem(disc.name))
            dept_name = disc.department.name if disc.department else "-"
            self.table_disc.setItem(row, 3, QTableWidgetItem(dept_name))

    def on_dept_selected(self):
        items = self.table_depts.selectedItems()
        if items:
            row = items[0].row()
            dept_id = int(self.table_depts.item(row, 0).text())
            idx = self.combo_dept_filter.findData(dept_id)
            if idx >= 0:
                self.combo_dept_filter.setCurrentIndex(idx)

    def on_add_department(self):
        dlg = DepartmentDialog(parent=self)
        if dlg.exec():
            self.refresh_departments()
            self.refresh_disciplines()

    def on_edit_department(self):
        items = self.table_depts.selectedItems()
        if not items:
            QMessageBox.information(self, "Выбор", "Выберите кафедру в таблице для редактирования!")
            return
        row = items[0].row()
        did = int(self.table_depts.item(row, 0).text())
        name = self.table_depts.item(row, 1).text()
        head = self.table_depts.item(row, 2).text()
        if head == "-":
            head = ""

        dlg = DepartmentDialog(dept_id=did, name=name, head=head, parent=self)
        if dlg.exec():
            self.refresh_departments()
            self.refresh_disciplines()

    def on_delete_department(self):
        items = self.table_depts.selectedItems()
        if not items:
            QMessageBox.information(self, "Выбор", "Выберите кафедру в таблице для удаления!")
            return
        row = items[0].row()
        did = int(self.table_depts.item(row, 0).text())
        name = self.table_depts.item(row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить кафедру '{name}'?\nСвязанные дисциплины и преподаватели также будут затронуты!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            ok, msg = delete_department(did)
            if ok:
                QMessageBox.information(self, "Успех", msg)
                self.refresh_departments()
                self.refresh_disciplines()
            else:
                QMessageBox.critical(self, "Ошибка удаления", msg)

    def on_add_discipline(self):
        cur_dept = self.combo_dept_filter.currentData()
        dlg = DisciplineDialog(dept_id=cur_dept if cur_dept > 0 else None, parent=self)
        if dlg.exec():
            self.refresh_disciplines()

    def on_edit_discipline(self):
        items = self.table_disc.selectedItems()
        if not items:
            QMessageBox.information(self, "Выбор", "Выберите дисциплину в таблице для редактирования!")
            return
        row = items[0].row()
        disc_id = int(self.table_disc.item(row, 0).text())
        code = self.table_disc.item(row, 1).text()
        name = self.table_disc.item(row, 2).text()
        dept_name = self.table_disc.item(row, 3).text()

        departments = get_departments()
        target_d = next((d for d in departments if d.name == dept_name), None)
        did = target_d.id if target_d else None

        dlg = DisciplineDialog(disc_id=disc_id, code=code, name=name, dept_id=did, parent=self)
        if dlg.exec():
            self.refresh_disciplines()

    def on_delete_discipline(self):
        items = self.table_disc.selectedItems()
        if not items:
            QMessageBox.information(self, "Выбор", "Выберите дисциплину в таблице для удаления!")
            return
        row = items[0].row()
        disc_id = int(self.table_disc.item(row, 0).text())
        name = self.table_disc.item(row, 2).text()

        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить дисциплину '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            ok, msg = delete_discipline(disc_id)
            if ok:
                QMessageBox.information(self, "Успех", msg)
                self.refresh_disciplines()
            else:
                QMessageBox.critical(self, "Ошибка удаления", msg)
