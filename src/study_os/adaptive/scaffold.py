"""Evidence-gated micro-controller for scaffolded learning episodes.

The controller is intentionally deterministic and persistence-free.  It may
recommend probing, remediation, assistance fading, or advancing exactly one
planned step.  It cannot award transfer or delayed mastery and it cannot use
self-report as advancement evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .contracts import ASSISTANCE_LEVELS, DecisionProposal, LearnerSnapshot, SelectedAction

SCAFFOLD_COMPONENT_VERSION = "0.1.0"
STEP_RESULTS = frozenset({"fail", "partial", "pass_supported", "pass_unaided"})


def _non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _string_tuple(values: Sequence[str], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an array of strings")
    result = tuple(values)
    if not result or any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must be unique")
    return result


def _lower_assistance(level: str) -> str:
    if level not in ASSISTANCE_LEVELS:
        raise ValueError(f"unsupported assistance level: {level}")
    number = int(level[1:])
    return f"A{max(0, number - 1)}"


@dataclass(frozen=True, slots=True)
class EpisodeStep:
    id: str
    competency_id: str
    item_ids: tuple[str, ...]
    complexity_stage: int
    entry_assistance: str
    remediation_assistance: str
    advance_requires: str = "pass_unaided"

    def __post_init__(self) -> None:
        _non_empty(self.id, "step.id")
        _non_empty(self.competency_id, "step.competency_id")
        object.__setattr__(self, "item_ids", _string_tuple(self.item_ids, "step.item_ids"))
        if isinstance(self.complexity_stage, bool) or not isinstance(self.complexity_stage, int):
            raise ValueError("step.complexity_stage must be an integer")
        if not 0 <= self.complexity_stage <= 10:
            raise ValueError("step.complexity_stage must be between 0 and 10")
        if self.entry_assistance not in ASSISTANCE_LEVELS:
            raise ValueError(f"unsupported entry assistance: {self.entry_assistance}")
        if self.remediation_assistance not in ASSISTANCE_LEVELS:
            raise ValueError(f"unsupported remediation assistance: {self.remediation_assistance}")
        if self.advance_requires != "pass_unaided":
            raise ValueError("early scaffold plans require pass_unaided to advance")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EpisodeStep":
        complexity_stage = value.get("complexity_stage")
        if isinstance(complexity_stage, bool) or not isinstance(complexity_stage, int):
            raise ValueError("step.complexity_stage must be an integer")
        return cls(
            id=str(value.get("id", "")),
            competency_id=str(value.get("competency_id", "")),
            item_ids=tuple(value.get("item_ids", ())),
            complexity_stage=complexity_stage,
            entry_assistance=str(value.get("entry_assistance", "")),
            remediation_assistance=str(value.get("remediation_assistance", "")),
            advance_requires=str(value.get("advance_requires", "")),
        )


@dataclass(frozen=True, slots=True)
class EpisodePlan:
    plan_id: str
    slice_id: str
    steps: tuple[EpisodeStep, ...]
    plan_version: str = SCAFFOLD_COMPONENT_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.plan_id, "plan_id")
        _non_empty(self.slice_id, "slice_id")
        if self.plan_version != SCAFFOLD_COMPONENT_VERSION:
            raise ValueError(f"unsupported plan_version: {self.plan_version}")
        if not self.steps:
            raise ValueError("episode plan must contain at least one step")
        step_ids = [step.id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("episode step IDs must be unique")
        stages = [step.complexity_stage for step in self.steps]
        if stages != sorted(stages):
            raise ValueError("episode complexity_stage must be non-decreasing")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EpisodePlan":
        return cls(
            plan_id=str(value.get("plan_id", "")),
            slice_id=str(value.get("slice_id", "")),
            steps=tuple(EpisodeStep.from_mapping(step) for step in value.get("steps", ())),
            plan_version=str(value.get("plan_version", "")),
        )

    def step_index(self, step_id: str) -> int:
        for index, step in enumerate(self.steps):
            if step.id == step_id:
                return index
        raise ValueError(f"unknown episode step: {step_id}")


@dataclass(frozen=True, slots=True)
class StepAssessment:
    assessment_id: str
    competency_id: str
    result: str
    assistance_level: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _non_empty(self.assessment_id, "assessment_id")
        _non_empty(self.competency_id, "competency_id")
        if self.result not in STEP_RESULTS:
            raise ValueError(
                "scaffold controller accepts only fail, partial, pass_supported, or pass_unaided behavioral results"
            )
        if self.assistance_level not in ASSISTANCE_LEVELS:
            raise ValueError(f"unsupported assistance level: {self.assistance_level}")
        object.__setattr__(self, "evidence_ids", _string_tuple(self.evidence_ids, "evidence_ids"))


def propose_scaffold_action(
    snapshot: LearnerSnapshot,
    plan: EpisodePlan,
    *,
    current_step_id: str,
    assessment: StepAssessment | None = None,
) -> DecisionProposal:
    """Return the next evidence-gated micro-action in shadow mode.

    `assessment` must be canonical behavioral evidence.  A missing assessment
    asks for a probe.  Supported success fades assistance on the same step;
    only unaided success advances, and then by at most one step.
    """

    if snapshot.phase not in {"instruction", "fading"}:
        raise ValueError("scaffold controller is limited to instruction/fading phases")
    index = plan.step_index(current_step_id)
    current = plan.steps[index]
    next_step = plan.steps[index + 1] if index + 1 < len(plan.steps) else None
    candidates = (current.id,) if next_step is None else (current.id, next_step.id)

    if assessment is None:
        selected = SelectedAction(
            candidate_id=current.id,
            action_type="probe_step",
            assistance_target=current.entry_assistance,
            learning_operation="assess",
        )
        rationale = "Current step lacks behavioral assessment evidence; probe it before changing episode state."
        expected = {
            "target_competency_id": current.competency_id,
            "item_ids": list(current.item_ids),
            "required_result_to_advance": current.advance_requires,
        }
    else:
        if assessment.competency_id != current.competency_id:
            raise ValueError("assessment competency must match the current episode step")
        if assessment.result in {"fail", "partial"}:
            selected = SelectedAction(
                candidate_id=current.id,
                action_type="remediate_step",
                assistance_target=current.remediation_assistance,
                learning_operation="remediate",
            )
            rationale = "Behavioral evidence is incomplete; remain on the same atomic target and remediate."
            expected = {
                "source_assessment_id": assessment.assessment_id,
                "source_evidence_ids": list(assessment.evidence_ids),
                "target_competency_id": current.competency_id,
                "next_required_evidence": "new behavioral assessment on the same competency",
            }
        elif assessment.result == "pass_supported":
            selected = SelectedAction(
                candidate_id=current.id,
                action_type="fade_same_step",
                assistance_target=_lower_assistance(assessment.assistance_level),
                learning_operation="fade",
            )
            rationale = "Supported success is not progression evidence; reduce assistance and retest the same target."
            expected = {
                "source_assessment_id": assessment.assessment_id,
                "source_evidence_ids": list(assessment.evidence_ids),
                "target_competency_id": current.competency_id,
                "next_required_result": "pass_unaided",
            }
        elif next_step is not None:
            selected = SelectedAction(
                candidate_id=next_step.id,
                action_type="advance_one_step",
                assistance_target=next_step.entry_assistance,
                learning_operation="advance",
            )
            rationale = "Unaided behavioral success satisfies this step gate; advance exactly one planned step."
            expected = {
                "source_assessment_id": assessment.assessment_id,
                "source_evidence_ids": list(assessment.evidence_ids),
                "completed_step_id": current.id,
                "next_step_id": next_step.id,
                "next_competency_id": next_step.competency_id,
            }
        else:
            selected = SelectedAction(
                candidate_id=current.id,
                action_type="episode_complete_candidate",
                assistance_target="A0",
                learning_operation="checkpoint",
            )
            rationale = (
                "Final instructional step passed unaided. The controller may signal episode completion, "
                "but cannot award transfer or delayed mastery."
            )
            expected = {
                "source_assessment_id": assessment.assessment_id,
                "source_evidence_ids": list(assessment.evidence_ids),
                "completed_step_id": current.id,
                "requires_separate_transfer_or_retention_evidence": True,
            }

    return DecisionProposal(
        component_name="scaffold_episode_controller",
        implementation="study_os_evidence_gated_micro_loop",
        component_version=SCAFFOLD_COMPONENT_VERSION,
        mode="shadow",
        phase=snapshot.phase,
        candidates=candidates,
        selected=selected,
        rationale=rationale,
        expected_evidence=expected,
    )
