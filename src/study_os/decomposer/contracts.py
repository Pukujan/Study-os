"""Decomposition v2 contracts: dataclasses, dict serde, validation, loader.

The frozen output contract is ``schemas/decomposition.v2.schema.json``.  JSON
Schema catches shape violations; cross-field rules (topological validity of
``learning_order``, concept coverage, step indexing) live here because JSON
Schema cannot express them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas" / "decomposition.v2.schema.json"
SCHEMA_VERSION = "study-os.decomposition.v2"
MODULE_VERSION = "decomposer-v2.1"
FROZEN_CREATED_AT = "2026-09-25T00:00:00+00:00"

_SCHEMA_CACHE: dict[str, dict[str, Any]] = {}


class DecompositionError(ValueError):
    """Raised when a problem cannot be decomposed or an artifact is invalid."""


def load_schema() -> dict[str, Any]:
    """Load the frozen decomposition.v2 JSON Schema from the repo tree."""

    cache_key = str(SCHEMA_PATH)
    if cache_key not in _SCHEMA_CACHE:
        _SCHEMA_CACHE[cache_key] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return _SCHEMA_CACHE[cache_key]


@dataclass
class ProblemSpec:
    """Input to the decomposer: a problem id, statement, and optional concepts."""

    problem_id: str
    statement: str
    declared_concepts: list[str] | None = None


@dataclass
class Strategy:
    summary: str
    approach: str
    invariants: list[str] = field(default_factory=list)


@dataclass
class ConceptNode:
    concept_id: str
    label: str
    kc: str | None = None


@dataclass
class ConceptEdge:
    source: str  # prerequisite
    target: str  # dependent
    kind: str = "prerequisite"


@dataclass
class Visual:
    format: str
    artifact: str
    caption: str | None = None


@dataclass
class Presentation:
    question: str
    example: str
    visual: Visual
    tutor_prompt: str | None = None
    expected_answer_patterns: list[str] = field(default_factory=list)


@dataclass
class Step:
    step_id: str
    step_index: int
    concept_id: str
    goal: str
    presentation: Presentation


@dataclass
class Provenance:
    module_version: str
    generator: str
    route: str | None
    created_at: str
    model: str | None = None
    prompt_sha256: str | None = None
    problem_sha256: str | None = None


@dataclass
class Decomposition:
    problem_id: str
    problem_statement_scrubbed: str
    revision: str
    strategy: Strategy
    nodes: list[ConceptNode]
    edges: list[ConceptEdge]
    learning_order: list[str]
    steps: list[Step]
    provenance: Provenance

    @property
    def concepts(self) -> list[str]:
        return [n.concept_id for n in self.nodes]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "problem_id": self.problem_id,
            "problem_statement_scrubbed": self.problem_statement_scrubbed,
            "revision": self.revision,
            "strategy": {
                "summary": self.strategy.summary,
                "approach": self.strategy.approach,
                "invariants": list(self.strategy.invariants),
            },
            "concept_dag": {
                "nodes": [
                    {"concept_id": n.concept_id, "label": n.label, "kc": n.kc}
                    for n in self.nodes
                ],
                "edges": [
                    {"from": e.source, "to": e.target, "kind": e.kind} for e in self.edges
                ],
            },
            "learning_order": list(self.learning_order),
            "steps": [
                {
                    "step_id": s.step_id,
                    "step_index": s.step_index,
                    "concept_id": s.concept_id,
                    "goal": s.goal,
                    "presentation": {
                        "question": {"md": s.presentation.question},
                        "example": {"md": s.presentation.example},
                        "visual": {
                            "format": s.presentation.visual.format,
                            "artifact": s.presentation.visual.artifact,
                            "caption": s.presentation.visual.caption,
                        },
                        "tutor_prompt": s.presentation.tutor_prompt,
                        "expected_answer_patterns": list(
                            s.presentation.expected_answer_patterns
                        ),
                    },
                }
                for s in self.steps
            ],
            "provenance": {
                "module_version": self.provenance.module_version,
                "generator": self.provenance.generator,
                "route": self.provenance.route,
                "model": self.provenance.model,
                "prompt_sha256": self.provenance.prompt_sha256,
                "problem_sha256": self.provenance.problem_sha256,
                "created_at": self.provenance.created_at,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Decomposition":
        return cls(
            problem_id=data["problem_id"],
            problem_statement_scrubbed=data["problem_statement_scrubbed"],
            revision=data["revision"],
            strategy=Strategy(
                summary=data["strategy"]["summary"],
                approach=data["strategy"]["approach"],
                invariants=list(data["strategy"].get("invariants", [])),
            ),
            nodes=[
                ConceptNode(concept_id=n["concept_id"], label=n["label"], kc=n.get("kc"))
                for n in data["concept_dag"]["nodes"]
            ],
            edges=[
                ConceptEdge(
                    source=e["from"], target=e["to"], kind=e.get("kind", "prerequisite")
                )
                for e in data["concept_dag"]["edges"]
            ],
            learning_order=list(data["learning_order"]),
            steps=[
                Step(
                    step_id=s["step_id"],
                    step_index=int(s["step_index"]),
                    concept_id=s["concept_id"],
                    goal=s["goal"],
                    presentation=Presentation(
                        question=s["presentation"]["question"]["md"],
                        example=s["presentation"]["example"]["md"],
                        visual=Visual(
                            format=s["presentation"]["visual"]["format"],
                            artifact=s["presentation"]["visual"]["artifact"],
                            caption=s["presentation"]["visual"].get("caption"),
                        ),
                        tutor_prompt=s["presentation"].get("tutor_prompt"),
                        expected_answer_patterns=list(
                            s["presentation"].get("expected_answer_patterns") or []
                        ),
                    ),
                )
                for s in data["steps"]
            ],
            provenance=Provenance(
                module_version=data["provenance"]["module_version"],
                generator=data["provenance"]["generator"],
                route=data["provenance"].get("route"),
                created_at=data["provenance"]["created_at"],
                model=data["provenance"].get("model"),
                prompt_sha256=data["provenance"].get("prompt_sha256"),
                problem_sha256=data["provenance"].get("problem_sha256"),
            ),
        )


def _schema_errors(data: dict[str, Any]) -> list[str]:
    validator = jsonschema.Draft202012Validator(load_schema())
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    return [e.message for e in errors]


def _cross_field_errors(data: dict[str, Any]) -> list[str]:
    """Topological validity, coverage, and step-indexing rules."""

    from .order import is_topological_order

    errors: list[str] = []
    try:
        node_ids = [n["concept_id"] for n in data["concept_dag"]["nodes"]]
        edges = [(e["from"], e["to"]) for e in data["concept_dag"]["edges"]]
        order = list(data["learning_order"])
        steps = list(data["steps"])
    except (KeyError, TypeError):
        return errors  # shape violations already reported by the schema gate

    node_set = set(node_ids)
    if len(node_set) != len(node_ids):
        errors.append("concept_dag has duplicate concept_id nodes")
    for src, dst in edges:
        if src not in node_set or dst not in node_set:
            errors.append(f"edge {src}->{dst} references an unknown concept_id")
    if len(set(order)) != len(order) or set(order) != node_set:
        errors.append("learning_order must list every concept_id exactly once")
    elif not is_topological_order(node_ids, edges, order):
        errors.append("learning_order is not a topological order of concept_dag")
    if not is_topological_order(node_ids, edges, node_ids):
        errors.append("concept_dag contains a cycle")

    step_concepts = [s.get("concept_id") for s in steps]
    for cid in step_concepts:
        if cid not in node_set:
            errors.append(f"step references unknown concept_id {cid!r}")
    for cid in node_set:
        if step_concepts.count(cid) != 1:
            errors.append(
                f"steps do not cover concept_id {cid!r} exactly once "
                "(every concept needs exactly one step)"
            )
    indices = [s.get("step_index") for s in steps]
    if sorted(i for i in indices if isinstance(i, int)) != list(range(len(steps))):
        errors.append("step_index values must be contiguous 0..n-1 in step order")

    return errors


def validate_decomposition(data: dict[str, Any]) -> list[str]:
    """Validate a decomposition dict; return a list of error strings (empty = valid)."""

    if not isinstance(data, dict):
        return ["decomposition must be a JSON object"]
    errors = _schema_errors(data)
    if errors:
        return errors
    return _cross_field_errors(data)


def load_decomposition(problem_id: str) -> Decomposition:
    """Load a packaged decomposition from package data (importlib.resources)."""

    from importlib.resources import files

    resource = files("study_os.decomposer").joinpath(
        f"decompositions/{problem_id}.v2.json"
    )
    if not resource.is_file():
        raise DecompositionError(f"no packaged decomposition for {problem_id!r}")
    data = json.loads(resource.read_text(encoding="utf-8"))
    errors = validate_decomposition(data)
    if errors:
        raise DecompositionError(
            f"packaged decomposition {problem_id!r} is invalid: {'; '.join(errors)}"
        )
    return Decomposition.from_dict(data)
