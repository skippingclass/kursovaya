"""
Главная точка входа приложения "Система учета преподавателей"
Высший колледж «Astana Polytechnic»
"""
import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from config import APP_NAME
from database.connection import init_db
from ui.styles import APP_STYLE
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def main():
    # Настройки отображения для High DPI экранов
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(APP_STYLE)

    # Инициализация базы данных и создание таблиц с начальными данными
    try:
        init_db()
    except Exception as e:
        QMessageBox.critical(
            None,
            "Критическая ошибка БД",
            f"Не удалось инициализировать базу данных:\n{e}\n\n"
            f"Проверьте настройки подключения к СУБД в окне авторизации."
        )

    # 1. Запуск окна авторизации (LoginWindow)
    login_dialog = LoginWindow()
    if login_dialog.exec():
        # 2. Если вход успешен -> открываем главное окно
        main_win = MainWindow()
        app._main_window = main_win  # Сохраняем ссылку от сборщика мусора
        main_win.show()
        sys.exit(app.exec())
    else:
        # Пользователь закрыл окно авторизации
        sys.exit(0)


if __name__ == "__main__":
    main()
