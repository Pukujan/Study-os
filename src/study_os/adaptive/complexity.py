"""Interpretable learner-relative task-load estimates.

Authored item complexity stays multidimensional. This module combines that
vector with a learner-specific strength/readiness profile to estimate relative
load for shadow ranking. The estimate is *not* a mastery probability and is not
psychometrically calibrated; CAT/IRT remains the separate path once enough
response data exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .contracts import CandidateScore, DecisionProposal, LearnerSnapshot, SelectedAction

RELATIVE_DIFFICULTY_VERSION = "0.1.0"
SCAFFOLD_RELIEF_WEIGHT = 0.20


def _unit(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")
    result = float(value)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return result


def _level(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
        raise ValueError(f"{field_name} must be an integer from 0 to 5")
    return value


@dataclass(frozen=True, slots=True)
class ItemComplexity:
    prerequisite_depth: int
    state_variables: int
    control_flow: int
    syntax_load: int
    representation_translation: int
    surface_novelty: int
    scaffold_amount: int
    transfer_distance: int

    def __post_init__(self) -> None:
        for field_name in self.__dataclass_fields__:
            object.__setattr__(self, field_name, _level(getattr(self, field_name), field_name))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ItemComplexity":
        return cls(
            prerequisite_depth=_level(value.get("prerequisite_depth"), "prerequisite_depth"),
            state_variables=_level(value.get("state_variables"), "state_variables"),
            control_flow=_level(value.get("control_flow"), "control_flow"),
            syntax_load=_level(value.get("syntax_load"), "syntax_load"),
            representation_translation=_level(
                value.get("representation_translation"), "representation_translation"
            ),
            surface_novelty=_level(value.get("surface_novelty"), "surface_novelty"),
            scaffold_amount=_level(value.get("scaffold_amount"), "scaffold_amount"),
            transfer_distance=_level(value.get("transfer_distance"), "transfer_distance"),
        )


@dataclass(frozen=True, slots=True)
class LearnerDifficultyProfile:
    prerequisite_readiness: float
    state_reasoning: float
    control_flow_fluency: float
    syntax_fluency: float
    representation_translation: float
    novelty_tolerance: float
    transfer_fluency: float
    scaffold_support_effectiveness: float

    def __post_init__(self) -> None:
        for field_name in self.__dataclass_fields__:
            object.__setattr__(self, field_name, _unit(getattr(self, field_name), field_name))


@dataclass(frozen=True, slots=True)
class RelativeDifficultyEstimate:
    relative_load: float
    components: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class ComplexityItemCandidate:
    item_id: str
    complexity: ItemComplexity

    def __post_init__(self) -> None:
        if not isinstance(self.item_id, str) or not self.item_id.strip():
            raise ValueError("item_id must be a non-empty string")


def estimate_relative_load(
    complexity: ItemComplexity,
    profile: LearnerDifficultyProfile,
) -> RelativeDifficultyEstimate:
    """Estimate relative cognitive/implementation load while retaining causes."""

    components = {
        "prerequisite_load": (complexity.prerequisite_depth / 5.0) * (1.0 - profile.prerequisite_readiness),
        "state_load": (complexity.state_variables / 5.0) * (1.0 - profile.state_reasoning),
        "control_flow_load": (complexity.control_flow / 5.0) * (1.0 - profile.control_flow_fluency),
        "syntax_load": (complexity.syntax_load / 5.0) * (1.0 - profile.syntax_fluency),
        "translation_load": (complexity.representation_translation / 5.0) * (1.0 - profile.representation_translation),
        "novelty_load": (complexity.surface_novelty / 5.0) * (1.0 - profile.novelty_tolerance),
        "transfer_load": (complexity.transfer_distance / 5.0) * (1.0 - profile.transfer_fluency),
    }
    base = sum(components.values()) / len(components)
    scaffold_relief = (
        (complexity.scaffold_amount / 5.0)
        * profile.scaffold_support_effectiveness
        * SCAFFOLD_RELIEF_WEIGHT
    )
    relative_load = max(0.0, min(1.0, base - scaffold_relief))
    components = {**components, "scaffold_relief": -scaffold_relief, "base_load": base}
    return RelativeDifficultyEstimate(relative_load=relative_load, components=components)


def propose_relative_difficulty_fit(
    snapshot: LearnerSnapshot,
    candidates: Sequence[ComplexityItemCandidate],
    *,
    profile: LearnerDifficultyProfile,
    target_relative_load: float,
) -> DecisionProposal:
    """Rank an already-eligible item pool by closeness to target relative load."""

    if snapshot.phase not in {"instruction", "fading"}:
        raise ValueError("relative difficulty fit is initially limited to instruction/fading phases")
    target = _unit(target_relative_load, "target_relative_load")
    candidate_ids = tuple(candidate.item_id for candidate in candidates)
    if not candidate_ids:
        raise ValueError("relative difficulty fit requires at least one candidate")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("complexity candidate IDs must be unique")

    scores = []
    ranked = []
    estimates: dict[str, float] = {}
    for candidate in candidates:
        estimate = estimate_relative_load(candidate.complexity, profile)
        fit = 1.0 - abs(estimate.relative_load - target)
        estimates[candidate.item_id] = estimate.relative_load
        scores.append(
            CandidateScore(
                candidate_id=candidate.item_id,
                components={
                    "relative_load": estimate.relative_load,
                    "target_relative_load": target,
                    "fit": fit,
                    **estimate.components,
                },
                total=fit,
            )
        )
        ranked.append((fit, candidate.item_id))

    _, selected_id = max(ranked, key=lambda value: (value[0], value[1]))
    return DecisionProposal(
        component_name="learner_relative_difficulty",
        implementation="study_os_interpretable_complexity_fit",
        component_version=RELATIVE_DIFFICULTY_VERSION,
        mode="shadow",
        phase=snapshot.phase,
        candidates=candidate_ids,
        scores=tuple(scores),
        selected=SelectedAction(candidate_id=selected_id, action_type="practice_item"),
        rationale=(
            "Rank the already-eligible item pool by an interpretable learner-relative load estimate; "
            "this is a shadow heuristic, not an IRT success probability."
        ),
        expected_evidence={
            "selected_relative_load": estimates[selected_id],
            "target_relative_load": target,
            "requires_behavioral_calibration": True,
            "psychometric_probability_claimed": False,
        },
    )
