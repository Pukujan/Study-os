from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PirModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class LearnerOutcome(StrEnum):
    CORRECT = "correct"
    PARTIAL = "partial"
    INCORRECT = "incorrect"
    META = "meta"
    HINT_REQUEST = "hint_request"
    UNRESOLVED = "unresolved"


class StepKind(StrEnum):
    EXPLAIN = "explain"
    PROBE = "probe"
    CORRECT = "correct"
    VALIDATE = "validate"
    ASSEMBLE = "assemble"
    STATUS = "status"


class AssessmentKind(StrEnum):
    INTEGER = "integer"
    INTEGER_SEQUENCE = "integer_sequence"
    TEXT = "text"


class ResponseKind(StrEnum):
    NONE = "none"
    INTEGER = "integer"
    INTEGER_SEQUENCE = "integer_sequence"
    TEXT = "text"
    CODE = "code"


class RunStatus(StrEnum):
    ACTIVE = "active"
    ASSEMBLED_MASTERY_UNPROVEN = "assembled_mastery_unproven"
    COMPLETED_VALIDATED = "completed_validated"
    BLOCKED = "blocked"


class ExpansionKind(StrEnum):
    WHY = "why"
    EASIER_EXAMPLE = "easier_example"
    MORE_DETAIL = "more_detail"
    REPEAT_REPRESENTATION = "repeat_representation"
    CLARIFY_TERM = "clarify_term"


class RepresentationSpec(PirModel):
    representation_id: str = Field(min_length=1)
    learner_visible_markdown: str = Field(min_length=1)
    visible_components: tuple[str, ...] = ()
    # Optional metadata for assets that opt into the deterministic
    # learner-facing presentation contract. Legacy assets remain valid.
    relation_id: str | None = Field(default=None, min_length=1)
    check_question: str | None = Field(default=None, min_length=1)


class VariableBinding(PirModel):
    name: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    role: str = Field(min_length=1)


class PresentationContract(PirModel):
    """Data contract for deterministic learner-visible teaching turns."""

    required_variable_map: tuple[VariableBinding, ...] = Field(min_length=1)
    forbidden_variable_names: tuple[str, ...] = ()
    visual_required: bool = True
    visual_before_explanation: bool = True
    max_relations_per_turn: int = Field(default=1, ge=1)
    max_nonempty_lines: int = Field(default=12, ge=1)
    tiny_check_required: bool = True
    render_mode: Literal["verbatim"] = "verbatim"


class TransitionSpec(PirModel):
    outcome: LearnerOutcome | None = None
    next_step_id: str | None = Field(default=None, min_length=1)
    exit_status: RunStatus | None = None

    @model_validator(mode="after")
    def require_exactly_one_target(self) -> TransitionSpec:
        if (self.next_step_id is None) == (self.exit_status is None):
            raise ValueError("transition requires exactly one of next_step_id or exit_status")
        if self.exit_status == RunStatus.ACTIVE:
            raise ValueError("transition exit_status may not be active")
        return self


class TeachingStep(PirModel):
    step_id: str = Field(min_length=1)
    kind: StepKind
    representation_id: str = Field(min_length=1)
    required_components: tuple[str, ...] = ()
    forbidden_components: tuple[str, ...] = ()
    response_kind: ResponseKind = ResponseKind.NONE
    assessment_id: str | None = Field(default=None, min_length=1)
    automatic_transition: TransitionSpec | None = None
    outcome_transitions: tuple[TransitionSpec, ...] = ()

    @model_validator(mode="after")
    def validate_transition_shape(self) -> TeachingStep:
        if self.kind == StepKind.PROBE:
            if self.assessment_id is None:
                raise ValueError("probe step requires assessment_id")
            if self.response_kind == ResponseKind.NONE:
                raise ValueError("probe step requires a response kind")
            if self.automatic_transition is not None:
                raise ValueError("probe step cannot have an automatic transition")
            if not self.outcome_transitions:
                raise ValueError("probe step requires outcome transitions")
            if any(transition.outcome is None for transition in self.outcome_transitions):
                raise ValueError("probe outcome transitions require an outcome")
        else:
            if self.assessment_id is not None:
                raise ValueError("non-probe step cannot have assessment_id")
            if self.response_kind != ResponseKind.NONE:
                raise ValueError("non-probe step cannot require a response")
            if self.outcome_transitions:
                raise ValueError("non-probe step cannot have outcome transitions")
            if self.automatic_transition is None:
                raise ValueError("non-probe step requires an automatic transition")
            if self.automatic_transition.outcome is not None:
                raise ValueError("automatic transition cannot declare learner outcome")
        return self


