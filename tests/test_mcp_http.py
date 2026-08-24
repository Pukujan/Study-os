import json
import sys
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig  # noqa: E402
from study_os.errors import StudyOSError  # noqa: E402
from study_os.mcp.http_server import create_http_server  # noqa: E402


class MCPHTTPTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.server = create_http_server(self.config, host="127.0.0.1", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp_dir.cleanup()

    def post(self, message, *, headers=None):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = json.dumps(message).encode("utf-8")
        request_headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        }
        request_headers.update(headers or {})
        connection.request("POST", "/mcp", body=body, headers=request_headers)
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response.status, dict(response.headers), json.loads(payload) if payload else None

    def test_streamable_http_dispatches_existing_mcp_surface(self):
        status, headers, initialize = self.post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}},
            },
            headers={"MCP-Protocol-Version": "2025-03-26"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(initialize["result"]["protocolVersion"], "2025-03-26")

        status, _, tools = self.post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        self.assertEqual(status, 200)
        self.assertEqual([tool["name"] for tool in tools["result"]["tools"]], [
            "doctor", "status", "start_session", "record_learning_event", "record_attempt",
            "record_assessment", "record_representation_intervention", "record_representation_outcome",
            "checkpoint", "resume", "schedule_retention_probe", "get_next_probe", "export_fossil",
        ])

        status, _, doctor = self.post({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "doctor", "arguments": {}}})
        self.assertEqual(status, 200)
        doctor_payload = json.loads(doctor["result"]["content"][0]["text"])
        self.assertTrue(doctor_payload["healthy"])

    def test_notification_returns_202_without_a_body(self):
        status, headers, payload = self.post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.assertEqual(status, 202)
        self.assertEqual(headers["Content-Length"], "0")
        self.assertIsNone(payload)

    def test_origin_and_bearer_guards_are_enforced(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.server = create_http_server(
            self.config,
            host="127.0.0.1",
            port=0,
            allowed_origins=["https://chatgpt.com"],
            bearer_token="test-token",
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]
        message = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        status, _, _ = self.post(message)
        self.assertEqual(status, 401)
        status, _, _ = self.post(message, headers={"Authorization": "Bearer test-token", "Origin": "https://evil.example"})
        self.assertEqual(status, 403)
        status, _, _ = self.post(message, headers={"Authorization": "Bearer test-token", "Origin": "https://chatgpt.com"})
        self.assertEqual(status, 200)

    def test_non_loopback_binding_is_rejected(self):
        with self.assertRaises(StudyOSError) as raised:
            create_http_server(self.config, host="0.0.0.0", port=0)
        self.assertEqual(raised.exception.category, "validation_error")


if __name__ == "__main__":
    unittest.main()
