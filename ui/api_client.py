"""Transport for the PyQt client. Requests never open a database connection."""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class ApiError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ApiClient:
    def __init__(self, url):
        address = urlsplit(url)
        local = address.hostname in {"127.0.0.1", "localhost", "::1"}
        if (not address.netloc or address.username or address.password or address.query or address.fragment
                or not (address.scheme == "https" or (address.scheme == "http" and local))):
            raise ValueError("Укажите HTTPS-адрес сервера или локальный HTTP-адрес.")
        self.url = url.rstrip("/") + "/api/v1"
        self.token = None
        self.opener = build_opener(NoRedirect())

    def request(self, path, *, method="GET", data=None, params=None, binary=False):
        headers = {}
        payload = None
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if data is not None:
            headers["Content-Type"] = "application/json"
            payload = json.dumps(data).encode()
        query = urlencode({key: value for key, value in (params or {}).items() if value not in (None, "")})
        target = self.url + path + ("?" + query if query else "")
        try:
            with self.opener.open(Request(target, payload, headers, method=method), timeout=5) as response:
                result = response.read()
        except HTTPError as exc:
            if exc.code == 401:
                self.token = None
            with exc:
                try:
                    detail = json.load(exc).get("detail")
                except (ValueError, AttributeError):
                    detail = None
            raise ApiError(detail or f"Ошибка сервера HTTP {exc.code}.") from exc
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise ApiError("Не удалось связаться с сервером.") from exc
        if binary or not result:
            return result
        try:
            return json.loads(result)
        except ValueError as exc:
            raise ApiError("Сервер вернул некорректный ответ.") from exc

    def login(self, username, password):
        response = self.request("/auth/login", method="POST", data={"username": username, "password": password})
        self.token = response["access_token"]
        return response["user"]
