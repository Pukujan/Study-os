"""Small dependency-free MCP stdio boundary for the semantic service."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from ..errors import StudyOSError, validation
from ..services.runtime import StudyOSService
from .tools import CONTRACT_PATH, load_contract


class MCPServer:
    def __init__(self, service: StudyOSService | None = None, contract_path: str | Path | None = None) -> None:
        self.service = service or StudyOSService()
        path = Path(contract_path) if contract_path else CONTRACT_PATH
        self.contract = load_contract(path)
        self.tool_specs = {tool["name"]: tool for tool in self.contract["tools"]}

    def list_tool_names(self) -> list[str]:
        return [tool["name"] for tool in self.contract["tools"]]

    def list_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for spec in self.contract["tools"]:
            required = list(spec["required_input"])
            properties = {name: {} for name in required}
            tools.append(
                {
                    "name": spec["name"],
                    "description": f"Study OS semantic operation: {spec['name']}",
                    "inputSchema": {"type": "object", "properties": properties, "required": required, "additionalProperties": True},
                }
            )
        return tools

    def _validate_arguments(self, name: str, arguments: dict[str, Any]) -> None:
        if not isinstance(arguments, dict):
            raise validation("Tool arguments must be an object")
        spec = self.tool_specs.get(name)
        if spec is None:
            raise validation("Unknown MCP tool", tool=name)
        missing = [field for field in spec["required_input"] if field not in arguments]
        if missing:
            raise validation("Required MCP tool arguments are missing", tool=name, missing=missing)

    def _dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        method = getattr(self.service, name, None)
        if method is None or not callable(method):
            raise StudyOSError("internal_error", f"No service implementation for MCP tool: {name}", False)
        result = method(**arguments)
        spec = self.tool_specs[name]
        missing = [field for field in spec["required_output"] if field not in result]
        if missing:
            raise StudyOSError("internal_error", "Service response does not satisfy MCP output contract", False, {"tool": name, "missing": missing})
        return result

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            args = arguments or {}
            self._validate_arguments(name, args)
            return self._dispatch(name, args)
        except StudyOSError as exc:
            return exc.as_dict()
        except (TypeError, ValueError, KeyError) as exc:
            return StudyOSError("validation_error", str(exc), False).as_dict()
        except Exception as exc:  # MCP must never expose a successful-looking response after an unexpected failure.
            return StudyOSError("internal_error", "Unexpected Study OS service failure", False, {"exception": type(exc).__name__}).as_dict()

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        request_id = message.get("id")
        method = message.get("method")
        params = message.get("params") or {}
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "study-os", "version": "0.1.0"},
            }
        elif method == "notifications/initialized":
            return None
        elif method == "tools/list":
            result = {"tools": self.list_tools()}
        elif method == "tools/call":
            if not isinstance(params, dict) or not isinstance(params.get("name"), str):
                error = validation("tools/call requires a tool name")
                return {"jsonrpc": "2.0", "id": request_id, "error": error.as_dict()["error"]}
            result = {"content": [{"type": "text", "text": json.dumps(self.call_tool(params["name"], params.get("arguments") or {}), sort_keys=True)}]}
        else:
            error = validation("Unsupported MCP method", method=method)
            return {"jsonrpc": "2.0", "id": request_id, "error": error.as_dict()["error"]}
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def run_stdio(self, input_stream: TextIO = sys.stdin, output_stream: TextIO = sys.stdout) -> None:
        for line in input_stream:
            if not line.strip():
                continue
            try:
                response = self.handle_message(json.loads(line))
                if response is not None:
                    output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
                    output_stream.flush()
            except Exception as exc:
                error = StudyOSError("internal_error", "Invalid MCP message", False, {"exception": type(exc).__name__})
                output_stream.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": error.as_dict()["error"]}) + "\n")
                output_stream.flush()