class AssessmentSpec(PirModel):
    assessment_id: str = Field(min_length=1)
    kind: AssessmentKind
    expected_values: tuple[int, ...] = ()
    partial_values: tuple[int, ...] = ()
    expected_text: tuple[str, ...] = ()
    partial_text: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_expected_shape(self) -> AssessmentSpec:
        if self.kind == AssessmentKind.INTEGER:
            if len(self.expected_values) != 1 or self.expected_text or self.partial_text:
                raise ValueError("integer assessment requires exactly one expected integer")
        elif self.kind == AssessmentKind.INTEGER_SEQUENCE:
            if not self.expected_values or self.expected_text or self.partial_text:
                raise ValueError("integer-sequence assessment requires expected integer values")
        else:
            if not self.expected_text or self.expected_values or self.partial_values:
                raise ValueError(
                    "text assessment requires expected_text and optional partial_text only"
                )
        return self


class ExpansionSpec(PirModel):
    step_id: str = Field(min_length=1)
    kind: ExpansionKind
    representation_id: str = Field(min_length=1)


class CanonicalTeachingAsset(PirModel):
    schema_version: str = Field(pattern=r"^study-os\.canonical-teaching-asset\.v0$")
    canonical_problem_id: str = Field(min_length=1)
    canonical_pir_revision: str = Field(min_length=1)
    source_pir_repository: str = Field(min_length=1)
    source_pir_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    controller_revision: str = Field(min_length=1)
    renderer_revision: str = Field(min_length=1)
    assessment_revision: str = Field(min_length=1)
    entry_step_id: str = Field(min_length=1)
    aliases: tuple[str, ...] = ()
    representations: tuple[RepresentationSpec, ...] = Field(min_length=1)
    steps: tuple[TeachingStep, ...] = Field(min_length=1)
    assessments: tuple[AssessmentSpec, ...] = ()
    expansions: tuple[ExpansionSpec, ...] = ()
    presentation_contract: PresentationContract | None = None


class ProblemRunState(PirModel):
    schema_version: str = Field(pattern=r"^study-os\.problem-run-state\.v0$")
    problem_run_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    canonical_problem_id: str = Field(min_length=1)
    canonical_pir_revision: str = Field(min_length=1)
    controller_revision: str = Field(min_length=1)
    renderer_revision: str = Field(min_length=1)
    assessment_revision: str = Field(min_length=1)
    current_step_id: str | None = Field(default=None, min_length=1)
    status: RunStatus
    transition_seq: int = Field(ge=0)


class TeachingTurn(PirModel):
    schema_version: str = Field(pattern=r"^study-os\.teaching-turn\.v0$")
    problem_run_id: str = Field(min_length=1)
    turn_id: str = Field(min_length=1)
    canonical_step_id: str = Field(min_length=1)
    turn_kind: StepKind
    representation_id: str = Field(min_length=1)
    learner_visible_markdown: str = Field(min_length=1)
    response_kind: ResponseKind
    allowed_actions: tuple[str, ...] = ()
    run_status: RunStatus
    relation_id: str | None = Field(default=None, min_length=1)
    render_mode: Literal["verbatim"] = "verbatim"


class TeachingBundle(PirModel):
    schema_version: str = Field(pattern=r"^study-os\.teaching-bundle\.v0$")
    problem_run_id: str = Field(min_length=1)
    turns: tuple[TeachingTurn, ...] = Field(min_length=1)
    response_turn_id: str | None = Field(default=None, min_length=1)
    run_status: RunStatus
    presentation_contract: PresentationContract | None = None
