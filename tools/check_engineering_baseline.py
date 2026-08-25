#!/usr/bin/env python3
"""Check Study OS engineering-baseline invariants.

These checks are intentionally lightweight and deterministic so they can run on
all pull requests. They protect version coherence, the approved semantic tool
surface, and modular-monolith dependency direction without changing runtime
behavior.
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
STUDY_OS_ROOT = ROOT / "src" / "study_os"

PURE_LOGIC_ROOTS = (
    STUDY_OS_ROOT / "adaptive",
    STUDY_OS_ROOT / "curriculum",
)
FORBIDDEN_PURE_LOGIC_PREFIXES = (
    "study_os.db",
    "study_os.evidence",
    "study_os.mcp",
    "study_os.services",
)

TRANSPORT_ROOTS = (STUDY_OS_ROOT / "mcp",)
FORBIDDEN_TRANSPORT_PREFIXES = (
    "study_os.adaptive",
    "study_os.curriculum",
    "study_os.db",
    "study_os.evidence",
)

TOP_LEVEL_PACKAGES = (
    "adaptive",
    "curriculum",
    "db",
    "evidence",
    "mcp",
    "services",
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
    """Return syntactic import modules without resolving relative imports."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _package_parts(path: Path) -> list[str]:
    parts = list(path.parent.parts)
    indexes = [index for index, part in enumerate(parts) if part == "study_os"]
    if not indexes:
        return []
    return parts[indexes[-1] :]


def _resolved_imported_modules(path: Path) -> set[str]:
    """Resolve absolute and Study OS relative imports into canonical module names."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    package_parts = _package_parts(path)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level == 0:
            if node.module:
                modules.add(node.module)
            continue
        if not package_parts:
            if node.module:
                modules.add(node.module)
            continue
        parent_hops = node.level - 1
        if parent_hops >= len(package_parts):
            continue
        resolved_parts = package_parts[: len(package_parts) - parent_hops]
        if node.module:
            resolved_parts.extend(node.module.split("."))
        if resolved_parts:
            modules.add(".".join(resolved_parts))
    return modules


def _matches_prefix(module: str, prefixes: tuple[str, ...]) -> bool:
    return any(module == prefix or module.startswith(prefix + ".") for prefix in prefixes)


def check_pure_logic_boundaries() -> None:
    violations: list[str] = []
    for root in PURE_LOGIC_ROOTS:
        for path in sorted(root.rglob("*.py")):
            for module in sorted(_resolved_imported_modules(path)):
                if _matches_prefix(module, FORBIDDEN_PURE_LOGIC_PREFIXES):
                    violations.append(f"{path.relative_to(ROOT)} -> {module}")
    if violations:
        raise BaselineFailure(
            "adaptive/curriculum pure logic crossed persistence/transport boundary: "
            + "; ".join(violations)
        )


def check_transport_boundaries() -> None:
    """Keep MCP as a transport adapter rather than a semantic/persistence owner."""

    violations: list[str] = []
    for root in TRANSPORT_ROOTS:
        for path in sorted(root.rglob("*.py")):
            for module in sorted(_resolved_imported_modules(path)):
                if _matches_prefix(module, FORBIDDEN_TRANSPORT_PREFIXES):
                    violations.append(f"{path.relative_to(ROOT)} -> {module}")
    if violations:
        raise BaselineFailure(
            "MCP transport reached persistence/pure semantic implementation directly: "
            + "; ".join(violations)
        )


def _top_level_dependency(module: str) -> str | None:
    parts = module.split(".")
    if len(parts) < 2 or parts[0] != "study_os":
        return None
    candidate = parts[1]
    return candidate if candidate in TOP_LEVEL_PACKAGES else None


def _top_level_dependency_graph() -> dict[str, set[str]]:
    graph = {package: set() for package in TOP_LEVEL_PACKAGES}
    for package in TOP_LEVEL_PACKAGES:
        root = STUDY_OS_ROOT / package
        for path in sorted(root.rglob("*.py")):
            for module in _resolved_imported_modules(path):
                dependency = _top_level_dependency(module)
                if dependency is not None and dependency != package:
                    graph[package].add(dependency)
    return graph


def _find_dependency_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    """Return one deterministic dependency cycle, including the repeated start node."""

    visited: set[str] = set()
    active: set[str] = set()
    path: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in active:
            start = path.index(node)
            return path[start:] + [node]
        if node in visited:
            return None
        active.add(node)
        path.append(node)
        for dependency in sorted(graph.get(node, set())):
            cycle = visit(dependency)
            if cycle is not None:
                return cycle
        path.pop()
        active.remove(node)
        visited.add(node)
        return None

    for node in sorted(graph):
        cycle = visit(node)
        if cycle is not None:
            return cycle
    return None


def check_top_level_dependency_cycles() -> None:
    cycle = _find_dependency_cycle(_top_level_dependency_graph())
    if cycle is not None:
        raise BaselineFailure("Study OS top-level package dependency cycle: " + " -> ".join(cycle))


def main() -> int:
    checks = (
        ("version and 13-tool consistency", check_version_consistency),
        ("adaptive/curriculum architecture boundary", check_pure_logic_boundaries),
        ("MCP transport architecture boundary", check_transport_boundaries),
        ("top-level package dependency cycles", check_top_level_dependency_cycles),
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
