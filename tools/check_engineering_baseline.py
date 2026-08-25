#!/usr/bin/env python3
"""Check Study OS engineering-baseline invariants.

These checks are intentionally lightweight and deterministic so they can run on
all pull requests. They protect version coherence, the approved semantic tool
surface, and the first modular-monolith dependency boundary without changing
runtime behavior.
"""

from __future__ import annotations

import ast
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

PURE_LOGIC_ROOTS = (
    ROOT / "src" / "study_os" / "adaptive",
    ROOT / "src" / "study_os" / "curriculum",
)
FORBIDDEN_PURE_LOGIC_PREFIXES = (
    "study_os.db",
    "study_os.evidence",
    "study_os.mcp",
    "study_os.services",
)


class BaselineFailure(RuntimeError):
    pass


def _load_manifest() -> dict[str, Any]:
    return yaml.safe_load((ROOT / "PROJECT_MANIFEST.yaml").read_text(encoding="utf-8"))


def check_version_consistency() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    manifest = _load_manifest()
    contract_path = ROOT / manifest["canonical_paths"]["mcp_contract"]
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    package_version = pyproject["project"]["version"]
    manifest_package_version = manifest["runtime"]["package_version"]
    if package_version != manifest_package_version:
        raise BaselineFailure(
            f"runtime package version drift: pyproject={package_version!r}, "
            f"manifest={manifest_package_version!r}"
        )

    contract_version = contract.get("contract_version")
    manifest_contract_version = manifest["runtime"]["app_surface"]["semantic_contract_version"]
    if contract_version != manifest_contract_version:
        raise BaselineFailure(
            f"MCP contract version drift: contract={contract_version!r}, "
            f"manifest={manifest_contract_version!r}"
        )

    tools = contract.get("tools")
    approved_tool_count = manifest["runtime"]["app_surface"]["approved_tool_count"]
    if not isinstance(tools, list) or len(tools) != approved_tool_count:
        actual = len(tools) if isinstance(tools, list) else None
        raise BaselineFailure(
            f"approved MCP tool-count drift: contract={actual!r}, manifest={approved_tool_count!r}"
        )
    if approved_tool_count != 13:
        raise BaselineFailure("approved MCP semantic boundary must remain exactly 13 tools")


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def check_pure_logic_boundaries() -> None:
    violations: list[str] = []
    for root in PURE_LOGIC_ROOTS:
        for path in sorted(root.rglob("*.py")):
            for module in sorted(_imported_modules(path)):
                if any(
                    module == prefix or module.startswith(prefix + ".")
                    for prefix in FORBIDDEN_PURE_LOGIC_PREFIXES
                ):
                    violations.append(f"{path.relative_to(ROOT)} -> {module}")
    if violations:
        raise BaselineFailure(
            "adaptive/curriculum pure logic crossed persistence/transport boundary: "
            + "; ".join(violations)
        )


def main() -> int:
    checks = (
        ("version and 13-tool consistency", check_version_consistency),
        ("adaptive/curriculum architecture boundary", check_pure_logic_boundaries),
    )
    try:
        for label, check in checks:
            check()
            print(f"PASS {label}")
    except (BaselineFailure, KeyError, TypeError, ValueError, SyntaxError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("Study OS engineering baseline checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
