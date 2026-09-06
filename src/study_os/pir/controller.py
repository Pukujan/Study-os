from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    AssessmentKind,
    AssessmentSpec,
    CanonicalTeachingAsset,
    ExpansionKind,
    LearnerOutcome,
    ProblemRunState,
    RepresentationSpec,
    ResponseKind,
    RunStatus,
    StepKind,
    TeachingBundle,
    TeachingStep,
    TeachingTurn,
    TransitionSpec,
)


class AssetViolationCode(StrEnum):
    DUPLICATE_REPRESENTATION = "DUPLICATE_REPRESENTATION"
    DUPLICATE_STEP = "DUPLICATE_STEP"
    DUPLICATE_ASSESSMENT = "DUPLICATE_ASSESSMENT"
    DUPLICATE_EXPANSION = "DUPLICATE_EXPANSION"
    UNKNOWN_ENTRY_STEP = "UNKNOWN_ENTRY_STEP"
    UNKNOWN_REPRESENTATION = "UNKNOWN_REPRESENTATION"
    REQUIRED_COMPONENT_MISSING = "REQUIRED_COMPONENT_MISSING"
    FORBIDDEN_COMPONENT_VISIBLE = "FORBIDDEN_COMPONENT_VISIBLE"
    UNKNOWN_ASSESSMENT = "UNKNOWN_ASSESSMENT"
    RESPONSE_KIND_MISMATCH = "RESPONSE_KIND_MISMATCH"
    UNKNOWN_TRANSITION_TARGET = "UNKNOWN_TRANSITION_TARGET"
    DUPLICATE_OUTCOME_ROUTE = "DUPLICATE_OUTCOME_ROUTE"
    MISSING_OUTCOME_ROUTE = "MISSING_OUTCOME_ROUTE"
    UNKNOWN_EXPANSION_STEP = "UNKNOWN_EXPANSION_STEP"
    UNKNOWN_EXPANSION_REPRESENTATION = "UNKNOWN_EXPANSION_REPRESENTATION"


class AssetViolation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    code: AssetViolationCode
    detail: str = Field(min_length=1)


@dataclass(frozen=True)
class ResponseResult:
    outcome: LearnerOutcome
    state: ProblemRunState
    bundle: TeachingBundle


def _duplicates(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if values.count(value) > 1}))


def _step_map(asset: CanonicalTeachingAsset) -> dict[str, TeachingStep]:
    return {step.step_id: step for step in asset.steps}


def _representation_map(asset: CanonicalTeachingAsset) -> dict[str, RepresentationSpec]:
    return {
        representation.representation_id: representation
        for representation in asset.representations
    }


def _assessment_map(asset: CanonicalTeachingAsset) -> dict[str, AssessmentSpec]:
    return {assessment.assessment_id: assessment for assessment in asset.assessments}


