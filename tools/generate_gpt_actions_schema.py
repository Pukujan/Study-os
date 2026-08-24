#!/usr/bin/env python3
"""Generate an OpenAPI schema for the Plus-compatible GPT Actions wrapper.

The schema is derived from the versioned MCP semantic contract so the GPT
Action surface cannot silently drift from the approved Study OS tools.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "study-os-mcp-tools.v0.1.json"


JSON_OBJECT_INPUT_FIELDS = {"payload", "response", "capability_state", "assistance_state", "resume"}


def _input_field_schema(name: str) -> dict[str, Any]:
    if name in JSON_OBJECT_INPUT_FIELDS:
        # GPT Actions currently drops free-form object inputs from the
        # generated callable interface. Keep the required field visible by
        # carrying the object as JSON text; the local adapter decodes it
        # before dispatching to the unchanged MCP service.
        return {
            "type": "string",
            "description": "JSON-encoded object; the adapter decodes this into the native Study OS object.",
        }
    if name in {"evidence_ids", "source_session_ids", "source_ids"}:
        return {"type": "array", "items": {"type": "string"}}
    if name == "evidence_score":
        return {"type": "number"}
    return {"type": "string"}


def _output_field_schema(name: str) -> dict[str, Any]:
    if name in JSON_OBJECT_INPUT_FIELDS:
        return {"type": "object"}
    if name in {"evidence_ids", "source_session_ids", "source_ids"}:
        return {"type": "array", "items": {"type": "string"}}
    if name == "evidence_score":
        return {"type": "number"}
    return {"type": "string"}


def _operation(name: str, required_input: list[str], required_output: list[str]) -> dict[str, Any]:
    request_schema: dict[str, Any] = {
        "type": "object",
        "properties": {field: _input_field_schema(field) for field in required_input},
        "additionalProperties": True,
    }
    if required_input:
        request_schema["required"] = required_input
    response_schema: dict[str, Any] = {
        "type": "object",
        "properties": {field: _output_field_schema(field) for field in required_output},
        "required": required_output,
        "additionalProperties": True,
    }
    return {
        "post": {
            "operationId": f"study_os_{name}",
            "summary": f"Study OS semantic operation: {name}",
            "security": [{"StudyOSBearer": []}],
            "requestBody": {
                "required": bool(required_input),
                "content": {"application/json": {"schema": request_schema}},
            },
            "responses": {
                "200": {
                    "description": "Study OS semantic result",
                    "content": {"application/json": {"schema": response_schema}},
                }
            },
        }
    }


def build_schema(server_url: str) -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Study OS GPT Actions",
            "version": contract["contract_version"],
            "description": "Authenticated semantic learning-session operations backed by the local Study OS runtime.",
        },
        "servers": [{"url": server_url.rstrip("/")}],
        "security": [{"StudyOSBearer": []}],
        "paths": {
            f"/actions/{tool['name']}": _operation(tool["name"], tool["required_input"], tool["required_output"])
            for tool in contract["tools"]
        },
        "components": {
            "schemas": {},
            "securitySchemes": {
                "StudyOSBearer": {"type": "http", "scheme": "bearer", "description": "Bearer token configured on the private Study OS tunnel endpoint."}
            }
        },
        "x-study-os-mcp-contract-version": contract["contract_version"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-url", required=True, help="HTTPS tunnel base URL, without /actions")
    args = parser.parse_args()
    print(json.dumps(build_schema(args.server_url), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
