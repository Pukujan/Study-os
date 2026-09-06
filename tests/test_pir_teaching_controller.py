from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from study_os.pir import (
    AssessmentKind,
    AssessmentSpec,
    AssetViolationCode,
    CanonicalTeachingAsset,
    ExpansionKind,
    ExpansionSpec,
    LearnerOutcome,
    RepresentationSpec,
    ResponseKind,
    RunStatus,
    StepKind,
    TeachingStep,
    TransitionSpec,
    build_expansion_bundle,
    classify_response,
    start_run,
    submit_response,
    validate_asset,
)


PIR_COMMIT = "43599ff8ed75bd7ceeab980d078e3a2570c7725d"


def asset() -> CanonicalTeachingAsset:
    return CanonicalTeachingAsset(
        schema_version="study-os.canonical-teaching-asset.v0",
        canonical_problem_id="sliding-window.test-slice.v0",
        canonical_pir_revision="sep4.i-sum.test.v0",
        source_pir_repository="Pukujan/study-os-pedagogical-IR",
        source_pir_commit=PIR_COMMIT,
        controller_revision="study-os.pir-controller.v0",
        renderer_revision="study-os.markdown-renderer.v0",
        assessment_revision="study-os.pir-assessment.v0",
        entry_step_id="intro",
        aliases=("sliding window test",),
        representations=(
            RepresentationSpec(
                representation_id="r.intro",
                learner_visible_markdown=(
                    "index: 0 1 2 3 4\nvalue: 4 7 [2] [6] 1\n"
                    "The box starts at i = 2 and k = 2."
                ),
                visible_components=("problem_anchor", "index_row", "numbers_row", "box"),
            ),
            RepresentationSpec(
                representation_id="r.sum",
                learner_visible_markdown=(
                    "index: 0 1 2 3 4\nvalue: 4 7 [2] [6] 1\n"
                    "What is sum[i=2]?"
                ),
                visible_components=(
                    "problem_anchor",
                    "index_row",
                    "numbers_row",
                    "box",
                    "sum_i",
                ),
            ),
            RepresentationSpec(
                representation_id="r.partial",
                learner_visible_markdown=(
                    "Those are the right numbers: 2 and 6. Keep the same box and finish only "
                    "the arithmetic."
                ),
                visible_components=(
                    "problem_anchor",
                    "index_row",
                    "numbers_row",
                    "box",
                    "sum_i",
                ),
            ),
            RepresentationSpec(
                representation_id="r.wrong",
                learner_visible_markdown=(
                    "Keep the same i = 2, k = 2 box. Recheck which values are inside it."
                ),
                visible_components=(
                    "problem_anchor",
                    "index_row",
                    "numbers_row",
                    "box",
                    "sum_i",
                ),
            ),
            RepresentationSpec(
                representation_id="r.final",
                learner_visible_markdown="sum[i=2] = 2 + 6 = 8",
                visible_components=(
                    "problem_anchor",
                    "index_row",
                    "numbers_row",
                    "box",
                    "sum_i",
                ),
            ),
            RepresentationSpec(
                representation_id="r.why",
                learner_visible_markdown=(
                    "i marks where the box begins. With i = 2 and k = 2, the box contains "
                    "the values at indexes 2 and 3."
                ),
                visible_components=(
                    "problem_anchor",
                    "index_row",
                    "numbers_row",
                    "box",
                    "sum_i",
                ),
            ),
        ),
        assessments=(
            AssessmentSpec(
                assessment_id="a.sum",
                kind=AssessmentKind.INTEGER,
                expected_values=(8,),
                partial_values=(2, 6),
            ),
            AssessmentSpec(
                assessment_id="a.arithmetic",
                kind=AssessmentKind.INTEGER,
                expected_values=(8,),
            ),
        ),
        steps=(
            TeachingStep(
                step_id="intro",
                kind=StepKind.EXPLAIN,
                representation_id="r.intro",
                required_components=("index_row", "numbers_row", "box"),
                automatic_transition=TransitionSpec(next_step_id="sum_probe"),
            ),
            TeachingStep(
                step_id="sum_probe",
                kind=StepKind.PROBE,
                representation_id="r.sum",
                required_components=("index_row", "numbers_row", "box", "sum_i"),
                response_kind=ResponseKind.INTEGER,
                assessment_id="a.sum",
                outcome_transitions=(
                    TransitionSpec(
                        outcome=LearnerOutcome.CORRECT,
                        next_step_id="final",
                    ),
                    TransitionSpec(
                        outcome=LearnerOutcome.PARTIAL,
                        next_step_id="partial_explain",
                    ),
                    TransitionSpec(
                        outcome=LearnerOutcome.INCORRECT,
                        next_step_id="wrong_explain",
                    ),
                ),
            ),
            TeachingStep(
                step_id="partial_explain",
                kind=StepKind.CORRECT,
                representation_id="r.partial",
                required_components=("index_row", "numbers_row", "box", "sum_i"),
                automatic_transition=TransitionSpec(next_step_id="arithmetic_probe"),
            ),
            TeachingStep(
                step_id="arithmetic_probe",
                kind=StepKind.PROBE,
                representation_id="r.sum",
                required_components=("index_row", "numbers_row", "box", "sum_i"),
                response_kind=ResponseKind.INTEGER,
                assessment_id="a.arithmetic",
                outcome_transitions=(
                    TransitionSpec(
                        outcome=LearnerOutcome.CORRECT,
                        next_step_id="final",
                    ),
                    TransitionSpec(
                        outcome=LearnerOutcome.INCORRECT,
                        next_step_id="partial_explain",
                    ),
                ),
            ),
            TeachingStep(
                step_id="wrong_explain",
                kind=StepKind.CORRECT,
                representation_id="r.wrong",
                required_components=("index_row", "numbers_row", "box", "sum_i"),
                automatic_transition=TransitionSpec(next_step_id="sum_probe"),
            ),
            TeachingStep(
                step_id="final",
                kind=StepKind.ASSEMBLE,
                representation_id="r.final",
                required_components=("index_row", "numbers_row", "box", "sum_i"),
                automatic_transition=TransitionSpec(
                    exit_status=RunStatus.ASSEMBLED_MASTERY_UNPROVEN
                ),
            ),
        ),
        expansions=(
            ExpansionSpec(
                step_id="sum_probe",
                kind=ExpansionKind.WHY,
                representation_id="r.why",
            ),
        ),
    )


