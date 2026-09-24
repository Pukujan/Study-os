"""Shared helpers for the web-app tests (not a test module itself)."""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:  # the web extra is part of requirements-dev.lock
    import fastapi  # noqa: F401
    import psycopg

    WEB_DEPS = True
except ImportError:  # pragma: no cover - exercised only without the web extra
    WEB_DEPS = False

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


def requires_web(cls: Any) -> Any:
    return unittest.skipUnless(WEB_DEPS, "web extra not installed")(cls)


def requires_db(cls: Any) -> Any:
    return unittest.skipUnless(WEB_DEPS and TEST_DATABASE_URL, "TEST_DATABASE_URL not set")(cls)


@contextmanager
def temp_database() -> Iterator[str]:
    """Create a throwaway database next to TEST_DATABASE_URL and drop it afterwards."""

    assert TEST_DATABASE_URL
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    name = "sos_t_" + uuid.uuid4().hex[:12]
    admin = psycopg.connect(TEST_DATABASE_URL, autocommit=True)
    try:
        admin.execute(f'CREATE DATABASE "{name}"')
        params = conninfo_to_dict(TEST_DATABASE_URL)
        params["dbname"] = name
        yield make_conninfo(**params)
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


def make_settings(database_url: str = "postgresql://unused/unused", **overrides: Any) -> Any:
    from study_os.web.config import Settings

    base: dict[str, Any] = {
        "database_url": database_url,
        "allowed_origins": ("http://testserver",),
        "cookie_secure": False,
        "server_secret": "test-secret-not-real",
    }
    base.update(overrides)
    return Settings(**base)


def answer_for(ctx: Any, correct: bool = True) -> str:
    """Produce a correct (or a definitely wrong) answer for a probe context."""

    if ctx.item is not None:
        idx = ctx.item.correct_index if correct else (ctx.item.correct_index + 1) % len(ctx.item.options)
        return str(idx + 1)
    spec = ctx.assessment
    kind = spec.kind.value
    if kind == "integer":
        return str(spec.expected_values[0] if correct else spec.expected_values[0] + 97)
    if kind == "integer_sequence":
        vals = list(spec.expected_values) if correct else [v + 97 for v in spec.expected_values]
        return ", ".join(str(v) for v in vals)
    return spec.expected_text[0] if correct else "zzz-not-it"


class ApiClient:
    """TestClient wrapper that carries the required headers and CSRF token."""

    def __init__(self, client: Any) -> None:
        self.c = client
        self.headers: dict[str, str] = {"X-Study-OS": "1"}

    def signup(self, email: str, passphrase: str = "correct horse battery staple") -> dict[str, Any]:
        r = self.c.post("/api/auth/signup", json={"email": email, "passphrase": passphrase}, headers=self.headers)
        assert r.status_code == 200, r.text
        self.headers["X-CSRF-Token"] = r.json()["csrf_token"]
        return r.json()

    def post(self, path: str, body: Any = None) -> Any:
        return self.c.post(path, json=body if body is not None else {}, headers=self.headers)

    def get(self, path: str) -> Any:
        return self.c.get(path)

    def awaiting(self, view: dict[str, Any]) -> dict[str, Any]:
        return [t for t in view["turns"] if t.get("awaiting")][-1]
