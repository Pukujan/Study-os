#!/usr/bin/env python3
"""Verify a Study OS MCP HTTP edge without printing its bearer secret."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


PROTOCOL_VERSION = "2026-07-28"
TOKEN_ENV = "STUDY_OS_MCP_BEARER_TOKEN"
EXPECTED_TOOLS = (
    "doctor",
    "status",
    "start_session",
    "record_learning_event",
    "record_attempt",
    "record_assessment",
    "record_representation_intervention",
    "record_representation_outcome",
    "checkpoint",
    "resume",
    "schedule_retention_probe",
    "get_next_probe",
    "export_fossil",
)
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _request(
    url: str,
    *,
    token: str | None = None,
    timeout: float = 10.0,
) -> tuple[int, bytes, dict[str, str]]:
    params: dict[str, Any] = {
        "_meta": {
            "io.modelcontextprotocol/protocolVersion": PROTOCOL_VERSION,
            "io.modelcontextprotocol/clientInfo": {
                "name": "study-os-mcp-endpoint-verifier",
                "version": "1",
            },
            "io.modelcontextprotocol/clientCapabilities": {},
        }
    }
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": params,
        }
    ).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": PROTOCOL_VERSION,
        "Mcp-Method": "tools/list",
    }
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(), dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers.items())


def _probe_route(url: str, *, token: str, timeout: float) -> int:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def _fail(message: str) -> int:
    print(json.dumps({"status": "FAIL", "reason": message}, sort_keys=True))
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the authenticated Study OS MCP endpoint without printing secrets."
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8765/mcp",
        help="MCP URL. Plain HTTP is accepted only for a loopback hostname.",
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    parsed = urllib.parse.urlsplit(args.url)
    if not parsed.netloc or parsed.path != "/mcp":
        return _fail("expected an MCP URL with path /mcp")
    hostname = parsed.hostname or ""
    if parsed.scheme == "http" and hostname not in LOOPBACK_HOSTS:
        return _fail("plain HTTP is allowed only for loopback verification")
    if parsed.scheme not in {"http", "https"}:
        return _fail("expected an HTTP or HTTPS MCP URL")

    token = os.environ.get(TOKEN_ENV)
    if not token:
        return _fail(f"{TOKEN_ENV} is not set")
    if any(character.isspace() for character in token):
        return _fail(f"{TOKEN_ENV} contains whitespace")

    missing_status, missing_body, missing_headers = _request(
        args.url, timeout=args.timeout
    )
    if missing_status != 401:
        return _fail(
            f"missing-token request returned HTTP {missing_status}, expected 401"
        )
    if missing_headers.get("WWW-Authenticate", "").lower() != "bearer":
        return _fail("missing-token response did not advertise Bearer authentication")
    if token.encode() in missing_body:
        return _fail("token appeared in an unauthenticated response body")

    wrong_status, wrong_body, _ = _request(
        args.url,
        token="study-os-deliberately-wrong-token",
        timeout=args.timeout,
    )
    if wrong_status != 401:
        return _fail(f"wrong-token request returned HTTP {wrong_status}, expected 401")
    if token.encode() in wrong_body:
        return _fail("token appeared in a wrong-token response body")

    valid_status, valid_body, _ = _request(
        args.url,
        token=token,
        timeout=args.timeout,
    )
    if valid_status != 200:
        return _fail(
            f"valid-token tools/list returned HTTP {valid_status}, expected 200"
        )
    if token.encode() in valid_body:
        return _fail("token appeared in a valid response body")
    try:
        payload = json.loads(valid_body)
        tool_names = tuple(tool["name"] for tool in payload["result"]["tools"])
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return _fail(
            "tools/list response was not the expected MCP JSON shape: "
            f"{type(exc).__name__}"
        )
    if tool_names != EXPECTED_TOOLS:
        return _fail(f"unexpected MCP tool surface: {tool_names!r}")

    base = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    exposed: dict[str, int] = {}
    for path in ("/healthz", "/readyz", "/openapi.json", "/admin", "/sql"):
        status = _probe_route(base + path, token=token, timeout=args.timeout)
        if status != 404:
            exposed[path] = status
    if exposed:
        return _fail(f"unexpected non-MCP routes: {exposed}")

    receipt = {
        "status": "PASS",
        "endpoint": f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
        "protocol_version": PROTOCOL_VERSION,
        "missing_token_http": missing_status,
        "wrong_token_http": wrong_status,
        "valid_token_http": valid_status,
        "tools": list(tool_names),
        "non_mcp_routes": "blocked",
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
