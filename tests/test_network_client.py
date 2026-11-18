import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from time import monotonic, sleep
import unittest

from PyQt6.QtWidgets import QApplication

from ui.api_client import ApiClient, ApiError
from ui.network_window import NetworkWindow


class NetworkClientTests(unittest.TestCase):
    def test_qt_client_reads_from_running_server(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "COLLEGE_DB_URL": f"sqlite:///{Path(directory) / 'staging.db'}",
                   "QT_QPA_PLATFORM": "offscreen"}
            with subprocess.Popen([sys.executable, "-m", "uvicorn", "server.api:app", "--port", str(port)],
                                  env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as server:
                try:
                    self.check_client(port, server)
                finally:
                    server.terminate()
                    server.communicate(timeout=8)

    def check_client(self, port, server):
        client = ApiClient(f"http://127.0.0.1:{port}")
        end = monotonic() + 10
        while monotonic() < end:
            try:
                self.assertEqual(client.request("/health")["status"], "ok")
                break
            except ApiError:
                if server.poll() is not None:
                    self.fail(server.stdout.read().decode(errors="replace"))
                sleep(0.1)
        else:
            self.fail("Локальный сервер не запустился")
        app = QApplication.instance() or QApplication([])
        user = client.login("operator", "operator123")
        window = NetworkWindow(client, user)
        self.assertGreater(window.tables["teachers"].rowCount(), 0)
        self.assertGreater(window.tables["pools"].rowCount(), 0)
        self.assertGreater(window.tables["assignments"].rowCount(), 0)
        discipline = client.request("/disciplines")[0]["id"]
        body = dict(academic_year="2030-2031", semester=1, group_name="QT-DEMO",
                    discipline_id=discipline, hours_lecture=18, hours_practice=18)
        client.request("/pools", method="POST", data=body)
        window.refresh(raise_errors=True)
        table = window.tables["pools"]
        self.assertTrue(any(table.item(row, 2).text() == "QT-DEMO" for row in range(table.rowCount())))
        window.close()
        self.assertIsNone(client.token)
        app.processEvents()
