from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.adaptive.telemetry import AttemptTelemetry  # noqa: E402
from study_os.application.contracts import RecordAttemptRequest  # noqa: E402
from study_os.application.service import (  # noqa: E402
    ApplicationService,
    project_record_attempt_to_mcp,
)
from study_os.mcp.server import MCPServer  # noqa: E402


class MalformedAttemptService:
    def record_attempt(self, **_: Any) -> dict[str, Any]:
        return {"attempt_id": 123, "created": "yes"}


class RecordAttemptApplicationConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)

    def tearDown(self) -> None:
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def seed_session(self, subject_id: str = "subject-attempt") -> dict[str, Any]:
        return self.service.start_session(
            idempotency_key=f"{subject_id}-session",
            subject_id=subject_id,
            project_id="project-attempt",
            domain_id="dsa",
        )

    def test_direct_application_and_mcp_are_differentially_equivalent(self) -> None:
        roots = [tempfile.TemporaryDirectory() for _ in range(3)]
        services = [StudyOSService(RuntimeConfig.from_env(root.name)) for root in roots]
        session_args = {
            "idempotency_key": "attempt-session-seed",
            "subject_id": "subject-differential-attempt",
            "project_id": "project-differential-attempt",
            "domain_id": "dsa",
        }
        telemetry = AttemptTelemetry(
            task_version="1.0.0",
            competency_ids=("algo.two_candidate_update_order",),
            attempt_number=1,
            interaction_mode="state_prediction",
            assistance_level_before_attempt="A3",
            representation_ids_visible=("state-table-v1",),
            feedback_exposure="structural_hint",
            self_report={"confidence": "low"},
        )
        args = {
            "idempotency_key": "attempt-differential-1",
            "session_id": "session-fixed",
            "subject_id": "subject-differential-attempt",
            "task_id": "item-update-order-v1",
            "response": {
                "prediction": "promote old largest before replacing it",
                "trace": [2, 5, 4],
            },
            **telemetry.record_attempt_fields(),
        }
        try:
            for service in services:
                with (
                    patch(
                        "study_os.services.runtime_base.new_id",
                        return_value="session-fixed",
                    ),
                    patch(
                        "study_os.services.runtime_base.utc_now",
                        return_value="2026-08-27T03:10:00.000000Z",
                    ),
                ):
                    session = service.start_session(**session_args)
                self.assertEqual(session["session_id"], "session-fixed")

            with (
                patch(
                    "study_os.services.runtime_base.new_id",
                    return_value="attempt-fixed",
                ),
                patch(
                    "study_os.services.runtime_base.utc_now",
                    return_value="2026-08-27T03:11:00.000000Z",
                ),
            ):
                direct = services[0].record_attempt(**args)
                application = project_record_attempt_to_mcp(
                    ApplicationService(services[1]).record_attempt(
                        RecordAttemptRequest(**args)
                    )
                )
                mcp = MCPServer(services[2]).call_tool("record_attempt", args)

            self.assertEqual(application, direct)
            self.assertEqual(mcp, direct)
            self.assertEqual(direct, {"attempt_id": "attempt-fixed", "created": True})

            expected_context = telemetry.to_context()
            for service in services:
                row = service.db.connection.execute(
                    "SELECT attempt_id, session_id, subject_id, task_id, response_json, "
                    "assistance_level, context_json, idempotency_key FROM attempts "
                    "WHERE attempt_id = ?",
                    ("attempt-fixed",),
                ).fetchone()
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["session_id"], "session-fixed")
                self.assertEqual(row["subject_id"], "subject-differential-attempt")
                self.assertEqual(row["task_id"], "item-update-order-v1")
                self.assertEqual(json.loads(row["response_json"]), args["response"])
                self.assertEqual(row["assistance_level"], "A3")
                self.assertEqual(json.loads(row["context_json"]), expected_context)
                self.assertEqual(row["idempotency_key"], "attempt-differential-1")
        finally:
            for service in services:
                service.close()
            for root in roots:
                root.cleanup()

    def test_optional_legacy_fields_and_normalization_remain_compatible(self) -> None:
        session = self.seed_session("subject-normalized-attempt")
        server = MCPServer(self.service)
        base = {
            "idempotency_key": "attempt-normalization-1",
            "session_id": session["session_id"],
            "subject_id": "subject-normalized-attempt",
            "task_id": "task-normalization",
            "response": {"answer": "right"},
        }

        first = server.call_tool("record_attempt", base)
        explicit_null = server.call_tool(
            "record_attempt",
            {**base, "assistance_level": "none", "context": None},
        )
        explicit_empty = server.call_tool(
            "record_attempt",
            {**base, "assistance_level": "none", "context": {}},
        )

        self.assertTrue(first["created"])
        self.assertFalse(explicit_null["created"])
        self.assertFalse(explicit_empty["created"])
        self.assertEqual(first["attempt_id"], explicit_null["attempt_id"])
        self.assertEqual(first["attempt_id"], explicit_empty["attempt_id"])
        row = self.service.db.connection.execute(
            "SELECT assistance_level, context_json FROM attempts WHERE attempt_id = ?",
            (first["attempt_id"],),
        ).fetchone()
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["assistance_level"], "none")
        self.assertEqual(json.loads(row["context_json"]), {})

    def test_existing_noncanonical_assistance_string_remains_accepted(self) -> None:
        session = self.seed_session("subject-legacy-assistance")
        result = MCPServer(self.service).call_tool(
            "record_attempt",
            {
                "idempotency_key": "attempt-legacy-assistance-1",
                "session_id": session["session_id"],
                "subject_id": "subject-legacy-assistance",
                "task_id": "task-legacy-assistance",
                "response": "answer",
                "assistance_level": "representation_visible",
                "context": {"legacy": True},
            },
        )
        self.assertNotIn("error", result)
        row = self.service.db.connection.execute(
            "SELECT assistance_level, context_json FROM attempts WHERE attempt_id = ?",
            (result["attempt_id"],),
        ).fetchone()
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["assistance_level"], "representation_visible")
        self.assertEqual(json.loads(row["context_json"]), {"legacy": True})

    def test_same_key_with_different_attempt_payload_conflicts(self) -> None:
        session = self.seed_session("subject-attempt-conflict")
        server = MCPServer(self.service)
        base = {
            "idempotency_key": "attempt-conflict-1",
            "session_id": session["session_id"],
            "subject_id": "subject-attempt-conflict",
            "task_id": "task-conflict",
            "response": {"answer": "first"},
            "context": {"attempt_number": 1},
        }
        first = server.call_tool("record_attempt", base)
        conflict = server.call_tool(
            "record_attempt",
            {**base, "response": {"answer": "changed"}},
        )

        self.assertTrue(first["created"])
        self.assertEqual(conflict["error"]["category"], "conflict")
        self.assertFalse(conflict["error"]["retryable"])
        count = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM attempts WHERE subject_id = ?",
            ("subject-attempt-conflict",),
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_missing_or_wrong_session_preserves_not_found_semantics(self) -> None:
        result = MCPServer(self.service).call_tool(
            "record_attempt",
            {
                "idempotency_key": "attempt-missing-session",
                "session_id": "missing-session",
                "subject_id": "subject-missing-session",
                "task_id": "task-1",
                "response": None,
            },
        )
        self.assertEqual(result["error"]["category"], "not_found")
        self.assertFalse(result["error"]["retryable"])

    def test_malformed_runtime_result_fails_closed(self) -> None:
        result = MCPServer(MalformedAttemptService()).call_tool(  # type: ignore[arg-type]
            "record_attempt",
            {
                "idempotency_key": "attempt-malformed",
                "session_id": "session-broken",
                "subject_id": "subject-broken",
                "task_id": "task-broken",
                "response": {"answer": "anything"},
            },
        )
        self.assertEqual(result["error"]["category"], "internal_error")
        self.assertEqual(result["error"]["details"]["exception"], "ApplicationBoundaryError")

    def test_rejects_application_only_or_unknown_transport_fields(self) -> None:
        session = self.seed_session("subject-attempt-unknown")
        base = {
            "idempotency_key": "attempt-unknown-1",
            "session_id": session["session_id"],
            "subject_id": "subject-attempt-unknown",
            "task_id": "task-unknown",
            "response": {"answer": "right"},
        }
        for extra in (
            {"application_contract_version": "0.1.0"},
            {"invented": True},
        ):
            with self.subTest(extra=extra):
                result = MCPServer(self.service).call_tool(
                    "record_attempt",
                    {**base, **extra},
                )
                self.assertEqual(result["error"]["category"], "validation_error")


if __name__ == "__main__":
    unittest.main()
