"""Small deterministic selector used as the P2 shadow-control baseline.

This is intentionally simple.  It exists so donor selectors can be compared
against an inspectable Study OS baseline on identical inputs; it is not a
claim that these weights are an optimal tutoring policy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from .contracts import (
    ASSISTANCE_LEVELS,
    CandidateExclusion,
    CandidateScore,
    DecisionProposal,
    LearnerSnapshot,
    SelectedAction,
)

BASELINE_COMPONENT_VERSION = "0.1.0"

# Larger means more instructional need.  The values are deliberately visible
# and replaceable rather than hidden in an opaque learner model.
STATUS_NEED = {
    "not_tested": 1.00,
    "fail": 0.95,
    "partial": 0.70,
    "pass_supported": 0.45,
    "pass_unaided": 0.15,
    "pass_transfer": 0.05,
    "pass_delayed": 0.00,
}
PREREQUISITE_PASS_STATUSES = frozenset({"pass_unaided", "pass_transfer", "pass_delayed"})
INSTRUCTION_COMPLETE_STATUSES = frozenset({"pass_unaided", "pass_transfer", "pass_delayed"})
RECENT_EXPOSURE_PENALTY = 0.20


@dataclass(frozen=True, slots=True)
class InstructionCandidate:
    """Approved candidate supplied by the curriculum layer."""

    candidate_id: str
    competency_id: str
    prerequisites: tuple[str, ...] = ()
    goal_relevance: float = 1.0
    action_type: str = "practice"
    assistance_target: str | None = None
    representation_id: str | None = None
    learning_operation: str | None = None

    def __post_init__(self) -> None:
        for name, value in (("candidate_id", self.candidate_id), ("competency_id", self.competency_id)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if any(not isinstance(value, str) or not value.strip() for value in self.prerequisites):
            raise ValueError("prerequisites must contain non-empty strings")
        if isinstance(self.goal_relevance, bool) or not isinstance(self.goal_relevance, (int, float)):
            raise ValueError("goal_relevance must be numeric")
        if not math.isfinite(float(self.goal_relevance)) or not 0.0 <= float(self.goal_relevance) <= 1.0:
            raise ValueError("goal_relevance must be finite and in [0,1]")
        if not isinstance(self.action_type, str) or not self.action_type.strip():
            raise ValueError("action_type must be a non-empty string")
        if self.assistance_target is not None and self.assistance_target not in ASSISTANCE_LEVELS:
            raise ValueError(f"unsupported assistance target: {self.assistance_target}")


def _prerequisite_missing(snapshot: LearnerSnapshot, candidate: InstructionCandidate) -> list[str]:
    missing: list[str] = []
    for prerequisite in candidate.prerequisites:
        state = snapshot.capabilities.get(prerequisite)
        if state is None or state.status not in PREREQUISITE_PASS_STATUSES:
            missing.append(prerequisite)
    return missing


def propose_instruction_baseline(
    snapshot: LearnerSnapshot,
    candidates: Iterable[InstructionCandidate],
) -> DecisionProposal:
    """Rank an approved instruction candidate set with visible heuristics.

    Eligibility is a hard gate.  Among eligible, not-yet-independent targets,
    the baseline ranks ``goal_relevance * instructional_need`` and subtracts a
    small recent-exposure penalty.  This mirrors the architecture under test
    without pretending the weights are empirically validated.
    """

    if snapshot.phase != "instruction":
        raise ValueError("instruction baseline requires snapshot.phase='instruction'")

    candidate_list = tuple(candidates)
    candidate_ids = tuple(candidate.candidate_id for candidate in candidate_list)
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidate IDs must be unique")

    exclusions: list[CandidateExclusion] = []
    scores: list[CandidateScore] = []
    eligible: list[tuple[InstructionCandidate, float]] = []
    recent = set(snapshot.recent_exposures)

    for candidate in candidate_list:
        missing = _prerequisite_missing(snapshot, candidate)
        if missing:
            exclusions.append(
                CandidateExclusion(
                    candidate_id=candidate.candidate_id,
                    reason_code="prerequisite_not_met",
                    detail=",".join(sorted(missing)),
                )
            )
            continue

        state = snapshot.capabilities.get(candidate.competency_id)
        status = state.status if state else "not_tested"
        if status in INSTRUCTION_COMPLETE_STATUSES:
            exclusions.append(
                CandidateExclusion(candidate.candidate_id, "instruction_target_already_independent")
            )
            continue

        instructional_need = STATUS_NEED[status]
        exposure_penalty = RECENT_EXPOSURE_PENALTY if candidate.candidate_id in recent else 0.0
        total = max(0.0, float(candidate.goal_relevance) * instructional_need - exposure_penalty)
        scores.append(
            CandidateScore(
                candidate_id=candidate.candidate_id,
                components={
                    "goal_relevance": float(candidate.goal_relevance),
                    "instructional_need": instructional_need,
                    "recent_exposure_penalty": exposure_penalty,
                },
                total=total,
            )
        )
        eligible.append((candidate, total))

    selected = None
    rationale: str
    if eligible:
        # Stable candidate_id tie-break keeps replay results deterministic.
        winner, winner_score = sorted(eligible, key=lambda pair: (-pair[1], pair[0].candidate_id))[0]
        selected = SelectedAction(
            candidate_id=winner.candidate_id,
            action_type=winner.action_type,
            assistance_target=winner.assistance_target,
            representation_id=winner.representation_id,
            learning_operation=winner.learning_operation,
        )
        rationale = (
            f"selected {winner.candidate_id} by deterministic instruction baseline "
            f"with score={winner_score:.3f} after prerequisite/independence gates"
        )
    else:
        rationale = "no eligible instruction candidate after prerequisite/independence gates"

    return DecisionProposal(
        component_name="study_os_instruction_baseline",
        implementation="study_os.adaptive.baseline.propose_instruction_baseline",
        component_version=BASELINE_COMPONENT_VERSION,
        mode="shadow",
        phase=snapshot.phase,
        candidates=candidate_ids,
        exclusions=tuple(exclusions),
        scores=tuple(scores),
        selected=selected,
        rationale=rationale,
        expected_evidence={
            "competencies": [selected.candidate_id] if selected else [],
            "policy": "baseline_not_validated_for_live_authority",
        },
    )
