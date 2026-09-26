"""API integration tests for the Study OS lesson player v2 (SOS-0005)."""

from __future__ import annotations

import sys
import unittest
import uuid
from contextlib import ExitStack
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web_testkit import ApiClient, make_settings, requires_db, temp_database  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.web.config import TUTOR_PROMPT_VERSION  # noqa: E402


class _PlayerDbCase(unittest.TestCase):
    """One throwaway database + app per test class, with a StubLLM for the tutor."""

    settings_overrides: dict[str, Any] = {}

    @classmethod
    def setUpClass(cls) -> None:
        from fastapi.testclient import TestClient
        from study_os.web.api import create_app
        from study_os.web.models import StubLLM

        def _llm_policy(name: str, messages: list[dict[str, str]]) -> dict[str, Any] | None:
            if name != "tutor_reply":
                return None
            return {"reply_md": "What do you notice about the picture?", "suggested_action": None}

        cls._stack = ExitStack()
        cls.db_url = cls._stack.enter_context(temp_database())
        cls.settings = make_settings(cls.db_url, **cls.settings_overrides)
        cls.llm = StubLLM(_llm_policy)
        cls.app = create_app(cls.settings, jev=None, llm=cls.llm, use_env_models=False)
        tc = TestClient(cls.app)
        cls._stack.enter_context(tc)
        cls.tc = tc

    @classmethod
    def tearDownClass(cls) -> None:
        cls._stack.close()

    def client(self) -> ApiClient:
        # New TestClient per caller so cookie jars stay isolated (important when
        # a test signs up two users). Class-scoped self.tc already ran lifespan,
        # so state["db"] is populated for this app instance.
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

    def _start_on_probe(self, c: ApiClient, lesson_id: str = "fractions-compare") -> tuple[str, dict]:
        """Start a session and skip teach-only intro steps until a real probe is showing."""
        view = c.c.post("/api/player/sessions", json={"lesson_id": lesson_id}, headers=c.headers).json()
        sid = view["session_id"]
        guard = 0
        while view.get("step", {}).get("probe") is None and view.get("phase") != "done" and guard < 8:
            guard += 1
            r = c.c.post(
                f"/api/player/sessions/{sid}/attempt",
                json={"response": "ok", "modality": "text", "idempotency_key": f"skip-{guard}"},
                headers=c.headers,
            )
            self.assertEqual(r.status_code, 200, r.text)
            r = c.c.post(f"/api/player/sessions/{sid}/next", json={}, headers=c.headers)
            self.assertEqual(r.status_code, 200, r.text)
            view = r.json()
        return sid, view



@requires_db
class PlayerGuestTests(_PlayerDbCase):
    def test_try_first_creates_guest_and_session(self) -> None:
        c = self.client()
        r = c.c.post("/api/try", json={}, headers={"X-Study-OS": "1"})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["me"]["is_guest"])
        self.assertIn("session", body)
        self.assertEqual(body["session"]["lesson"]["lesson_id"], "fractions-compare")
        self.assertIn("set-cookie", r.headers)

    def test_try_first_rejected_when_signed_in(self) -> None:
        c = self.client()
        c.signup(self.email())
        r = c.c.post("/api/try", json={}, headers={"X-Study-OS": "1"})
        self.assertEqual(r.status_code, 409)

    def test_claim_upgrades_guest_and_keeps_progress(self) -> None:
        c = self.client()
        r = c.c.post("/api/try", json={}, headers={"X-Study-OS": "1"})
        body = r.json()
        session_id = body["session"]["session_id"]
        email = self.email()
        c.headers["X-CSRF-Token"] = body["me"]["csrf_token"]
        claim = c.c.post("/api/auth/claim", json={"email": email, "passphrase": "a long enough passphrase"}, headers=c.headers)
        self.assertEqual(claim.status_code, 200, claim.text)
        self.assertFalse(claim.json()["is_guest"])
        me = c.c.get("/api/auth/me", headers=c.headers)
        self.assertFalse(me.json()["is_guest"])
        # session still reachable
        self.assertEqual(c.c.get(f"/api/player/sessions/{session_id}", headers=c.headers).status_code, 200)

    def test_claim_email_conflict(self) -> None:
        email = self.email()
        c1 = self.client()
        c1.signup(email)
        c2 = self.client()
        r = c2.c.post("/api/try", json={}, headers={"X-Study-OS": "1"})
        c2.headers["X-CSRF-Token"] = r.json()["me"]["csrf_token"]
        claim = c2.c.post("/api/auth/claim", json={"email": email, "passphrase": "another long enough passphrase"}, headers=c2.headers)
        self.assertEqual(claim.status_code, 409)


