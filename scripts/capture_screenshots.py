"""Снимки актуального интерфейса на одноразовых демонстрационных базах."""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from time import monotonic, sleep
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine

from config import DEFAULT_CONFIG
from database import connection
from services.auth_service import authenticate, logout
from services.workload_service import add_workload, save_pool
from ui.api_client import ApiClient, ApiError
from ui.i18n import install_russian_translations
from ui.styles import APP_STYLE


def capture(app, widget, destination):
    widget.show()
    app.processEvents()
    if not widget.grab().save(str(destination)):
        raise RuntimeError(f"Не удалось сохранить снимок {destination}")


def capture_desktop(app, out, temp):
    from ui.db_settings_dialog import DBSettingsDialog
    from ui.login_window import LoginWindow
    from ui.main_window import MainWindow
    from ui.teacher_card_dialog import TeacherCardDialog
    from ui.teacher_dialog import TeacherDialog
    from ui.workload_dialog import WorkloadDialog

    previous = connection._engine
    widgets = []
    connection._engine = create_engine(f"sqlite:///{temp / 'desktop.db'}")
    try:
        connection.init_db()
        authenticate("admin", "admin123")
        pool = save_pool("2026-2027", 1, "П-24-67Б", 1, 360, 540, 18)[2]
        add_workload("", 1, 1, 180, 180, pool_id=pool)
        add_workload("", 2, 1, 90, 180, pool_id=pool)
        save_pool("2026-2027", 2, "П-24-67Б", 2, 180, 360, 18)
        window = MainWindow()
        widgets.append(window)
        window.resize(1800, 900)
        capture(app, window, out / "main_window.png")
        window.tabs.setCurrentIndex(1)
        tab = window.tab_workload
        tab.combo_year.setCurrentIndex(tab.combo_year.findData("2026-2027"))
        tab.refresh_table()
        capture(app, window, out / "workload_pool.png")
        tab.pages.setCurrentIndex(1)
        capture(app, window, out / "workload_assignments.png")
        window.tabs.setCurrentIndex(3)
        report = window.tab_reports
        report.combo_type.setCurrentIndex(1)
        report.combo_year.setCurrentIndex(report.combo_year.findData("2026-2027"))
        report.combo_semester.setCurrentIndex(report.combo_semester.findData(1))
        report.generate_report()
        for column, width in enumerate([40, 120, 90, 90, 210, 250, 72, 345, 100, 108, 90, 120]):
            report.table.setColumnWidth(column, width)
        capture(app, window, out / "workload_report.png")
        for dialog, filename in (
            (TeacherDialog(1), "teacher_form.png"),
            (WorkloadDialog(pool_id=pool), "workload_form.png"),
            (TeacherCardDialog(1), "teacher_card.png"),
            (LoginWindow(), "login_window.png"),
        ):
            widgets.append(dialog)
            if isinstance(dialog, TeacherCardDialog):
                dialog.combo_year.setCurrentIndex(dialog.combo_year.findData("2026-2027"))
                dialog.combo_semester.setCurrentIndex(dialog.combo_semester.findData(1))
                dialog.resize(1420, 650)
            if isinstance(dialog, WorkloadDialog):
                dialog.resize(1000, 440)
                dialog.combo_teacher.setCurrentIndex(dialog.combo_teacher.findData(3))
                dialog.spin_lec.setValue(45)
                dialog.spin_prac.setValue(90)
            capture(app, dialog, out / filename)
            dialog.close()
        settings = {**DEFAULT_CONFIG, "sqlite_path": "data/college_teachers.db"}
        with patch("ui.db_settings_dialog.load_config", return_value=settings):
            dialog = DBSettingsDialog()
        widgets.append(dialog)
        capture(app, dialog, out / "db_settings.png")
    finally:
        for widget in widgets:
            widget.close()
        app.processEvents()
        logout()
        connection._engine.dispose()
        connection._engine = previous


def capture_network(app, out, temp):
    from ui.network_window import NetworkWindow

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = {**os.environ, "COLLEGE_DB_URL": f"sqlite:///{temp / 'network.db'}"}
    command = [sys.executable, "-m", "uvicorn", "server.api:app", "--port", str(port)]
    with subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as server:
        window = None
        try:
            client = ApiClient(f"http://127.0.0.1:{port}")
            deadline = monotonic() + 15
            while monotonic() < deadline:
                try:
                    client.request("/health")
                    break
                except ApiError:
                    if server.poll() is not None:
                        raise RuntimeError(server.stdout.read().decode(errors="replace"))
                    sleep(0.1)
            else:
                raise RuntimeError("Сервер для снимка интерфейса не запустился.")
            user = client.login("operator", "operator123")
            disciplines = client.request("/disciplines")
            discipline = next((row for row in disciplines if "алгоритм" in row["name"].casefold()), disciplines[0])
            teacher = client.request("/teachers")[0]["id"]
            for group, theory, practice in [("П-24-67Б", 36, 54), ("П-24-68А", 30, 42), ("ИС-24-22А", 24, 48)]:
                result = client.request("/pools", method="POST", data={
                    "academic_year": "2026-2027", "semester": 1, "group_name": group,
                    "discipline_id": discipline["id"], "hours_lecture": theory,
                    "hours_practice": practice, "weeks": 18,
                })
                if group == "П-24-67Б":
                    client.request("/assignments", method="POST", data={
                        "pool_id": result["id"], "teacher_id": teacher,
                        "hours_lecture": 12, "hours_practice": 24,
                    })
            window = NetworkWindow(client, user)
            window.resize(1460, 520)
            window.year.setCurrentIndex(window.year.findData("2026-2027"))
            window.semester.setCurrentIndex(window.semester.findData(1))
            window.refresh(raise_errors=True)
            window.tabs.setCurrentIndex(1)
            window.tables["pools"].setColumnWidth(3, 430)
            capture(app, window, out / "network_client.png")
        finally:
            if window:
                window.close()
                app.processEvents()
            server.terminate()
            server.communicate(timeout=8)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/screenshots")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    install_russian_translations(app)
    app.setStyleSheet(APP_STYLE)
    app.setFont(QFont("DejaVu Sans", 10))
    with tempfile.TemporaryDirectory(prefix="college-screenshots-") as folder:
        temp = Path(folder)
        capture_desktop(app, args.output, temp)
        capture_network(app, args.output, temp)
    print(f"Сохранено 10 снимков в {args.output}")


if __name__ == "__main__":
    main()
