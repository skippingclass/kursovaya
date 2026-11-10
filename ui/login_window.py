"""
Окно авторизации (LoginWindow)
Топ-монохромный дизайн в стиле TuneCloud.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config import APP_NAME, COLLEGE_NAME
from services.auth_service import authenticate
from ui.db_settings_dialog import DBSettingsDialog


class LoginWindow(QDialog):
    """Окно авторизации пользователя"""
    login_successful = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Авторизация — {APP_NAME}")
        self.setFixedSize(440, 530)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 24)
        main_layout.setSpacing(16)

        # Контейнер-карточка (TuneCloud style)
        card_frame = QFrame()
        card_frame.setObjectName("panelCard")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(14)

        # Заголовок
        college_lbl = QLabel(COLLEGE_NAME.upper())
        college_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        college_lbl.setStyleSheet("color: #71717a; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        card_layout.addWidget(college_lbl)

        title_lbl = QLabel(APP_NAME)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("color: #ffffff; font-size: 19px; font-weight: 800; margin-top: 2px;")
        card_layout.addWidget(title_lbl)

        sub_lbl = QLabel("Вход в систему учета и распределения нагрузки")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("color: #a1a1aa; font-size: 12px; margin-bottom: 8px;")
        card_layout.addWidget(sub_lbl)

        # Разделитель
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("border: none; background-color: #27272a; height: 1px; margin: 4px 0px 8px 0px;")
        card_layout.addWidget(sep)

        # Поля ввода
        form_box = QVBoxLayout()
        form_box.setSpacing(12)

        # Логин
        login_label = QLabel("Имя пользователя:")
        login_label.setStyleSheet("color: #e4e4e7; font-weight: 600; font-size: 12px;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("admin / operator / methodist")
        self.username_input.setFixedHeight(40)
        self.username_input.setText("admin")
        form_box.addWidget(login_label)
        form_box.addWidget(self.username_input)

        # Пароль
        pwd_label = QLabel("Пароль:")
        pwd_label.setStyleSheet("color: #e4e4e7; font-weight: 600; font-size: 12px;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(40)
        self.password_input.setText("admin123")
        self.password_input.returnPressed.connect(self.handle_login)
        self.username_input.returnPressed.connect(lambda: self.password_input.setFocus())
        form_box.addWidget(pwd_label)
        form_box.addWidget(self.password_input)

        card_layout.addLayout(form_box)

        # Кнопка входа (Акцентная белая)
        card_layout.addSpacing(6)
        self.btn_login = QPushButton("Войти в систему")
        self.btn_login.setObjectName("btnPrimary")
        self.btn_login.setFixedHeight(42)
        self.btn_login.clicked.connect(self.handle_login)
        card_layout.addWidget(self.btn_login)

        # Быстрые пресеты ролей (Pills)
        roles_box = QVBoxLayout()
        roles_box.setSpacing(6)
        roles_lbl = QLabel("Быстрый выбор учетной записи для теста:")
        roles_lbl.setStyleSheet("font-size: 11px; color: #71717a; font-weight: 600;")
        roles_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        roles_box.addWidget(roles_lbl)

        pills_layout = QHBoxLayout()
        pills_layout.setSpacing(6)

        btn_admin = QPushButton("Администратор")
        btn_admin.setStyleSheet("font-size: 11px; padding: 5px 8px; background-color: #16161b; border: 1px solid #27272a; border-radius: 6px; color: #d4d4d8;")
        btn_admin.clicked.connect(lambda: self.set_credentials("admin", "admin123"))
        pills_layout.addWidget(btn_admin)

        btn_op = QPushButton("Зав. кафедрой")
        btn_op.setStyleSheet("font-size: 11px; padding: 5px 8px; background-color: #16161b; border: 1px solid #27272a; border-radius: 6px; color: #d4d4d8;")
        btn_op.clicked.connect(lambda: self.set_credentials("operator", "operator123"))
        pills_layout.addWidget(btn_op)

        btn_meth = QPushButton("Методист")
        btn_meth.setStyleSheet("font-size: 11px; padding: 5px 8px; background-color: #16161b; border: 1px solid #27272a; border-radius: 6px; color: #d4d4d8;")
        btn_meth.clicked.connect(lambda: self.set_credentials("methodist", "methodist123"))
        pills_layout.addWidget(btn_meth)

        roles_box.addLayout(pills_layout)
        card_layout.addLayout(roles_box)

        main_layout.addWidget(card_frame)

        # Ссылка на настройки СУБД внизу
        btn_db_settings = QPushButton("⚙ Параметры базы данных (PostgreSQL / SQLite)")
        btn_db_settings.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #71717a;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        btn_db_settings.clicked.connect(self.open_db_settings)
        main_layout.addWidget(btn_db_settings, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_credentials(self, username: str, pwd: str):
        self.username_input.setText(username)
        self.password_input.setText(pwd)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        success, err_msg, user_info = authenticate(username, password)

        if success and user_info:
            self.login_successful.emit(user_info)
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Ошибка авторизации",
                err_msg or "Неверный логин или пароль!"
            )
            self.password_input.clear()
            self.password_input.setFocus()

    def open_db_settings(self):
        dialog = DBSettingsDialog(self)
        dialog.exec()
