"""Interpretable CAT/IRT shadow selectors.

This module implements small, standard psychometric primitives so Study OS
can reproduce and test candidate-ranking behavior before deciding whether to
wrap a larger OSS package such as catsim/EduCAT.  It does not persist learner
state and it does not estimate ability from raw history yet.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from .contracts import CandidateExclusion, CandidateScore, DecisionProposal, LearnerSnapshot, SelectedAction

CAT_COMPONENT_VERSION = "0.1.0"
DEFAULT_TARGET_SUCCESS = 0.70


@dataclass(frozen=True, slots=True)
class CatItemCandidate:
    """Approved item with 2PL IRT parameters and exposure metadata."""

    candidate_id: str
    competency_id: str
    difficulty: float
    discrimination: float = 1.0
    exposure_count: int = 0
    exposure_limit: int | None = None
    action_type: str = "diagnostic_probe"

    def __post_init__(self) -> None:
        for field_name, value in (("candidate_id", self.candidate_id), ("competency_id", self.competency_id)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        for field_name, value in (("difficulty", self.difficulty), ("discrimination", self.discrimination)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError(f"{field_name} must be a finite number")
        if float(self.discrimination) <= 0.0:
            raise ValueError("discrimination must be > 0")
        if isinstance(self.exposure_count, bool) or not isinstance(self.exposure_count, int) or self.exposure_count < 0:
            raise ValueError("exposure_count must be an integer >= 0")
        if self.exposure_limit is not None:
            if isinstance(self.exposure_limit, bool) or not isinstance(self.exposure_limit, int) or self.exposure_limit < 1:
                raise ValueError("exposure_limit must be an integer >= 1 when supplied")
        if not isinstance(self.action_type, str) or not self.action_type.strip():
            raise ValueError("action_type must be a non-empty string")


def _finite(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def irt_probability_correct(theta: float, item: CatItemCandidate) -> float:
    """2PL probability of a correct response using logistic scale D=1."""
    ability = _finite(theta, "theta")
    exponent = -float(item.discrimination) * (ability - float(item.difficulty))
    # Stable logistic evaluation for large magnitudes.
    if exponent >= 0:
        exp_neg = math.exp(-exponent)
        return exp_neg / (1.0 + exp_neg)
    exp_pos = math.exp(exponent)
    return 1.0 / (1.0 + exp_pos)


def irt_fisher_information(theta: float, item: CatItemCandidate) -> float:
    """2PL Fisher information at the supplied learner ability."""
    probability = irt_probability_correct(theta, item)
    discrimination = float(item.discrimination)
    return discrimination * discrimination * probability * (1.0 - probability)


def _partition_exposure(
    candidates: tuple[CatItemCandidate, ...],
) -> tuple[list[CatItemCandidate], list[CandidateExclusion]]:
    eligible: list[CatItemCandidate] = []
    exclusions: list[CandidateExclusion] = []
    for item in candidates:
        if item.exposure_limit is not None and item.exposure_count >= item.exposure_limit:
            exclusions.append(
                CandidateExclusion(
                    candidate_id=item.candidate_id,
                    reason_code="item_exposure_limit_reached",
                    detail=f"exposure_count={item.exposure_count},limit={item.exposure_limit}",
                )
            )
        else:
            eligible.append(item)
    return eligible, exclusions


def _validate_candidates(candidates: Iterable[CatItemCandidate]) -> tuple[CatItemCandidate, ...]:
    result = tuple(candidates)
    ids = [item.candidate_id for item in result]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate IDs must be unique")
    return result


def propose_maximum_fisher_information(
    snapshot: LearnerSnapshot,
    candidates: Iterable[CatItemCandidate],
    *,
    ability_theta: float,
) -> DecisionProposal:
    """Diagnostic CAT selector: choose maximum 2PL Fisher information."""
    if snapshot.phase != "diagnostic":
        raise ValueError("maximum Fisher information selector requires diagnostic phase")
    theta = _finite(ability_theta, "ability_theta")
    candidate_tuple = _validate_candidates(candidates)
    eligible, exclusions = _partition_exposure(candidate_tuple)

    values: dict[str, tuple[float, float]] = {}
    scores: list[CandidateScore] = []
    for item in eligible:
        probability = irt_probability_correct(theta, item)
        information = irt_fisher_information(theta, item)
        values[item.candidate_id] = (probability, information)
        scores.append(
            CandidateScore(
                candidate_id=item.candidate_id,
                components={
                    "predicted_success": probability,
                    "fisher_information": information,
                },
                total=information,
            )
        )

    selected = None
    expected: dict[str, object] = {"competencies": [], "ability_theta": theta, "selection_objective": "maximum_fisher_information"}
    if eligible:
        winner = sorted(eligible, key=lambda item: (-values[item.candidate_id][1], item.candidate_id))[0]
        probability, information = values[winner.candidate_id]
        selected = SelectedAction(winner.candidate_id, winner.action_type, assistance_target="A0")
        rationale = (
            f"selected {winner.candidate_id} at theta={theta:.3f} by maximum 2PL Fisher information="
            f"{information:.6f} (predicted_success={probability:.3f})"
        )
        expected = {
            "competencies": [winner.competency_id],
            "ability_theta": theta,
            "selection_objective": "maximum_fisher_information",
            "predicted_success": probability,
        }
    else:
        rationale = "no CAT candidate remains after exposure gates"

    return DecisionProposal(
        component_name="catsim_style_maximum_fisher_information",
        implementation="study_os.adaptive.cat.propose_maximum_fisher_information",
        component_version=CAT_COMPONENT_VERSION,
        mode="shadow",
        phase=snapshot.phase,
        candidates=tuple(item.candidate_id for item in candidate_tuple),
        exclusions=tuple(exclusions),
        scores=tuple(scores),
        selected=selected,
        rationale=rationale,
        expected_evidence=expected,
    )


def propose_target_success_item(
    snapshot: LearnerSnapshot,
    candidates: Iterable[CatItemCandidate],
    *,
    ability_theta: float,
    target_success: float = DEFAULT_TARGET_SUCCESS,
) -> DecisionProposal:
    """Instruction selector: choose the item closest to a target success probability."""
    if snapshot.phase != "instruction":
        raise ValueError("target-success selector requires instruction phase")
    theta = _finite(ability_theta, "ability_theta")
    target = _finite(target_success, "target_success")
    if not 0.0 < target < 1.0:
        raise ValueError("target_success must be in (0,1)")
    candidate_tuple = _validate_candidates(candidates)
    eligible, exclusions = _partition_exposure(candidate_tuple)

    values: dict[str, tuple[float, float]] = {}
    scores: list[CandidateScore] = []
    for item in eligible:
        probability = irt_probability_correct(theta, item)
        target_fit = 1.0 - abs(probability - target)
        values[item.candidate_id] = (probability, target_fit)
        scores.append(
            CandidateScore(
                candidate_id=item.candidate_id,
                components={
                    "predicted_success": probability,
                    "target_success": target,
                    "target_fit": target_fit,
                },
                total=target_fit,
            )
        )

    selected = None
    expected: dict[str, object] = {"competencies": [], "ability_theta": theta, "selection_objective": "target_success_fit"}
    if eligible:
        winner = sorted(eligible, key=lambda item: (-values[item.candidate_id][1], item.candidate_id))[0]
        probability, target_fit = values[winner.candidate_id]
        selected = SelectedAction(winner.candidate_id, winner.action_type, assistance_target="A0")
        rationale = (
            f"selected {winner.candidate_id} at theta={theta:.3f} for target_success={target:.3f}; "
            f"predicted_success={probability:.3f}, target_fit={target_fit:.6f}"
        )
        expected = {
            "competencies": [winner.competency_id],
            "ability_theta": theta,
            "selection_objective": "target_success_fit",
            "target_success": target,
            "predicted_success": probability,
        }
    else:
        rationale = "no instructional item remains after exposure gates"

    return DecisionProposal(
        component_name="irt_target_success_selector",
        implementation="study_os.adaptive.cat.propose_target_success_item",
        component_version=CAT_COMPONENT_VERSION,
        mode="shadow",
        phase=snapshot.phase,
        candidates=tuple(item.candidate_id for item in candidate_tuple),
        exclusions=tuple(exclusions),
        scores=tuple(scores),
        selected=selected,
        rationale=rationale,
        expected_evidence=expected,
    )
