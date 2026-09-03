"""Contract-backed MCP tool metadata.

This module is intentionally a thin registry: behavior remains in the
semantic service and the versioned JSON contract remains the source of truth.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MCP_CONTRACT_VERSION = "0.3.0"
CONTRACT_PATH = Path(__file__).resolve().parents[3] / "contracts" / "study-os-mcp-tools.v0.3.json"


def load_contract(path: str | Path | None = None) -> dict[str, Any]:
    selected = Path(path) if path else CONTRACT_PATH
    return json.loads(selected.read_text(encoding="utf-8"))


def approved_tool_specs(path: str | Path | None = None) -> list[dict[str, Any]]:
    return list(load_contract(path)["tools"])


def approved_tool_names(path: str | Path | None = None) -> list[str]:
    return [tool["name"] for tool in approved_tool_specs(path)]


TOOL_NAMES = approved_tool_names()
