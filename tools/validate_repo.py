#!/usr/bin/env python3
"""Validate Study OS repository invariants.

The validator intentionally checks both software structure and research/data
integrity. It is lightweight enough to run locally and in CI.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"

REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "PROJECT_MANIFEST.yaml",
    "docs/PROJECT_BOUNDARY.md",
    "docs/RESEARCH_FOUNDATIONS.md",
    "docs/FAILURE_MODES.md",
    "docs/RESEARCH_PLAN.md",
    "docs/FOSSIL_INTEGRATION.md",
    "docs/HANDOFF.md",
    "docs/DECISIONS.md",
    "plugins/study-os-ingest/skill.md",
    "schemas/session-manifest.schema.json",
    "schemas/learning-event.schema.json",
    "schemas/learning-episode.schema.json",
    "schemas/representation.schema.json",
    "schemas/lesson-ir.schema.json",
]

SCHEMA_FILES = {
    "session": "session-manifest.schema.json",
    "event": "learning-event.schema.json",
    "episode": "learning-episode.schema.json",
}


class ValidationFailure(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / name
    schema = load_json(path)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_instance(instance: Any, schema: dict[str, Any], source: Path) -> None:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        rendered = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            rendered.append(f"{source}: {location}: {error.message}")
        raise ValidationFailure("\n".join(rendered))


def check_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise ValidationFailure(f"Missing required project files: {', '.join(missing)}")


def check_manifest() -> None:
    manifest_path = ROOT / "PROJECT_MANIFEST.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    required = ["manifest_version", "project", "research", "privacy", "fossil", "engineering"]
    missing = [key for key in required if key not in manifest]
    if missing:
        raise ValidationFailure(f"PROJECT_MANIFEST.yaml missing keys: {', '.join(missing)}")

    project = manifest["project"]
    if project.get("current_gate") not in {"R0", "R1", "R2"}:
        raise ValidationFailure("project.current_gate must be R0, R1, or R2")

    privacy = manifest["privacy"]
    if privacy.get("repository_visibility") == "public" and privacy.get("raw_transcript_policy") != "local_or_private_by_default":
        raise ValidationFailure("Public repo must retain local/private raw transcript policy")

    fossil = manifest["fossil"]
    if fossil.get("canonical_source_of_learning_events") != "study_os":
        raise ValidationFailure("Study OS must remain canonical source of learning events")
    if fossil.get("runtime_dependency") is not False:
        raise ValidationFailure("FOSSIL must remain optional during the current research phase")

    prohibited = set(manifest["research"].get("prohibited_claims", []))
    expected = {
        "fixed_learning_styles",
        "subject_001_generalizes_to_population",
        "self_report_equals_mastery",
    }
    if not expected.issubset(prohibited):
        raise ValidationFailure("Manifest lost required prohibited research claims")


def tracked_files() -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def check_public_data_boundary() -> None:
    violations = []
    for path in tracked_files():
        normalized = path.replace("\\", "/")
        if "/raw/" in normalized and normalized.startswith("sessions/"):
            if not normalized.endswith("/raw/.gitkeep"):
                violations.append(normalized)
        if normalized.startswith(".study-os-private/"):
            violations.append(normalized)
    if violations:
        raise ValidationFailure(
            "Private/raw evidence appears tracked in public repo: " + ", ".join(violations)
        )


def validate_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for key, filename in SCHEMA_FILES.items():
        schemas[key] = load_schema(filename)
    # Validate all schema files, not only schemas currently used for session walking.
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        Draft202012Validator.check_schema(load_json(path))
    return schemas


def validate_session_tree(schemas: dict[str, dict[str, Any]]) -> None:
    sessions_root = ROOT / "sessions"
    if not sessions_root.exists():
        return

    for manifest_path in sessions_root.glob("*/*/manifest.json"):
        validate_instance(load_json(manifest_path), schemas["session"], manifest_path)

    for events_path in sessions_root.glob("*/*/events/*.jsonl"):
        for line_number, line in enumerate(events_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValidationFailure(f"{events_path}:{line_number}: invalid JSON: {exc}") from exc
            validate_instance(event, schemas["event"], Path(f"{events_path}:{line_number}"))

    for episode_path in sessions_root.glob("*/*/episodes/*.json"):
        validate_instance(load_json(episode_path), schemas["episode"], episode_path)


def main() -> int:
    checks = [
        ("required files", check_required_files),
        ("project manifest", check_manifest),
        ("public data boundary", check_public_data_boundary),
    ]

    try:
        for label, check in checks:
            check()
            print(f"PASS {label}")
        schemas = validate_schemas()
        print("PASS JSON schemas")
        validate_session_tree(schemas)
        print("PASS session data")
    except (ValidationFailure, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    print("Study OS repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