@requires_db
class PlayerSessionTests(_PlayerDbCase):
    def test_lanes_returns_four_lanes_and_continue(self) -> None:
        c = self.client()
        c.signup(self.email())
        r = c.c.get("/api/lanes", headers=c.headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(len(body["lanes"]), 4)
        self.assertIn("continue", body)
        lane_ids = [lane["lane_id"] for lane in body["lanes"]]
        self.assertEqual(lane_ids, ["dsa", "hesi", "ai-from-scratch", "study-os"])
        self.assertIsNotNone(body["continue"])

    def test_attempt_correct_incorrect_partial(self) -> None:
        c = self.client()
        c.signup(self.email())
        # Incorrect path
        sid, _ = self._start_on_probe(c)
        r = c.c.post(f"/api/player/sessions/{sid}/attempt", json={"response": "1", "modality": "text", "idempotency_key": "k1"}, headers=c.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["feedback"]["outcome"], "incorrect")
        # Correct path on a fresh session (stay on the main probe, not a post-miss variant)
        c2 = self.client()
        c2.signup(self.email())
        sid2, _ = self._start_on_probe(c2)
        r2 = c2.c.post(f"/api/player/sessions/{sid2}/attempt", json={"response": "4", "modality": "text", "idempotency_key": "k2"}, headers=c2.headers)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["feedback"]["outcome"], "correct")
        # Idempotency replay
        r3 = c2.c.post(f"/api/player/sessions/{sid2}/attempt", json={"response": "4", "modality": "text", "idempotency_key": "k2"}, headers=c2.headers)
        self.assertEqual(r3.status_code, 200)
        # Teach-skip + the real attempt both log as 'attempt'; idempotent replay must not add a third.
        events = self.sql(
            "SELECT * FROM learn.player_event WHERE session_id = %s AND event = 'attempt' AND idempotency_key LIKE '%%:k2'",
            (sid2,),
        )
        self.assertEqual(len(events), 1)

    def test_confused_queues_new_variant_on_same_step(self) -> None:
        c = self.client()
        c.signup(self.email())
        sid, before = self._start_on_probe(c)
        r = c.c.post(f"/api/player/sessions/{sid}/confused", json={}, headers=c.headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("feedback", body)
        # Re-explain keeps the step and queues the next variant; the variant is
        # applied only when the learner acknowledges the feedback.
        self.assertEqual(body["step"]["step_id"], before["step"]["step_id"])
        self.assertEqual(body["phase"], "feedback")
        self.assertEqual(body["feedback"]["next_action"], "retry")
        after = c.c.post(f"/api/player/sessions/{sid}/next", json={}, headers=c.headers).json()
        self.assertEqual(after["step"]["step_id"], before["step"]["step_id"])
        self.assertNotEqual(after["step"]["variant"], -1)
        self.assertEqual(after["phase"], "probe")

    def test_next_advances(self) -> None:
        c = self.client()
        c.signup(self.email())
        view = c.c.post("/api/player/sessions", json={"lesson_id": "fractions-compare"}, headers=c.headers).json()
        sid = view["session_id"]
        # first step has no probe (problem statement), next should advance
        r = c.c.post(f"/api/player/sessions/{sid}/next", json={}, headers=c.headers)
        self.assertEqual(r.status_code, 200)

    def test_another_users_session_is_404(self) -> None:
        a, b = self.client(), self.client()
        a.signup(self.email())
        b.signup(self.email())
        view = a.c.post("/api/player/sessions", json={"lesson_id": "fractions-compare"}, headers=a.headers).json()
        sid = view["session_id"]
        self.assertEqual(b.c.get(f"/api/player/sessions/{sid}", headers=b.headers).status_code, 404)
        self.assertEqual(b.c.post(f"/api/player/sessions/{sid}/next", json={}, headers=b.headers).status_code, 404)


@requires_db
class PlayerTutorTests(_PlayerDbCase):
    def test_tutor_reply_generated_and_logged(self) -> None:
        c = self.client()
        c.signup(self.email())
        view = c.c.post("/api/player/sessions", json={"lesson_id": "fractions-compare"}, headers=c.headers).json()
        sid = view["session_id"]
        r = c.c.post(f"/api/player/sessions/{sid}/tutor", json={"message": "I am stuck"}, headers=c.headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("reply_md", body)
        self.assertEqual(body["served"], "generated")
        self.assertEqual(body["prompt_version"], TUTOR_PROMPT_VERSION)
        self.assertTrue(body["message_id"])
        rows = self.sql("SELECT * FROM learn.llm_interaction WHERE session_id = %s", (sid,))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["served"], "generated")
        self.assertEqual(rows[0]["prompt_version"], TUTOR_PROMPT_VERSION)

    def test_tutor_leak_is_repaired_or_fallback(self) -> None:
        from contextlib import ExitStack
        from fastapi.testclient import TestClient
        from study_os.web.api import create_app
        from study_os.web.models import StubLLM

        def _leaky(name: str, messages: list[dict[str, str]]) -> dict[str, Any] | None:
            if name != "tutor_reply":
                return None
            return {"reply_md": "The answer is 4, which is the right value."}

        with ExitStack() as stack:
            db_url = stack.enter_context(temp_database())
            settings = make_settings(db_url)
            app = create_app(settings, jev=None, llm=StubLLM(_leaky), use_env_models=False)
            tc = stack.enter_context(TestClient(app))
            c = ApiClient(tc)
            c.signup(self.email())
            sid, _ = self._start_on_probe(c)
            r = c.c.post(f"/api/player/sessions/{sid}/tutor", json={"message": "tell me"}, headers=c.headers)
            self.assertEqual(r.status_code, 200)
            self.assertIn(r.json()["served"], ("generated", "fallback"))
            # Should never leak the forbidden answer while the probe is open.
            self.assertNotIn(" 4", " " + r.json()["reply_md"] + " ")
            self.assertNotIn("answer is 4", r.json()["reply_md"].lower())

    def test_tutor_disabled_uses_fallback(self) -> None:
        from contextlib import ExitStack
        from fastapi.testclient import TestClient
        from study_os.web.api import create_app
        from study_os.web.models import StubLLM

        with ExitStack() as stack:
            db_url = stack.enter_context(temp_database())
            settings = make_settings(db_url, llm_enabled=False)
            app = create_app(settings, jev=None, llm=StubLLM(lambda _n, _m: None), use_env_models=False)
            tc = stack.enter_context(TestClient(app))
            c = ApiClient(tc)
            c.signup(self.email())
            sid, _ = self._start_on_probe(c)
            r = c.c.post(f"/api/player/sessions/{sid}/tutor", json={"message": "help"}, headers=c.headers)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()["served"], "fallback")


