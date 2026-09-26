"""RED learner step-review contract for #126; no product implementation here."""

from __future__ import annotations

import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_web_player_api import _PlayerDbCase  # noqa: E402
from web_testkit import requires_db  # noqa: E402


@requires_db
class PlayerStepReviewContractTests(_PlayerDbCase):
    def _start(self) -> tuple[Any, str, dict[str, Any]]:
        client = self.client()
        client.signup(self.email())
        view = client.post("/api/player/sessions", {"lesson_id": "sliding-window-box"}).json()
        return client, view["session_id"], view

    @staticmethod
    def _payload(session_id: str, view: dict[str, Any], **changes: Any) -> dict[str, Any]:
        step = view["step"]
        payload = {
            "session_id": session_id,
            "step_id": step["step_id"],
            "target_kind": "step",
            "target_id": f"{step['step_id']}:{step['variant']}",
            "presentation_version": view["presentation_version"],
            "rating": 3,
            "free_text": "The box helped; the index label was unclear.",
            "idempotency_key": str(uuid.uuid4()),
        }
        payload.update(changes)
        return payload

    def _rows(self, session_id: str) -> list[dict[str, Any]]:
        return self.sql("SELECT * FROM ux.feedback WHERE session_id = %s ORDER BY created_at, feedback_id", (session_id,))

    def test_replay_is_one_logical_append_and_fresh_key_appends(self) -> None:
        client, sid, view = self._start()
        payload = self._payload(sid, view)
        first = client.post("/api/feedback", payload)
        self.assertEqual(first.status_code, 200, first.text)
        replay = client.post("/api/feedback", payload)
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertEqual(replay.json()["feedback_id"], first.json()["feedback_id"])
        rows = self._rows(sid)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["rating"], "3")
        self.assertEqual(rows[0]["step_id"], view["step"]["step_id"])
        self.assertEqual(rows[0]["presentation_version"], view["presentation_version"])
        self.assertEqual(rows[0]["idempotency_key"], payload["idempotency_key"])

        again = client.post("/api/feedback", {**payload, "idempotency_key": str(uuid.uuid4()), "rating": 5})
        self.assertEqual(again.status_code, 200, again.text)
        after = self._rows(sid)
        self.assertEqual(len(after), 2)
        self.assertEqual(after[0], rows[0])
        self.assertEqual({row["rating"] for row in after}, {"3", "5"})

    def test_rating_and_typed_why_are_server_required(self) -> None:
        client, sid, view = self._start()
        valid = self._payload(sid, view)
        invalid = [
            {**valid, "rating": value, "idempotency_key": str(uuid.uuid4())}
            for value in (0, 6, True, 3.5, "3", "like")
        ]
        invalid += [{**valid, "free_text": reason, "idempotency_key": str(uuid.uuid4())} for reason in ("", " \t\n")]
        invalid.append({key: value for key, value in valid.items() if key != "free_text"})
        for payload in invalid:
            with self.subTest(payload=payload):
                response = client.post("/api/feedback", payload)
                self.assertGreaterEqual(response.status_code, 400, response.text)
        self.assertEqual(self._rows(sid), [])
        for edge in (1, 5):
            response = client.post("/api/feedback", self._payload(sid, view, rating=edge))
            self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual({row["rating"] for row in self._rows(sid)}, {"1", "5"})

    def test_wrong_identity_version_and_changed_replay_are_rejected(self) -> None:
        client, sid, view = self._start()
        valid = self._payload(sid, view)
        for changes in (
            {"step_id": "index"},
            {"target_id": "index:-1"},
            {"target_id": f"{view['step']['step_id']}:99"},
            {"presentation_version": view["presentation_version"] + 1},
            {"session_id": str(uuid.uuid4())},
        ):
            response = client.post("/api/feedback", {**valid, **changes, "idempotency_key": str(uuid.uuid4())})
            self.assertGreaterEqual(response.status_code, 400, response.text)
        self.assertEqual(self._rows(sid), [])
        first = client.post("/api/feedback", valid)
        self.assertEqual(first.status_code, 200, first.text)
        conflict = client.post("/api/feedback", {**valid, "rating": 4})
        self.assertGreaterEqual(conflict.status_code, 400, conflict.text)
        self.assertEqual(len(self._rows(sid)), 1)
        self.assertEqual(self._rows(sid)[0]["rating"], "3")

    def test_double_submit_race_has_one_receipt(self) -> None:
        client, sid, view = self._start()
        payload = self._payload(sid, view)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: client.post("/api/feedback", payload), range(2)))
        self.assertEqual([response.status_code for response in results], [200, 200])
        self.assertEqual(results[0].json()["feedback_id"], results[1].json()["feedback_id"])
        self.assertEqual(len(self._rows(sid)), 1)

    def test_feedback_table_has_database_append_only_guard(self) -> None:
        import psycopg

        client, sid, view = self._start()
        response = client.post("/api/feedback", self._payload(sid, view))
        self.assertEqual(response.status_code, 200, response.text)
        feedback_id = response.json()["feedback_id"]
        with psycopg.connect(self.db_url) as conn:
            for statement, params in (
                ("UPDATE ux.feedback SET rating = '4' WHERE feedback_id = %s", (feedback_id,)),
                ("DELETE FROM ux.feedback WHERE feedback_id = %s", (feedback_id,)),
                ("TRUNCATE ux.feedback", ()),
            ):
                with self.subTest(statement=statement):
                    conn.execute("SAVEPOINT append_only_probe")
                    try:
                        with self.assertRaises(psycopg.Error):
                            conn.execute(statement, params)
                    finally:
                        conn.execute("ROLLBACK TO SAVEPOINT append_only_probe")
        self.assertEqual(len(self._rows(sid)), 1)

    def test_regenerated_presentation_keeps_review_on_same_step(self) -> None:
        from fastapi.testclient import TestClient
        from study_os.web.api import create_app
        from study_os.web.models import StubLLM
        from web_testkit import ApiClient, make_settings

        llm = StubLLM(lambda _name, _messages: {
            "reply_md": "Look at the same box.",
            "suggested_action": None,
            "regenerate_presentation": {"teach_md": "Same box, read from its left edge.", "frame_indices": [0]},
        })
        app = create_app(make_settings(self.db_url, llm_enabled=True), jev=None, llm=llm, use_env_models=False)
        with TestClient(app) as tc:
            client = ApiClient(tc)
            client.signup(self.email())
            sid, before = self._start_on_probe(client, "sliding-window-box")
            tutor = client.post(f"/api/player/sessions/{sid}/tutor", {"message": "Show this step another way."})
            self.assertEqual(tutor.status_code, 200, tutor.text)
            after = client.get(f"/api/player/sessions/{sid}").json()
            self.assertEqual(after["step"]["step_id"], before["step"]["step_id"])
            self.assertGreater(after["presentation_version"], before["presentation_version"])
            review = client.post("/api/feedback", self._payload(sid, after))
            self.assertEqual(review.status_code, 200, review.text)
            rows = self._rows(sid)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["step_id"], before["step"]["step_id"])
            self.assertEqual(rows[0]["presentation_version"], after["presentation_version"])
            served = client.get(f"/api/player/sessions/{sid}").json()
            self.assertEqual(served["progress"], after["progress"])
            self.assertEqual(served["phase"], after["phase"])
