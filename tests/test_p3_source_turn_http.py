from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.mcp.http_server import create_http_server  # noqa: E402


class SourceTurnHTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)
        self.session = self.service.start_session(
            idempotency_key="http-session-1",
            subject_id="subject-http",
            project_id="project-http",
            domain_id="domain-http",
        )
        self.service.close()
        self.server = create_http_server(self.config, host="127.0.0.1", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp_dir.cleanup()

    def post(self, message: dict, *, path: str = "/mcp") -> tuple[int, dict]:
        body = json.dumps(message).encode("utf-8")
        connection = HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=5)
        connection.request(
            "POST",
            path,
            body=body,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "MCP-Protocol-Version": "2025-03-26",
            },
        )
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, payload

    def call_tool(self, request_id: int, name: str, arguments: dict) -> dict:
        _, response = self.post(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        return json.loads(response["result"]["content"][0]["text"])

    def test_http_mcp_appends_both_turns_durably(self) -> None:
        session_id = self.session["session_id"]
        user = self.call_tool(
            1,
            "append_conversation_turn",
            {
                "idempotency_key": "http-turn-user-1",
                "session_id": session_id,
                "subject_id": "subject-http",
                "role": "user",
                "content": "Synthetic user turn.",
            },
        )
        assistant = self.call_tool(
            2,
            "append_conversation_turn",
            {
                "idempotency_key": "http-turn-assistant-1",
                "session_id": session_id,
                "subject_id": "subject-http",
                "role": "assistant",
                "content": "Synthetic assistant turn.",
            },
        )
        service = StudyOSService(self.config)
        try:
            rows = service.db.connection.execute(
                "SELECT role, artifact_id, content_sha256 FROM messages ORDER BY created_at, message_id"
            ).fetchall()
            self.assertEqual([(row["role"], row["artifact_id"]) for row in rows], [("user", user["artifact_id"]), ("assistant", assistant["artifact_id"])])
            self.assertEqual(len(rows), 2)
            self.assertTrue(service.doctor()["healthy"])
        finally:
            service.close()

    def test_gpt_action_route_uses_same_bounded_append(self) -> None:
        status, action = self.post(
            {
                "idempotency_key": "http-action-turn-1",
                "session_id": self.session["session_id"],
                "subject_id": "subject-http",
                "role": "user",
                "content": "Synthetic action route turn.",
            },
            path="/actions/append_conversation_turn",
        )
        self.assertEqual(status, 200)
        self.assertTrue(action["created"])
        self.assertEqual(action["capture_origin"], "live")


if __name__ == "__main__":
    unittest.main()
