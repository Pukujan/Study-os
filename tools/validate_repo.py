#!/usr/bin/env python3
"""Validate Study OS repository invariants.

The validator intentionally checks both software structure and research/data
integrity. It is lightweight enough to run locally and in CI.
"""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
METHODOLOGY_DATASET_PATH = ROOT / "datasets" / "learner-methodology" / "2026-08-29-study-os-methodology-capture.json"
FOSSIL_RESEARCH_EXPORT_PATH = ROOT / "fossil" / "exports" / "research" / "2026-08-29-study-os-methodology.json"

REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "PROJECT_MANIFEST.yaml",
    "docs/PROJECT_BOUNDARY.md",
    "docs/RESEARCH_FOUNDATIONS.md",
    "docs/FAILURE_MODES.md",
    "docs/RESEARCH_PLAN.md",
    "docs/CHECKPOINTING.md",
    "docs/FOSSIL_INTEGRATION.md",
    "docs/HANDOFF.md",
    "docs/DECISIONS.md",
    "docs/VALIDATION_STRATEGY.md",
    "docs/LUNA_LOCAL_HANDOFF.md",
    "docs/DATABASE_CONTRACT.md",
    "docs/ERROR_IDEMPOTENCY_CONTRACT.md",
    "contracts/study-os-mcp-tools.v0.1.json",
    "src/study_os/services/runtime.py",
    "src/study_os/mcp/server.py",
    "src/study_os/db/migrations/0001_initial.sql",
    "plugins/study-os-ingest/skill.md",
    "plugins/study-os-checkpoint/skill.md",
    "schemas/session-manifest.schema.json",
    "schemas/learning-event.schema.json",
    "schemas/learning-episode.schema.json",
    "schemas/representation.schema.json",
    "schemas/lesson-ir.schema.json",
    "schemas/learner-checkpoint.schema.json",
    "schemas/current-checkpoint.schema.json",
    "subjects/subject-001/CURRENT.json",
]

