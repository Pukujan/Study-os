"""Shadow-only contextual representation policy.

This module ranks representation interventions *after* a competency and task
have already been selected. It does not model fixed learning styles. The
heuristic weights are explicit, versioned, and intentionally provisional until
Study OS has enough within-subject outcome evidence to calibrate them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .contracts import (
    ASSISTANCE_LEVELS,
    CandidateExclusion,
    CandidateScore,
    DecisionProposal,
    LearnerSnapshot,
    SelectedAction,
)

REPRESENTATION_POLICY_VERSION = "0.1.0"
BOTTLENECK_WEIGHT = 0.55
BEHAVIORAL_EFFECT_WEIGHT = 0.35
UNTESTED_EXPLORATION_BONUS = 0.12
ONE_WINDOW_EXPLORATION_BONUS = 0.04
RECENT_EXPOSURE_PENALTY = 0.15
OUTCOME_WINDOW_WEIGHTS = {
    "immediate": 1.0,
    "faded": 2.0,
    "transfer": 3.0,
    "delayed": 4.0,
}


def _non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _unit_interval(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")
    result = float(value)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return result


def _assistance_number(level: str) -> int:
    if level not in ASSISTANCE_LEVELS:
        raise ValueError(f"unsupported assistance level: {level}")
    return int(level[1:])


@dataclass(frozen=True, slots=True)
class RepresentationOutcomeSummary:
    """Behavioral effectiveness observed for one contextual intervention.

    Scores are normalized 0..1 summaries derived elsewhere from canonical
    behavioral assessment evidence. Self-report is deliberately not a field in
    this scoring input.
    """

    immediate: float | None = None
    faded: float | None = None
    transfer: float | None = None
    delayed: float | None = None
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        observed = 0
        for field_name in OUTCOME_WINDOW_WEIGHTS:
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _unit_interval(value, field_name))
                observed += 1
        evidence = tuple(self.evidence_ids)
        if any(not isinstance(value, str) or not value.strip() for value in evidence):
            raise ValueError("representation outcome evidence_ids must contain non-empty strings")
        if observed and not evidence:
            raise ValueError("behavioral outcome scores require canonical evidence_ids")
        object.__setattr__(self, "evidence_ids", evidence)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RepresentationOutcomeSummary":
        return cls(
            immediate=value.get("immediate"),
            faded=value.get("faded"),
            transfer=value.get("transfer"),
            delayed=value.get("delayed"),
            evidence_ids=tuple(value.get("evidence_ids", ())),
        )

    def persistent_effect(self) -> tuple[float, int]:
        weighted = []
        for field_name, weight in OUTCOME_WINDOW_WEIGHTS.items():
            value = getattr(self, field_name)
            if value is not None:
                weighted.append((float(value), weight))
        if not weighted:
            return 0.0, 0
        mean = sum(value * weight for value, weight in weighted) / sum(weight for _, weight in weighted)
        coverage = len(weighted) / len(OUTCOME_WINDOW_WEIGHTS)
        # Sparse immediate-only evidence should count less than effects that
        # survive fade, transfer, and delay.
        return mean * (0.5 + 0.5 * coverage), len(weighted)


@dataclass(frozen=True, slots=True)
class RepresentationCandidate:
    candidate_id: str
    task_id: str
    competency_id: str
    representation_id: str
    representation_family: str
    representation_version: str
    operation: str
    assistance_target: str
    target_bottleneck: str
    bottleneck_match: float
    semantic_validated: bool
    outcomes: RepresentationOutcomeSummary = field(default_factory=RepresentationOutcomeSummary)

    def __post_init__(self) -> None:
        for name in (
            "candidate_id",
            "task_id",
            "competency_id",
            "representation_id",
            "representation_family",
            "representation_version",
            "operation",
            "target_bottleneck",
        ):
            _non_empty(getattr(self, name), name)
        if self.assistance_target not in ASSISTANCE_LEVELS:
            raise ValueError(f"unsupported assistance target: {self.assistance_target}")
        object.__setattr__(self, "bottleneck_match", _unit_interval(self.bottleneck_match, "bottleneck_match"))
        if not isinstance(self.semantic_validated, bool):
            raise ValueError("semantic_validated must be boolean")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RepresentationCandidate":
        return cls(
            candidate_id=str(value.get("candidate_id", "")),
            task_id=str(value.get("task_id", "")),
            competency_id=str(value.get("competency_id", "")),
            representation_id=str(value.get("representation_id", "")),
            representation_family=str(value.get("representation_family", "")),
            representation_version=str(value.get("representation_version", "")),
            operation=str(value.get("operation", "")),
            assistance_target=str(value.get("assistance_target", "")),
            target_bottleneck=str(value.get("target_bottleneck", "")),
            bottleneck_match=value.get("bottleneck_match"),
            semantic_validated=value.get("semantic_validated"),
            outcomes=RepresentationOutcomeSummary.from_mapping(value.get("outcomes", {})),
        )


def propose_representation_intervention(
    snapshot: LearnerSnapshot,
    candidates: Sequence[RepresentationCandidate],
    *,
    selected_task_id: str,
    target_competency_id: str,
    assistance_ceiling: str,
    allowed_representation_families: Sequence[str],
) -> DecisionProposal:
    """Rank contextual representation tuples for one already-selected task."""

    if snapshot.phase not in {"instruction", "fading"}:
        raise ValueError("representation policy is initially limited to instruction/fading phases")
    _non_empty(selected_task_id, "selected_task_id")
    _non_empty(target_competency_id, "target_competency_id")
    ceiling = _assistance_number(assistance_ceiling)
    allowed_families = tuple(allowed_representation_families)
    if not allowed_families or any(not isinstance(value, str) or not value.strip() for value in allowed_families):
        raise ValueError("allowed_representation_families must contain non-empty strings")
    candidate_ids = tuple(candidate.candidate_id for candidate in candidates)
    if not candidate_ids:
        raise ValueError("representation policy requires at least one candidate")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("representation candidate IDs must be unique")

    exclusions: list[CandidateExclusion] = []
    scores: list[CandidateScore] = []
    eligible: list[tuple[float, str, RepresentationCandidate]] = []
    recent = set(snapshot.recent_exposures)

    for candidate in candidates:
        reason = None
        detail = None
        if candidate.task_id != selected_task_id:
            reason, detail = "different_task", "representation policy cannot bypass the upstream task selection"
        elif candidate.competency_id != target_competency_id:
            reason, detail = "different_competency", "representation policy cannot switch the upstream competency target"
        elif candidate.representation_family not in allowed_families:
            reason, detail = "representation_not_allowed_for_task", "candidate family is not declared by the selected task"
        elif not candidate.semantic_validated:
            reason, detail = "semantic_not_validated", "representation has not passed semantic fidelity validation"
        elif _assistance_number(candidate.assistance_target) > ceiling:
            reason, detail = "assistance_ceiling_exceeded", "candidate requires more assistance than the upstream controller permits"
        if reason is not None:
            exclusions.append(CandidateExclusion(candidate.candidate_id, reason, detail))
            continue

        persistent_effect, observed_windows = candidate.outcomes.persistent_effect()
        exploration_bonus = (
            UNTESTED_EXPLORATION_BONUS
            if observed_windows == 0
            else ONE_WINDOW_EXPLORATION_BONUS if observed_windows == 1 else 0.0
        )
        repeat_penalty = RECENT_EXPOSURE_PENALTY if candidate.representation_id in recent else 0.0
        bottleneck_contribution = BOTTLENECK_WEIGHT * candidate.bottleneck_match
        behavioral_effect_contribution = BEHAVIORAL_EFFECT_WEIGHT * persistent_effect
        total = bottleneck_contribution + behavioral_effect_contribution + exploration_bonus - repeat_penalty
        scores.append(
            CandidateScore(
                candidate_id=candidate.candidate_id,
                components={
                    "bottleneck_contribution": bottleneck_contribution,
                    "persistent_behavioral_effect": persistent_effect,
                    "behavioral_effect_contribution": behavioral_effect_contribution,
                    "observed_window_coverage": observed_windows / 4.0,
                    "exploration_bonus": exploration_bonus,
                    "recent_exposure_penalty": -repeat_penalty,
                },
                total=total,
            )
        )
        eligible.append((total, candidate.candidate_id, candidate))

    selected_action = None
    expected: Mapping[str, object]
    rationale: str
    if eligible:
        _, _, selected = max(eligible, key=lambda value: (value[0], value[1]))
        selected_action = SelectedAction(
            candidate_id=selected.candidate_id,
            action_type="apply_representation_intervention",
            assistance_target=selected.assistance_target,
            representation_id=selected.representation_id,
            learning_operation=selected.operation,
        )
        rationale = (
            "Choose the highest-scoring semantically valid representation tuple for the already-selected task; "
            "persistent behavioral effects count more than immediate-only effects, with a small exploration bonus."
        )
        expected = {
            "selected_task_id": selected_task_id,
            "target_competency_id": target_competency_id,
            "representation_family": selected.representation_family,
            "representation_version": selected.representation_version,
            "target_bottleneck": selected.target_bottleneck,
            "behavioral_assessment_required": True,
            "outcome_windows": ["immediate", "faded", "transfer", "delayed"],
            "policy_status": "heuristic_shadow_only_not_calibrated",
        }
    else:
        rationale = "No representation candidate survived task, competency, family, semantic-fidelity, and assistance hard gates."
        expected = {
            "selected_task_id": selected_task_id,
            "target_competency_id": target_competency_id,
            "behavioral_assessment_required": True,
            "policy_status": "no_eligible_candidate",
        }

    return DecisionProposal(
        component_name="contextual_representation_policy",
        implementation="study_os_persistent_effect_heuristic",
        component_version=REPRESENTATION_POLICY_VERSION,
        mode="shadow",
        phase=snapshot.phase,
        candidates=candidate_ids,
        exclusions=tuple(exclusions),
        scores=tuple(scores),
        selected=selected_action,
        rationale=rationale,
        expected_evidence=expected,
    )
