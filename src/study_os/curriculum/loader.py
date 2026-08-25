"""Load and validate versioned Study OS curriculum slices."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class CurriculumValidationError(ValueError):
    """Raised when curriculum files violate cross-file invariants."""


@dataclass(frozen=True, slots=True)
class CurriculumSlice:
    graph: dict[str, Any]
    item_bank: dict[str, Any]
    competency_by_id: dict[str, dict[str, Any]]
    item_by_id: dict[str, dict[str, Any]]


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CurriculumValidationError(f"{path}: top-level JSON value must be an object")
    return value


def _validate_schema(instance: dict[str, Any], schema: dict[str, Any], source: Path) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        rendered: list[str] = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            rendered.append(f"{source}: {location}: {error.message}")
        raise CurriculumValidationError("\n".join(rendered))


def _index_unique(records: list[dict[str, Any]], *, label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        record_id = record["id"]
        if record_id in indexed:
            raise CurriculumValidationError(f"duplicate {label} id: {record_id}")
        indexed[record_id] = record
    return indexed


def _validate_dag(competency_by_id: dict[str, dict[str, Any]]) -> None:
    for competency_id, competency in competency_by_id.items():
        for prerequisite in competency["prerequisites"]:
            if prerequisite == competency_id:
                raise CurriculumValidationError(f"competency {competency_id} cannot depend on itself")
            if prerequisite not in competency_by_id:
                raise CurriculumValidationError(
                    f"competency {competency_id} references unknown prerequisite {prerequisite}"
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(competency_id: str, trail: tuple[str, ...]) -> None:
        if competency_id in visiting:
            cycle = " -> ".join((*trail, competency_id))
            raise CurriculumValidationError(f"competency prerequisite cycle detected: {cycle}")
        if competency_id in visited:
            return
        visiting.add(competency_id)
        for prerequisite in competency_by_id[competency_id]["prerequisites"]:
            visit(prerequisite, (*trail, competency_id))
        visiting.remove(competency_id)
        visited.add(competency_id)

    for competency_id in competency_by_id:
        visit(competency_id, ())


def validate_curriculum_pair(
    graph: dict[str, Any],
    item_bank: dict[str, Any],
    *,
    graph_source: Path | None = None,
    item_source: Path | None = None,
    schema_root: Path | None = None,
) -> CurriculumSlice:
    """Validate schemas plus graph/item cross references and return indexes."""

    if schema_root is not None:
        graph_schema = _load_json(schema_root / "competency-graph.schema.json")
        item_schema = _load_json(schema_root / "curriculum-item-bank.schema.json")
        _validate_schema(graph, graph_schema, graph_source or Path("<competency-graph>"))
        _validate_schema(item_bank, item_schema, item_source or Path("<item-bank>"))

    for field in ("domain_id", "slice_id"):
        if graph[field] != item_bank[field]:
            raise CurriculumValidationError(
                f"curriculum {field} mismatch: graph={graph[field]!r}, bank={item_bank[field]!r}"
            )
    if graph["graph_version"] != item_bank["graph_version"]:
        raise CurriculumValidationError(
            "item bank graph_version does not match competency graph version"
        )

    competency_by_id = _index_unique(graph["competencies"], label="competency")
    item_by_id = _index_unique(item_bank["items"], label="item")
    _validate_dag(competency_by_id)

    misconception_ids: set[str] = set()
    for competency_id, competency in competency_by_id.items():
        for misconception in competency["misconceptions"]:
            misconception_id = misconception["id"]
            if misconception_id in misconception_ids:
                raise CurriculumValidationError(f"duplicate misconception id: {misconception_id}")
            misconception_ids.add(misconception_id)

    for item_id, item in item_by_id.items():
        primary = item["primary_competency_id"]
        competency_ids = item["competency_ids"]
        if primary not in competency_ids:
            raise CurriculumValidationError(
                f"item {item_id} primary_competency_id must be included in competency_ids"
            )
        unknown = sorted(set(competency_ids) - competency_by_id.keys())
        if unknown:
            raise CurriculumValidationError(
                f"item {item_id} references unknown competencies: {', '.join(unknown)}"
            )
        if item["task_mode"] not in competency_by_id[primary]["task_modes"]:
            raise CurriculumValidationError(
                f"item {item_id} task_mode {item['task_mode']} is not allowed by primary competency {primary}"
            )
        if item["exposure_class"] in {"transfer_public_fixture", "retention_public_fixture"}:
            if item["assistance_ceiling"] != "A0":
                raise CurriculumValidationError(
                    f"item {item_id} public transfer/retention fixture must use A0 assistance ceiling"
                )

    return CurriculumSlice(
        graph=graph,
        item_bank=item_bank,
        competency_by_id=competency_by_id,
        item_by_id=item_by_id,
    )


def load_curriculum_slice(root: Path, relative_dir: str, *, version: str = "0.1") -> CurriculumSlice:
    """Load one versioned curriculum slice from the repository tree."""

    directory = root / relative_dir
    graph_path = directory / f"competencies.v{version}.json"
    item_path = directory / f"items.v{version}.json"
    if not graph_path.is_file() or not item_path.is_file():
        raise CurriculumValidationError(
            f"curriculum slice is incomplete: expected {graph_path} and {item_path}"
        )
    return validate_curriculum_pair(
        _load_json(graph_path),
        _load_json(item_path),
        graph_source=graph_path,
        item_source=item_path,
        schema_root=root / "schemas",
    )
