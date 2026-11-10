"""
Главное окно приложения (MainWindow)
Топ-монохромный дизайн в стиле TuneCloud.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QMenuBar, QMenu, QStatusBar, QMessageBox,
    QPushButton, QFrame, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont
from config import APP_NAME, COLLEGE_NAME, APP_VERSION, load_config, BASE_DIR
from services.auth_service import get_current_user, logout, is_admin, is_operator
from database.backup import create_backup, restore_backup
from ui.teacher_tab import TeacherTab
from ui.workload_tab import WorkloadTab
from ui.departments_tab import DepartmentsTab
from ui.reports_tab import ReportsTab
from ui.users_tab import UsersTab
from ui.db_settings_dialog import DBSettingsDialog


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — {COLLEGE_NAME}")
        self.resize(1220, 790)
        self.setMinimumSize(960, 620)

        self.init_ui()
        self.apply_role_permissions()

    def init_ui(self):
        # 1. Меню
        self.create_menu_bar()

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(10)

        # 2. Верхняя информационная панель (Header Banner - TuneCloud style)
        header_frame = QFrame()
        header_frame.setObjectName("panelCard")
        header_frame.setStyleSheet("""
            QFrame#panelCard {
                background-color: #0f0f13;
                border: 1px solid #1f1f25;
                border-radius: 10px;
                padding: 10px 18px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_college = QLabel(COLLEGE_NAME.upper())
        lbl_college.setStyleSheet("font-size: 11px; font-weight: 700; color: #71717a; letter-spacing: 0.5px;")
        lbl_app = QLabel(APP_NAME)
        lbl_app.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
        title_box.addWidget(lbl_college)
        title_box.addWidget(lbl_app)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Данные пользователя
        user_info = get_current_user() or {}
        uname = user_info.get("username", "Пользователь")
        rname = user_info.get("role_name", "Гость")

        user_badge = QFrame()
        user_badge.setStyleSheet("background-color: #16161b; border: 1px solid #27272a; border-radius: 8px; padding: 4px 12px;")
        badge_layout = QHBoxLayout(user_badge)
        badge_layout.setContentsMargins(6, 2, 6, 2)
        badge_layout.setSpacing(10)

        user_vbox = QVBoxLayout()
        user_vbox.setSpacing(1)
        lbl_user = QLabel(f"● {uname}")
        lbl_user.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff;")
        lbl_role = QLabel(rname)
        lbl_role.setStyleSheet("font-size: 11px; color: #a1a1aa;")
        user_vbox.addWidget(lbl_user)
        user_vbox.addWidget(lbl_role)
        badge_layout.addLayout(user_vbox)

        btn_logout = QPushButton("Выход")
        btn_logout.setObjectName("btnSecondary")
        btn_logout.setStyleSheet("padding: 5px 12px; font-size: 12px;")
        btn_logout.clicked.connect(self.on_logout)
        badge_layout.addWidget(btn_logout)

        header_layout.addWidget(user_badge)
        main_layout.addWidget(header_frame)

        # 3. Вкладки (QTabWidget)
        self.tabs = QTabWidget()

        self.tab_teachers = TeacherTab(self)
        self.tab_teachers.status_updated.connect(self.set_status)
        self.tabs.addTab(self.tab_teachers, "Преподаватели")

        self.tab_workload = WorkloadTab(self)
        self.tab_workload.status_updated.connect(self.set_status)
        self.tabs.addTab(self.tab_workload, "Учебная нагрузка")

        self.tab_departments = DepartmentsTab(self)
        self.tab_departments.status_updated.connect(self.set_status)
        self.tabs.addTab(self.tab_departments, "Кафедры и дисциплины")

        self.tab_reports = ReportsTab(self)
        self.tab_reports.status_updated.connect(self.set_status)
        self.tabs.addTab(self.tab_reports, "Отчеты и экспорт")

        # Вкладка пользователей (только для Администратора)
        self.tab_users = UsersTab(self)
        self.tab_users.status_updated.connect(self.set_status)
        self.users_tab_index = self.tabs.addTab(self.tab_users, "Пользователи")

        self.tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tabs)

        # 4. Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        cfg = load_config()
        db_type_name = "PostgreSQL" if cfg.get("db_type") == "postgresql" else "SQLite"
        self.lbl_db_status = QLabel(f"СУБД: {db_type_name}  |  Пользователь: {uname} ({rname})")
        self.lbl_db_status.setStyleSheet("color: #71717a; font-size: 11px;")
        self.status_bar.addPermanentWidget(self.lbl_db_status)
        self.set_status("Система готова к работе")

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # Меню: Файл
        file_menu = menu_bar.addMenu("Файл")

        act_switch_user = QAction("Сменить пользователя...", self)
        act_switch_user.setShortcut("Ctrl+L")
        act_switch_user.triggered.connect(self.on_logout)
        file_menu.addAction(act_switch_user)

        file_menu.addSeparator()

        act_exit = QAction("Выход из программы", self)
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # Меню: База данных
        self.db_menu = menu_bar.addMenu("База данных")

        act_db_settings = QAction("Параметры подключения (PostgreSQL / SQLite)...", self)
        act_db_settings.triggered.connect(self.open_db_settings)
        self.db_menu.addAction(act_db_settings)

        self.db_menu.addSeparator()

        self.act_backup = QAction("Создать резервную копию БД...", self)
        self.act_backup.triggered.connect(self.on_backup)
        self.db_menu.addAction(self.act_backup)

        self.act_restore = QAction("Восстановить БД из копии...", self)
        self.act_restore.triggered.connect(self.on_restore)
        self.db_menu.addAction(self.act_restore)

        # Меню: Отчеты
        reports_menu = menu_bar.addMenu("Отчеты")

        act_rep_kadry = QAction("Кадровый состав преподавателей", self)
        act_rep_kadry.triggered.connect(lambda: self.switch_to_reports(0))
        reports_menu.addAction(act_rep_kadry)

        act_rep_workload = QAction("Ведомость распределения нагрузки", self)
        act_rep_workload.triggered.connect(lambda: self.switch_to_reports(1))
        reports_menu.addAction(act_rep_workload)

        act_rep_stats = QAction("Сводная статистика по кафедрам", self)
        act_rep_stats.triggered.connect(lambda: self.switch_to_reports(2))
        reports_menu.addAction(act_rep_stats)

        # Меню: Справка
        help_menu = menu_bar.addMenu("Справка")

        act_guide = QAction("Руководство пользователя", self)
        act_guide.triggered.connect(self.show_user_guide)
        help_menu.addAction(act_guide)
        for label, filename in [("Руководство разработчика", "Руководство_разработчика.pdf"),
                                ("Требования к программному обеспечению", "Требования_к_ПО.pdf")]:
            action = QAction(label, self)
            action.triggered.connect(lambda checked=False, name=filename: self.open_document(name))
            help_menu.addAction(action)

        act_about = QAction("О программе", self)
        act_about.triggered.connect(self.show_about_dialog)
        help_menu.addAction(act_about)

    def apply_role_permissions(self):
        user = get_current_user() or {}
        is_adm = is_admin()

        self.tabs.setTabVisible(self.users_tab_index, is_adm)
        self.act_backup.setEnabled(is_adm)
        self.act_restore.setEnabled(is_adm)

        self.tab_teachers.apply_role_permissions()
        self.tab_workload.apply_role_permissions()
        self.tab_departments.apply_role_permissions()

    def set_status(self, message: str):
        self.status_bar.showMessage(message, 5000)

    def on_tab_changed(self, index: int):
        if index == 0:
            self.tab_teachers.load_filters()
            self.tab_teachers.refresh_table()
        elif index == 1:
            self.tab_workload.load_filters()
            self.tab_workload.refresh_table()
        elif index == 2:
            self.tab_departments.refresh_departments()
            self.tab_departments.refresh_disciplines()
        elif index == 3:
            self.tab_reports.load_filters()
            self.tab_reports.generate_report()
        elif index == 4:
            self.tab_users.refresh_table()

    def switch_to_reports(self, report_idx: int):
        self.tabs.setCurrentIndex(3)
        self.tab_reports.combo_type.setCurrentIndex(report_idx)

    def open_db_settings(self):
        dlg = DBSettingsDialog(self)
        if dlg.exec():
            cfg = load_config()
            db_type_name = "PostgreSQL" if cfg.get("db_type") == "postgresql" else "SQLite"
            u = get_current_user() or {}
            self.lbl_db_status.setText(f"СУБД: {db_type_name}  |  Пользователь: {u.get('username')} ({u.get('role_name')})")
            self.on_tab_changed(self.tabs.currentIndex())

    def on_backup(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить резервную копию базы данных",
            "college_teachers_backup.json",
            "JSON файлы (*.json)"
        )
        if filepath:
            ok, msg = create_backup(filepath)
            if ok:
                QMessageBox.information(self, "Резервное копирование", msg)
            else:
                QMessageBox.critical(self, "Ошибка", msg)

    def on_restore(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать файл резервной копии",
            "",
            "JSON файлы (*.json)"
        )
        if filepath:
            confirm = QMessageBox.question(
                self,
                "Подтверждение",
                "ВНИМАНИЕ! Восстановление перезапишет все текущие записи в базе данных!\nПродолжить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                ok, msg = restore_backup(filepath)
                if ok:
                    QMessageBox.information(self, "Восстановление", msg)
                    self.on_tab_changed(self.tabs.currentIndex())
                else:
                    QMessageBox.critical(self, "Ошибка", msg)

    def show_user_guide(self):
        if self.open_document("Руководство_пользователя.pdf"):
            return
        guide_text = f"""
        <h3>Руководство пользователя</h3>
        <p><b>{COLLEGE_NAME}</b></p>
        <p><b>Основные возможности системы:</b></p>
        <ul>
            <li><b>Преподаватели:</b> Ведение личных дел, мгновенная фильтрация по ФИО, кафедре, стажу и категории.</li>
            <li><b>Учебная нагрузка:</b> Добавьте общий план для группы, года и семестра. Выберите строку и назначьте часы преподавателю. При отмене назначения часы возвращаются в план.</li>
            <li><b>Кафедры и дисциплины:</b> Справочники подразделений и учебных предметов.</li>
            <li><b>Отчеты:</b> Экспорт сводных ведомостей в Excel (.xlsx) и PDF (.pdf).</li>
            <li><b>Пользователи:</b> Администрирование учетных записей (для роли 'Администратор').</li>
        </ul>
        """
        QMessageBox.about(self, "Руководство пользователя", guide_text)

    def open_document(self, filename):
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        path = BASE_DIR / "docs" / filename
        return path.exists() and QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def show_about_dialog(self):
        about_text = f"""
        <h3>{APP_NAME} v{APP_VERSION}</h3>
        <p><b>Учебное заведение:</b> {COLLEGE_NAME}</p>
        <p><b>Автор:</b> Евполов Владислав, группа П-24-67Б</p>
        <p><b>GitHub:</b> <a href="https://github.com/skippingclass">skippingclass</a></p>
        <p><b>Стек технологий:</b> Python 3.12, PyQt6, PostgreSQL / SQLite (SQLAlchemy ORM), Openpyxl, ReportLab.</p>
        <p>Современный интерфейс в монохромной стилистике.</p>
        """
        QMessageBox.about(self, "О программе", about_text)

    def on_logout(self):
        confirm = QMessageBox.question(
            self,
            "Смена пользователя",
            "Вы действительно хотите выйти из текущей учетной записи?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            logout()
            self.close()
            from ui.login_window import LoginWindow
            login = LoginWindow()
            if login.exec():
                new_main = MainWindow()
                new_main.show()
                from PyQt6.QtWidgets import QApplication
                app = QApplication.instance()
                app._main_window = new_main
