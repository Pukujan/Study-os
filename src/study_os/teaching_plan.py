"""Generic, immutable teaching-plan contract for model-driven tutoring.

The JSON schema defines the serializable shape.  This module adds the
cross-record checks that a JSON schema cannot express reliably: reference
integrity, prerequisite acyclicity, terminal evidence coverage, and immutable
provenance matching the source problem and schema version.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

TEACHING_PLAN_SCHEMA_VERSION = "study-os.teaching-plan.v0.1"
TEACHING_PLAN_SCHEMA_FILENAME = "teaching-plan.v0.1.schema.json"
ASSISTANCE_CEILINGS = frozenset({"A0", "A1", "A2"})

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class TeachingPlanValidationError(ValueError):
    """Raised when a teaching plan is structurally or semantically invalid."""


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TeachingPlanValidationError(f"{field_name} must be a non-empty string")
    return value.strip()


def _identifier(value: object, field_name: str) -> str:
    value = _text(value, field_name)
    if _IDENTIFIER.fullmatch(value) is None:
        raise TeachingPlanValidationError(
            f"{field_name} must be a Python-style identifier: {value!r}"
        )
    return value


def _id(value: object, field_name: str) -> str:
    value = _text(value, field_name)
    if _ID.fullmatch(value) is None:
        raise TeachingPlanValidationError(
            f"{field_name} must be an alphanumeric, underscore, or hyphen ID: {value!r}"
        )
    return value


def _text_tuple(value: object, field_name: str, *, required: bool = False) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise TeachingPlanValidationError(f"{field_name} must be an array of strings")
    result = tuple(_text(item, f"{field_name}[]") for item in value)
    if required and not result:
        raise TeachingPlanValidationError(f"{field_name} must not be empty")
    if len(result) != len(set(result)):
        raise TeachingPlanValidationError(f"{field_name} must contain unique values")
    return result


def _identifier_tuple(
    value: object, field_name: str, *, required: bool = False
) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise TeachingPlanValidationError(f"{field_name} must be an array of identifiers")
    result = tuple(_identifier(item, f"{field_name}[]") for item in value)
    if required and not result:
        raise TeachingPlanValidationError(f"{field_name} must not be empty")
    if len(result) != len(set(result)):
        raise TeachingPlanValidationError(f"{field_name} must contain unique values")
    return result


def _id_tuple(value: object, field_name: str, *, required: bool = False) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise TeachingPlanValidationError(f"{field_name} must be an array of IDs")
    result = tuple(_id(item, f"{field_name}[]") for item in value)
    if required and not result:
        raise TeachingPlanValidationError(f"{field_name} must not be empty")
    if len(result) != len(set(result)):
        raise TeachingPlanValidationError(f"{field_name} must contain unique values")
    return result


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TeachingPlanValidationError(f"{field_name} must be an object")
    return value


def _unique_ids(records: Iterable[Any], field_name: str) -> dict[str, Any]:
    indexed: dict[str, Any] = {}
    for record in records:
        record_id = record.id
        if record_id in indexed:
            raise TeachingPlanValidationError(f"duplicate {field_name} id: {record_id}")
        indexed[record_id] = record
    return indexed


@dataclass(frozen=True, slots=True)
class ProblemSpec:
    """Source problem identity and wording used to create the plan."""

    id: str
    statement: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _id(self.id, "problem.id"))
        object.__setattr__(self, "statement", _text(self.statement, "problem.statement"))


@dataclass(frozen=True, slots=True)
class VariableSpec:
    """Stable semantic binding for one variable name."""

    role: str
    meaning: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _text(self.role, "variable.role"))
        object.__setattr__(self, "meaning", _text(self.meaning, "variable.meaning"))


@dataclass(frozen=True, slots=True)
class RepresentationRequirement:
    """A representation family/operation required by one or more concepts."""

    id: str
    kind: str
    operation: str
    description: str
    required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _id(self.id, "representation_requirement.id"))
        object.__setattr__(self, "kind", _text(self.kind, "representation_requirement.kind"))
        object.__setattr__(
            self, "operation", _text(self.operation, "representation_requirement.operation")
        )
        object.__setattr__(
            self,
            "description",
            _text(self.description, "representation_requirement.description"),
        )
        if not isinstance(self.required, bool):
            raise TeachingPlanValidationError("representation_requirement.required must be boolean")


@dataclass(frozen=True, slots=True)
class SemanticInvariant:
    """A deterministic meaning that must remain stable during tutoring."""

    id: str
    concept_id: str
    statement: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _id(self.id, "semantic_invariant.id"))
        object.__setattr__(self, "concept_id", _id(self.concept_id, "semantic_invariant.concept_id"))
        object.__setattr__(self, "statement", _text(self.statement, "semantic_invariant.statement"))


@dataclass(frozen=True, slots=True)
class CompletionEvidence:
    """Observable evidence that a concept or terminal behavior was completed."""

    id: str
    concept_id: str
    evidence_type: str
    description: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _id(self.id, "completion_evidence.id"))
        object.__setattr__(self, "concept_id", _id(self.concept_id, "completion_evidence.concept_id"))
        object.__setattr__(self, "evidence_type", _text(self.evidence_type, "completion_evidence.evidence_type"))
        object.__setattr__(self, "description", _text(self.description, "completion_evidence.description"))


@dataclass(frozen=True, slots=True)
class ConceptSpec:
    """One concept in the prerequisite DAG and its semantic contract."""

    id: str
    prerequisites: tuple[str, ...]
    allowed_variables: tuple[str, ...]
    representation_requirement_ids: tuple[str, ...]
    semantic_invariant_ids: tuple[str, ...]
    completion_evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _id(self.id, "concept.id"))
        object.__setattr__(
            self, "prerequisites", _id_tuple(self.prerequisites, "concept.prerequisites")
        )
        object.__setattr__(
            self,
            "allowed_variables",
            _identifier_tuple(self.allowed_variables, "concept.allowed_variables", required=True),
        )
        object.__setattr__(
            self,
            "representation_requirement_ids",
            _id_tuple(
                self.representation_requirement_ids,
                "concept.representation_requirement_ids",
                required=True,
            ),
        )
        object.__setattr__(
            self,
            "semantic_invariant_ids",
            _id_tuple(
                self.semantic_invariant_ids,
                "concept.semantic_invariant_ids",
                required=True,
            ),
        )
        object.__setattr__(
            self,
            "completion_evidence_ids",
            _id_tuple(self.completion_evidence_ids, "concept.completion_evidence_ids"),
        )


@dataclass(frozen=True, slots=True)
class TeachingPlanProvenance:
    """Immutable identity of the model/prompt/run that produced a plan."""

    prompt_version: str
    prompt_hash: str
    model_identifier: str
    teaching_plan_schema_version: str
    turn_trace_schema_version: str
    run_id: str
    source_problem_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "prompt_version",
            "model_identifier",
            "teaching_plan_schema_version",
            "turn_trace_schema_version",
            "run_id",
        ):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        object.__setattr__(
            self, "source_problem_id", _id(self.source_problem_id, "source_problem_id")
        )
        prompt_hash = _text(self.prompt_hash, "prompt_hash").lower()
        if _SHA256.fullmatch(prompt_hash) is None:
            raise TeachingPlanValidationError("prompt_hash must be a SHA-256 hexadecimal digest")
        object.__setattr__(self, "prompt_hash", prompt_hash)
        if self.teaching_plan_schema_version != TEACHING_PLAN_SCHEMA_VERSION:
            raise TeachingPlanValidationError(
                "provenance.teaching_plan_schema_version must match the plan schema version"
            )

    @classmethod
    def from_prompt_provenance(cls, provenance: Any) -> "TeachingPlanProvenance":
        """Copy the immutable identity emitted by ``prompt_registry``."""

        required = (
            "prompt_version",
            "prompt_hash",
            "model_identifier",
            "teaching_plan_schema_version",
            "turn_trace_schema_version",
            "run_id",
            "source_problem_id",
        )
        values = {
            name: _text(getattr(provenance, name, None), f"provenance.{name}")
            for name in required
        }
        return cls(**values)


@dataclass(frozen=True, slots=True)
class TeachingPlan:
    """Validated generic plan; all nested values are immutable after creation."""

    schema_version: str
    problem: ProblemSpec
    concepts: tuple[ConceptSpec, ...]
    variables: Mapping[str, VariableSpec]
    representation_requirements: tuple[RepresentationRequirement, ...]
    semantic_invariants: tuple[SemanticInvariant, ...]
    completion_evidence: tuple[CompletionEvidence, ...]
    terminal_behavior: tuple[str, ...]
    assistance_ceiling: str
    provenance: TeachingPlanProvenance

    def __post_init__(self) -> None:
        if self.schema_version != TEACHING_PLAN_SCHEMA_VERSION:
            raise TeachingPlanValidationError(
                f"unsupported teaching plan schema version: {self.schema_version!r}"
            )
        if not isinstance(self.problem, ProblemSpec):
            raise TeachingPlanValidationError("problem must be a ProblemSpec")
        if not isinstance(self.provenance, TeachingPlanProvenance):
            raise TeachingPlanValidationError("provenance must be TeachingPlanProvenance")
        if self.provenance.source_problem_id != self.problem.id:
            raise TeachingPlanValidationError(
                "provenance.source_problem_id must match problem.id"
            )
        if self.provenance.teaching_plan_schema_version != self.schema_version:
            raise TeachingPlanValidationError(
                "provenance schema version must match the plan schema version"
            )
        if self.assistance_ceiling not in ASSISTANCE_CEILINGS:
            raise TeachingPlanValidationError("assistance_ceiling must be A0, A1, or A2")

        concepts = tuple(self.concepts)
        representations = tuple(self.representation_requirements)
        invariants = tuple(self.semantic_invariants)
        evidence = tuple(self.completion_evidence)
        terminal_behavior = _text_tuple(
            self.terminal_behavior, "terminal_behavior", required=True
        )
        if not concepts:
            raise TeachingPlanValidationError("concepts must not be empty")
        if not representations:
            raise TeachingPlanValidationError("representation_requirements must not be empty")
        if not invariants:
            raise TeachingPlanValidationError("semantic_invariants must not be empty")
        if not evidence:
            raise TeachingPlanValidationError("completion_evidence must not be empty")
        if any(not isinstance(item, ConceptSpec) for item in concepts):
            raise TeachingPlanValidationError("concepts must contain ConceptSpec values")
        if any(not isinstance(item, RepresentationRequirement) for item in representations):
            raise TeachingPlanValidationError(
                "representation_requirements must contain RepresentationRequirement values"
            )
        if any(not isinstance(item, SemanticInvariant) for item in invariants):
            raise TeachingPlanValidationError(
                "semantic_invariants must contain SemanticInvariant values"
            )
        if any(not isinstance(item, CompletionEvidence) for item in evidence):
            raise TeachingPlanValidationError(
                "completion_evidence must contain CompletionEvidence values"
            )
        if not isinstance(self.variables, Mapping):
            raise TeachingPlanValidationError("variables must be an object")
        variables = {
            _identifier(name, "variables key"): value for name, value in self.variables.items()
        }
        if not variables:
            raise TeachingPlanValidationError("variables must not be empty")
        if any(not isinstance(value, VariableSpec) for value in variables.values()):
            raise TeachingPlanValidationError("variables must contain VariableSpec values")

        concept_by_id = _unique_ids(concepts, "concept")
        representation_by_id = _unique_ids(representations, "representation requirement")
        invariant_by_id = _unique_ids(invariants, "semantic invariant")
        evidence_by_id = _unique_ids(evidence, "completion evidence")

        for concept in concepts:
            self._require_refs(concept.prerequisites, concept_by_id, f"concept {concept.id} prerequisites")
            self._require_refs(
                concept.allowed_variables, variables, f"concept {concept.id} allowed_variables"
            )
            self._require_refs(
                concept.representation_requirement_ids,
                representation_by_id,
                f"concept {concept.id} representation requirements",
            )
            self._require_refs(
                concept.semantic_invariant_ids,
                invariant_by_id,
                f"concept {concept.id} semantic invariants",
            )
            self._require_refs(
                concept.completion_evidence_ids,
                evidence_by_id,
                f"concept {concept.id} completion evidence",
            )
        self._validate_prerequisite_dag(concept_by_id)

        for invariant in invariants:
            if invariant.concept_id not in concept_by_id:
                raise TeachingPlanValidationError(
                    f"semantic invariant {invariant.id} references unknown concept "
                    f"{invariant.concept_id}"
                )
        for item in evidence:
            if item.concept_id not in concept_by_id:
                raise TeachingPlanValidationError(
                    f"completion evidence {item.id} references unknown concept {item.concept_id}"
                )
        referenced_invariants = {
            invariant_id
            for concept in concepts
            for invariant_id in concept.semantic_invariant_ids
        }
        if referenced_invariants != set(invariant_by_id):
            raise TeachingPlanValidationError(
                "every semantic invariant must be referenced by exactly one plan concept"
            )
        referenced_evidence = {
            evidence_id
            for concept in concepts
            for evidence_id in concept.completion_evidence_ids
        }
        if not referenced_evidence:
            raise TeachingPlanValidationError(
                "at least one concept must declare completion evidence"
            )
        if referenced_evidence != set(evidence_by_id):
            raise TeachingPlanValidationError(
                "every completion evidence record must be referenced by a plan concept"
            )

        object.__setattr__(self, "schema_version", _text(self.schema_version, "schema_version"))
        object.__setattr__(self, "concepts", concepts)
        object.__setattr__(self, "variables", MappingProxyType(variables))
        object.__setattr__(self, "representation_requirements", representations)
        object.__setattr__(self, "semantic_invariants", invariants)
        object.__setattr__(self, "completion_evidence", evidence)
        object.__setattr__(self, "terminal_behavior", terminal_behavior)

    @staticmethod
    def _require_refs(values: Iterable[str], known: Mapping[str, Any], field_name: str) -> None:
        unknown = sorted(set(values) - set(known))
        if unknown:
            raise TeachingPlanValidationError(
                f"{field_name} references unknown identifiers: {', '.join(unknown)}"
            )

    @staticmethod
    def _validate_prerequisite_dag(concept_by_id: Mapping[str, ConceptSpec]) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(concept_id: str, trail: tuple[str, ...]) -> None:
            if concept_id in visiting:
                cycle = " -> ".join((*trail, concept_id))
                raise TeachingPlanValidationError(
                    f"concept prerequisite cycle detected: {cycle}"
                )
            if concept_id in visited:
                return
            visiting.add(concept_id)
            for prerequisite in concept_by_id[concept_id].prerequisites:
                visit(prerequisite, (*trail, concept_id))
            visiting.remove(concept_id)
            visited.add(concept_id)

        for concept_id in concept_by_id:
            visit(concept_id, ())

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "TeachingPlan":
        """Validate a JSON-compatible payload and return an immutable model."""

        validate_teaching_plan_schema(payload)
        problem_payload = _mapping(payload["problem"], "problem")
        concepts_payload = payload["concepts"]
        variables_payload = _mapping(payload["variables"], "variables")
        concepts = tuple(
            ConceptSpec(
                id=item["id"],
                prerequisites=tuple(item["prerequisites"]),
                allowed_variables=tuple(item["allowed_variables"]),
                representation_requirement_ids=tuple(item["representation_requirement_ids"]),
                semantic_invariant_ids=tuple(item["semantic_invariant_ids"]),
                completion_evidence_ids=tuple(item["completion_evidence_ids"]),
            )
            for item in concepts_payload
        )
        provenance_payload = _mapping(payload["provenance"], "provenance")
        return cls(
            schema_version=payload["schema_version"],
            problem=ProblemSpec(
                id=problem_payload["id"], statement=problem_payload["statement"]
            ),
            concepts=concepts,
            variables={
                name: VariableSpec(role=item["role"], meaning=item["meaning"])
                for name, item in variables_payload.items()
            },
            representation_requirements=tuple(
                RepresentationRequirement(
                    id=item["id"],
                    kind=item["kind"],
                    operation=item["operation"],
                    description=item["description"],
                    required=item["required"],
                )
                for item in payload["representation_requirements"]
            ),
            semantic_invariants=tuple(
                SemanticInvariant(
                    id=item["id"], concept_id=item["concept_id"], statement=item["statement"]
                )
                for item in payload["semantic_invariants"]
            ),
            completion_evidence=tuple(
                CompletionEvidence(
                    id=item["id"],
                    concept_id=item["concept_id"],
                    evidence_type=item["evidence_type"],
                    description=item["description"],
                )
                for item in payload["completion_evidence"]
            ),
            terminal_behavior=tuple(payload["terminal_behavior"]),
            assistance_ceiling=payload["assistance_ceiling"],
            provenance=TeachingPlanProvenance(**provenance_payload),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a fresh JSON-compatible representation of the immutable plan."""

        return {
            "schema_version": self.schema_version,
            "problem": {"id": self.problem.id, "statement": self.problem.statement},
            "concepts": [
                {
                    "id": concept.id,
                    "prerequisites": list(concept.prerequisites),
                    "allowed_variables": list(concept.allowed_variables),
                    "representation_requirement_ids": list(
                        concept.representation_requirement_ids
                    ),
                    "semantic_invariant_ids": list(concept.semantic_invariant_ids),
                    "completion_evidence_ids": list(concept.completion_evidence_ids),
                }
                for concept in self.concepts
            ],
            "variables": {
                name: {"role": variable.role, "meaning": variable.meaning}
                for name, variable in self.variables.items()
            },
            "representation_requirements": [
                {
                    "id": requirement.id,
                    "kind": requirement.kind,
                    "operation": requirement.operation,
                    "description": requirement.description,
                    "required": requirement.required,
                }
                for requirement in self.representation_requirements
            ],
            "semantic_invariants": [
                {
                    "id": invariant.id,
                    "concept_id": invariant.concept_id,
                    "statement": invariant.statement,
                }
                for invariant in self.semantic_invariants
            ],
            "completion_evidence": [
                {
                    "id": item.id,
                    "concept_id": item.concept_id,
                    "evidence_type": item.evidence_type,
                    "description": item.description,
                }
                for item in self.completion_evidence
            ],
            "terminal_behavior": list(self.terminal_behavior),
            "assistance_ceiling": self.assistance_ceiling,
            "provenance": {
                "prompt_version": self.provenance.prompt_version,
                "prompt_hash": self.provenance.prompt_hash,
                "model_identifier": self.provenance.model_identifier,
                "teaching_plan_schema_version": self.provenance.teaching_plan_schema_version,
                "turn_trace_schema_version": self.provenance.turn_trace_schema_version,
                "run_id": self.provenance.run_id,
                "source_problem_id": self.provenance.source_problem_id,
            },
        }


