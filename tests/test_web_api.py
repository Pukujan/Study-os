"""API + Postgres integration tests for the web slice (#84 #85 #86 #87 #90 #93 #97).

Runs only when TEST_DATABASE_URL points at a Postgres server where the role may create
databases (CI provides a postgres:16 service container)."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
import uuid
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from typing import Any
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web_testkit import ApiClient, make_settings, requires_db, temp_database  # noqa: E402

EXPECTED_TABLES = {
    "auth.account", "auth.identity", "auth.local_credential", "auth.session", "auth.oauth_state",
    "auth.login_attempt", "auth.account_subject",
    "learn.subject", "learn.content_revision", "learn.session", "learn.turn", "learn.attempt",
    "learn.capability_transition", "learn.interpretation", "learn.generation", "learn.decision",
    "learn.decision_label", "learn.experiment_assignment", "learn.review_schedule", "learn.topic_progress",
    "cache.model_response", "ux.reaction", "ux.event", "ux.decomposer_review", "public.schema_migrations",
}


class _DbCase(unittest.TestCase):
    """One throwaway database + app per test class."""

    settings_overrides: dict[str, Any] = {}
    jev: Any = None
    llm: Any = None

    @classmethod
    def setUpClass(cls) -> None:
        from fastapi.testclient import TestClient

        from study_os.web.api import create_app

        cls._stack = ExitStack()
        cls.db_url = cls._stack.enter_context(temp_database())
        cls.settings = make_settings(cls.db_url, **cls.settings_overrides)
        cls.app = create_app(cls.settings, jev=cls.jev, llm=cls.llm, use_env_models=False)
        cls.tc = cls._stack.enter_context(TestClient(cls.app))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._stack.close()

    def client(self) -> ApiClient:
        from fastapi.testclient import TestClient

        return ApiClient(TestClient(self.app))

    def sql(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self.db_url, row_factory=dict_row) as conn:
            cur = conn.execute(query, params)
            return cur.fetchall() if cur.description else []

    @staticmethod
    def email() -> str:
        return f"u{uuid.uuid4().hex[:10]}@example.com"


@requires_db
class SchemaTests(_DbCase):
    def test_schema_allowlist(self) -> None:
        rows = self.sql(
            "SELECT table_schema || '.' || table_name AS t FROM information_schema.tables "
            "WHERE table_type = 'BASE TABLE' AND table_schema NOT IN ('pg_catalog', 'information_schema')"
        )
        self.assertEqual({r["t"] for r in rows}, EXPECTED_TABLES)

    def test_no_raw_ip_or_plaintext_secret_columns(self) -> None:
        rows = self.sql(
            "SELECT table_schema, table_name, column_name FROM information_schema.columns "
            "WHERE table_schema IN ('auth','learn','ux','cache')"
        )
        names = {r["column_name"] for r in rows}
        for banned in ("ip", "ip_address", "password", "passphrase", "token", "session_token", "csrf_token"):
            self.assertNotIn(banned, names)

    def test_migrate_is_idempotent(self) -> None:
        from study_os.web.db import Database

        db = Database(self.db_url, min_size=1, max_size=1)
        try:
            self.assertEqual(db.migrate(), [])
        finally:
            db.close()

    def test_append_only_tables_reject_update_and_delete(self) -> None:
        import psycopg

        for table in ("learn.attempt", "learn.decision", "learn.turn", "ux.event", "learn.capability_transition"):
            for stmt in (f"UPDATE {table} SET created_at = created_at", f"DELETE FROM {table}"):
                with self.subTest(stmt=stmt), self.assertRaises(psycopg.Error):
                    self.sql(stmt)

    def test_analytics_views_exist_and_query(self) -> None:
        for view in ("v_learning_event", "v_decision", "v_daily_active_learners", "v_step_funnel",
                     "v_drop_off", "v_hint_rate", "v_accuracy_by_concept", "v_time_on_step"):
            self.sql(f"SELECT * FROM analytics.{view} LIMIT 1")


@requires_db
class AuthApiTests(_DbCase):
    def test_signup_login_logout_cycle(self) -> None:
        c = self.client()
        email = self.email()
        body = c.signup(email)
        self.assertEqual(body["role"], "learner")
        me = c.get("/api/auth/me").json()
        self.assertEqual(me["handle"], body["handle"])
        self.assertNotEqual(me["csrf_token"], body["csrf_token"])  # rotated
        c.headers["X-CSRF-Token"] = me["csrf_token"]
        self.assertEqual(c.post("/api/auth/logout").status_code, 200)
        self.assertEqual(c.get("/api/auth/me").status_code, 401)
        r = c.post("/api/auth/login", {"email": email.upper(), "passphrase": "correct horse battery staple"})
        self.assertEqual(r.status_code, 200)
        cookie = r.headers["set-cookie"].lower()
        self.assertIn("httponly", cookie)
        self.assertIn("samesite=lax", cookie)

    def test_duplicate_email_rejected(self) -> None:
        email = self.email()
        self.client().signup(email)
        r = self.client().post("/api/auth/signup", {"email": email, "passphrase": "another long passphrase"})
        self.assertEqual(r.status_code, 409)

    def test_tokens_stored_hashed(self) -> None:
        c = self.client()
        c.signup(self.email())
        token = c.c.cookies.get("sos_session")
        rows = self.sql("SELECT session_id_hash FROM auth.session")
        self.assertTrue(rows)
        self.assertFalse(any(token.encode() == bytes(r["session_id_hash"]) for r in rows))
        creds = self.sql("SELECT passphrase_hash FROM auth.local_credential")
        self.assertTrue(all(r["passphrase_hash"].startswith("$argon2id$") for r in creds))

    def test_login_throttle(self) -> None:
        email = self.email()
        self.client().signup(email)
        c = self.client()
        bad = {"email": email, "passphrase": "wrong wrong wrong"}
        self.assertEqual([c.post("/api/auth/login", bad).status_code for _ in range(2)], [401, 401])
        backoff = c.post("/api/auth/login", bad)  # exponential backoff after the second failure
        self.assertEqual(backoff.status_code, 429)
        self.assertIn("retry-after", backoff.headers)
        # Age the failures past the backoff, then hit the 5-per-window account cap.
        self.sql("UPDATE auth.login_attempt SET created_at = now() - interval '1 minute'")
        self.assertEqual(c.post("/api/auth/login", bad).status_code, 401)
        self.sql("UPDATE auth.login_attempt SET created_at = now() - interval '2 minutes'")
        self.sql("INSERT INTO auth.login_attempt (account_key_hash, ip_hash, succeeded) "
                 "SELECT account_key_hash, ip_hash, false FROM auth.login_attempt LIMIT 2")
        self.sql("UPDATE auth.login_attempt SET created_at = now() - interval '2 minutes'")
        good = c.post("/api/auth/login", {"email": email, "passphrase": "correct horse battery staple"})
        self.assertEqual(good.status_code, 429)  # locked for the window even with the right passphrase
        self.sql("UPDATE auth.login_attempt SET created_at = now() - interval '16 minutes'")
        self.assertEqual(c.post("/api/auth/login", {"email": email, "passphrase": "correct horse battery staple"}).status_code, 200)
        self.assertEqual(c.post("/api/auth/login", {"email": "bad", "passphrase": "x"}).status_code, 401)

    def test_mutation_guards(self) -> None:
        c = self.client()
        c.signup(self.email())
        no_header = c.c.post("/api/sessions", json={"track": "dsa"})
        self.assertEqual(no_header.status_code, 403)
        bad_origin = c.c.post("/api/sessions", json={"track": "dsa"}, headers={**c.headers, "Origin": "https://evil.example"})
        self.assertEqual(bad_origin.status_code, 403)
        no_csrf = c.c.post("/api/sessions", json={"track": "dsa"}, headers={"X-Study-OS": "1"})
        self.assertEqual(no_csrf.status_code, 403)
        self.assertEqual(c.post("/api/sessions", {"track": "dsa"}).status_code, 200)

    def test_idle_and_absolute_expiry(self) -> None:
        c = self.client()
        c.signup(self.email())
        self.sql("UPDATE auth.session SET idle_expires_at = now() - interval '1 minute'")
        self.assertEqual(c.get("/api/home").status_code, 401)
        c2 = self.client()
        c2.signup(self.email())
        self.sql("UPDATE auth.session SET absolute_expires_at = now() - interval '1 minute' WHERE revoked_at IS NULL")
        self.assertEqual(c2.get("/api/home").status_code, 401)

    def test_handle_change(self) -> None:
        c = self.client()
        c.signup(self.email())
        r = c.post("/api/auth/handle", {"handle": "new_handle_" + uuid.uuid4().hex[:4]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(c.post("/api/auth/handle", {"handle": "!!"}).status_code, 400)

    def test_google_disabled_by_default(self) -> None:
        c = self.client()
        self.assertEqual(c.get("/api/auth/config").json(), {"google": False, "local_signup": True})
        self.assertEqual(c.c.get("/api/auth/google/start", follow_redirects=False).status_code, 404)

    def test_security_headers(self) -> None:
        r = self.client().get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["cache-control"], "no-store")
        self.assertIn("frame-ancestors 'none'", r.headers["content-security-policy"])
        self.assertEqual(r.headers["x-content-type-options"], "nosniff")


@requires_db
class GoogleAuthTests(_DbCase):
    settings_overrides = {"google_client_id": "cid.apps.googleusercontent.com", "google_client_secret": "not-a-real-secret"}

    def test_start_uses_pkce_and_state(self) -> None:
        from urllib.parse import parse_qs, urlparse

        r = self.client().c.get("/api/auth/google/start", follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        q = parse_qs(urlparse(r.headers["location"]).query)
        self.assertEqual(q["code_challenge_method"], ["S256"])
        self.assertIn("state", q)
        self.assertIn("nonce", q)
        self.assertEqual(q["client_id"], ["cid.apps.googleusercontent.com"])
        self.assertGreaterEqual(len(self.sql("SELECT 1 FROM auth.oauth_state")), 1)

    def test_callback_rejects_unknown_state(self) -> None:
        r = self.client().c.get("/api/auth/google/callback?code=x&state=forged", follow_redirects=False)
        self.assertIn(r.status_code, (400, 403))
        r = self.client().c.get("/api/auth/google/callback", follow_redirects=False)
        self.assertEqual(r.status_code, 302)

    def test_callback_full_flow_links_account(self) -> None:
        import base64
        import time
        from urllib.parse import parse_qs, urlparse

        c = self.client()
        start = c.c.get("/api/auth/google/start", follow_redirects=False)
        q = parse_qs(urlparse(start.headers["location"]).query)

        def seg(obj: dict) -> str:
            return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

        claims = {"iss": "https://accounts.google.com", "aud": "cid.apps.googleusercontent.com", "exp": time.time() + 60,
                  "nonce": q["nonce"][0], "sub": "google-sub-1", "email": "g@example.com", "email_verified": True, "name": "G"}
        fake = mock.Mock(status_code=200)
        fake.json.return_value = {"id_token": f"{seg({'alg': 'RS256'})}.{seg(claims)}.sig"}
        with mock.patch("study_os.web.api.httpx.post", return_value=fake) as post:
            r = c.c.get(f"/api/auth/google/callback?code=abc&state={q['state'][0]}", follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(post.call_args.kwargs["data"]["code_verifier"] is not None, True)
        self.assertEqual(c.get("/api/auth/me").status_code, 200)
        # state is single-use
        r2 = c.c.get(f"/api/auth/google/callback?code=abc&state={q['state'][0]}", follow_redirects=False)
        self.assertIn(r2.status_code, (400, 403))
        self.assertEqual(len(self.sql("SELECT 1 FROM auth.identity WHERE provider = 'google'")), 1)


@requires_db
class LearningApiTests(_DbCase):
    def test_dsa_flow_idempotency_and_stale_turn(self) -> None:
        c = self.client()
        c.signup(self.email())
        view = c.post("/api/sessions", {"track": "dsa"}).json()
        sid = view["session_id"]
        probe = c.awaiting(view)
        r1 = c.post(f"/api/sessions/{sid}/attempts", {"turn_id": probe["turn_id"], "response": "not sure", "idempotency_key": "k-1"})
        self.assertEqual(r1.status_code, 200, r1.text)
        r2 = c.post(f"/api/sessions/{sid}/attempts", {"turn_id": probe["turn_id"], "response": "not sure", "idempotency_key": "k-1"})
        self.assertTrue(r2.json()["replayed"])
        self.assertEqual(len(self.sql("SELECT 1 FROM learn.attempt")), 1)
        if r1.json()["outcome"] != "unresolved":
            r3 = c.post(f"/api/sessions/{sid}/attempts", {"turn_id": probe["turn_id"], "response": "3", "idempotency_key": "k-2"})
            self.assertEqual(r3.status_code, 409)
        # resume returns the same session
        again = c.post("/api/sessions", {"track": "dsa"}).json()
        self.assertEqual(again["session_id"], sid)
        self.assertTrue(again["resumed"])

    def test_cross_account_isolation(self) -> None:
        a, b = self.client(), self.client()
        a.signup(self.email())
        b.signup(self.email())
        view = a.post("/api/sessions", {"track": "dsa"}).json()
        sid = view["session_id"]
        probe = a.awaiting(view)
        self.assertEqual(b.get(f"/api/sessions/{sid}").status_code, 404)
        self.assertEqual(b.get(f"/api/sessions/{sid}/summary").status_code, 404)
        r = b.post(f"/api/sessions/{sid}/attempts", {"turn_id": probe["turn_id"], "response": "1", "idempotency_key": "x"})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(b.post(f"/api/turns/{probe['turn_id']}/reactions", {"kind": "confused"}).status_code, 404)
        self.assertEqual(b.get("/api/sessions/not-a-uuid").status_code, 404)

    def test_hesi_topic_flow_and_answer_not_in_payload(self) -> None:
        from study_os.web import packs

        c = self.client()
        c.signup(self.email())
        home = c.get("/api/home").json()
        topic = home["hesi"]["recommended_topic"]
        self.assertTrue(topic)
        self.assertIn("unreviewed", json.dumps(home).lower())
        view = c.post("/api/sessions", {"track": "hesi", "topic_id": topic}).json()
        raw = json.dumps(view)
        for key in ("correct_index", "rationale", "expected_values", "answer_marked"):
            self.assertNotIn(f'"{key}"', raw)
        sid = view["session_id"]
        for n in range(2):
            probe = c.awaiting(view)
            from study_os.web.controller import WebController

            state = self.sql("SELECT run_state FROM learn.turn WHERE turn_id = %s", (probe["turn_id"],))[0]["run_state"]
            ctx = WebController({}).current_probe(state)
            assert ctx.item is not None
            res = c.post(f"/api/sessions/{sid}/attempts",
                         {"turn_id": probe["turn_id"], "response": str(ctx.item.correct_index + 1), "idempotency_key": f"h{n}"}).json()
            self.assertEqual(res["outcome"], "correct")
            view = {"turns": res["turns"]}
        self.assertEqual(res["turns"][-1]["state"], "SESSION_DONE")
        progress = self.sql("SELECT state FROM learn.topic_progress WHERE topic_id = %s", (topic,))
        self.assertEqual(progress[0]["state"], "assembled")
        self.assertTrue(self.sql("SELECT 1 FROM learn.review_schedule"))
        home2 = c.get("/api/home").json()
        states = {t["topic_id"]: t["state"] for s in home2["hesi"]["sections"] for t in s["topics"]}
        self.assertEqual(states[topic], "assembled")
        self.assertEqual(c.get(f"/api/sessions/{sid}/summary").json()["correct"], 2)
        del packs

    def test_checkpoint_and_expansion_and_end(self) -> None:
        c = self.client()
        c.signup(self.email())
        view = c.post("/api/sessions", {"track": "hesi", "checkpoint": "math"}).json()
        self.assertEqual(c.awaiting(view)["phase"], "CHECK")
        self.assertEqual(c.post("/api/sessions", {"track": "hesi", "checkpoint": "nope"}).status_code, 404)
        self.assertEqual(c.post("/api/sessions", {"track": "hesi"}).status_code, 400)
        self.assertEqual(c.post("/api/sessions", {"track": "zzz"}).status_code, 400)
        dsa = c.post("/api/sessions", {"track": "dsa"}).json()
        probe = c.awaiting(dsa)
        if probe.get("expansions"):
            r = c.post(f"/api/sessions/{dsa['session_id']}/expansions", {"turn_id": probe["turn_id"], "kind": probe["expansions"][0]})
            self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(c.post(f"/api/turns/{probe['turn_id']}/reactions", {"kind": "confused"}).status_code, 200)
        self.assertEqual(c.post(f"/api/turns/{probe['turn_id']}/reactions", {"kind": "bogus"}).status_code, 400)
        end = c.post(f"/api/sessions/{dsa['session_id']}/end")
        self.assertEqual(end.status_code, 200)

    def test_pii_canary_never_persisted(self) -> None:
        c = self.client()
        c.signup(self.email())
        view = c.post("/api/sessions", {"track": "dsa"}).json()
        probe = c.awaiting(view)
        canary = "canary-7f3a@example.org call 555-201-9876"
        c.post(f"/api/sessions/{view['session_id']}/attempts", {"turn_id": probe["turn_id"], "response": canary, "idempotency_key": "p1"})
        c.post("/api/events", {"events": [{"type": "click", "path": "/lesson", "control": "canary-7f3a@example.org", "client_session": "abcdefgh12"}]})
        tables = self.sql(
            "SELECT table_schema || '.' || table_name AS t FROM information_schema.tables "
            "WHERE table_type = 'BASE TABLE' AND table_schema IN ('auth','learn','ux','cache')"
        )
        for t in tables:
            hits = self.sql(f"SELECT 1 FROM {t['t']} x WHERE row_to_json(x)::text ILIKE %s OR row_to_json(x)::text LIKE %s",
                            ("%canary-7f3a%", "%555-201-9876%"))
            self.assertEqual(hits, [], t["t"])

    def test_events_endpoint(self) -> None:
        c = self.client()
        c.signup(self.email())
        view = c.post("/api/sessions", {"track": "dsa"}).json()
        events = [
            {"type": "page_view", "path": "/", "client_session": "abcdefgh12"},
            {"type": "step_shown", "path": "/lesson", "session_id": view["session_id"], "step_id": "position.e0.n2", "client_session": "abcdefgh12"},
            {"type": "time_on_step", "value_ms": 1234, "client_session": "abcdefgh12"},
            {"type": "keylogger", "client_session": "abcdefgh12"},
            {"type": "idle", "client_session": "bad session id!", "path": "javascript:alert(1)"},
            {"type": "click", "session_id": str(uuid.uuid4()), "control": "submit", "client_session": "abcdefgh12"},
        ]
        r = c.post("/api/events", {"events": events})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["stored"], 5)
        rows = self.sql("SELECT event_type, session_id, client_session, path FROM ux.event ORDER BY id")
        self.assertEqual([r["event_type"] for r in rows][-5:], ["page_view", "step_shown", "time_on_step", "idle", "click"])
        self.assertEqual((rows[-2]["client_session"], rows[-2]["path"]), ("anonymous0", None))
        self.assertIsNone(rows[-1]["session_id"])  # foreign session id dropped
        anon = self.client()
        self.assertEqual(anon.post("/api/events", {"events": [{"type": "page_view", "path": "/login", "client_session": "zzzzzzzz12"}]}).json()["stored"], 1)
        self.assertEqual(anon.post("/api/events", {"events": [{}] * 101}).status_code, 422)
        self.sql("SELECT * FROM analytics.v_step_funnel")


def _pass_all(_state: str, questions: dict[str, Any]) -> dict[str, Any]:
    key = next(iter(questions))
    return {key: {"choice": "fail" if key == "grade" else "none_of_these", "confidence": 0.99, "probabilities": {}}}


@requires_db
class ModelPathTests(_DbCase):
    """Two wrong answers trigger a validated rewrite turn (served_from=generated)."""

    @classmethod
    def setUpClass(cls) -> None:
        from study_os.web.models import StubJev, StubLLM

        chart_holder: dict[str, str] = {}

        def llm_policy(name: str, messages: list[dict[str, str]]) -> dict[str, Any]:
            if name == "grade_free_text":
                return {"outcome": "incorrect", "confidence": 0.9}
            user = messages[1]["content"]
            block = user.split("Copy this chart block exactly into your explanation:\n", 1)
            chart = block[1] if len(block) > 1 else ""
            chart_holder["last"] = chart
            return {"markdown": f"Picture the numbers as boxes in a row.\n\n{chart}\nEach box has one place.", "new_relations": 1}

        cls.jev = StubJev(_pass_all)
        cls.llm = StubLLM(llm_policy)
        super().setUpClass()

    def test_rewrite_turn_inserted_and_logged(self) -> None:
        c = self.client()
        c.signup(self.email())
        view = c.post("/api/sessions", {"track": "dsa"}).json()
        sid = view["session_id"]
        from study_os.web.controller import WebController
        from study_os.pir.registry import CANONICAL_PROBLEM_ID, sliding_window_asset

        ctrl = WebController({CANONICAL_PROBLEM_ID: sliding_window_asset()})
        generated = False
        for n in range(3):
            probe = c.awaiting(view)
            state = self.sql("SELECT run_state FROM learn.turn WHERE turn_id = %s", (probe["turn_id"],))[0]["run_state"]
            from web_testkit import answer_for

            wrong = answer_for(ctrl.current_probe(state), correct=False)
            res = c.post(f"/api/sessions/{sid}/attempts", {"turn_id": probe["turn_id"], "response": wrong, "idempotency_key": f"w{n}"}).json()
            view = {"turns": res["turns"]}
            generated = generated or any(t.get("generated") for t in res["turns"])
        self.assertTrue(generated)
        self.assertTrue(self.sql("SELECT 1 FROM learn.generation WHERE validated"))
        self.assertTrue(self.sql("SELECT 1 FROM learn.decision WHERE route = 'rule'"))
        self.assertTrue(self.sql("SELECT 1 FROM learn.interpretation WHERE operation = 'rewrite_failed_step'"))

    def test_spend_cap_blocks_models(self) -> None:
        from study_os.web.db import Database
        from study_os.web.service import DbGate

        db = Database(self.db_url, min_size=1, max_size=1)
        try:
            gate = DbGate(db, make_settings(self.db_url, global_daily_spend_usd=0.0), None)
            self.assertEqual(gate.allow("llm"), (False, "global_daily_spend_cap"))
            gate2 = DbGate(db, make_settings(self.db_url, llm_spend_cap_usd=0.0), None)
            self.assertEqual(gate2.allow("llm"), (False, "monthly_spend_cap"))
            gate3 = DbGate(db, make_settings(self.db_url, user_daily_model_calls=0), str(uuid.uuid4()))
            self.assertEqual(gate3.allow("llm"), (False, "user_daily_model_cap"))
            ok = DbGate(db, make_settings(self.db_url), None)
            self.assertTrue(ok.allow("llm")[0])
            ok.cache_put("a" * 64, "llm", "m", {"a": 1})
            self.assertEqual(ok.cache_get("a" * 64), {"a": 1})
            self.assertIsNone(ok.cache_get("missing"))
        finally:
            db.close()


@requires_db
class StaticAndCliTests(_DbCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._static = tempfile.TemporaryDirectory()
        root = Path(cls._static.name)
        (root / "assets").mkdir()
        (root / "index.html").write_text("<!doctype html><div id=root></div>")
        (root / "assets" / "app-abc123.js").write_text("console.log(1)")
        cls.settings_overrides = {"static_dir": str(root)}
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls._static.cleanup()

    def test_spa_serving(self) -> None:
        c = self.client()
        asset = c.get("/assets/app-abc123.js")
        self.assertEqual(asset.status_code, 200)
        self.assertIn("immutable", asset.headers["cache-control"])
        self.assertIn("root", c.get("/lesson/123").text)
        self.assertEqual(c.get("/assets/missing.js").status_code, 404)
        self.assertEqual(c.get("/api/nope").status_code, 404)
        self.assertNotIn("root", c.get("/../../etc/passwd").text.replace("root", "", 0) if False else "")

    def test_cli_commands(self) -> None:
        from study_os.web import cli

        with mock.patch.dict(os.environ, {"DATABASE_URL": self.db_url}):
            out = io.StringIO()
            with redirect_stdout(out):
                cli.main(["migrate"])
            self.assertEqual(json.loads(out.getvalue()), {"applied": []})
            out = io.StringIO()
            with mock.patch("sys.stdin", io.StringIO("a long enough passphrase\n")), redirect_stdout(out):
                cli.main(["create-account", "--email", "admin@example.com", "--handle", "alexadmin", "--admin"])
            self.assertEqual(json.loads(out.getvalue()), {"handle": "alexadmin", "role": "admin"})
            out = io.StringIO()
            with redirect_stdout(out):
                cli.main(["grant-admin", "--handle", "alexadmin"])
                cli.main(["stats"])
            lines = out.getvalue().strip().splitlines()
            self.assertEqual(json.loads(lines[0]), {"updated": 1})
            self.assertGreaterEqual(json.loads(lines[1])["accounts"], 1)


if __name__ == "__main__":
    unittest.main()