SCHEMA_FILES = {
    "session": "session-manifest.schema.json",
    "event": "learning-event.schema.json",
    "episode": "learning-episode.schema.json",
    "checkpoint": "learner-checkpoint.schema.json",
    "current_checkpoint": "current-checkpoint.schema.json",
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
    if fossil.get("canonical_source_of_learner_checkpoints") != "study_os":
        raise ValidationFailure("Study OS must remain canonical source of learner checkpoints")
    if fossil.get("runtime_dependency") is not False:
        raise ValidationFailure("FOSSIL must remain optional during the current research phase")
    if fossil.get("resume_dependency") is not False:
        raise ValidationFailure("Cross-session resume must not depend on FOSSIL")

    prohibited = set(manifest["research"].get("prohibited_claims", []))
    expected = {
        "fixed_learning_styles",
        "subject_001_generalizes_to_population",
        "self_report_equals_mastery",
    }
    if not expected.issubset(prohibited):
        raise ValidationFailure("Manifest lost required prohibited research claims")


def check_mcp_contract() -> None:
    contract_path = ROOT / "contracts" / "study-os-mcp-tools.v0.1.json"
    contract = load_json(contract_path)
    if contract.get("contract_version") != "0.1.0":
        raise ValidationFailure("MCP contract version must remain 0.1.0 for this runtime")
    principles = contract.get("principles", {})
    for key in (
        "semantic_tools_only",
        "generic_sql_allowed",
        "generic_shell_allowed",
        "generic_file_write_allowed",
        "arbitrary_code_execution_allowed",
        "github_runtime_dependency",
        "fossil_runtime_dependency",
    ):
        if key not in principles:
            raise ValidationFailure(f"MCP contract missing principle: {key}")
    if not principles["semantic_tools_only"]:
        raise ValidationFailure("MCP surface must remain semantic-tools-only")
    if any(principles[key] for key in ("generic_sql_allowed", "generic_shell_allowed", "generic_file_write_allowed", "arbitrary_code_execution_allowed", "github_runtime_dependency", "fossil_runtime_dependency")):
        raise ValidationFailure("MCP contract permits a prohibited generic/runtime dependency")
    tools = contract.get("tools")
    if not isinstance(tools, list) or not tools:
        raise ValidationFailure("MCP contract must declare tools")
    names = [tool.get("name") for tool in tools]
    if any(not isinstance(name, str) or not name for name in names) or len(names) != len(set(names)):
        raise ValidationFailure("MCP tool names must be unique non-empty strings")
    forbidden_fragments = ("sql", "shell", "terminal", "exec", "execute_code", "run_code", "write_file", "filesystem")
    if any(any(fragment in name.lower() for fragment in forbidden_fragments) for name in names):
        raise ValidationFailure("MCP contract exposes a prohibited generic machine tool")
    for tool in tools:
        for field in ("mutating", "idempotency_required", "required_input", "required_output"):
            if field not in tool:
                raise ValidationFailure(f"MCP tool {tool.get('name')} is missing {field}")
        if tool["mutating"] and (not tool["idempotency_required"] or "idempotency_key" not in tool["required_input"]):
            raise ValidationFailure(f"Mutating MCP tool {tool['name']} must require idempotency_key")


def check_runtime_layout() -> None:
    required = [
        ROOT / "src" / "study_os" / "config.py",
        ROOT / "src" / "study_os" / "errors.py",
        ROOT / "src" / "study_os" / "db" / "connection.py",
        ROOT / "src" / "study_os" / "db" / "repositories" / "sqlite.py",
        ROOT / "src" / "study_os" / "evidence" / "store.py",
        ROOT / "src" / "study_os" / "services" / "runtime.py",
        ROOT / "src" / "study_os" / "mcp" / "server.py",
        ROOT / "cli" / "study_os.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise ValidationFailure("Local runtime layout is incomplete: " + ", ".join(missing))


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


def check_curated_public_data() -> None:
    dataset_schema = load_schema("learner-methodology-capture.schema.json")
    export_schema = load_schema("fossil-research-export.schema.json")

    if not METHODOLOGY_DATASET_PATH.is_file():
        raise ValidationFailure(f"Missing curated methodology dataset: {METHODOLOGY_DATASET_PATH}")
    if not FOSSIL_RESEARCH_EXPORT_PATH.is_file():
        raise ValidationFailure(f"Missing FOSSIL research export: {FOSSIL_RESEARCH_EXPORT_PATH}")

    dataset = load_json(METHODOLOGY_DATASET_PATH)
    export = load_json(FOSSIL_RESEARCH_EXPORT_PATH)
    validate_instance(dataset, dataset_schema, METHODOLOGY_DATASET_PATH)
    validate_instance(export, export_schema, FOSSIL_RESEARCH_EXPORT_PATH)

    expected_dataset_path = METHODOLOGY_DATASET_PATH.relative_to(ROOT).as_posix()
    if export["dataset_path"] != expected_dataset_path:
        raise ValidationFailure("FOSSIL research export points to an unexpected dataset path")

    dataset_hash = hashlib.sha256(METHODOLOGY_DATASET_PATH.read_bytes()).hexdigest()
    if export["dataset_sha256"] != dataset_hash:
        raise ValidationFailure("FOSSIL research export dataset_sha256 does not match the dataset")

    expected_counts = {
        "self_reported": len(dataset["self_reported"]),
        "observed": len(dataset["observed"]),
        "derived": len(dataset["derived"]),
        "instrumentation_proposals": len(dataset["instrumentation_proposals"]),
    }
    if export.get("record_counts") != expected_counts:
        raise ValidationFailure("FOSSIL research export record_counts do not match the dataset")


def validate_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for key, filename in SCHEMA_FILES.items():
        schemas[key] = load_schema(filename)
    # Validate all schema files, not only schemas currently used for data walking.
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


def validate_subject_checkpoints(schemas: dict[str, dict[str, Any]]) -> None:
    subjects_root = ROOT / "subjects"
    if not subjects_root.exists():
        return

    for subject_dir in subjects_root.iterdir():
        if not subject_dir.is_dir():
            continue

        current_path = subject_dir / "CURRENT.json"
        if current_path.exists():
            current = load_json(current_path)
            validate_instance(current, schemas["current_checkpoint"], current_path)

            checkpoint_path = current.get("checkpoint_path")
            checkpoint_id = current.get("checkpoint_id")
            status = current.get("status")

            if status == "not_started":
                if checkpoint_path is not None or checkpoint_id is not None:
                    raise ValidationFailure(
                        f"{current_path}: not_started pointer must not reference a checkpoint"
                    )
            elif checkpoint_path is None or checkpoint_id is None:
                raise ValidationFailure(
                    f"{current_path}: active/paused/retention/completed state requires checkpoint reference"
                )
            else:
                resolved = ROOT / checkpoint_path
                if not resolved.is_file():
                    raise ValidationFailure(f"{current_path}: checkpoint does not exist: {checkpoint_path}")
                checkpoint = load_json(resolved)
                validate_instance(checkpoint, schemas["checkpoint"], resolved)
                if checkpoint.get("checkpoint_id") != checkpoint_id:
                    raise ValidationFailure(
                        f"{current_path}: checkpoint_id does not match referenced checkpoint"
                    )
                if checkpoint.get("subject_id") != current.get("subject_id"):
                    raise ValidationFailure(
                        f"{current_path}: subject_id does not match referenced checkpoint"
                    )

        checkpoints_dir = subject_dir / "checkpoints"
        if checkpoints_dir.exists():
            for checkpoint_file in checkpoints_dir.glob("*.json"):
                validate_instance(load_json(checkpoint_file), schemas["checkpoint"], checkpoint_file)


def main() -> int:
    checks = [
        ("required files", check_required_files),
        ("project manifest", check_manifest),
        ("MCP semantic contract", check_mcp_contract),
        ("local runtime layout", check_runtime_layout),
        ("public data boundary", check_public_data_boundary),
        ("curated public data", check_curated_public_data),
    ]

    try:
        for label, check in checks:
            check()
            print(f"PASS {label}")
        schemas = validate_schemas()
        print("PASS JSON schemas")
        validate_session_tree(schemas)
        print("PASS session data")
        validate_subject_checkpoints(schemas)
        print("PASS learner checkpoints")
    except (ValidationFailure, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    print("Study OS repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
