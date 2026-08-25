"""Deterministic audit checks for LLM tutor actions.

This module evaluates an action envelope, not raw transcript text. It keeps
learner-state correctness separate from tutor-behavior quality and provides
hard regression checks for assistance ceilings, solution leakage, hidden-answer
protection, evidence-gated advancement, and representation fidelity.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import ASSISTANCE_LEVELS

TUTOR_ACTION_VERSION = "0.1.0"
ACTION_KINDS = frozenset({"question", "hint", "explanation", "worked_example", "full_solution", "assessment", "feedback", "representation"})
ADVANCEMENT_BASES = frozenset({"none", "behavioral_assessment", "self_report", "conversation_fluency"})


def _nonempty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _assist(level: str) -> int:
    if level not in ASSISTANCE_LEVELS:
        raise ValueError(f"unsupported assistance level: {level}")
    return int(level[1:])


@dataclass(frozen=True, slots=True)
class TutorAction:
    action_id: str
    task_id: str
    action_kind: str
    assistance_level: str
    contains_full_solution: bool
    reveals_hidden_answer: bool
    advancement_basis: str = "none"
    advancement_claim: str | None = None
    advancement_evidence_ids: tuple[str, ...] = ()
    representation_id: str | None = None
    representation_semantic_validated: bool | None = None
    schema_version: str = TUTOR_ACTION_VERSION

    def __post_init__(self) -> None:
        _nonempty(self.action_id, "action_id")
        _nonempty(self.task_id, "task_id")
        if self.action_kind not in ACTION_KINDS:
            raise ValueError(f"unsupported action_kind: {self.action_kind}")
        _assist(self.assistance_level)
        if self.advancement_basis not in ADVANCEMENT_BASES:
            raise ValueError(f"unsupported advancement_basis: {self.advancement_basis}")
        if self.schema_version != TUTOR_ACTION_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")
        evidence = tuple(self.advancement_evidence_ids)
        if any(not isinstance(value, str) or not value.strip() for value in evidence):
            raise ValueError("advancement_evidence_ids must contain non-empty strings")
        object.__setattr__(self, "advancement_evidence_ids", evidence)
        if self.advancement_claim is not None:
            _nonempty(self.advancement_claim, "advancement_claim")
        if self.representation_id is not None:
            _nonempty(self.representation_id, "representation_id")


@dataclass(frozen=True, slots=True)
class TutorPolicyConstraints:
    assistance_ceiling: str
    allow_full_solution: bool = False
    hidden_answer_protected: bool = True
    require_behavioral_advancement: bool = True

    def __post_init__(self) -> None:
        _assist(self.assistance_ceiling)


@dataclass(frozen=True, slots=True)
class TutorPolicyViolation:
    code: str
    detail: str


@dataclass(frozen=True, slots=True)
class TutorPolicyEvaluation:
    action_id: str
    allowed: bool
    violations: tuple[TutorPolicyViolation, ...]


def evaluate_tutor_action(action: TutorAction, constraints: TutorPolicyConstraints) -> TutorPolicyEvaluation:
    violations: list[TutorPolicyViolation] = []

    if _assist(action.assistance_level) > _assist(constraints.assistance_ceiling):
        violations.append(TutorPolicyViolation("assistance_ceiling_exceeded", "action assistance exceeds the controller ceiling"))

    if action.contains_full_solution and not constraints.allow_full_solution:
        violations.append(TutorPolicyViolation("premature_full_solution", "full solution is not authorized for this action"))

    if constraints.hidden_answer_protected and action.reveals_hidden_answer:
        violations.append(TutorPolicyViolation("hidden_answer_exposure", "protected assessment/transfer answer was exposed"))

    if action.advancement_claim is not None:
        if action.advancement_claim in {"pass_transfer", "pass_delayed"}:
            violations.append(TutorPolicyViolation("reserved_capability_promotion", "transfer/delayed promotion requires its dedicated behavioral evidence gate"))
        if constraints.require_behavioral_advancement:
            if action.advancement_basis != "behavioral_assessment":
                violations.append(TutorPolicyViolation("nonbehavioral_advancement", "advancement cannot be based on self-report or conversational fluency"))
            if not action.advancement_evidence_ids:
                violations.append(TutorPolicyViolation("missing_advancement_evidence", "advancement claim requires canonical behavioral evidence IDs"))

    if action.representation_id is not None and action.representation_semantic_validated is not True:
        violations.append(TutorPolicyViolation("unvalidated_representation", "representation must pass semantic fidelity validation before use"))

    return TutorPolicyEvaluation(action_id=action.action_id, allowed=not violations, violations=tuple(violations))
