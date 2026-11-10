"""
Вкладка управления пользователями системы (Use Case: Управление пользователями)
Топ-монохромный дизайн в стиле TuneCloud.
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QComboBox, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from services.user_service import get_users, get_roles, add_user, update_user, delete_user


# --- ДИАЛОГ ДОБАВЛЕНИЯ / РЕДАКТИРОВАНИЯ ПОЛЬЗОВАТЕЛЯ ---
class UserDialog(QDialog):
    def __init__(self, user_id: Optional[int] = None, username: str = "", role_id: int = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        is_edit = user_id is not None
        self.setWindowTitle("Редактирование пользователя" if is_edit else "Создание пользователя")
        self.setFixedWidth(480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Редактирование аккаунта" if is_edit else "Новый пользователь системы")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("panelCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)

        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        grid.setHorizontalSpacing(12)

        # 1. Логин
        grid.addWidget(QLabel("Логин: *"), 0, 0)
        self.input_username = QLineEdit(username)
        self.input_username.setPlaceholderText("Логин учетной записи...")
        grid.addWidget(self.input_username, 0, 1)

        # 2. Пароль
        pwd_label_text = "Новый пароль (опционально):" if is_edit else "Пароль: *"
        grid.addWidget(QLabel(pwd_label_text), 1, 0)
        self.input_pwd = QLineEdit()
        self.input_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pwd.setPlaceholderText("Минимум 4 символа...")
        grid.addWidget(self.input_pwd, 1, 1)

        # 3. Роль
        grid.addWidget(QLabel("Роль доступа: *"), 2, 0)
        self.combo_role = QComboBox()
        roles = get_roles()
        for r in roles:
            self.combo_role.addItem(r.name, r.id)
        if role_id:
            idx = self.combo_role.findData(role_id)
            if idx >= 0:
                self.combo_role.setCurrentIndex(idx)
        grid.addWidget(self.combo_role, 2, 1)

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
        uname = self.input_username.text().strip()
        pwd = self.input_pwd.text()
        role_id = self.combo_role.currentData()

        if self.user_id:
            ok, msg = update_user(self.user_id, uname, role_id, pwd)
        else:
            ok, msg, _ = add_user(uname, pwd, role_id)

        if ok:
            QMessageBox.information(self, "Успех", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", msg)


# --- ОСНОВНАЯ ВКЛАДКА ---
class UsersTab(QWidget):
    status_updated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        top_layout = QHBoxLayout()
        title = QLabel("Управление учетными записями сотрудников")
        title.setStyleSheet("font-weight: 700; font-size: 15px; color: #ffffff;")
        top_layout.addWidget(title)
        top_layout.addStretch()

        btn_add = QPushButton("➕ Создать пользователя")
        btn_add.setObjectName("btnPrimary")
        btn_add.clicked.connect(self.on_add_user)
        top_layout.addWidget(btn_add)

        btn_edit = QPushButton("✏ Редактировать")
        btn_edit.clicked.connect(self.on_edit_user)
        top_layout.addWidget(btn_edit)

        btn_del = QPushButton("🗑 Удалить")
        btn_del.setObjectName("btnDanger")
        btn_del.clicked.connect(self.on_delete_user)
        top_layout.addWidget(btn_del)

        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Имя пользователя (Логин)", "Назначенная роль"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.on_edit_user)
        layout.addWidget(self.table)

    def refresh_table(self):
        users = get_users()
        self.table.setRowCount(len(users))
        for row, u in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(u.id)))
            self.table.setItem(row, 1, QTableWidgetItem(u.username))
            role_name = u.role.name if u.role else "Без роли"
            self.table.setItem(row, 2, QTableWidgetItem(role_name))

        self.status_updated.emit(f"Всего пользователей в системе: {len(users)}")

    def on_add_user(self):
        dlg = UserDialog(parent=self)
        if dlg.exec():
            self.refresh_table()

    def on_edit_user(self):
        items = self.table.selectedItems()
        if not items:
            QMessageBox.information(self, "Выбор", "Выберите пользователя для редактирования!")
            return
        row = items[0].row()
        uid = int(self.table.item(row, 0).text())
        uname = self.table.item(row, 1).text()
        role_name = self.table.item(row, 2).text()

        roles = get_roles()
        target_r = next((r for r in roles if r.name == role_name), None)
        rid = target_r.id if target_r else None

        dlg = UserDialog(user_id=uid, username=uname, role_id=rid, parent=self)
        if dlg.exec():
            self.refresh_table()

    def on_delete_user(self):
        items = self.table.selectedItems()
        if not items:
            QMessageBox.information(self, "Выбор", "Выберите пользователя для удаления!")
            return
        row = items[0].row()
        uid = int(self.table.item(row, 0).text())
        uname = self.table.item(row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить пользователя '{uname}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            ok, msg = delete_user(uid)
            if ok:
                QMessageBox.information(self, "Успех", msg)
                self.refresh_table()
            else:
                QMessageBox.critical(self, "Ошибка удаления", msg)