@requires_db
class PlayerRegeneratePresentationTests(_PlayerDbCase):
    """Chat-triggered current-step re-render (#126)."""

    @staticmethod
    def _policy(render):
        def _llm(name: str, _messages: list[dict[str, str]]) -> dict[str, Any] | None:
            if name != "tutor_reply":
                return None
            return {"reply_md": "Look at the same box again. What changed?", "suggested_action": None, "regenerate_presentation": render}
        return _llm

    def _app_with(self, render) -> Any:
        from fastapi.testclient import TestClient
        from study_os.web.api import create_app
        from study_os.web.models import StubLLM

        return create_app(make_settings(self.db_url, llm_enabled=True), jev=None, llm=StubLLM(self._policy(render)), use_env_models=False), TestClient

    def _run(self, render) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        app, TestClient = self._app_with(render)
        with TestClient(app) as tc:
            c = ApiClient(tc)
            c.signup(self.email())
            sid, before = self._start_on_probe(c, "sliding-window-box")
            reply = c.c.post(f"/api/player/sessions/{sid}/tutor", json={"message": "show me this another way"}, headers=c.headers)
            self.assertEqual(reply.status_code, 200, reply.text)
            body = reply.json()
            after = c.c.get(f"/api/player/sessions/{sid}", headers=c.headers).json()
            return before, body, after

    def test_valid_regeneration_is_applied_in_place_without_advancing(self) -> None:
        before, body, after = self._run({"teach_md": "Same box, read from its left edge.", "frame_indices": [0]})
        update = body["regenerate_presentation"]
        self.assertEqual(update["schema_version"], "study-os.player-presentation.v1")
        self.assertEqual(update["operation"], "regenerate_presentation")
        self.assertEqual((update["previous_version"], update["version"]), (0, 1))
        self.assertEqual(update["provenance"]["prompt_version"], "tutor.v3")
        # Same step identity, and the served view adopted the new presentation.
        self.assertEqual(after["step"]["step_id"], before["step"]["step_id"])
        self.assertEqual(after["step"]["concept_id"], before["step"]["concept_id"])
        self.assertEqual(after["presentation_version"], 1)
        self.assertEqual(after["step"]["teach_md"], "Same box, read from its left edge.")
        self.assertEqual(after["step"]["teach_frames"], update["teach_frames"])
        # Nothing else moved.
        self.assertEqual(after["phase"], before["phase"])
        self.assertEqual(after["step"]["variant"], before["step"]["variant"])
        self.assertEqual(after["step"]["probe"], before["step"]["probe"])
        self.assertEqual(after["progress"], before["progress"])

    def test_regeneration_survives_reload_and_bumps_the_version(self) -> None:
        app, TestClient = self._app_with({"teach_md": "Same box, read from its left edge.", "frame_indices": [0]})
        with TestClient(app) as tc:
            c = ApiClient(tc)
            c.signup(self.email())
            sid, _ = self._start_on_probe(c, "sliding-window-box")
            first = c.c.post(f"/api/player/sessions/{sid}/tutor", json={"message": "again"}, headers=c.headers).json()["regenerate_presentation"]
            resumed = c.c.post("/api/player/sessions", json={"lesson_id": "sliding-window-box"}, headers=c.headers).json()
            self.assertEqual(resumed["presentation_version"], first["version"])
            self.assertEqual(resumed["step"]["teach_md"], first["teach_md"])
            second = c.c.post(f"/api/player/sessions/{sid}/tutor", json={"message": "again"}, headers=c.headers).json()["regenerate_presentation"]
            self.assertEqual((second["previous_version"], second["version"]), (1, 2))

    def test_rejected_regeneration_leaves_the_session_untouched(self) -> None:
        # The probe answer is 4; a proposal that leaks it must be refused.
        before, body, after = self._run({"teach_md": "The position is 4.", "frame_indices": [0]})
        self.assertIsNone(body["regenerate_presentation"])
        self.assertEqual(after["presentation_version"], 0)
        self.assertEqual(after["step"]["teach_md"], before["step"]["teach_md"])
        self.assertNotIn("4", after["step"]["teach_md"])

    def test_out_of_range_frames_are_refused(self) -> None:
        before, body, after = self._run({"teach_md": "Another look at the same box.", "frame_indices": [7]})
        self.assertIsNone(body["regenerate_presentation"])
        self.assertEqual(after["presentation_version"], 0)
        self.assertEqual(after["step"]["teach_frames"], before["step"]["teach_frames"])

    def test_absent_regeneration_is_still_a_normal_reply(self) -> None:
        before, body, after = self._run(None)
        self.assertIsNone(body["regenerate_presentation"])
        self.assertEqual(body["served"], "generated")
        self.assertEqual(after["presentation_version"], 0)


