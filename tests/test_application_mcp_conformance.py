from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.application.service import (  # noqa: E402
    ApplicationService,
    project_runtime_health_to_mcp,
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

    def test_public_mcp_tool_set_remains_exactly_thirteen(self) -> None:
        names = MCPServer(self.service).list_tool_names()
        self.assertEqual(len(names), 13)
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
