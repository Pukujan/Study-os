"""Versioned contracts for isolated adaptive components.

The contracts intentionally contain no persistence code.  Adaptive libraries
consume :class:`LearnerSnapshot` and emit :class:`DecisionProposal`; the
Study OS semantic service decides what, if anything, becomes canonical
learner evidence.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

LEARNER_SNAPSHOT_VERSION = "0.1.0"
DECISION_PROPOSAL_VERSION = "0.1.0"
SHADOW_EVENT_PAYLOAD_VERSION = "p2-shadow-0.1.0"

CAPABILITY_STATUSES = frozenset(
    {
        "not_tested",
        "fail",
        "partial",
        "pass_supported",
        "pass_unaided",
        "pass_transfer",
        "pass_delayed",
    }
)
ASSISTANCE_LEVELS = frozenset({f"A{level}" for level in range(7)})
PHASES = frozenset({"diagnostic", "instruction", "fading", "transfer", "maintenance"})
PROPOSAL_MODES = frozenset({"shadow", "advisory", "live"})


def _require_non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _string_tuple(values: Sequence[str] | None, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an array of strings")
    result = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return result


def _json_object(value: Mapping[str, Any] | None, field_name: str) -> dict[str, Any]:
    result = dict(value or {})
    try:
        json.dumps(result, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be JSON serializable") from exc
    return result


def _finite_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


@dataclass(frozen=True, slots=True)
class CapabilityState:
    """Compact evidence-backed state for one atomic competency."""

    status: str
    assistance_level: str | None = None
    evidence_ids: tuple[str, ...] = ()
    last_assessed_at: str | None = None

    def __post_init__(self) -> None:
        if self.status not in CAPABILITY_STATUSES:
            raise ValueError(f"unsupported capability status: {self.status}")
        if self.assistance_level is not None and self.assistance_level not in ASSISTANCE_LEVELS:
            raise ValueError(f"unsupported assistance level: {self.assistance_level}")
        object.__setattr__(self, "evidence_ids", _string_tuple(self.evidence_ids, "evidence_ids"))
        if self.last_assessed_at is not None:
            _require_non_empty(self.last_assessed_at, "last_assessed_at")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CapabilityState":
        return cls(
            status=str(value.get("status", "")),
            assistance_level=value.get("assistance_level"),
            evidence_ids=_string_tuple(value.get("evidence_ids"), "evidence_ids"),
            last_assessed_at=value.get("last_assessed_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "assistance_level": self.assistance_level,
            "evidence_ids": list(self.evidence_ids),
            "last_assessed_at": self.last_assessed_at,
        }


@dataclass(frozen=True, slots=True)
class LearnerSnapshot:
    """Versioned read-only projection supplied to adaptive components."""

    subject_id: str
    checkpoint_id: str | None
    phase: str
    current_focus: str | None = None
    capabilities: Mapping[str, CapabilityState] = field(default_factory=dict)
    open_hypotheses: tuple[Mapping[str, Any], ...] = ()
    active_misconceptions: tuple[Mapping[str, Any], ...] = ()
    retention_state: Mapping[str, Any] = field(default_factory=dict)
    recent_exposures: tuple[str, ...] = ()
    active_goal_ids: tuple[str, ...] = ()
    interaction_constraints: Mapping[str, Any] = field(default_factory=dict)
    snapshot_version: str = LEARNER_SNAPSHOT_VERSION

    def __post_init__(self) -> None:
        _require_non_empty(self.subject_id, "subject_id")
        if self.checkpoint_id is not None:
            _require_non_empty(self.checkpoint_id, "checkpoint_id")
        if self.phase not in PHASES:
            raise ValueError(f"unsupported phase: {self.phase}")
        if self.current_focus is not None:
            _require_non_empty(self.current_focus, "current_focus")
        if self.snapshot_version != LEARNER_SNAPSHOT_VERSION:
            raise ValueError(f"unsupported snapshot_version: {self.snapshot_version}")

        normalized_capabilities: dict[str, CapabilityState] = {}
        for competency_id, state in dict(self.capabilities).items():
            _require_non_empty(competency_id, "competency_id")
            normalized_capabilities[competency_id] = (
                state if isinstance(state, CapabilityState) else CapabilityState.from_mapping(state)
            )
        object.__setattr__(self, "capabilities", normalized_capabilities)
        object.__setattr__(
            self,
            "open_hypotheses",
            tuple(_json_object(value, "open_hypothesis") for value in self.open_hypotheses),
        )
        object.__setattr__(
            self,
            "active_misconceptions",
            tuple(_json_object(value, "active_misconception") for value in self.active_misconceptions),
        )
        object.__setattr__(self, "retention_state", _json_object(self.retention_state, "retention_state"))
        object.__setattr__(self, "recent_exposures", _string_tuple(self.recent_exposures, "recent_exposures"))
        object.__setattr__(self, "active_goal_ids", _string_tuple(self.active_goal_ids, "active_goal_ids"))
        object.__setattr__(
            self,
            "interaction_constraints",
            _json_object(self.interaction_constraints, "interaction_constraints"),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "LearnerSnapshot":
        capabilities = {
            competency_id: CapabilityState.from_mapping(state)
            for competency_id, state in dict(value.get("capabilities", {})).items()
        }
        return cls(
            subject_id=str(value.get("subject_id", "")),
            checkpoint_id=value.get("checkpoint_id"),
            phase=str(value.get("phase", "")),
            current_focus=value.get("current_focus"),
            capabilities=capabilities,
            open_hypotheses=tuple(value.get("open_hypotheses", ())),
            active_misconceptions=tuple(value.get("active_misconceptions", ())),
            retention_state=dict(value.get("retention_state", {})),
            recent_exposures=_string_tuple(value.get("recent_exposures"), "recent_exposures"),
            active_goal_ids=_string_tuple(value.get("active_goal_ids"), "active_goal_ids"),
            interaction_constraints=dict(value.get("interaction_constraints", {})),
            snapshot_version=str(value.get("snapshot_version", LEARNER_SNAPSHOT_VERSION)),
        )

    def evidence_ids(self) -> tuple[str, ...]:
        """Return deduplicated canonical evidence supporting this projection."""
        ordered: list[str] = []
        if self.checkpoint_id:
            ordered.append(self.checkpoint_id)
        for state in self.capabilities.values():
            ordered.extend(state.evidence_ids)
        return tuple(dict.fromkeys(ordered))

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_version": self.snapshot_version,
            "subject_id": self.subject_id,
            "checkpoint_id": self.checkpoint_id,
            "phase": self.phase,
            "current_focus": self.current_focus,
            "capabilities": {
                competency_id: state.to_dict() for competency_id, state in sorted(self.capabilities.items())
            },
            "open_hypotheses": [dict(value) for value in self.open_hypotheses],
            "active_misconceptions": [dict(value) for value in self.active_misconceptions],
            "retention_state": dict(self.retention_state),
            "recent_exposures": list(self.recent_exposures),
            "active_goal_ids": list(self.active_goal_ids),
            "interaction_constraints": dict(self.interaction_constraints),
        }


@dataclass(frozen=True, slots=True)
class CandidateExclusion:
    candidate_id: str
    reason_code: str
    detail: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.candidate_id, "candidate_id")
        _require_non_empty(self.reason_code, "reason_code")
        if self.detail is not None:
            _require_non_empty(self.detail, "detail")

    def to_dict(self) -> dict[str, Any]:
        return {"candidate_id": self.candidate_id, "reason_code": self.reason_code, "detail": self.detail}


@dataclass(frozen=True, slots=True)
class CandidateScore:
    candidate_id: str
    components: Mapping[str, float | None]
    total: float

    def __post_init__(self) -> None:
        _require_non_empty(self.candidate_id, "candidate_id")
        normalized: dict[str, float | None] = {}
        for name, value in dict(self.components).items():
            _require_non_empty(name, "score component")
            normalized[name] = None if value is None else _finite_number(value, f"score component {name}")
        object.__setattr__(self, "components", normalized)
        object.__setattr__(self, "total", _finite_number(self.total, "total"))

    def to_dict(self) -> dict[str, Any]:
        return {"candidate_id": self.candidate_id, "components": dict(self.components), "total": self.total}


@dataclass(frozen=True, slots=True)
class SelectedAction:
    candidate_id: str
    action_type: str
    assistance_target: str | None = None
    representation_id: str | None = None
    learning_operation: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.candidate_id, "candidate_id")
        _require_non_empty(self.action_type, "action_type")
        if self.assistance_target is not None and self.assistance_target not in ASSISTANCE_LEVELS:
            raise ValueError(f"unsupported assistance target: {self.assistance_target}")
        if self.representation_id is not None:
            _require_non_empty(self.representation_id, "representation_id")
        if self.learning_operation is not None:
            _require_non_empty(self.learning_operation, "learning_operation")

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "action_type": self.action_type,
            "assistance_target": self.assistance_target,
            "representation_id": self.representation_id,
            "learning_operation": self.learning_operation,
        }


@dataclass(frozen=True, slots=True)
class DecisionProposal:
    """Auditable recommendation emitted by one isolated component."""

    component_name: str
    implementation: str
    component_version: str
    mode: str
    phase: str
    candidates: tuple[str, ...]
    exclusions: tuple[CandidateExclusion, ...] = ()
    scores: tuple[CandidateScore, ...] = ()
    selected: SelectedAction | None = None
    rationale: str = ""
    expected_evidence: Mapping[str, Any] = field(default_factory=dict)
    proposal_version: str = DECISION_PROPOSAL_VERSION

    def __post_init__(self) -> None:
        _require_non_empty(self.component_name, "component_name")
        _require_non_empty(self.implementation, "implementation")
        _require_non_empty(self.component_version, "component_version")
        if self.mode not in PROPOSAL_MODES:
            raise ValueError(f"unsupported proposal mode: {self.mode}")
        if self.phase not in PHASES:
            raise ValueError(f"unsupported phase: {self.phase}")
        if self.proposal_version != DECISION_PROPOSAL_VERSION:
            raise ValueError(f"unsupported proposal_version: {self.proposal_version}")
        candidates = _string_tuple(self.candidates, "candidates")
        if len(candidates) != len(set(candidates)):
            raise ValueError("candidates must be unique")
        object.__setattr__(self, "candidates", candidates)
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("rationale must be a non-empty string")
        object.__setattr__(self, "expected_evidence", _json_object(self.expected_evidence, "expected_evidence"))

        candidate_set = set(candidates)
        excluded_ids = {exclusion.candidate_id for exclusion in self.exclusions}
        if any(exclusion.candidate_id not in candidate_set for exclusion in self.exclusions):
            raise ValueError("excluded candidates must appear in candidates")
        if any(score.candidate_id not in candidate_set for score in self.scores):
            raise ValueError("scored candidates must appear in candidates")
        if self.selected is not None:
            if self.selected.candidate_id not in candidate_set:
                raise ValueError("selected candidate must appear in candidates")
            if self.selected.candidate_id in excluded_ids:
                raise ValueError("selected candidate cannot be excluded")

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_version": self.proposal_version,
            "component": {
                "name": self.component_name,
                "implementation": self.implementation,
                "version": self.component_version,
            },
            "mode": self.mode,
            "phase": self.phase,
            "candidates": list(self.candidates),
            "exclusions": [value.to_dict() for value in self.exclusions],
            "scores": [value.to_dict() for value in self.scores],
            "selected": self.selected.to_dict() if self.selected else None,
            "rationale": self.rationale,
            "expected_evidence": dict(self.expected_evidence),
        }


def shadow_learning_event(snapshot: LearnerSnapshot, proposal: DecisionProposal) -> dict[str, Any]:
    """Build arguments for the existing ``record_learning_event`` tool.

    This helper deliberately does not perform persistence.  The caller passes
    the returned fields through the existing semantic service boundary and
    supplies an idempotency key/session ID there.
    """

    if proposal.mode != "shadow":
        raise ValueError("only shadow proposals may be serialized as shadow learning events")
    if proposal.phase != snapshot.phase:
        raise ValueError("proposal phase must match learner snapshot phase")
    source_ids = snapshot.evidence_ids()
    if not source_ids:
        raise ValueError("shadow proposal requires canonical source evidence")
    return {
        "evidence_class": "derived",
        "event_type": "controller_shadow_proposal",
        "payload_version": SHADOW_EVENT_PAYLOAD_VERSION,
        "source_ids": list(source_ids),
        "payload": {
            "snapshot_ref": {
                "snapshot_version": snapshot.snapshot_version,
                "subject_id": snapshot.subject_id,
                "checkpoint_id": snapshot.checkpoint_id,
                "phase": snapshot.phase,
            },
            "proposal": proposal.to_dict(),
        },
    }
