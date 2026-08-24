"""Loopback-only Streamable HTTP transport for the existing MCP server.

This module is transport plumbing only. Every request is dispatched through
``MCPServer`` and therefore reaches the existing semantic service and its P0
invariants. It intentionally binds to 127.0.0.1 by default; Secure MCP Tunnel
is expected to provide the remote/private connection and any outer access
control.
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


def _json_error(category: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return StudyOSError(category, message, False, details or {}).as_dict()


class MCPHTTPServer(ThreadingHTTPServer):
    """Threaded HTTP server with one MCP endpoint and per-request services."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        *,
        config: RuntimeConfig,
        mcp_path: str = "/mcp",
        allowed_origins: Iterable[str] = (),
        bearer_token: str | None = None,
        contract_path: str | Path | None = None,
    ) -> None:
        self.study_os_config = config
        self.mcp_path = "/" + mcp_path.strip("/")
        self.allowed_origins = frozenset(origin for origin in allowed_origins if origin)
        self.bearer_token = bearer_token
        self.contract_path = contract_path
        super().__init__(server_address, _MCPRequestHandler)


class _MCPRequestHandler(BaseHTTPRequestHandler):
    server: MCPHTTPServer
    protocol_version = "HTTP/1.1"
    server_version = "StudyOS-MCP/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        # Do not log request bodies, authorization headers, or tool arguments.
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

    def _authorize(self) -> bool:
        origin = self.headers.get("Origin")
        if origin and origin not in self.server.allowed_origins:
            self._send_json(
                HTTPStatus.FORBIDDEN,
                {"jsonrpc": "2.0", "id": None, "error": _json_error("validation_error", "Origin is not allowed", details={"origin": origin})["error"]},
            )
            return False
        expected_token = self.server.bearer_token
        if expected_token is not None:
            authorization = self.headers.get("Authorization", "")
            expected = f"Bearer {expected_token}"
            if not secrets.compare_digest(authorization, expected):
                self._send_json(
                    HTTPStatus.UNAUTHORIZED,
                    {"jsonrpc": "2.0", "id": None, "error": _json_error("validation_error", "Bearer authentication required")["error"]},
                    headers={"WWW-Authenticate": "Bearer"},
                )
                return False
        return True

    def _protocol_valid(self, message: dict[str, Any]) -> bool:
        header_version = self.headers.get("MCP-Protocol-Version")
        if header_version and header_version not in SUPPORTED_PROTOCOL_VERSIONS:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"jsonrpc": "2.0", "id": message.get("id"), "error": _json_error("unsupported_version", "Unsupported MCP protocol version", details={"protocol_version": header_version})["error"]},
            )
            return False
        params = message.get("params")
        if message.get("method") == "initialize" and isinstance(params, dict):
            requested = params.get("protocolVersion")
            if requested and requested not in SUPPORTED_PROTOCOL_VERSIONS:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"jsonrpc": "2.0", "id": message.get("id"), "error": _json_error("unsupported_version", "Unsupported MCP protocol version", details={"protocol_version": requested})["error"]},
                )
                return False
        return True

    def _dispatch(self, message: dict[str, Any]) -> dict[str, Any] | None:
        service = None
        try:
            from ..services.runtime import StudyOSService

            service = StudyOSService(self.server.study_os_config)
            response = MCPServer(service, contract_path=self.server.contract_path).handle_message(message)
            if response and message.get("method") == "initialize":
                requested = (message.get("params") or {}).get("protocolVersion")
                response_result = response.get("result")
                if isinstance(response_result, dict):
                    response_result["protocolVersion"] = requested or DEFAULT_PROTOCOL_VERSION
            return response
        finally:
            if service is not None:
                service.close()

    def do_GET(self) -> None:
        if not self._path_matches():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": _json_error("not_found", "MCP endpoint not found")["error"]})
            return
        # Current Streamable HTTP is POST-only. Secure MCP Tunnel should target
        # the MCP endpoint, not a browser GET health probe.
        self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
        self.send_header("Allow", "POST")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:
        if not self._path_matches():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": _json_error("not_found", "MCP endpoint not found")["error"]})
            return
        if not self._authorize():
            return
        accept = self.headers.get("Accept", "")
        if accept and not any(value in accept for value in ("application/json", "text/event-stream", "*/*")):
            self._send_json(HTTPStatus.NOT_ACCEPTABLE, {"error": _json_error("validation_error", "Accept header must allow JSON or SSE")["error"]})
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_REQUEST_BYTES:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": _json_error("validation_error", "Invalid or oversized Content-Length")["error"]})
            return
        try:
            message = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": _json_error("validation_error", "Request body must be valid UTF-8 JSON", details={"exception": type(exc).__name__})["error"]})
            return
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": _json_error("validation_error", "Request body must be a JSON-RPC 2.0 request or notification")["error"]})
            return
        if not self._protocol_valid(message):
            return
        try:
            response = self._dispatch(message)
        except StudyOSError as exc:
            response = {"jsonrpc": "2.0", "id": message.get("id"), "error": exc.as_dict()["error"]}
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": message.get("id"), "error": _json_error("internal_error", "Unexpected MCP service failure", details={"exception": type(exc).__name__})["error"]}
        if "id" not in message:
            self._send_empty(HTTPStatus.ACCEPTED)
        elif response is None:
            self._send_empty(HTTPStatus.ACCEPTED)
        else:
            self._send_json(HTTPStatus.OK, response)


def create_http_server(
    config: RuntimeConfig | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    mcp_path: str = "/mcp",
    allowed_origins: Iterable[str] = (),
    bearer_token: str | None = None,
    contract_path: str | Path | None = None,
) -> MCPHTTPServer:
    """Create, but do not start, the loopback MCP HTTP server."""

    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise validation("Study OS MCP HTTP transport must bind to loopback")
    if not 0 <= port <= 65535:
        raise validation("port must be between 0 and 65535")
    selected_config = config or RuntimeConfig.from_env()
    return MCPHTTPServer(
        (host, port),
        config=selected_config,
        mcp_path=mcp_path,
        allowed_origins=allowed_origins,
        bearer_token=bearer_token,
        contract_path=contract_path,
    )


def serve_http(
    config: RuntimeConfig | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    mcp_path: str = "/mcp",
    allowed_origins: Iterable[str] = (),
    bearer_token: str | None = None,
    contract_path: str | Path | None = None,
) -> None:
    server = create_http_server(
        config,
        host=host,
        port=port,
        mcp_path=mcp_path,
        allowed_origins=allowed_origins,
        bearer_token=bearer_token,
        contract_path=contract_path,
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()
