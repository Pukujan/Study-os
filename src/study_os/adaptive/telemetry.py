"""Structured P2 attempt telemetry carried in the existing attempt context JSON.

The first P2 iteration intentionally proves the instrumentation contract before
normalizing individual fields into SQL columns.  ``AttemptTelemetry`` can be
serialized into the existing ``record_attempt(context=...)`` semantic call.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .contracts import ASSISTANCE_LEVELS

ATTEMPT_CONTEXT_VERSION = "0.1.0"
INTERACTION_MODES = frozenset(
    {
        "manual_code_blank",
        "manual_code_scaffolded",
        "phone_shorthand",
        "verbal_explanation",
        "state_prediction",
        "code_trace",
        "code_reading",
        "parsons_completion",
        "debug_existing_code",
        "ai_oversight_review",
    }
)
FEEDBACK_EXPOSURES = frozenset(
    {
        "none",
        "correctness_only",
        "small_cue",
        "structural_hint",
        "partial_scaffold",
        "worked_example",
        "complete_solution",
    }
)
ERROR_TAG_PROVENANCE = frozenset({"observed", "deterministic", "derived"})
SELF_REPORT_FIELDS = frozenset({"confidence", "effort", "clarity", "overload"})


def _non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _strings(values: Sequence[str] | None, field_name: str) -> tuple[str, ...]:
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


@dataclass(frozen=True, slots=True)
class ErrorTag:
    """A cautious error classification that preserves its provenance."""

    code: str
    provenance: str
    detail: str | None = None
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _non_empty(self.code, "error_tag.code")
        if self.provenance not in ERROR_TAG_PROVENANCE:
            raise ValueError(f"unsupported error tag provenance: {self.provenance}")
        if self.detail is not None:
            _non_empty(self.detail, "error_tag.detail")
        object.__setattr__(self, "evidence_ids", _strings(self.evidence_ids, "error_tag.evidence_ids"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "provenance": self.provenance,
            "detail": self.detail,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True, slots=True)
class HintExposure:
    hint_id: str
    hint_type: str
    assistance_level: str

    def __post_init__(self) -> None:
        _non_empty(self.hint_id, "hint_id")
        _non_empty(self.hint_type, "hint_type")
        if self.assistance_level not in ASSISTANCE_LEVELS:
            raise ValueError(f"unsupported hint assistance level: {self.assistance_level}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "hint_id": self.hint_id,
            "hint_type": self.hint_type,
            "assistance_level": self.assistance_level,
        }


@dataclass(frozen=True, slots=True)
class AttemptTelemetry:
    """Versioned learning-process context for one attempt."""

    task_version: str
    competency_ids: tuple[str, ...]
    attempt_number: int
    interaction_mode: str
    assistance_level_before_attempt: str
    prior_attempt_id: str | None = None
    representation_ids_visible: tuple[str, ...] = ()
    hints_seen: tuple[HintExposure, ...] = ()
    feedback_exposure: str = "none"
    started_at: str | None = None
    submitted_at: str | None = None
    latency_ms: int | None = None
    tools_allowed: tuple[str, ...] = ()
    tools_used: tuple[str, ...] = ()
    deterministic_result_refs: tuple[str, ...] = ()
    error_tags: tuple[ErrorTag, ...] = ()
    self_report: Mapping[str, Any] = field(default_factory=dict)
    context_version: str = ATTEMPT_CONTEXT_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.task_version, "task_version")
        object.__setattr__(self, "competency_ids", _strings(self.competency_ids, "competency_ids"))
        if not self.competency_ids:
            raise ValueError("competency_ids must not be empty")
        if isinstance(self.attempt_number, bool) or not isinstance(self.attempt_number, int) or self.attempt_number < 1:
            raise ValueError("attempt_number must be an integer >= 1")
        if self.interaction_mode not in INTERACTION_MODES:
            raise ValueError(f"unsupported interaction_mode: {self.interaction_mode}")
        if self.assistance_level_before_attempt not in ASSISTANCE_LEVELS:
            raise ValueError(f"unsupported assistance level: {self.assistance_level_before_attempt}")
        if self.prior_attempt_id is not None:
            _non_empty(self.prior_attempt_id, "prior_attempt_id")
        if self.attempt_number == 1 and self.prior_attempt_id is not None:
            raise ValueError("attempt_number=1 must not have prior_attempt_id")
        if self.attempt_number > 1 and self.prior_attempt_id is None:
            raise ValueError("attempt_number>1 requires prior_attempt_id")
        object.__setattr__(
            self,
            "representation_ids_visible",
            _strings(self.representation_ids_visible, "representation_ids_visible"),
        )
        if self.feedback_exposure not in FEEDBACK_EXPOSURES:
            raise ValueError(f"unsupported feedback_exposure: {self.feedback_exposure}")
        for name, value in (("started_at", self.started_at), ("submitted_at", self.submitted_at)):
            if value is not None:
                _non_empty(value, name)
        if self.latency_ms is not None:
            if isinstance(self.latency_ms, bool) or not isinstance(self.latency_ms, int) or self.latency_ms < 0:
                raise ValueError("latency_ms must be an integer >= 0")
        object.__setattr__(self, "tools_allowed", _strings(self.tools_allowed, "tools_allowed"))
        object.__setattr__(self, "tools_used", _strings(self.tools_used, "tools_used"))
        if not set(self.tools_used).issubset(set(self.tools_allowed)):
            raise ValueError("tools_used must be a subset of tools_allowed")
        object.__setattr__(
            self,
            "deterministic_result_refs",
            _strings(self.deterministic_result_refs, "deterministic_result_refs"),
        )
        report = _json_object(self.self_report, "self_report")
        unknown = set(report) - SELF_REPORT_FIELDS
        if unknown:
            raise ValueError(f"unsupported self_report fields: {sorted(unknown)}")
        object.__setattr__(self, "self_report", report)
        if self.context_version != ATTEMPT_CONTEXT_VERSION:
            raise ValueError(f"unsupported context_version: {self.context_version}")

    def to_context(self) -> dict[str, Any]:
        return {
            "context_version": self.context_version,
            "task_version": self.task_version,
            "competency_ids": list(self.competency_ids),
            "attempt_number": self.attempt_number,
            "prior_attempt_id": self.prior_attempt_id,
            "interaction_mode": self.interaction_mode,
            "representation_ids_visible": list(self.representation_ids_visible),
            "assistance_level_before_attempt": self.assistance_level_before_attempt,
            "hints_seen": [value.to_dict() for value in self.hints_seen],
            "feedback_exposure": self.feedback_exposure,
            "started_at": self.started_at,
            "submitted_at": self.submitted_at,
            "latency_ms": self.latency_ms,
            "tools_allowed": list(self.tools_allowed),
            "tools_used": list(self.tools_used),
            "deterministic_result_refs": list(self.deterministic_result_refs),
            "error_tags": [value.to_dict() for value in self.error_tags],
            "self_report": dict(self.self_report),
        }

    def record_attempt_fields(self) -> dict[str, Any]:
        """Return the standardized fields consumed by ``record_attempt``."""
        return {
            "assistance_level": self.assistance_level_before_attempt,
            "context": self.to_context(),
        }