def _schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "contracts" / TEACHING_PLAN_SCHEMA_FILENAME


def load_teaching_plan_schema() -> dict[str, Any]:
    """Load the repository contract used for structural plan validation."""

    path = _schema_path()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TeachingPlanValidationError(f"unable to load teaching-plan schema: {path}") from exc
    if not isinstance(value, dict):
        raise TeachingPlanValidationError("teaching-plan schema must be a JSON object")
    return value


def validate_teaching_plan_schema(payload: Mapping[str, Any]) -> None:
    """Validate the JSON-schema portion of a teaching-plan payload."""

    if not isinstance(payload, Mapping):
        raise TeachingPlanValidationError("teaching plan payload must be an object")
    schema = load_teaching_plan_schema()
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(payload)),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        rendered = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            rendered.append(f"{location}: {error.message}")
        raise TeachingPlanValidationError("; ".join(rendered))


__all__ = [
    "ASSISTANCE_CEILINGS",
    "CompletionEvidence",
    "ConceptSpec",
    "ProblemSpec",
    "RepresentationRequirement",
    "SemanticInvariant",
    "TEACHING_PLAN_SCHEMA_FILENAME",
    "TEACHING_PLAN_SCHEMA_VERSION",
    "TeachingPlan",
    "TeachingPlanProvenance",
    "TeachingPlanValidationError",
    "VariableSpec",
    "load_teaching_plan_schema",
    "validate_teaching_plan_schema",
]