def validate_asset(asset: CanonicalTeachingAsset) -> tuple[AssetViolation, ...]:
    violations: list[AssetViolation] = []

    representation_ids = tuple(item.representation_id for item in asset.representations)
    step_ids = tuple(step.step_id for step in asset.steps)
    assessment_ids = tuple(item.assessment_id for item in asset.assessments)
    expansion_keys = tuple(f"{item.step_id}:{item.kind.value}" for item in asset.expansions)

    for duplicate in _duplicates(representation_ids):
        violations.append(
            AssetViolation(
                code=AssetViolationCode.DUPLICATE_REPRESENTATION,
                detail=f"duplicate representation: {duplicate}",
            )
        )
    for duplicate in _duplicates(step_ids):
        violations.append(
            AssetViolation(
                code=AssetViolationCode.DUPLICATE_STEP,
                detail=f"duplicate step: {duplicate}",
            )
        )
    for duplicate in _duplicates(assessment_ids):
        violations.append(
            AssetViolation(
                code=AssetViolationCode.DUPLICATE_ASSESSMENT,
                detail=f"duplicate assessment: {duplicate}",
            )
        )
    for duplicate in _duplicates(expansion_keys):
        violations.append(
            AssetViolation(
                code=AssetViolationCode.DUPLICATE_EXPANSION,
                detail=f"duplicate expansion: {duplicate}",
            )
        )

    step_by_id = _step_map(asset)
    representation_by_id = _representation_map(asset)
    assessment_by_id = _assessment_map(asset)

    if asset.entry_step_id not in step_by_id:
        violations.append(
            AssetViolation(
                code=AssetViolationCode.UNKNOWN_ENTRY_STEP,
                detail=f"unknown entry step: {asset.entry_step_id}",
            )
        )

    for step in asset.steps:
        representation = representation_by_id.get(step.representation_id)
        if representation is None:
            violations.append(
                AssetViolation(
                    code=AssetViolationCode.UNKNOWN_REPRESENTATION,
                    detail=(
                        f"step {step.step_id} references unknown representation "
                        f"{step.representation_id}"
                    ),
                )
            )
        else:
            visible = set(representation.visible_components)
            for component in step.required_components:
                if component not in visible:
                    violations.append(
                        AssetViolation(
                            code=AssetViolationCode.REQUIRED_COMPONENT_MISSING,
                            detail=f"step {step.step_id} is missing required {component}",
                        )
                    )
            for component in step.forbidden_components:
                if component in visible:
                    violations.append(
                        AssetViolation(
                            code=AssetViolationCode.FORBIDDEN_COMPONENT_VISIBLE,
                            detail=f"step {step.step_id} exposes forbidden {component}",
                        )
                    )

        if step.kind == StepKind.PROBE:
            assessment = assessment_by_id.get(step.assessment_id or "")
            if assessment is None:
                violations.append(
                    AssetViolation(
                        code=AssetViolationCode.UNKNOWN_ASSESSMENT,
                        detail=f"probe {step.step_id} references unknown assessment",
                    )
                )
            else:
                valid_response_kinds = {
                    AssessmentKind.INTEGER: {ResponseKind.INTEGER},
                    AssessmentKind.INTEGER_SEQUENCE: {ResponseKind.INTEGER_SEQUENCE},
                    AssessmentKind.TEXT: {ResponseKind.TEXT, ResponseKind.CODE},
                }[assessment.kind]
                if step.response_kind not in valid_response_kinds:
                    violations.append(
                        AssetViolation(
                            code=AssetViolationCode.RESPONSE_KIND_MISMATCH,
                            detail=(
                                f"step {step.step_id} response kind {step.response_kind.value} "
                                f"does not match {assessment.kind.value} assessment"
                            ),
                        )
                    )

                outcomes = tuple(
                    transition.outcome
                    for transition in step.outcome_transitions
                    if transition.outcome is not None
                )
                for duplicate in _duplicates(tuple(outcome.value for outcome in outcomes)):
                    violations.append(
                        AssetViolation(
                            code=AssetViolationCode.DUPLICATE_OUTCOME_ROUTE,
                            detail=f"step {step.step_id} duplicates outcome route {duplicate}",
                        )
                    )
                required_outcomes = {LearnerOutcome.CORRECT, LearnerOutcome.INCORRECT}
                if assessment.partial_values or assessment.partial_text:
                    required_outcomes.add(LearnerOutcome.PARTIAL)
                for outcome in sorted(required_outcomes, key=lambda item: item.value):
                    if outcome not in outcomes:
                        violations.append(
                            AssetViolation(
                                code=AssetViolationCode.MISSING_OUTCOME_ROUTE,
                                detail=f"step {step.step_id} lacks {outcome.value} route",
                            )
                        )

        transitions = (
            step.outcome_transitions
            if step.kind == StepKind.PROBE
            else (() if step.automatic_transition is None else (step.automatic_transition,))
        )
        for transition in transitions:
            if transition.next_step_id is not None and transition.next_step_id not in step_by_id:
                violations.append(
                    AssetViolation(
                        code=AssetViolationCode.UNKNOWN_TRANSITION_TARGET,
                        detail=(
                            f"step {step.step_id} targets unknown step "
                            f"{transition.next_step_id}"
                        ),
                    )
                )

    for expansion in asset.expansions:
        if expansion.step_id not in step_by_id:
            violations.append(
                AssetViolation(
                    code=AssetViolationCode.UNKNOWN_EXPANSION_STEP,
                    detail=f"expansion references unknown step {expansion.step_id}",
                )
            )
        if expansion.representation_id not in representation_by_id:
            violations.append(
                AssetViolation(
                    code=AssetViolationCode.UNKNOWN_EXPANSION_REPRESENTATION,
                    detail=(
                        f"expansion {expansion.step_id}:{expansion.kind.value} references "
                        f"unknown representation {expansion.representation_id}"
                    ),
                )
            )

    return tuple(violations)


