"""Loopback HTTP transport for the versioned semantic MCP surface.

The transport owns HTTP concerns only. Requests are dispatched through
``MCPServer`` so the application/runtime contracts remain the sole semantic
boundary. The optional action routes exist for the GPT Actions adapter and
accept the same bounded tool names.
"""

from __future__ import annotations

import json
import secrets
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

from ..config import RuntimeConfig
from ..errors import StudyOSError, validation
from .server import MCPServer


SUPPORTED_PROTOCOL_VERSIONS = {
    "2024-11-05",
    "2025-03-26",
    "2025-06-18",
    "2025-11-25",
}
DEFAULT_PROTOCOL_VERSION = "2025-03-26"
MAX_REQUEST_BYTES = 1024 * 1024
GPT_ACTION_JSON_FIELDS = frozenset({"payload", "response", "capability_state", "assistance_state", "resume"})


def _json_error(category: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return StudyOSError(category, message, False, details or {}).as_dict()


class MCPHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        *,
        config: RuntimeConfig,
        mcp_path: str = "/mcp",
        actions_path: str = "/actions",
        allowed_origins: Iterable[str] = (),
        bearer_token: str | None = None,
        contract_path: str | Path | None = None,
    ) -> None:
        self.study_os_config = config
        self.mcp_path = "/" + mcp_path.strip("/")
        self.actions_path = "/" + actions_path.strip("/")
        self.allowed_origins = frozenset(origin for origin in allowed_origins if origin)
        self.bearer_token = bearer_token
        self.contract_path = contract_path
        super().__init__(server_address, _MCPRequestHandler)


