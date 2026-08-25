#!/usr/bin/env python3
"""Validate that Study OS CI installs an exact dependency lock without direct-dependency drift."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_PATH = ROOT / "requirements-dev.txt"
LOCK_PATH = ROOT / "requirements-dev.lock"
PYPROJECT_PATH = ROOT / "pyproject.toml"

_NAME_RE = re.compile(r"^([A-Za-z0-9_.-]+)")
_EXACT_RE = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s;]+)$")


class DependencyLockFailure(RuntimeError):
    pass


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(requirement: str) -> str:
    match = _NAME_RE.match(requirement.strip())
    if match is None:
        raise DependencyLockFailure(f"cannot parse requirement: {requirement!r}")
    return normalize_name(match.group(1))


def parse_lock(text: str) -> dict[str, str]:
    locked: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _EXACT_RE.fullmatch(line)
        if match is None:
            raise DependencyLockFailure(f"lock entry must use an exact == version: {line!r}")
        name = normalize_name(match.group(1))
        if name in locked:
            raise DependencyLockFailure(f"duplicate lock entry: {name}")
        locked[name] = match.group(2)
    if not locked:
        raise DependencyLockFailure("dependency lock is empty")
    return locked


def direct_requirement_names(requirements_text: str, pyproject_text: str) -> set[str]:
    direct: set[str] = set()
    for raw_line in requirements_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        direct.add(requirement_name(line))

    pyproject = tomllib.loads(pyproject_text)
    for requirement in pyproject.get("project", {}).get("dependencies", []):
        if not isinstance(requirement, str):
            raise DependencyLockFailure("pyproject project.dependencies must contain strings")
        direct.add(requirement_name(requirement))
    return direct


def check_dependency_lock(
    requirements_path: Path = REQUIREMENTS_PATH,
    lock_path: Path = LOCK_PATH,
    pyproject_path: Path = PYPROJECT_PATH,
) -> None:
    locked = parse_lock(lock_path.read_text(encoding="utf-8"))
    direct = direct_requirement_names(
        requirements_path.read_text(encoding="utf-8"),
        pyproject_path.read_text(encoding="utf-8"),
    )
    missing = sorted(direct - locked.keys())
    if missing:
        raise DependencyLockFailure(
            "direct runtime/dev dependencies missing from exact lock: " + ", ".join(missing)
        )


def main() -> int:
    try:
        check_dependency_lock()
    except (DependencyLockFailure, OSError, tomllib.TOMLDecodeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("Study OS dependency lock checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