def _parse_integer(response: str) -> tuple[int, ...]:
    text = response.strip()
    if re.fullmatch(r"[+-]?\d+", text) is None:
        raise ValueError("response is not a single integer")
    return (int(text),)


def _parse_integer_sequence(response: str) -> tuple[int, ...]:
    normalized = response.strip()
    for character in "[],(),":
        normalized = normalized.replace(character, " ")
    tokens = normalized.split()
    if not tokens:
        raise ValueError("response does not contain an integer sequence")

    values: list[int] = []
    for token in tokens:
        if re.fullmatch(r"[+-]?\d+", token) is None:
            raise ValueError("response is not a supported integer sequence")
        values.append(int(token))
    return tuple(values)


def _normalize_text(response: str) -> str:
    return re.sub(r"\s+", "", response.strip())


def _matches_partial(spec: AssessmentSpec, response: str) -> bool:
    if not spec.partial_values:
        return False
    try:
        observed = _parse_integer_sequence(response)
    except ValueError:
        return False
    return observed == spec.partial_values


def classify_response(spec: AssessmentSpec, response: str) -> LearnerOutcome:
    if spec.kind == AssessmentKind.TEXT:
        observed_text = _normalize_text(response)
        if any(observed_text == _normalize_text(expected) for expected in spec.expected_text):
            return LearnerOutcome.CORRECT
        if any(observed_text == _normalize_text(partial) for partial in spec.partial_text):
            return LearnerOutcome.PARTIAL
        return LearnerOutcome.INCORRECT

    try:
        observed = (
            _parse_integer(response)
            if spec.kind == AssessmentKind.INTEGER
            else _parse_integer_sequence(response)
        )
    except ValueError:
        if _matches_partial(spec, response):
            return LearnerOutcome.PARTIAL
        raise
    if observed == spec.expected_values:
        return LearnerOutcome.CORRECT
    if _matches_partial(spec, response):
        return LearnerOutcome.PARTIAL
    return LearnerOutcome.INCORRECT


def _require_valid_asset(asset: CanonicalTeachingAsset) -> None:
    violations = validate_asset(asset)
    if violations:
        codes = ", ".join(violation.code.value for violation in violations)
        raise ValueError(f"canonical teaching asset is invalid: {codes}")


def _require_matching_state(asset: CanonicalTeachingAsset, state: ProblemRunState) -> None:
    expected = (
        asset.canonical_problem_id,
        asset.canonical_pir_revision,
        asset.controller_revision,
        asset.renderer_revision,
        asset.assessment_revision,
    )
    observed = (
        state.canonical_problem_id,
        state.canonical_pir_revision,
        state.controller_revision,
        state.renderer_revision,
        state.assessment_revision,
    )
    if observed != expected:
        raise ValueError("problem-run revision tuple does not match canonical asset")


def _turn_id(state: ProblemRunState, step_id: str) -> str:
    return f"{state.problem_run_id}:{state.transition_seq}:{step_id}"