def test_valid_asset_passes_validation() -> None:
    assert validate_asset(asset()) == ()


def test_start_batches_automatic_intro_then_stops_at_probe() -> None:
    state, bundle = start_run(
        asset(), problem_run_id="run-1", subject_id="subject-1", session_id="session-1"
    )

    assert state.current_step_id == "sum_probe"
    assert state.transition_seq == 1
    assert [turn.canonical_step_id for turn in bundle.turns] == ["intro", "sum_probe"]
    assert bundle.response_turn_id == "run-1:1:sum_probe"
    assert bundle.turns[-1].allowed_actions == ("submit_response", "request_expansion")


def test_historical_box_contents_route_partial_not_incorrect() -> None:
    state, bundle = start_run(
        asset(), problem_run_id="run-1", subject_id="subject-1", session_id="session-1"
    )
    result = submit_response(
        asset(), state, turn_id=bundle.response_turn_id or "", response="2 6"
    )

    assert result.outcome == LearnerOutcome.PARTIAL
    assert result.state.current_step_id == "arithmetic_probe"
    assert [turn.canonical_step_id for turn in result.bundle.turns] == [
        "partial_explain",
        "arithmetic_probe",
    ]


def test_partial_arithmetic_then_correct_ends_mastery_unproven() -> None:
    state, bundle = start_run(
        asset(), problem_run_id="run-1", subject_id="subject-1", session_id="session-1"
    )
    partial = submit_response(
        asset(), state, turn_id=bundle.response_turn_id or "", response="[2, 6]"
    )
    correct = submit_response(
        asset(),
        partial.state,
        turn_id=partial.bundle.response_turn_id or "",
        response="8",
    )

    assert correct.outcome == LearnerOutcome.CORRECT
    assert correct.state.status == RunStatus.ASSEMBLED_MASTERY_UNPROVEN
    assert correct.state.current_step_id is None
    assert correct.bundle.run_status == RunStatus.ASSEMBLED_MASTERY_UNPROVEN
    assert correct.bundle.turns[-1].canonical_step_id == "final"


def test_direct_correct_response_can_finish_without_partial_repair() -> None:
    state, bundle = start_run(
        asset(), problem_run_id="run-2", subject_id="subject-1", session_id="session-1"
    )
    result = submit_response(
        asset(), state, turn_id=bundle.response_turn_id or "", response="8"
    )

    assert result.outcome == LearnerOutcome.CORRECT
    assert result.state.status == RunStatus.ASSEMBLED_MASTERY_UNPROVEN


def test_wrong_response_retries_same_probe_after_localized_correction() -> None:
    state, bundle = start_run(
        asset(), problem_run_id="run-3", subject_id="subject-1", session_id="session-1"
    )
    result = submit_response(
        asset(), state, turn_id=bundle.response_turn_id or "", response="9"
    )

    assert result.outcome == LearnerOutcome.INCORRECT
    assert result.state.current_step_id == "sum_probe"
    assert [turn.canonical_step_id for turn in result.bundle.turns] == [
        "wrong_explain",
        "sum_probe",
    ]


