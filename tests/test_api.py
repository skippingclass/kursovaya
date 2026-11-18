import hashlib
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from database import connection
from database.models import User
from server.api import app

PREFIX = "/api/v1"


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        url = f"sqlite:///{Path(self.temp.name) / 'test.db'}"
        connection.reset_engine()
        database_url = patch.object(connection, "get_database_url", return_value=url)
        database_url.start()
        self.addCleanup(database_url.stop)
        self.addCleanup(connection.reset_engine)
        context = TestClient(app)
        self.client = context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)

    def request(self, method, path, **kwargs):
        return self.client.request(method, PREFIX + path, **kwargs)

    def login(self, user, password):
        response = self.request("POST", "/auth/login", json={"username": user, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_login_roles_contract_and_logout(self):
        self.assertEqual(self.request("GET", "/teachers").status_code, 401)
        invalid = self.request("POST", "/auth/login", json={"username": "admin", "password": "incorrect"})
        self.assertEqual(invalid.status_code, 401)
        rejected = self.request("POST", "/auth/login", json={"username": 8, "password": "private"})
        self.assertEqual(rejected.status_code, 422)
        self.assertNotIn("private", rejected.text)
        headers = self.login("methodist", "methodist123")
        self.assertEqual(self.request("GET", "/pools", headers=headers).status_code, 200)
        self.assertEqual(self.request("DELETE", "/assignments/1", headers=headers).status_code, 403)
        spec = self.client.get("/openapi.json").json()
        self.assertIn("HTTPBearer", spec["components"]["securitySchemes"])
        self.assertIn("put", spec["paths"][PREFIX + "/assignments/{assignment_id}"])
        teacher = self.request("GET", "/teachers", headers=headers).json()[0]["id"]
        card = self.request("GET", f"/teachers/{teacher}", headers=headers)
        self.assertEqual(card.status_code, 200, card.text)
        self.assertTrue(card.json()["first_name"])
        self.assertEqual(self.request("GET", "/teachers/999999", headers=headers).status_code, 404)
        self.assertEqual(self.request("DELETE", "/auth/session", headers=headers).status_code, 204)
        self.assertEqual(self.request("GET", "/teachers", headers=headers).status_code, 401)

    def test_legacy_password_migrates_after_login(self):
        old_hash = hashlib.sha256(b"admin123").hexdigest()
        with connection.get_session() as session:
            user = session.query(User).filter_by(username="admin").one()
            user.password_hash = old_hash
            session.commit()
        self.login("admin", "admin123")
        with connection.get_session() as session:
            user = session.query(User).filter_by(username="admin").one()
            self.assertTrue(user.password_hash.startswith("scrypt$"))
        self.login("admin", "admin123")

    def test_pool_assignment_rejection_edit_cancel_and_filtered_exports(self):
        headers = self.login("operator", "operator123")

        def get(path, **params):
            response = self.request("GET", path, headers=headers, params=params)
            self.assertEqual(response.status_code, 200, response.text[:300])
            return response.json()

        discipline = get("/disciplines")[0]["id"]
        teacher = get("/teachers")[0]["id"]
        plan = dict(academic_year="2030-2031", semester=2, group_name="API-TEST",
                    discipline_id=discipline, hours_lecture=36, hours_practice=18, weeks=18)
        response = self.request("POST", "/pools", json=plan, headers=headers)
        self.assertEqual(response.status_code, 201, response.text)
        pool = response.json()["id"]
        allocation = dict(pool_id=pool, teacher_id=teacher, hours_lecture=37, hours_practice=18)
        invalid = self.request("POST", "/assignments", json=allocation, headers=headers)
        self.assertEqual(invalid.status_code, 409, invalid.text)
        self.assertEqual(get("/pools", academic_year="2030-2031")[0]["available_lecture"], 36)
        allocation["hours_lecture"] = 18
        response = self.request("POST", "/assignments", json=allocation, headers=headers)
        self.assertEqual(response.status_code, 201, response.text)
        identifier = response.json()["id"]
        allocation["hours_practice"] = 0
        response = self.request("PUT", f"/assignments/{identifier}", json=allocation, headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        filters = {"academic_year": "2030-2031", "semester": 2, "teacher_id": teacher}
        records = get("/assignments", **filters)
        self.assertEqual([(row["group_name"], row["hours_per_week"]) for row in records], [("API-TEST", 1.0)])
        spreadsheet = self.request("GET", "/reports/workload/xlsx", headers=headers, params=filters)
        self.assertEqual(spreadsheet.status_code, 200)
        sheet = load_workbook(BytesIO(spreadsheet.content)).active
        self.assertTrue(any("API-TEST" in row for row in sheet.values))
        pdf = self.request("GET", "/reports/workload/pdf", headers=headers, params=filters)
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        self.assertEqual(self.request("DELETE", f"/assignments/{identifier}", headers=headers).status_code, 200)
        self.assertEqual(get("/pools", academic_year="2030-2031")[0]["available_practice"], 18)
        self.assertEqual(get("/assignments", **filters), [])
        self.assertEqual(self.request("DELETE", f"/pools/{pool}", headers=headers).status_code, 200)