def _make_turn(
    asset: CanonicalTeachingAsset,
    state: ProblemRunState,
    step: TeachingStep,
    *,
    turn_id: str | None = None,
) -> TeachingTurn:
    representation = _representation_map(asset)[step.representation_id]
    actions = (
        ("submit_response", "request_expansion")
        if step.kind == StepKind.PROBE
        else ()
    )
    return TeachingTurn(
        schema_version="study-os.teaching-turn.v0",
        problem_run_id=state.problem_run_id,
        turn_id=turn_id or _turn_id(state, step.step_id),
        canonical_step_id=step.step_id,
        turn_kind=step.kind,
        representation_id=representation.representation_id,
        learner_visible_markdown=representation.learner_visible_markdown,
        response_kind=step.response_kind,
        allowed_actions=actions,
        run_status=state.status,
    )


def _apply_transition(
    state: ProblemRunState,
    transition: TransitionSpec,
) -> ProblemRunState:
    if transition.exit_status is not None:
        return state.model_copy(
            update={
                "current_step_id": None,
                "status": transition.exit_status,
                "transition_seq": state.transition_seq + 1,
            }
        )
    if transition.next_step_id is None:
        raise ValueError("transition has no target")
    return state.model_copy(
        update={
            "current_step_id": transition.next_step_id,
            "transition_seq": state.transition_seq + 1,
        }
    )


def build_interaction_bundle(
    asset: CanonicalTeachingAsset,
    state: ProblemRunState,
) -> tuple[ProblemRunState, TeachingBundle]:
    _require_valid_asset(asset)
    _require_matching_state(asset, state)
    if state.status != RunStatus.ACTIVE:
        raise ValueError("interaction bundle requires an active problem run")

    step_by_id = _step_map(asset)
    current = state
    turns: list[TeachingTurn] = []
    auto_seen: set[str] = set()

    while True:
        if current.current_step_id is None:
            raise ValueError("active problem run has no current step")
        step = step_by_id.get(current.current_step_id)
        if step is None:
            raise ValueError(f"problem run references unknown step {current.current_step_id}")
        turn = _make_turn(asset, current, step)
        turns.append(turn)

        if step.kind == StepKind.PROBE:
            return current, TeachingBundle(
                schema_version="study-os.teaching-bundle.v0",
                problem_run_id=current.problem_run_id,
                turns=tuple(turns),
                response_turn_id=turn.turn_id,
                run_status=current.status,
            )

        if step.step_id in auto_seen:
            raise ValueError("automatic teaching-step cycle detected")
        auto_seen.add(step.step_id)
        if step.automatic_transition is None:
            raise ValueError("non-probe step has no automatic transition")
        current = _apply_transition(current, step.automatic_transition)
        if current.status != RunStatus.ACTIVE:
            return current, TeachingBundle(
                schema_version="study-os.teaching-bundle.v0",
                problem_run_id=current.problem_run_id,
                turns=tuple(turns),
                response_turn_id=None,
                run_status=current.status,
            )


def start_run(
    asset: CanonicalTeachingAsset,
    *,
    problem_run_id: str,
    subject_id: str,
    session_id: str,
) -> tuple[ProblemRunState, TeachingBundle]:
    _require_valid_asset(asset)
    state = ProblemRunState(
        schema_version="study-os.problem-run-state.v0",
        problem_run_id=problem_run_id,
        subject_id=subject_id,
        session_id=session_id,
        canonical_problem_id=asset.canonical_problem_id,
        canonical_pir_revision=asset.canonical_pir_revision,
        controller_revision=asset.controller_revision,
        renderer_revision=asset.renderer_revision,
        assessment_revision=asset.assessment_revision,
        current_step_id=asset.entry_step_id,
        status=RunStatus.ACTIVE,
        transition_seq=0,
    )
    return build_interaction_bundle(asset, state)


