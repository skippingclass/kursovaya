"""Снимки актуального интерфейса на одноразовой демонстрационной базе."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from database import connection
from services.auth_service import authenticate
from services.workload_service import save_pool, add_workload


def main():
    app=QApplication.instance() or QApplication([])
    from ui.styles import APP_STYLE
    app.setStyleSheet(APP_STYLE)
    app.setFont(QFont("DejaVu Sans",10))
    root=Path(__file__).resolve().parents[1]
    out=root/'docs/screenshots'; out.mkdir(parents=True,exist_ok=True)
    previous=connection._engine
    with tempfile.TemporaryDirectory() as temp:
        connection._engine=create_engine(f'sqlite:///{temp}/demo.db'); connection.init_db()
        authenticate('admin','admin123')
        p=save_pool('2026-2027',1,'П-24-67Б',1,360,540,18)[2]
        add_workload('',1,1,180,180,pool_id=p)
        add_workload('',2,1,90,180,pool_id=p)
        save_pool('2026-2027',2,'П-24-67Б',2,180,360,18)
        from ui.main_window import MainWindow
        from ui.teacher_dialog import TeacherDialog
        from ui.workload_dialog import WorkloadDialog
        from ui.teacher_card_dialog import TeacherCardDialog
        from ui.login_window import LoginWindow
        window=MainWindow(); window.resize(1500,900); window.show(); app.processEvents()
        window.grab().save(str(out/'main_window.png'))
        window.tabs.setCurrentIndex(1)
        tab=window.tab_workload
        tab.combo_year.setCurrentIndex(tab.combo_year.findData('2026-2027'))
        tab.refresh_table(); app.processEvents()
        window.grab().save(str(out/'workload_pool.png'))
        tab.pages.setCurrentIndex(1); app.processEvents()
        window.grab().save(str(out/'workload_assignments.png'))
        window.tabs.setCurrentIndex(3)
        report=window.tab_reports; report.combo_type.setCurrentIndex(1)
        report.combo_year.setCurrentIndex(report.combo_year.findData('2026-2027'))
        report.combo_semester.setCurrentIndex(report.combo_semester.findData(1))
        app.processEvents(); window.grab().save(str(out/'workload_report.png'))
        for dialog,filename in [(TeacherDialog(1),'teacher_form.png'),(WorkloadDialog(pool_id=p),'workload_form.png'),
                                 (TeacherCardDialog(1),'teacher_card.png'),(LoginWindow(),'login_window.png')]:
            dialog.show(); app.processEvents(); dialog.grab().save(str(out/filename)); dialog.close()
        window.close(); connection._engine.dispose()
    connection._engine=previous

if __name__=='__main__': main()
