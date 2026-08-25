"""Diagnostic shadow selectors for the first P2 component bake-off.

Both selectors consume the same approved candidate set.  The uncertainty
baseline ignores response noise; the BKT information-gain selector models
slip/guess and chooses the probe with the greatest expected entropy reduction.
Neither selector has live authority.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from .contracts import CandidateExclusion, CandidateScore, DecisionProposal, LearnerSnapshot, SelectedAction

DIAGNOSTIC_COMPONENT_VERSION = "0.1.0"
SATURATION_LOW = 0.05
SATURATION_HIGH = 0.95


@dataclass(frozen=True, slots=True)
class DiagnosticCandidate:
    candidate_id: str
    competency_id: str
    p_mastery: float
    p_slip: float
    p_guess: float
    action_type: str = "diagnostic_probe"

    def __post_init__(self) -> None:
        for field_name, value in (("candidate_id", self.candidate_id), ("competency_id", self.competency_id)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        for field_name, value in (
            ("p_mastery", self.p_mastery),
            ("p_slip", self.p_slip),
            ("p_guess", self.p_guess),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{field_name} must be numeric")
            if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{field_name} must be finite and in [0,1]")
        if not isinstance(self.action_type, str) or not self.action_type.strip():
            raise ValueError("action_type must be a non-empty string")


def bernoulli_entropy(probability: float) -> float:
    """Binary entropy in bits, with stable edge handling."""
    p = float(probability)
    if not 0.0 <= p <= 1.0 or not math.isfinite(p):
        raise ValueError("probability must be finite and in [0,1]")
    if p in (0.0, 1.0):
        return 0.0
    return -(p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p))


def bkt_information_gain(candidate: DiagnosticCandidate) -> float:
    """Expected reduction in mastery entropy after the next BKT response."""
    p = float(candidate.p_mastery)
    slip = float(candidate.p_slip)
    guess = float(candidate.p_guess)
    p_correct = p * (1.0 - slip) + (1.0 - p) * guess

    if p_correct <= 0.0 or p_correct >= 1.0:
        return 0.0

    p_mastery_given_correct = p * (1.0 - slip) / p_correct
    p_mastery_given_incorrect = p * slip / (1.0 - p_correct)
    expected_posterior_entropy = (
        p_correct * bernoulli_entropy(p_mastery_given_correct)
        + (1.0 - p_correct) * bernoulli_entropy(p_mastery_given_incorrect)
    )
    # Floating-point noise can produce tiny negative values at degenerate edges.
    return max(0.0, bernoulli_entropy(p) - expected_posterior_entropy)


def _eligible(candidates: tuple[DiagnosticCandidate, ...]) -> tuple[list[DiagnosticCandidate], list[CandidateExclusion]]:
    eligible: list[DiagnosticCandidate] = []
    exclusions: list[CandidateExclusion] = []
    for candidate in candidates:
        if candidate.p_mastery <= SATURATION_LOW or candidate.p_mastery >= SATURATION_HIGH:
            exclusions.append(
                CandidateExclusion(
                    candidate_id=candidate.candidate_id,
                    reason_code="diagnostic_state_saturated",
                    detail=f"p_mastery={candidate.p_mastery:.3f}",
                )
            )
        else:
            eligible.append(candidate)
    return eligible, exclusions


def _proposal(
    *,
    snapshot: LearnerSnapshot,
    candidates: tuple[DiagnosticCandidate, ...],
    component_name: str,
    implementation: str,
    score_name: str,
    score_values: dict[str, float],
    exclusions: list[CandidateExclusion],
) -> DecisionProposal:
    excluded_ids = {value.candidate_id for value in exclusions}
    eligible = [candidate for candidate in candidates if candidate.candidate_id not in excluded_ids]
    scores = tuple(
        CandidateScore(
            candidate_id=candidate.candidate_id,
            components={score_name: score_values[candidate.candidate_id]},
            total=score_values[candidate.candidate_id],
        )
        for candidate in eligible
    )
    selected = None
    if eligible:
        winner = sorted(
            eligible,
            key=lambda candidate: (-score_values[candidate.candidate_id], candidate.candidate_id),
        )[0]
        selected = SelectedAction(winner.candidate_id, winner.action_type, assistance_target="A0")
        rationale = (
            f"selected {winner.candidate_id} by maximum {score_name}="
            f"{score_values[winner.candidate_id]:.6f}"
        )
        expected = {
            "competencies": [winner.competency_id],
            "selection_objective": score_name,
        }
    else:
        rationale = "no non-saturated diagnostic candidate"
        expected = {"competencies": [], "selection_objective": score_name}

    return DecisionProposal(
        component_name=component_name,
        implementation=implementation,
        component_version=DIAGNOSTIC_COMPONENT_VERSION,
        mode="shadow",
        phase=snapshot.phase,
        candidates=tuple(candidate.candidate_id for candidate in candidates),
        exclusions=tuple(exclusions),
        scores=scores,
        selected=selected,
        rationale=rationale,
        expected_evidence=expected,
    )


def propose_uncertainty_baseline(
    snapshot: LearnerSnapshot,
    candidates: Iterable[DiagnosticCandidate],
) -> DecisionProposal:
    """Choose maximum prior mastery entropy, ignoring slip/guess."""
    if snapshot.phase != "diagnostic":
        raise ValueError("diagnostic selector requires snapshot.phase='diagnostic'")
    candidate_tuple = tuple(candidates)
    if len({candidate.candidate_id for candidate in candidate_tuple}) != len(candidate_tuple):
        raise ValueError("candidate IDs must be unique")
    eligible, exclusions = _eligible(candidate_tuple)
    values = {candidate.candidate_id: bernoulli_entropy(candidate.p_mastery) for candidate in eligible}
    return _proposal(
        snapshot=snapshot,
        candidates=candidate_tuple,
        component_name="study_os_diagnostic_uncertainty_baseline",
        implementation="study_os.adaptive.diagnostic.propose_uncertainty_baseline",
        score_name="prior_entropy",
        score_values=values,
        exclusions=exclusions,
    )


def propose_bkt_information_gain(
    snapshot: LearnerSnapshot,
    candidates: Iterable[DiagnosticCandidate],
) -> DecisionProposal:
    """Choose maximum expected BKT information gain (Tutor-MCP-style donor mechanism)."""
    if snapshot.phase != "diagnostic":
        raise ValueError("diagnostic selector requires snapshot.phase='diagnostic'")
    candidate_tuple = tuple(candidates)
    if len({candidate.candidate_id for candidate in candidate_tuple}) != len(candidate_tuple):
        raise ValueError("candidate IDs must be unique")
    eligible, exclusions = _eligible(candidate_tuple)
    values = {candidate.candidate_id: bkt_information_gain(candidate) for candidate in eligible}
    return _proposal(
        snapshot=snapshot,
        candidates=candidate_tuple,
        component_name="tutor_mcp_style_bkt_information_gain",
        implementation="study_os.adaptive.diagnostic.propose_bkt_information_gain",
        score_name="expected_bkt_information_gain",
        score_values=values,
        exclusions=exclusions,
    )