@requires_db
class PlayerFeedbackTests(_PlayerDbCase):
    def test_feedback_stored_for_step(self) -> None:
        c = self.client()
        c.signup(self.email())
        view = c.c.post("/api/player/sessions", json={"lesson_id": "fractions-compare"}, headers=c.headers).json()
        sid = view["session_id"]
        # A step review is a 1-5 rating plus a typed why (SOS-0016, #126); the
        # old like/dislike step payload is intentionally no longer accepted.
        r = c.c.post("/api/feedback", json={
            "session_id": sid,
            "step_id": view["step"]["step_id"],
            "target_kind": "step",
            "target_id": f"{view['step']['step_id']}:{view['step']['variant']}",
            "presentation_version": view["presentation_version"],
            "rating": 2,
            "free_text": "I already knew this, my email is a@b.com",
            "idempotency_key": str(uuid.uuid4()),
        }, headers=c.headers)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])
        rows = self.sql("SELECT * FROM ux.feedback WHERE session_id = %s", (sid,))
        self.assertEqual(len(rows), 1)
        self.assertNotIn("@", rows[0]["free_text_scrubbed"])
        self.assertEqual(rows[0]["rating"], "2")

    def test_feedback_for_tutor_message_looks_up_model(self) -> None:
        c = self.client()
        c.signup(self.email())
        view = c.c.post("/api/player/sessions", json={"lesson_id": "fractions-compare"}, headers=c.headers).json()
        sid = view["session_id"]
        r = c.c.post(f"/api/player/sessions/{sid}/tutor", json={"message": "hi"}, headers=c.headers)
        message_id = r.json()["message_id"]
        r2 = c.c.post("/api/feedback", json={
            "target_kind": "tutor_message",
            "target_id": message_id,
            "rating": "like",
            "reasons": [],
        }, headers=c.headers)
        self.assertEqual(r2.status_code, 200)
        rows = self.sql("SELECT * FROM ux.feedback WHERE llm_interaction_id = %s", (message_id,))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["model"], "cb/glm-5.3")

    def test_admin_feedback_forbidden_for_learner(self) -> None:
        c = self.client()
        c.signup(self.email())
        r = c.c.get("/api/admin/feedback", headers=c.headers)
        self.assertEqual(r.status_code, 403)

    def test_admin_feedback_works_for_admin(self) -> None:
        c = self.client()
        c.signup(self.email())
        self.sql("UPDATE auth.account SET role = 'admin' WHERE handle = %s", (c.c.cookies.get("sos_session"),))
        # Need to identify the account by session; easier: set all to admin in tests.
        self.sql("UPDATE auth.account SET role = 'admin'")
        r = c.c.get("/api/admin/feedback", headers=c.headers)
        self.assertEqual(r.status_code, 200)
        self.assertIn("rows", r.json())
        self.assertIn("by_prompt_version", r.json())


@requires_db
class PlayerAdaptTests(_PlayerDbCase):
    def test_adapt_example_and_back(self) -> None:
        c = self.client()
        c.signup(self.email())
        sid, _ = self._start_on_probe(c)
        r = c.c.post(f"/api/player/sessions/{sid}/adapt", json={"kind": "example"}, headers=c.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["card_mode"], "worked_example")
        r2 = c.c.post(f"/api/player/sessions/{sid}/adapt", json={"kind": "back"}, headers=c.headers)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["card_mode"], "probe")
        events = self.sql("SELECT * FROM learn.player_event WHERE session_id = %s AND event = 'adapt'", (sid,))
        self.assertEqual(len(events), 2)

    def test_adapt_invalid_kind(self) -> None:
        c = self.client()
        c.signup(self.email())
        sid, _ = self._start_on_probe(c)
        r = c.c.post(f"/api/player/sessions/{sid}/adapt", json={"kind": "jump"}, headers=c.headers)
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
