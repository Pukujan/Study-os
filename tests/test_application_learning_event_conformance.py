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
from study_os.application.contracts import RecordLearningEventRequest  # noqa: E402
from study_os.application.service import (  # noqa: E402
    ApplicationService,
    project_record_learning_event_to_mcp,
)
from study_os.mcp.server import MCPServer  # noqa: E402


class MalformedLearningEventService:
    def record_learning_event(self, **_: Any) -> dict[str, Any]:
        return {
            "event_id": 123,
            "created": True,
            "evidence_class": "observed",
        }


class RecordLearningEventApplicationConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)
        self.session = self.service.start_session(
            idempotency_key="event-session",
            subject_id="subject-event",
            project_id="project-event",
            domain_id="dsa",
        )

    def tearDown(self) -> None:
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def test_direct_application_and_mcp_are_differentially_equivalent(self) -> None:
        roots = [tempfile.TemporaryDirectory() for _ in range(3)]
        services = [StudyOSService(RuntimeConfig.from_env(root.name)) for root in roots]
        sessions = [
            service.start_session(
                idempotency_key="event-differential-session",
                subject_id="subject-differential-event",
                project_id="project-differential-event",
                domain_id="dsa",
            )
            for service in services
        ]
        common = {
            "idempotency_key": "event-differential",
            "subject_id": "subject-differential-event",
            "evidence_class": "observed",
            "event_type": "prediction_submitted",
            "payload": {"prediction": "right", "confidence": "low"},
            "source_ids": None,
            "payload_version": "0.1.0",
        }
        try:
            with patch(
                "study_os.services.runtime_base.new_id",
                return_value="event-fixed",
            ):
                direct = services[0].record_learning_event(
                    **common,
                    session_id=sessions[0]["session_id"],
                )
                application = project_record_learning_event_to_mcp(
                    ApplicationService(services[1]).record_learning_event(
                        RecordLearningEventRequest(
                            **common,
                            session_id=sessions[1]["session_id"],
                        )
                    )
                )
                mcp = MCPServer(services[2]).call_tool(
                    "record_learning_event",
                    {**common, "session_id": sessions[2]["session_id"]},
                )

            self.assertEqual(application, direct)
            self.assertEqual(mcp, direct)
            for service in services:
                row = service.db.connection.execute(
                    "SELECT event_id, evidence_class, event_type, payload_json, "
                    "payload_version, source_ids_json FROM learning_events "
                    "WHERE subject_id = ?",
                    ("subject-differential-event",),
                ).fetchone()
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["event_id"], "event-fixed")
                self.assertEqual(row["evidence_class"], "observed")
                self.assertEqual(row["event_type"], "prediction_submitted")
                self.assertEqual(json.loads(row["payload_json"]), common["payload"])
                self.assertEqual(row["payload_version"], "0.1.0")
                self.assertEqual(json.loads(row["source_ids_json"]), [])
        finally:
            for service in services:
                service.close()
            for root in roots:
                root.cleanup()

    def test_payload_evidence_ids_are_derived_when_source_ids_absent_or_null(self) -> None:
        artifact = self.service.capture_evidence(
            session_id=self.session["session_id"],
            subject_id="subject-event",
            content=b"derived event evidence",
            media_type="text/plain",
        )
        base = {
            "idempotency_key": "derived-event",
            "session_id": self.session["session_id"],
            "subject_id": "subject-event",
            "evidence_class": "derived",
            "event_type": "diagnosis",
            "payload": {
                "evidence_ids": [artifact["artifact_id"]],
                "claim": "possible update-order bottleneck",
            },
        }
        server = MCPServer(self.service)
        first = server.call_tool("record_learning_event", base)
        explicit_null = server.call_tool(
            "record_learning_event",
            {**base, "source_ids": None, "payload_version": "0.1.0"},
        )
        explicit_sources = server.call_tool(
            "record_learning_event",
            {
                **base,
                "source_ids": [artifact["artifact_id"]],
                "payload_version": "0.1.0",
            },
        )

        self.assertTrue(first["created"])
        self.assertFalse(explicit_null["created"])
        self.assertFalse(explicit_sources["created"])
        self.assertEqual(first["event_id"], explicit_null["event_id"])
        self.assertEqual(first["event_id"], explicit_sources["event_id"])
        row = self.service.db.connection.execute(
            "SELECT source_ids_json, payload_version FROM learning_events WHERE event_id = ?",
            (first["event_id"],),
        ).fetchone()
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(json.loads(row["source_ids_json"]), [artifact["artifact_id"]])
        self.assertEqual(row["payload_version"], "0.1.0")

    def test_idempotent_retry_and_changed_payload_conflict_are_preserved(self) -> None:
        server = MCPServer(self.service)
        base = {
            "idempotency_key": "event-retry",
            "session_id": self.session["session_id"],
            "subject_id": "subject-event",
            "evidence_class": "observed",
            "event_type": "prediction_submitted",
            "payload": {"prediction": "right"},
        }
        first = server.call_tool("record_learning_event", base)
        retry = server.call_tool("record_learning_event", base)
        conflict = server.call_tool(
            "record_learning_event",
            {**base, "payload": {"prediction": "left"}},
        )

        self.assertTrue(first["created"])
        self.assertFalse(retry["created"])
        self.assertEqual(first["event_id"], retry["event_id"])
        self.assertEqual(conflict["error"]["category"], "conflict")
        count = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM learning_events WHERE subject_id = ?",
            ("subject-event",),
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_missing_session_preserves_not_found(self) -> None:
        result = MCPServer(self.service).call_tool(
            "record_learning_event",
            {
                "idempotency_key": "missing-session-event",
                "session_id": "missing-session",
                "subject_id": "subject-event",
                "evidence_class": "observed",
                "event_type": "prediction_submitted",
                "payload": {},
            },
        )
        self.assertEqual(result["error"]["category"], "not_found")
        self.assertFalse(result["error"]["retryable"])

    def test_malformed_runtime_result_fails_closed(self) -> None:
        result = MCPServer(MalformedLearningEventService()).call_tool(  # type: ignore[arg-type]
            "record_learning_event",
            {
                "idempotency_key": "malformed-event",
                "session_id": "session-broken",
                "subject_id": "subject-broken",
                "evidence_class": "observed",
                "event_type": "prediction_submitted",
                "payload": {},
            },
        )
        self.assertEqual(result["error"]["category"], "internal_error")
        self.assertEqual(result["error"]["details"]["exception"], "ApplicationBoundaryError")

    def test_mcp_rejects_application_only_or_unknown_fields(self) -> None:
        base = {
            "idempotency_key": "unexpected-event",
            "session_id": self.session["session_id"],
            "subject_id": "subject-event",
            "evidence_class": "observed",
            "event_type": "prediction_submitted",
            "payload": {},
        }
        for extra in (
            {"application_contract_version": "0.1.0"},
            {"invented": True},
        ):
            with self.subTest(extra=extra):
                result = MCPServer(self.service).call_tool(
                    "record_learning_event",
                    {**base, **extra},
                )
                self.assertEqual(result["error"]["category"], "validation_error")


if __name__ == "__main__":
    unittest.main()