class _MCPRequestHandler(BaseHTTPRequestHandler):
    server: MCPHTTPServer
    protocol_version = "HTTP/1.1"
    server_version = "StudyOS-MCP/0.2"

    def log_message(self, format: str, *args: Any) -> None:
        # Never log request bodies, credentials, or private source content.
        return

    def _send_json(self, status: int, payload: dict[str, Any], *, headers: dict[str, str] | None = None) -> None:
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(encoded)

    def _send_empty(self, status: int) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _path_matches(self) -> bool:
        return urlsplit(self.path).path.rstrip("/") == self.server.mcp_path.rstrip("/")

    def _action_name(self) -> str | None:
        path = urlsplit(self.path).path.rstrip("/")
        prefix = self.server.actions_path.rstrip("/") + "/"
        if not path.startswith(prefix):
            return None
        name = path[len(prefix):]
        return name if name and "/" not in name else None

    def _authorize(self) -> bool:
        origin = self.headers.get("Origin")
        if origin and origin not in self.server.allowed_origins:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": _json_error("validation_error", "Origin is not allowed", details={"origin": origin})["error"]})
            return False
        expected_token = self.server.bearer_token
        if expected_token is not None:
            if not secrets.compare_digest(self.headers.get("Authorization", ""), f"Bearer {expected_token}"):
                self._send_json(
                    HTTPStatus.UNAUTHORIZED,
                    {"error": _json_error("validation_error", "Bearer authentication required")["error"]},
                    headers={"WWW-Authenticate": "Bearer"},
                )
                return False
        return True

    def _read_json_body(self) -> dict[str, Any] | None:
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_REQUEST_BYTES:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": _json_error("validation_error", "Invalid or oversized Content-Length")["error"]})
            return None
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": _json_error("validation_error", "Request body must be valid UTF-8 JSON", details={"exception": type(exc).__name__})["error"]})
            return None
        if not isinstance(payload, dict):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": _json_error("validation_error", "Request body must be a JSON object")["error"]})
            return None
        return payload

    def _dispatch(self, message: dict[str, Any]) -> dict[str, Any] | None:
        service = None
        try:
            from ..services.runtime import StudyOSService

            service = StudyOSService(self.server.study_os_config)
            response = MCPServer(service, contract_path=self.server.contract_path).handle_message(message)
            if response and message.get("method") == "initialize":
                requested = (message.get("params") or {}).get("protocolVersion")
                if isinstance(response.get("result"), dict):
                    response["result"]["protocolVersion"] = requested or DEFAULT_PROTOCOL_VERSION
            return response
        finally:
            if service is not None:
                service.close()

    def _dispatch_action(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        service = None
        try:
            from ..services.runtime import StudyOSService

            service = StudyOSService(self.server.study_os_config)
            return MCPServer(service, contract_path=self.server.contract_path).call_tool(name, arguments)
        finally:
            if service is not None:
                service.close()

    def _protocol_valid(self, message: dict[str, Any]) -> bool:
        header_version = self.headers.get("MCP-Protocol-Version")
        requested = (message.get("params") or {}).get("protocolVersion") if message.get("method") == "initialize" else None
        if (header_version and header_version not in SUPPORTED_PROTOCOL_VERSIONS) or (requested and requested not in SUPPORTED_PROTOCOL_VERSIONS):
            version = header_version or requested
            self._send_json(HTTPStatus.BAD_REQUEST, {"jsonrpc": "2.0", "id": message.get("id"), "error": _json_error("unsupported_version", "Unsupported MCP protocol version", details={"protocol_version": version})["error"]})
            return False
        return True

    def _handle_action(self, name: str) -> None:
        if not self._authorize():
            return
        arguments = self._read_json_body()
        if arguments is None:
            return
        for field in GPT_ACTION_JSON_FIELDS:
            if isinstance(arguments.get(field), str):
                try:
                    arguments[field] = json.loads(arguments[field])
                except json.JSONDecodeError:
                    pass
        try:
            result = self._dispatch_action(name, arguments)
        except Exception as exc:
            result = _json_error("internal_error", "Unexpected Study OS service failure", details={"exception": type(exc).__name__})
        self._send_json(HTTPStatus.OK, result)

    def do_GET(self) -> None:
        if not self._path_matches():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": _json_error("not_found", "MCP endpoint not found")["error"]})
            return
        self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
        self.send_header("Allow", "POST")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:
        action_name = self._action_name()
        if not self._path_matches() and action_name is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": _json_error("not_found", "MCP endpoint not found")["error"]})
            return
        if action_name is not None:
            self._handle_action(action_name)
            return
        if not self._authorize():
            return
        if not self._protocol_valid_message_body():
            return
        message = self._message_body
        if not self._protocol_valid(message):
            return
        try:
            response = self._dispatch(message)
        except StudyOSError as exc:
            response = {"jsonrpc": "2.0", "id": message.get("id"), "error": exc.as_dict()["error"]}
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": message.get("id"), "error": _json_error("internal_error", "Unexpected MCP service failure", details={"exception": type(exc).__name__})["error"]}
        if "id" not in message or response is None:
            self._send_empty(HTTPStatus.ACCEPTED)
        else:
            self._send_json(HTTPStatus.OK, response)

    def _protocol_valid_message_body(self) -> bool:
        message = self._read_json_body()
        if message is None:
            return False
        if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": _json_error("validation_error", "Request body must be a JSON-RPC 2.0 request or notification")["error"]})
            return False
        self._message_body = message
        return True


def create_http_server(
    config: RuntimeConfig | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    mcp_path: str = "/mcp",
    actions_path: str = "/actions",
    allowed_origins: Iterable[str] = (),
    bearer_token: str | None = None,
    contract_path: str | Path | None = None,
) -> MCPHTTPServer:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise validation("Study OS MCP HTTP transport must bind to loopback")
    if not 0 <= port <= 65535:
        raise validation("port must be between 0 and 65535")
    return MCPHTTPServer(
        (host, port),
        config=config or RuntimeConfig.from_env(),
        mcp_path=mcp_path,
        actions_path=actions_path,
        allowed_origins=allowed_origins,
        bearer_token=bearer_token,
        contract_path=contract_path,
    )


def serve_http(config: RuntimeConfig | None = None, **kwargs: Any) -> None:
    server = create_http_server(config, **kwargs)
    try:
        server.serve_forever()
    finally:
        server.server_close()
