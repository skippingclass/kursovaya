"""
Диалоговое окно настроек базы данных (PostgreSQL / SQLite) и Резервного копирования
Топ-монохромный дизайн в стиле TuneCloud.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QButtonGroup, QFrame,
    QMessageBox, QFileDialog, QSpinBox, QWidget
)
from PyQt6.QtCore import Qt
from config import load_config, save_config
from database.connection import test_connection, reset_engine, init_db
from database.backup import create_backup, restore_backup


class DBSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Параметры базы данных")
        self.setFixedWidth(560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.config = load_config()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        # Заголовок окна
        title_label = QLabel("Управление хранилищем данных")
        title_label.setStyleSheet("font-size: 17px; font-weight: 700; color: #ffffff;")
        layout.addWidget(title_label)

        sub_label = QLabel("Выберите тип используемой СУБД для хранения сведений о преподавателях и нагрузке:")
        sub_label.setStyleSheet("color: #a1a1aa; font-size: 12px; margin-bottom: 4px;")
        sub_label.setWordWrap(True)
        layout.addWidget(sub_label)

        # 1. Карточка выбора типа СУБД (Селектор)
        type_card = QFrame()
        type_card.setObjectName("panelCard")
        type_layout = QVBoxLayout(type_card)
        type_layout.setContentsMargins(16, 14, 16, 14)
        type_layout.setSpacing(10)

        self.rb_sqlite = QRadioButton("SQLite — Автономная локальная база данных (без сервера)")
        self.rb_postgres = QRadioButton("PostgreSQL — Корпоративный сетевой сервер колледжа")

        self.btn_group = QButtonGroup(self)
        self.btn_group.addButton(self.rb_sqlite)
        self.btn_group.addButton(self.rb_postgres)

        type_layout.addWidget(self.rb_sqlite)
        type_layout.addWidget(self.rb_postgres)
        layout.addWidget(type_card)

        # 2a. Карточка информации о SQLite
        self.sqlite_card = QFrame()
        self.sqlite_card.setObjectName("panelCard")
        sqlite_layout = QVBoxLayout(self.sqlite_card)
        sqlite_layout.setContentsMargins(16, 16, 16, 16)
        sqlite_layout.setSpacing(8)

        sqlite_header = QLabel("Параметры локального хранилища SQLite")
        sqlite_header.setStyleSheet("font-weight: 700; color: #ffffff; font-size: 13px;")
        sqlite_layout.addWidget(sqlite_header)

        sqlite_info = QLabel(
            "Локальный режим активен. Все таблицы и записи хранятся на этом компьютере.\n"
            f"Файл базы данных: {self.config.get('sqlite_path', 'data/college_teachers.db')}\n\n"
            "Серверные порты и учетные записи не требуются."
        )
        sqlite_info.setStyleSheet("color: #a1a1aa; font-size: 12px; line-height: 1.4;")
        sqlite_info.setWordWrap(True)
        sqlite_layout.addWidget(sqlite_info)
        layout.addWidget(self.sqlite_card)

        # 2b. Карточка параметров PostgreSQL
        self.pg_card = QFrame()
        self.pg_card.setObjectName("panelCard")
        pg_layout = QVBoxLayout(self.pg_card)
        pg_layout.setContentsMargins(16, 16, 16, 16)
        pg_layout.setSpacing(12)

        pg_header = QLabel("Параметры соединения с сервером PostgreSQL")
        pg_header.setStyleSheet("font-weight: 700; color: #ffffff; font-size: 13px;")
        pg_layout.addWidget(pg_header)

        # Хост и Порт
        host_port_layout = QHBoxLayout()
        host_port_layout.setSpacing(12)

        host_box = QVBoxLayout()
        host_box.setSpacing(4)
        host_box.addWidget(QLabel("Хост / IP-адрес сервера:"))
        self.input_host = QLineEdit(self.config.get("pg_host", "localhost"))
        self.input_host.setPlaceholderText("localhost или IP")
        host_box.addWidget(self.input_host)
        host_port_layout.addLayout(host_box, 3)

        port_box = QVBoxLayout()
        port_box.setSpacing(4)
        port_box.addWidget(QLabel("Порт:"))
        self.input_port = QSpinBox()
        self.input_port.setRange(1, 65535)
        self.input_port.setValue(int(self.config.get("pg_port", 5432)))
        port_box.addWidget(self.input_port)
        host_port_layout.addLayout(port_box, 1)

        pg_layout.addLayout(host_port_layout)

        # Имя базы данных
        db_box = QVBoxLayout()
        db_box.setSpacing(4)
        db_box.addWidget(QLabel("Имя базы данных:"))
        self.input_db = QLineEdit(self.config.get("pg_database", "college_teachers"))
        self.input_db.setPlaceholderText("college_teachers")
        db_box.addWidget(self.input_db)
        pg_layout.addLayout(db_box)

        # Пользователь и Пароль
        cred_layout = QHBoxLayout()
        cred_layout.setSpacing(12)

        user_box = QVBoxLayout()
        user_box.setSpacing(4)
        user_box.addWidget(QLabel("Пользователь (User):"))
        self.input_user = QLineEdit(self.config.get("pg_user", "postgres"))
        self.input_user.setPlaceholderText("postgres")
        user_box.addWidget(self.input_user)
        cred_layout.addLayout(user_box)

        pwd_box = QVBoxLayout()
        pwd_box.setSpacing(4)
        pwd_box.addWidget(QLabel("Пароль:"))
        self.input_pwd = QLineEdit(self.config.get("pg_password", ""))
        self.input_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pwd.setPlaceholderText("••••••••")
        pwd_box.addWidget(self.input_pwd)
        cred_layout.addLayout(pwd_box)

        pg_layout.addLayout(cred_layout)

        # Кнопка проверки связи
        self.btn_test = QPushButton("🔍 Проверить соединение с PostgreSQL")
        self.btn_test.clicked.connect(self.on_test_connection)
        pg_layout.addWidget(self.btn_test)

        layout.addWidget(self.pg_card)

        # 3. Карточка резервного копирования
        backup_card = QFrame()
        backup_card.setObjectName("panelCard")
        backup_layout = QVBoxLayout(backup_card)
        backup_layout.setContentsMargins(16, 14, 16, 14)
        backup_layout.setSpacing(8)

        backup_title = QLabel("Резервное копирование и восстановление")
        backup_title.setStyleSheet("font-weight: 700; color: #ffffff; font-size: 13px;")
        backup_layout.addWidget(backup_title)

        backup_btns = QHBoxLayout()
        backup_btns.setSpacing(10)

        btn_backup = QPushButton("💾 Экспорт бэкапа (.json)")
        btn_backup.clicked.connect(self.on_create_backup)
        backup_btns.addWidget(btn_backup)

        btn_restore = QPushButton("📂 Восстановить из файла")
        btn_restore.clicked.connect(self.on_restore_backup)
        backup_btns.addWidget(btn_restore)

        backup_layout.addLayout(backup_btns)
        layout.addWidget(backup_card)

        # 4. Нижние кнопки (Сохранить / Отмена)
        layout.addSpacing(6)
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        btn_cancel = QPushButton("Отмена")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        bottom_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Сохранить и применить")
        btn_save.setObjectName("btnPrimary")
        btn_save.setMinimumWidth(180)
        btn_save.clicked.connect(self.on_save)
        bottom_layout.addWidget(btn_save)

        layout.addLayout(bottom_layout)

        # Подключение обработчиков
        self.rb_sqlite.toggled.connect(self.on_type_changed)
        if self.config.get("db_type") == "postgresql":
            self.rb_postgres.setChecked(True)
        else:
            self.rb_sqlite.setChecked(True)
        self.on_type_changed()

    def on_type_changed(self):
        is_pg = self.rb_postgres.isChecked()
        self.pg_card.setVisible(is_pg)
        self.sqlite_card.setVisible(not is_pg)
        self.adjustSize()

    def get_current_db_url(self) -> str:
        if self.rb_postgres.isChecked():
            host = self.input_host.text().strip()
            port = self.input_port.value()
            dbname = self.input_db.text().strip()
            user = self.input_user.text().strip()
            pwd = self.input_pwd.text()
            if pwd:
                return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{dbname}"
            return f"postgresql+psycopg2://{user}@{host}:{port}/{dbname}"
        else:
            sqlite_path = self.config.get("sqlite_path", "college_teachers.db")
            return f"sqlite:///{sqlite_path}"

    def on_test_connection(self):
        url = self.get_current_db_url()
        self.btn_test.setEnabled(False)
        self.btn_test.setText("⏳ Проверка соединения...")
        self.repaint()

        ok, msg = test_connection(url)
        self.btn_test.setEnabled(True)
        self.btn_test.setText("🔍 Проверить соединение с PostgreSQL")

        if ok:
            QMessageBox.information(self, "Тест соединения", "Соединение с базой данных PostgreSQL успешно установлено!")
        else:
            QMessageBox.critical(self, "Ошибка подключения", f"Не удалось подключиться к серверу PostgreSQL:\n\n{msg}")

    def on_save(self):
        self.config["db_type"] = "postgresql" if self.rb_postgres.isChecked() else "sqlite"
        self.config["pg_host"] = self.input_host.text().strip()
        self.config["pg_port"] = self.input_port.value()
        self.config["pg_database"] = self.input_db.text().strip()
        self.config["pg_user"] = self.input_user.text().strip()
        self.config["pg_password"] = self.input_pwd.text()

        save_config(self.config)
        reset_engine()
        try:
            init_db()
            QMessageBox.information(self, "Успешно", "Конфигурация сохранена. Хранилище данных готово к работе!")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Предупреждение", f"Конфигурация сохранена, однако при обращении к БД возникла ошибка:\n\n{e}")
            self.accept()

    def on_create_backup(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить резервную копию",
            "college_teachers_backup.json",
            "JSON файлы (*.json)"
        )
        if filepath:
            ok, msg = create_backup(filepath)
            if ok:
                QMessageBox.information(self, "Резервное копирование", msg)
            else:
                QMessageBox.critical(self, "Ошибка", msg)

    def on_restore_backup(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать файл резервной копии",
            "",
            "JSON файлы (*.json)"
        )
        if filepath:
            confirm = QMessageBox.question(
                self,
                "Подтверждение восстановления",
                "ВНИМАНИЕ! Восстановление перезапишет все текущие записи в базе данных!\nПродолжить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                ok, msg = restore_backup(filepath)
                if ok:
                    QMessageBox.information(self, "Восстановление", msg)
                else:
                    QMessageBox.critical(self, "Ошибка восстановления", msg)
