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
from study_os.application.contracts import (  # noqa: E402
    NextRetentionProbeRequest,
    StartStudySessionRequest,
    SubjectStatusRequest,
)
from study_os.application.service import (  # noqa: E402
    ApplicationService,
    project_next_retention_probe_to_mcp,
    project_runtime_health_to_mcp,
    project_start_study_session_to_mcp,
    project_subject_status_to_mcp,
)
from study_os.mcp.server import MCPServer  # noqa: E402


class MalformedDoctorService:
    def doctor(self) -> dict[str, Any]:
        return {
            "healthy": True,
            "runtime_version": "0.1.0",
            "schema_version": 1,
            "checks": {"broken": {"healthy": True}},
        }


class MalformedStatusService:
    def status(self, *, subject_id: str) -> dict[str, Any]:
        return {
            "subject_id": subject_id,
            "current_session_id": 123,
            "current_checkpoint_id": None,
            "current_focus": None,
            "next_action": None,
        }


class MalformedNextProbeService:
    def get_next_probe(self, *, subject_id: str) -> dict[str, Any]:
        return {
            "subject_id": subject_id,
            "probe": None,
            "reason": "scheduled_retention_probe",
            "source_checkpoint_id": "checkpoint-impossible",
        }


class MalformedStartSessionService:
    def start_session(self, **_: Any) -> dict[str, Any]:
        return {
            "session_id": "session-broken",
            "subject_id": "subject-broken",
            "started_at": "not-a-timestamp",
            "created": True,
        }


class ApplicationMcpConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)

    def tearDown(self) -> None:
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def fixture_scheduled_probe(self, subject_id: str = "subject-probe") -> dict[str, Any]:
        session = self.service.start_session(
            idempotency_key=f"{subject_id}-session",
            subject_id=subject_id,
            project_id=f"{subject_id}-project",
            domain_id=f"{subject_id}-domain",
        )
        artifact = self.service.capture_evidence(
            session_id=session["session_id"],
            subject_id=subject_id,
            content=b"public-safe probe evidence",
            media_type="text/plain",
        )
        event = self.service.record_learning_event(
            idempotency_key=f"{subject_id}-event",
            session_id=session["session_id"],
            subject_id=subject_id,
            evidence_class="observed",
            event_type="probe_seed",
            payload={"summary": "scheduled-probe fixture"},
        )
        checkpoint = self.service.checkpoint(
            idempotency_key=f"{subject_id}-checkpoint",
            subject_id=subject_id,
            source_session_ids=[session["session_id"]],
            evidence_ids=[artifact["artifact_id"], event["event_id"]],
            capability_state={"retention": "not_tested"},
            assistance_state={},
            resume={"current_focus": "retention", "next_action": "run delayed probe"},
        )
        return self.service.schedule_retention_probe(
            idempotency_key=f"{subject_id}-probe",
            subject_id=subject_id,
            concept_id="sliding-window",
            due_at="2026-08-26T00:00:00Z",
            source_checkpoint_id=checkpoint["checkpoint_id"],
        )

    def test_doctor_round_trip_matches_direct_runtime_exactly(self) -> None:
        direct = self.service.doctor()
        application = ApplicationService(self.service).inspect_runtime_health()
        projected = project_runtime_health_to_mcp(application)
        self.assertEqual(projected, direct)

        mcp = MCPServer(self.service).call_tool("doctor", {})
        self.assertEqual(mcp, direct)

    def test_doctor_jsonrpc_payload_preserves_same_semantic_object(self) -> None:
        direct = self.service.doctor()
        response = MCPServer(self.service).handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "doctor", "arguments": {}},
            }
        )
        self.assertIsNotNone(response)
        assert response is not None
        text = response["result"]["content"][0]["text"]
        self.assertEqual(json.loads(text), direct)

    def test_doctor_rejects_transport_arguments_instead_of_ignoring_them(self) -> None:
        result = MCPServer(self.service).call_tool("doctor", {"invented": True})
        self.assertEqual(result["error"]["category"], "validation_error")
        self.assertFalse(result["error"]["retryable"])

    def test_malformed_runtime_result_fails_as_internal_error(self) -> None:
        result = MCPServer(MalformedDoctorService()).call_tool("doctor", {})  # type: ignore[arg-type]
        self.assertEqual(result["error"]["category"], "internal_error")
        self.assertFalse(result["error"]["retryable"])
        self.assertEqual(result["error"]["details"]["exception"], "ApplicationBoundaryError")

    def test_status_direct_application_and_mcp_are_exactly_equivalent(self) -> None:
        started = self.service.start_session(
            idempotency_key="status-seed-1",
            subject_id="subject-status",
            project_id="project-status",
            domain_id="dsa",
        )
        direct = self.service.status(subject_id="subject-status")
        application = project_subject_status_to_mcp(
            ApplicationService(self.service).get_subject_status(
                SubjectStatusRequest(subject_id="subject-status")
            )
        )
        mcp = MCPServer(self.service).call_tool("status", {"subject_id": "subject-status"})

        self.assertEqual(application, direct)
        self.assertEqual(mcp, direct)
        self.assertEqual(direct["current_session_id"], started["session_id"])
        self.assertIsNone(direct["current_checkpoint_id"])
        self.assertIsNone(direct["current_focus"])
        self.assertIsNone(direct["next_action"])

    def test_status_preserves_not_found_semantics(self) -> None:
        result = MCPServer(self.service).call_tool("status", {"subject_id": "missing-subject"})
        self.assertEqual(result["error"]["category"], "not_found")
        self.assertFalse(result["error"]["retryable"])

    def test_status_malformed_runtime_result_fails_closed(self) -> None:
        result = MCPServer(MalformedStatusService()).call_tool(  # type: ignore[arg-type]
            "status",
            {"subject_id": "subject-broken"},
        )
        self.assertEqual(result["error"]["category"], "internal_error")
        self.assertEqual(result["error"]["details"]["exception"], "ApplicationBoundaryError")

    def test_status_rejects_application_only_transport_fields(self) -> None:
        result = MCPServer(self.service).call_tool(
            "status",
            {
                "subject_id": "subject-001",
                "application_contract_version": "0.1.0",
            },
        )
        self.assertEqual(result["error"]["category"], "validation_error")

    def test_next_probe_empty_state_is_exactly_equivalent(self) -> None:
        self.service.start_session(
            idempotency_key="empty-probe-session",
            subject_id="subject-empty-probe",
            project_id="project-empty-probe",
            domain_id="dsa",
        )
        direct = self.service.get_next_probe(subject_id="subject-empty-probe")
        application = project_next_retention_probe_to_mcp(
            ApplicationService(self.service).get_next_retention_probe(
                NextRetentionProbeRequest(subject_id="subject-empty-probe")
            )
        )
        mcp = MCPServer(self.service).call_tool(
            "get_next_probe",
            {"subject_id": "subject-empty-probe"},
        )
        self.assertEqual(application, direct)
        self.assertEqual(mcp, direct)
        self.assertIsNone(direct["probe"])
        self.assertEqual(direct["reason"], "no_scheduled_probe")
        self.assertIsNone(direct["source_checkpoint_id"])

    def test_next_probe_scheduled_state_is_exactly_equivalent(self) -> None:
        scheduled = self.fixture_scheduled_probe()
        direct = self.service.get_next_probe(subject_id="subject-probe")
        application = project_next_retention_probe_to_mcp(
            ApplicationService(self.service).get_next_retention_probe(
                NextRetentionProbeRequest(subject_id="subject-probe")
            )
        )
        mcp = MCPServer(self.service).call_tool(
            "get_next_probe",
            {"subject_id": "subject-probe"},
        )
        self.assertEqual(application, direct)
        self.assertEqual(mcp, direct)
        self.assertEqual(
            direct["probe"]["retention_probe_id"],
            scheduled["retention_probe_id"],
        )
        self.assertEqual(direct["reason"], "scheduled_retention_probe")
        self.assertIsNotNone(direct["source_checkpoint_id"])

    def test_next_probe_preserves_not_found_semantics(self) -> None:
        result = MCPServer(self.service).call_tool(
            "get_next_probe",
            {"subject_id": "missing-probe-subject"},
        )
        self.assertEqual(result["error"]["category"], "not_found")
        self.assertFalse(result["error"]["retryable"])

    def test_next_probe_malformed_runtime_state_fails_closed(self) -> None:
        result = MCPServer(MalformedNextProbeService()).call_tool(  # type: ignore[arg-type]
            "get_next_probe",
            {"subject_id": "subject-broken"},
        )
        self.assertEqual(result["error"]["category"], "internal_error")
        self.assertEqual(result["error"]["details"]["exception"], "ApplicationBoundaryError")

    def test_next_probe_rejects_application_only_transport_fields(self) -> None:
        result = MCPServer(self.service).call_tool(
            "get_next_probe",
            {
                "subject_id": "subject-001",
                "application_contract_version": "0.1.0",
            },
        )
        self.assertEqual(result["error"]["category"], "validation_error")

    def test_start_session_direct_application_and_mcp_are_differentially_equivalent(self) -> None:
        roots = [tempfile.TemporaryDirectory() for _ in range(3)]
        services = [StudyOSService(RuntimeConfig.from_env(root.name)) for root in roots]
        args = {
            "idempotency_key": "differential-start-1",
            "subject_id": "subject-differential",
            "project_id": "project-differential",
            "domain_id": "dsa",
            "source_client": "mcp",
            "metadata": {"surface": "chat", "mode": "study"},
        }
        try:
            with (
                patch("study_os.services.runtime_base.new_id", return_value="session-fixed"),
                patch(
                    "study_os.services.runtime_base.utc_now",
                    return_value="2026-08-25T23:40:00.123456Z",
                ),
            ):
                direct = services[0].start_session(**args)
                application_result = ApplicationService(services[1]).start_study_session(
                    StartStudySessionRequest(**args)
                )
                application = project_start_study_session_to_mcp(application_result)
                mcp = MCPServer(services[2]).call_tool("start_session", args)

            self.assertEqual(application, direct)
            self.assertEqual(mcp, direct)
            for service in services:
                row = service.db.connection.execute(
                    "SELECT session_id, source_client, metadata_json FROM sessions WHERE subject_id = ?",
                    ("subject-differential",),
                ).fetchone()
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["session_id"], "session-fixed")
                self.assertEqual(row["source_client"], "mcp")
                self.assertEqual(json.loads(row["metadata_json"]), args["metadata"])
        finally:
            for service in services:
                service.close()
            for root in roots:
                root.cleanup()

    def test_start_session_optional_legacy_arguments_remain_accepted(self) -> None:
        result = MCPServer(self.service).call_tool(
            "start_session",
            {
                "idempotency_key": "legacy-optionals-1",
                "subject_id": "subject-001",
                "project_id": "dsa-python",
                "domain_id": "dsa",
                "source_client": "existing-client",
                "metadata": {"existing": True},
            },
        )
        self.assertNotIn("error", result)
        self.assertTrue(result["created"])

    def test_start_session_absent_null_and_empty_metadata_are_same_idempotent_request(self) -> None:
        server = MCPServer(self.service)
        base = {
            "idempotency_key": "start-normalization-1",
            "subject_id": "subject-normalization",
            "project_id": "project-normalization",
            "domain_id": "dsa",
        }
        first = server.call_tool("start_session", base)
        explicit_null = server.call_tool(
            "start_session",
            {**base, "source_client": None, "metadata": None},
        )
        explicit_empty = server.call_tool("start_session", {**base, "metadata": {}})

        self.assertTrue(first["created"])
        self.assertFalse(explicit_null["created"])
        self.assertFalse(explicit_empty["created"])
        self.assertEqual(first["session_id"], explicit_null["session_id"])
        self.assertEqual(first["session_id"], explicit_empty["session_id"])
        count = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM sessions WHERE subject_id = ?",
            ("subject-normalization",),
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_start_session_same_key_with_different_semantic_metadata_conflicts(self) -> None:
        server = MCPServer(self.service)
        base = {
            "idempotency_key": "start-conflict-1",
            "subject_id": "subject-conflict",
            "project_id": "project-conflict",
            "domain_id": "dsa",
            "metadata": {"surface": "chat"},
        }
        first = server.call_tool("start_session", base)
        conflict = server.call_tool(
            "start_session",
            {**base, "metadata": {"surface": "web"}},
        )

        self.assertTrue(first["created"])
        self.assertEqual(conflict["error"]["category"], "conflict")
        self.assertFalse(conflict["error"]["retryable"])
        count = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM sessions WHERE subject_id = ?",
            ("subject-conflict",),
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_start_session_malformed_runtime_result_fails_closed(self) -> None:
        result = MCPServer(MalformedStartSessionService()).call_tool(  # type: ignore[arg-type]
            "start_session",
            {
                "idempotency_key": "malformed-start-1",
                "subject_id": "subject-broken",
                "project_id": "project-broken",
                "domain_id": "dsa",
            },
        )
        self.assertEqual(result["error"]["category"], "internal_error")
        self.assertEqual(result["error"]["details"]["exception"], "ApplicationBoundaryError")

    def test_start_session_rejects_nonlegacy_transport_extras(self) -> None:
        result = MCPServer(self.service).call_tool(
            "start_session",
            {
                "idempotency_key": "extra-start-1",
                "subject_id": "subject-extra",
                "project_id": "project-extra",
                "domain_id": "dsa",
                "application_contract_version": "0.1.0",
            },
        )
        self.assertEqual(result["error"]["category"], "validation_error")
        count = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM sessions WHERE subject_id = ?",
            ("subject-extra",),
        ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_public_mcp_tool_set_is_exactly_fourteen_with_bounded_append(self) -> None:
        names = MCPServer(self.service).list_tool_names()
        self.assertEqual(len(names), 14)
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("append_conversation_turn", names)


if __name__ == "__main__":
    unittest.main()
