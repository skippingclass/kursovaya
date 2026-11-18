"""Start the PyQt network client."""
import argparse
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from ui.api_client import ApiClient, ApiError
from ui.network_window import NetworkLogin, NetworkWindow
from ui.styles import APP_STYLE


def main():
    parser = argparse.ArgumentParser(description="Сетевой клиент учета преподавателей")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        client = ApiClient(args.url)
    except ValueError as exc:
        parser.error(str(exc))
    app = QApplication(sys.argv[:1])
    app.setStyleSheet(APP_STYLE)
    dialog = NetworkLogin(client)
    while dialog.exec():
        try:
            window = NetworkWindow(client, dialog.user)
        except ApiError as exc:
            QMessageBox.warning(dialog, "Запуск клиента", str(exc))
            continue
        window.show()
        return app.exec()
    return 0


if __name__ == "__main__":
    sys.exit(main())
