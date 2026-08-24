from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mcp import Client  # noqa: E402
from mcp.server.transport_security import TransportSecuritySettings  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.mcp.network import (  # noqa: E402
    MCP_BEARER_TOKEN_ENV,
    build_network_mcp_server,
    create_network_app,
)


BEARER_TOKEN = "study-os-p1-test-bearer-token"
PROTOCOL_VERSION = "2026-07-28"


def expected_tools() -> tuple[str, ...]:
    contract = json.loads(
        (ROOT / "contracts" / "study-os-mcp-tools.v0.1.json").read_text(encoding="utf-8")
    )
    return tuple(tool["name"] for tool in contract["tools"])


def tool_payload(result):
    if result.structured_content is None:
        raise AssertionError("expected structured MCP tool content")
    return result.structured_content


class P1MCPNetworkTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)

    def tearDown(self):
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def test_network_server_preserves_exact_semantic_tool_surface(self):
        server = build_network_mcp_server(self.service)

        async def scenario() -> None:
            async with Client(server) as client:
                listing = await client.list_tools()
                self.assertEqual(tuple(tool.name for tool in listing.tools), expected_tools())
                doctor = await client.call_tool("doctor", {})
                self.assertFalse(doctor.is_error)
                self.assertTrue(tool_payload(doctor)["healthy"])

        asyncio.run(scenario())

    def test_streamable_http_requires_bearer_before_mcp_dispatch(self):
        app = create_network_app(
            self.service,
            bearer_token=BEARER_TOKEN,
            transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        )
        envelope = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {
                "_meta": {
                    "io.modelcontextprotocol/protocolVersion": PROTOCOL_VERSION,
                    "io.modelcontextprotocol/clientInfo": {
                        "name": "study-os-p1-test",
                        "version": "1",
                    },
                    "io.modelcontextprotocol/clientCapabilities": {},
                }
            },
        }

        with TestClient(app, base_url="http://localhost") as client:
            common_headers = {
                "content-type": "application/json",
                "accept": "application/json, text/event-stream",
                "mcp-protocol-version": PROTOCOL_VERSION,
                "mcp-method": "tools/list",
            }
            for authorization in (None, "Bearer wrong-token", "Basic anything"):
                headers = dict(common_headers)
                if authorization is not None:
                    headers["authorization"] = authorization
                response = client.post("/mcp", headers=headers, json=envelope)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.headers["www-authenticate"], "Bearer")
                self.assertNotIn(BEARER_TOKEN, response.text)

            response = client.post(
                "/mcp",
                headers={**common_headers, "authorization": f"Bearer {BEARER_TOKEN}"},
                json=envelope,
            )
            self.assertEqual(response.status_code, 200)
            names = tuple(tool["name"] for tool in response.json()["result"]["tools"])
            self.assertEqual(names, expected_tools())
            self.assertNotIn(BEARER_TOKEN, response.text)

            # There is intentionally no parallel health/admin/OpenAPI surface.
            non_mcp = client.get(
                "/healthz", headers={"authorization": f"Bearer {BEARER_TOKEN}"}
            )
            self.assertEqual(non_mcp.status_code, 404)

    def test_network_app_fails_closed_without_token_or_loopback(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(MCP_BEARER_TOKEN_ENV, None)
            with self.assertRaisesRegex(ValueError, MCP_BEARER_TOKEN_ENV):
                create_network_app(self.service)

        with self.assertRaisesRegex(ValueError, "loopback"):
            create_network_app(
                self.service,
                bearer_token=BEARER_TOKEN,
                host="0.0.0.0",
            )

    def test_fresh_mcp_client_resumes_after_service_restart(self):
        first_server = build_network_mcp_server(self.service)

        async def chat_a() -> tuple[str, str, str]:
            async with Client(first_server) as client:
                session = tool_payload(
                    await client.call_tool(
                        "start_session",
                        {
                            "idempotency_key": "p1-chat-a-session",
                            "subject_id": "subject-p1",
                            "project_id": "p1-integration",
                            "domain_id": "integration",
                            "source_client": "chat-a",
                        },
                    )
                )
                attempt = tool_payload(
                    await client.call_tool(
                        "record_attempt",
                        {
                            "idempotency_key": "p1-chat-a-attempt",
                            "session_id": session["session_id"],
                            "subject_id": "subject-p1",
                            "task_id": "p1-baseline",
                            "response": {"answer": "synthetic-pass"},
                            "assistance_level": "none",
                        },
                    )
                )
                assessment = tool_payload(
                    await client.call_tool(
                        "record_assessment",
                        {
                            "idempotency_key": "p1-chat-a-assessment",
                            "session_id": session["session_id"],
                            "subject_id": "subject-p1",
                            "capability": "state_prediction",
                            "result": "pass",
                            "assistance_level": "none",
                            "evidence_ids": [attempt["attempt_id"]],
                        },
                    )
                )
                checkpoint = tool_payload(
                    await client.call_tool(
                        "checkpoint",
                        {
                            "idempotency_key": "p1-chat-a-checkpoint",
                            "subject_id": "subject-p1",
                            "source_session_ids": [session["session_id"]],
                            "evidence_ids": [assessment["assessment_id"]],
                            "capability_state": {"state_prediction": "pass_unaided"},
                            "assistance_state": {"level": "none"},
                            "resume": {
                                "current_focus": "p1-cross-session",
                                "next_action": "fresh-client-transfer-probe",
                            },
                        },
                    )
                )
                return (
                    session["session_id"],
                    assessment["assessment_id"],
                    checkpoint["checkpoint_id"],
                )

        session_id, assessment_id, checkpoint_id = asyncio.run(chat_a())

        # Simulate closing Chat A and restarting the local Study OS process.
        self.service.close()
        self.service = StudyOSService(self.config)
        second_server = build_network_mcp_server(self.service)

        async def chat_b() -> None:
            async with Client(second_server) as client:
                resumed = tool_payload(
                    await client.call_tool("resume", {"subject_id": "subject-p1"})
                )
                self.assertEqual(resumed["checkpoint_id"], checkpoint_id)
                self.assertEqual(resumed["next_action"], "fresh-client-transfer-probe")
                self.assertEqual(
                    resumed["capability_state"]["state_prediction"], "pass_unaided"
                )

                event = tool_payload(
                    await client.call_tool(
                        "record_learning_event",
                        {
                            "idempotency_key": "p1-chat-b-event",
                            "session_id": session_id,
                            "subject_id": "subject-p1",
                            "evidence_class": "observed",
                            "event_type": "fresh_client_resumed",
                            "payload": {"checkpoint_id": checkpoint_id},
                        },
                    )
                )
                next_checkpoint = tool_payload(
                    await client.call_tool(
                        "checkpoint",
                        {
                            "idempotency_key": "p1-chat-b-checkpoint",
                            "subject_id": "subject-p1",
                            "source_session_ids": [session_id],
                            "evidence_ids": [assessment_id, event["event_id"]],
                            "capability_state": {"state_prediction": "pass_unaided"},
                            "assistance_state": {"level": "none"},
                            "resume": {
                                "current_focus": "p1-cross-session",
                                "next_action": "continue-learning",
                                "expected_current_checkpoint_id": checkpoint_id,
                            },
                        },
                    )
                )
                self.assertNotEqual(next_checkpoint["checkpoint_id"], checkpoint_id)

        asyncio.run(chat_b())


if __name__ == "__main__":
    unittest.main()
