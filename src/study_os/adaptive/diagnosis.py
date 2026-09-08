"""Versioned structured diagnosis proposals for bounded learning control.

Diagnosis is derived evidence. A model may propose hypotheses and representation
signals, but this module deliberately grants no course-progression authority.
The deterministic controller consumes these records separately.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

DIAGNOSIS_SCHEMA_VERSION = "0.1.0"
DIAGNOSIS_PROMPT_VERSION = "p4-diagnosis-proposal.v0.1"
DIAGNOSIS_FAMILIES = frozenset(
    {
        "missing_prerequisite",
        "concept_failure",
        "representation_interference",
        "identifier_interference",
        "information_overload",
        "information_underload",
        "decomposition_too_coarse",
        "over_decomposition",
        "over_help",
        "uncertain_mixed",
    }
)
DIAGNOSIS_STATUSES = frozenset({"proposed", "supported", "contradicted", "unresolved"})
CODE_VISIBILITY = frozenset({"unspecified", "hide_initially", "allow", "require"})
INTERACTION_GRANULARITY = frozenset({"unspecified", "single_probe", "multi_part"})


def _non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _string_tuple(values: Sequence[str] | None, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be an array of strings")
    result = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must be unique")
    return result


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    return value


def _mapping_array(value: Any, field_name: str) -> tuple[Mapping[str, Any], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be an array of objects")
    result: list[Mapping[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{field_name} must contain objects")
        result.append(item)
    return tuple(result)


def _confidence(value: float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("confidence must be numeric or null")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError("confidence must be finite and in [0,1]")
    return result


def _reject_unknown(value: Mapping[str, Any], allowed: set[str], field_name: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"{field_name} contains unsupported fields: {','.join(unknown)}")


@dataclass(frozen=True, slots=True)
class DiagnosisHypothesis:
    """One source-linked, non-authoritative explanation of learner difficulty."""

    diagnosis_id: str
    family: str
    source_evidence_ids: tuple[str, ...]
    suspected_competency_ids: tuple[str, ...] = ()
    confidence: float | None = None
    status: str = "proposed"

    def __post_init__(self) -> None:
        _non_empty(self.diagnosis_id, "diagnosis_id")
        if self.family not in DIAGNOSIS_FAMILIES:
            raise ValueError(f"unsupported diagnosis family: {self.family}")
        object.__setattr__(
            self,
            "source_evidence_ids",
            _string_tuple(self.source_evidence_ids, "source_evidence_ids"),
        )
        if not self.source_evidence_ids:
            raise ValueError("diagnosis requires at least one source evidence ID")
        object.__setattr__(
            self,
            "suspected_competency_ids",
            _string_tuple(self.suspected_competency_ids, "suspected_competency_ids"),
        )
        object.__setattr__(self, "confidence", _confidence(self.confidence))
        if self.status not in DIAGNOSIS_STATUSES:
            raise ValueError(f"unsupported diagnosis status: {self.status}")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DiagnosisHypothesis":
        value = _mapping(value, "diagnosis hypothesis")
        _reject_unknown(
            value,
            {
                "diagnosis_id",
                "family",
                "source_evidence_ids",
                "suspected_competency_ids",
                "confidence",
                "status",
            },
            "diagnosis hypothesis",
        )
        return cls(
            diagnosis_id=str(value.get("diagnosis_id", "")),
            family=str(value.get("family", "")),
            source_evidence_ids=_string_tuple(value.get("source_evidence_ids"), "source_evidence_ids"),
            suspected_competency_ids=_string_tuple(
                value.get("suspected_competency_ids"), "suspected_competency_ids"
            ),
            confidence=value.get("confidence"),
            status=str(value.get("status", "proposed")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "diagnosis_id": self.diagnosis_id,
            "family": self.family,
            "source_evidence_ids": list(self.source_evidence_ids),
            "suspected_competency_ids": list(self.suspected_competency_ids),
            "confidence": self.confidence,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class RepresentationSignals:
    """Structured learner-facing representation preferences inferred from evidence.

    These are signals, not permission to render or advance. A downstream
    representation policy still applies semantic-fidelity and assistance gates.
    """

    requested_families: tuple[str, ...] = ()
    avoid_families: tuple[str, ...] = ()
    code_visibility: str = "unspecified"
    interaction_granularity: str = "unspecified"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "requested_families",
            _string_tuple(self.requested_families, "requested_families"),
        )
        object.__setattr__(
            self,
            "avoid_families",
            _string_tuple(self.avoid_families, "avoid_families"),
        )
        if set(self.requested_families) & set(self.avoid_families):
            raise ValueError("representation family cannot be both requested and avoided")
        if self.code_visibility not in CODE_VISIBILITY:
            raise ValueError(f"unsupported code_visibility: {self.code_visibility}")
        if self.interaction_granularity not in INTERACTION_GRANULARITY:
            raise ValueError(
                f"unsupported interaction_granularity: {self.interaction_granularity}"
            )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RepresentationSignals":
        value = _mapping(value, "representation signals")
        _reject_unknown(
            value,
            {
                "requested_families",
                "avoid_families",
                "code_visibility",
                "interaction_granularity",
            },
            "representation signals",
        )
        return cls(
            requested_families=_string_tuple(value.get("requested_families"), "requested_families"),
            avoid_families=_string_tuple(value.get("avoid_families"), "avoid_families"),
            code_visibility=str(value.get("code_visibility", "unspecified")),
            interaction_granularity=str(value.get("interaction_granularity", "unspecified")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_families": list(self.requested_families),
            "avoid_families": list(self.avoid_families),
            "code_visibility": self.code_visibility,
            "interaction_granularity": self.interaction_granularity,
        }


@dataclass(frozen=True, slots=True)
class DiagnosisProposal:
    """Schema-shaped output from a versioned diagnosis prompt/model adapter."""

    source_evidence_ids: tuple[str, ...]
    hypotheses: tuple[DiagnosisHypothesis, ...]
    model_adapter: str
    representation_signals: RepresentationSignals = field(default_factory=RepresentationSignals)
    schema_version: str = DIAGNOSIS_SCHEMA_VERSION
    prompt_version: str = DIAGNOSIS_PROMPT_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != DIAGNOSIS_SCHEMA_VERSION:
            raise ValueError(f"unsupported diagnosis schema_version: {self.schema_version}")
        if self.prompt_version != DIAGNOSIS_PROMPT_VERSION:
            raise ValueError(f"unsupported diagnosis prompt_version: {self.prompt_version}")
        _non_empty(self.model_adapter, "model_adapter")
        object.__setattr__(
            self,
            "source_evidence_ids",
            _string_tuple(self.source_evidence_ids, "source_evidence_ids"),
        )
        if not self.source_evidence_ids:
            raise ValueError("diagnosis proposal requires source evidence")
        if not self.hypotheses:
            raise ValueError("diagnosis proposal requires at least one hypothesis")
        proposal_sources = set(self.source_evidence_ids)
        for hypothesis in self.hypotheses:
            if not set(hypothesis.source_evidence_ids).issubset(proposal_sources):
                raise ValueError("hypothesis source evidence must belong to proposal source evidence")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DiagnosisProposal":
        value = _mapping(value, "diagnosis proposal")
        _reject_unknown(
            value,
            {
                "schema_version",
                "prompt_version",
                "model_adapter",
                "source_evidence_ids",
                "hypotheses",
                "representation_signals",
            },
            "diagnosis proposal",
        )
        raw_hypotheses = _mapping_array(value.get("hypotheses", ()), "hypotheses")
        raw_signals = _mapping(value.get("representation_signals", {}), "representation_signals")
        return cls(
            schema_version=str(value.get("schema_version", "")),
            prompt_version=str(value.get("prompt_version", "")),
            model_adapter=str(value.get("model_adapter", "")),
            source_evidence_ids=_string_tuple(value.get("source_evidence_ids"), "source_evidence_ids"),
            hypotheses=tuple(
                DiagnosisHypothesis.from_mapping(hypothesis) for hypothesis in raw_hypotheses
            ),
            representation_signals=RepresentationSignals.from_mapping(raw_signals),
        )

    def families(self) -> frozenset[str]:
        return frozenset(hypothesis.family for hypothesis in self.hypotheses)

    def suspected_competency_ids(self, family: str) -> tuple[str, ...]:
        ordered: list[str] = []
        for hypothesis in self.hypotheses:
            if hypothesis.family == family:
                ordered.extend(hypothesis.suspected_competency_ids)
        return tuple(dict.fromkeys(ordered))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "prompt_version": self.prompt_version,
            "model_adapter": self.model_adapter,
            "source_evidence_ids": list(self.source_evidence_ids),
            "hypotheses": [hypothesis.to_dict() for hypothesis in self.hypotheses],
            "representation_signals": self.representation_signals.to_dict(),
        }