def test_stale_turn_cannot_advance_problem_run() -> None:
    state, _ = start_run(
        asset(), problem_run_id="run-4", subject_id="subject-1", session_id="session-1"
    )
    with pytest.raises(ValueError, match="stale"):
        submit_response(asset(), state, turn_id="run-4:0:intro", response="8")


def test_expansion_does_not_advance_state_and_repeats_same_probe() -> None:
    state, bundle = start_run(
        asset(), problem_run_id="run-5", subject_id="subject-1", session_id="session-1"
    )
    expanded = build_expansion_bundle(
        asset(),
        state,
        turn_id=bundle.response_turn_id or "",
        kind=ExpansionKind.WHY,
    )

    assert state.current_step_id == "sum_probe"
    assert state.transition_seq == 1
    assert expanded.response_turn_id == bundle.response_turn_id
    assert [turn.canonical_step_id for turn in expanded.turns] == ["sum_probe", "sum_probe"]
    assert "i marks where the box begins" in expanded.turns[0].learner_visible_markdown


def test_renderer_safe_bundle_does_not_expose_controller_oracle_fields() -> None:
    _, bundle = start_run(
        asset(), problem_run_id="run-6", subject_id="subject-1", session_id="session-1"
    )
    rendered = bundle.model_dump_json()

    assert "expected_values" not in rendered
    assert "partial_values" not in rendered
    assert "assessment_id" not in rendered
    assert '"8"' not in json.dumps(bundle.model_dump())


def test_representation_drop_is_rejected_by_asset_validation() -> None:
    original = asset()
    broken_representation = original.representations[1].model_copy(
        update={"visible_components": ("problem_anchor", "numbers_row", "sum_i")}
    )
    broken = original.model_copy(
        update={
            "representations": (
                original.representations[0],
                broken_representation,
                *original.representations[2:],
            )
        }
    )

    codes = {violation.code for violation in validate_asset(broken)}
    assert AssetViolationCode.REQUIRED_COMPONENT_MISSING in codes


def test_duplicate_outcome_route_is_rejected() -> None:
    original = asset()
    probe = original.steps[1]
    broken_probe = probe.model_copy(
        update={
            "outcome_transitions": (
                *probe.outcome_transitions,
                TransitionSpec(
                    outcome=LearnerOutcome.CORRECT,
                    next_step_id="final",
                ),
            )
        }
    )
    broken = original.model_copy(
        update={"steps": (original.steps[0], broken_probe, *original.steps[2:])}
    )

    codes = {violation.code for violation in validate_asset(broken)}
    assert AssetViolationCode.DUPLICATE_OUTCOME_ROUTE in codes


def test_revision_mismatch_fails_closed() -> None:
    original = asset()
    state, bundle = start_run(
        original, problem_run_id="run-7", subject_id="subject-1", session_id="session-1"
    )
    changed = original.model_copy(update={"canonical_pir_revision": "different"})

    with pytest.raises(ValueError, match="revision tuple"):
        submit_response(changed, state, turn_id=bundle.response_turn_id or "", response="8")


def test_integer_and_text_assessment_classification() -> None:
    integer = AssessmentSpec(
        assessment_id="int", kind=AssessmentKind.INTEGER, expected_values=(5,)
    )
    text = AssessmentSpec(
        assessment_id="text",
        kind=AssessmentKind.TEXT,
        expected_text=("S[i] > max_sum",),
        partial_text=("S[i]>max",),
    )

    assert classify_response(integer, "5") == LearnerOutcome.CORRECT
    assert classify_response(integer, "4") == LearnerOutcome.INCORRECT
    assert classify_response(text, " S[i] > max_sum ") == LearnerOutcome.CORRECT
    assert classify_response(text, "S[i] > max") == LearnerOutcome.PARTIAL


def test_integer_sequence_parser_accepts_common_delimiters() -> None:
    sequence = AssessmentSpec(
        assessment_id="seq",
        kind=AssessmentKind.INTEGER_SEQUENCE,
        expected_values=(2, 6, 1),
    )

    assert classify_response(sequence, "[2, 6, 1]") == LearnerOutcome.CORRECT
    assert classify_response(sequence, "2 6 9") == LearnerOutcome.INCORRECT


def test_contracts_forbid_extra_fields() -> None:
    with pytest.raises(ValidationError):
        RepresentationSpec.model_validate(
            {
                "representation_id": "r",
                "learner_visible_markdown": "hello",
                "visible_components": [],
                "expected_answer": 8,
            }
        )