def submit_response(
    asset: CanonicalTeachingAsset,
    state: ProblemRunState,
    *,
    turn_id: str,
    response: str,
) -> ResponseResult:
    _require_valid_asset(asset)
    _require_matching_state(asset, state)
    if state.status != RunStatus.ACTIVE or state.current_step_id is None:
        raise ValueError("response requires an active problem run")

    step = _step_map(asset).get(state.current_step_id)
    if step is None or step.kind != StepKind.PROBE:
        raise ValueError("current problem-run step is not a probe")
    if turn_id != _turn_id(state, step.step_id):
        raise ValueError("response turn_id is stale or does not match current step")

    assessment = _assessment_map(asset).get(step.assessment_id or "")
    if assessment is None:
        raise ValueError("current probe has no assessment")
    outcome = classify_response(assessment, response)
    routes = tuple(
        transition
        for transition in step.outcome_transitions
        if transition.outcome == outcome
    )
    if len(routes) != 1:
        raise ValueError(f"no unique {outcome.value} route for current probe")

    next_state = _apply_transition(state, routes[0])
    if next_state.status != RunStatus.ACTIVE:
        terminal_turn = TeachingTurn(
            schema_version="study-os.teaching-turn.v0",
            problem_run_id=next_state.problem_run_id,
            turn_id=f"{next_state.problem_run_id}:{next_state.transition_seq}:status",
            canonical_step_id=step.step_id,
            turn_kind=StepKind.STATUS,
            representation_id="status",
            learner_visible_markdown=(
                "The reviewed lesson frontier is assembled. Independent mastery remains unproven."
                if next_state.status == RunStatus.ASSEMBLED_MASTERY_UNPROVEN
                else f"Problem run status: {next_state.status.value}."
            ),
            response_kind=ResponseKind.NONE,
            allowed_actions=(),
            run_status=next_state.status,
        )
        bundle = TeachingBundle(
            schema_version="study-os.teaching-bundle.v0",
            problem_run_id=next_state.problem_run_id,
            turns=(terminal_turn,),
            response_turn_id=None,
            run_status=next_state.status,
        )
        return ResponseResult(outcome=outcome, state=next_state, bundle=bundle)

    advanced_state, bundle = build_interaction_bundle(asset, next_state)
    return ResponseResult(outcome=outcome, state=advanced_state, bundle=bundle)


def build_expansion_bundle(
    asset: CanonicalTeachingAsset,
    state: ProblemRunState,
    *,
    turn_id: str,
    kind: ExpansionKind,
) -> TeachingBundle:
    _require_valid_asset(asset)
    _require_matching_state(asset, state)
    if state.status != RunStatus.ACTIVE or state.current_step_id is None:
        raise ValueError("expansion requires an active problem run")

    step = _step_map(asset).get(state.current_step_id)
    if step is None or step.kind != StepKind.PROBE:
        raise ValueError("expansion is available only for the current probe")
    if turn_id != _turn_id(state, step.step_id):
        raise ValueError("expansion turn_id is stale or does not match current step")

    matches = tuple(
        expansion
        for expansion in asset.expansions
        if expansion.step_id == step.step_id and expansion.kind == kind
    )
    if len(matches) != 1:
        raise ValueError(f"no unique {kind.value} expansion for current probe")
    expansion = matches[0]
    representation = _representation_map(asset)[expansion.representation_id]
    expansion_turn = TeachingTurn(
        schema_version="study-os.teaching-turn.v0",
        problem_run_id=state.problem_run_id,
        turn_id=f"{turn_id}:expansion:{kind.value}",
        canonical_step_id=step.step_id,
        turn_kind=StepKind.EXPLAIN,
        representation_id=representation.representation_id,
        learner_visible_markdown=representation.learner_visible_markdown,
        response_kind=ResponseKind.NONE,
        allowed_actions=(),
        run_status=state.status,
    )
    probe_turn = _make_turn(asset, state, step, turn_id=turn_id)
    return TeachingBundle(
        schema_version="study-os.teaching-bundle.v0",
        problem_run_id=state.problem_run_id,
        turns=(expansion_turn, probe_turn),
        response_turn_id=turn_id,
        run_status=state.status,
    )
