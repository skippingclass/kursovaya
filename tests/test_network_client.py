import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from scripts import run_network
from ui.api_client import ApiClient
from ui.network_window import NetworkWindow


class NetworkClientTests(unittest.TestCase):
    def test_qt_client_reads_from_running_server(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            standalone_db = data_dir / "standalone.db"
            env = {"COLLEGE_DB_URL": f"sqlite:///{standalone_db.as_posix()}", "QT_QPA_PLATFORM": "offscreen"}
            with (patch.dict(os.environ, env), patch.object(run_network, "DATA_DIR", data_dir),
                  patch.object(run_network, "open_client", self.check_client)):
                self.assertEqual(run_network.main(), 0)
            self.assertTrue((data_dir / "network_demo.db").is_file())
            self.assertFalse(standalone_db.exists())

    def check_client(self, args):
        self.assertEqual(args[0], "--url")
        client = ApiClient(args[1])
        self.assertEqual(client.request("/health")["status"], "ok")
        app = QApplication.instance() or QApplication([])
        user = client.login("operator", "operator123")
        window = NetworkWindow(client, user)
        try:
            self.assertGreater(window.tables["teachers"].rowCount(), 0)
            self.assertGreater(window.tables["pools"].rowCount(), 0)
            self.assertGreater(window.tables["assignments"].rowCount(), 0)
            discipline = client.request("/disciplines")[0]["id"]
            body = dict(academic_year="2030-2031", semester=1, group_name="QT-DEMO",
                        discipline_id=discipline, hours_lecture=18, hours_practice=18)
            client.request("/pools", method="POST", data=body)
            window.refresh(raise_errors=True)
            year_index = window.year.findData("2030-2031")
            self.assertGreaterEqual(year_index, 0)
            window.year.setCurrentIndex(year_index)
            window.refresh(raise_errors=True)
            self.assertEqual(window.year.currentData(), "2030-2031")
            table = window.tables["pools"]
            self.assertEqual(table.rowCount(), 1)
            self.assertEqual(table.item(0, 2).text(), "QT-DEMO")
        finally:
            window.close()
            app.processEvents()
        self.assertIsNone(client.token)
        return 0
