import json
from io import BytesIO
from urllib.parse import urlencode

import pytest
from bottle import Bottle

from server.api_handlers import register_routes
from server.race_state import RaceState


class WSGIClient:
    """Dependency-free WSGI test client for a Bottle app (no requests/webtest needed)."""

    def __init__(self, app):
        self.app = app

    def _call(self, method, path, json_body=None, query=None):
        body = b""
        extra_headers = {}
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            extra_headers["CONTENT_TYPE"] = "application/json"
            extra_headers["CONTENT_LENGTH"] = str(len(body))

        query_string = urlencode(query) if query else ""

        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
            "SERVER_NAME": "testserver",
            "SERVER_PORT": "80",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": BytesIO(body),
            "wsgi.errors": BytesIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
        }
        environ.update(extra_headers)

        captured = {}

        def start_response(status, response_headers, exc_info=None):
            captured["status"] = status
            captured["headers"] = response_headers

        raw = b"".join(self.app(environ, start_response))
        status_code = int(captured["status"].split(" ", 1)[0])
        if not raw:
            return status_code, None
        try:
            payload = json.loads(raw.decode("utf-8"))
        except ValueError:
            payload = raw.decode("utf-8")
        return status_code, payload

    def get(self, path, query=None):
        return self._call("GET", path, query=query)

    def post_json(self, path, data=None):
        return self._call("POST", path, json_body=data if data is not None else {})


@pytest.fixture
def state():
    return RaceState()


@pytest.fixture
def client(state):
    app = Bottle()
    register_routes(app, state)
    return WSGIClient(app)


@pytest.fixture
def clock(monkeypatch):
    """Controllable fake clock shared by race_state.now_ts and api_handlers.now_ts
    (the latter is `from server.race_state import now_ts`, a separate binding, so
    both must be patched for timing to be deterministic end-to-end in HTTP tests)."""

    current = [1_700_000_000.0]

    def fake_now():
        return current[0]

    monkeypatch.setattr("server.race_state.now_ts", fake_now)
    monkeypatch.setattr("server.api_handlers.now_ts", fake_now)

    class Clock:
        def advance(self, seconds):
            current[0] += seconds
            return current[0]

        def set(self, value):
            current[0] = value

        @property
        def value(self):
            return current[0]

    return Clock()
