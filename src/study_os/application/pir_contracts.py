from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, JsonValue, field_validator, model_validator

from .contracts import ApplicationContractModel, NonEmptyString, _validate_public_json


RunStatusValue = Literal[
    "active",
    "assembled_mastery_unproven",
    "completed_validated",
    "blocked",
]
OutcomeValue = Literal[
    "correct",
    "partial",
    "incorrect",
    "meta",
    "hint_request",
    "unresolved",
]
ExpansionKindValue = Literal[
    "why",
    "easier_example",
    "more_detail",
    "repeat_representation",
    "clarify_term",
]
ProblemResolutionStatus = Literal["known", "needs_compilation"]


def _validate_turn_payload(value: dict[str, JsonValue]) -> dict[str, JsonValue]:
    _validate_public_json(value)
    if value.get("schema_version") != "study-os.teaching-bundle.v0":
        raise ValueError("turn must be a renderer-safe Study OS teaching bundle")
    if not isinstance(value.get("problem_run_id"), str) or not value["problem_run_id"]:
        raise ValueError("turn must identify its problem run")
    if not isinstance(value.get("turns"), list) or not value["turns"]:
        raise ValueError("turn bundle must contain at least one teaching turn")
    forbidden = {"expected_values", "expected_text", "partial_values", "partial_text"}
    rendered = str(value)
    if any(field in rendered for field in forbidden):
        raise ValueError("turn bundle exposes controller-only assessment fields")
    return value


class ResolveProblemRequest(ApplicationContractModel):
    problem_text: NonEmptyString
    domain: NonEmptyString


class ResolveProblemResult(ApplicationContractModel):
    status: ProblemResolutionStatus
    canonical_problem_id: NonEmptyString | None
    canonical_pir_revision: NonEmptyString | None
    reason: NonEmptyString

    @model_validator(mode="after")
    def validate_resolution_pair(self) -> ResolveProblemResult:
        known = self.status == "known"
        has_identity = (
            self.canonical_problem_id is not None
            and self.canonical_pir_revision is not None
        )
        if known != has_identity:
            raise ValueError("known resolution requires canonical identity and unknown does not")
        return self


class StartProblemRequest(ApplicationContractModel):
    idempotency_key: NonEmptyString
    session_id: NonEmptyString
    subject_id: NonEmptyString
    canonical_problem_id: NonEmptyString


class StartProblemResult(ApplicationContractModel):
    problem_run_id: NonEmptyString
    canonical_problem_id: NonEmptyString
    canonical_pir_revision: NonEmptyString
    run_status: RunStatusValue
    turn: dict[str, JsonValue]
    created: bool

    _turn = field_validator("turn")(_validate_turn_payload)


class GetProblemTurnRequest(ApplicationContractModel):
    problem_run_id: NonEmptyString
    subject_id: NonEmptyString


class GetProblemTurnResult(ApplicationContractModel):
    problem_run_id: NonEmptyString
    run_status: RunStatusValue
    turn: dict[str, JsonValue]

    _turn = field_validator("turn")(_validate_turn_payload)


class SubmitProblemResponseRequest(ApplicationContractModel):
    idempotency_key: NonEmptyString
    problem_run_id: NonEmptyString
    subject_id: NonEmptyString
    turn_id: NonEmptyString
    response: NonEmptyString


class SubmitProblemResponseResult(ApplicationContractModel):
    problem_run_id: NonEmptyString
    outcome: OutcomeValue
    run_status: RunStatusValue
    turn: dict[str, JsonValue]
    created: bool

    _turn = field_validator("turn")(_validate_turn_payload)


class RequestProblemExpansionRequest(ApplicationContractModel):
    idempotency_key: NonEmptyString
    problem_run_id: NonEmptyString
    subject_id: NonEmptyString
    turn_id: NonEmptyString
    request_kind: ExpansionKindValue
    learner_request: NonEmptyString


class RequestProblemExpansionResult(ApplicationContractModel):
    problem_run_id: NonEmptyString
    run_status: RunStatusValue
    turn: dict[str, JsonValue]
    created: bool

    _turn = field_validator("turn")(_validate_turn_payload)


PIR_APPLICATION_SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "resolve_problem_request": ResolveProblemRequest,
    "resolve_problem_result": ResolveProblemResult,
    "start_problem_request": StartProblemRequest,
    "start_problem_result": StartProblemResult,
    "get_problem_turn_request": GetProblemTurnRequest,
    "get_problem_turn_result": GetProblemTurnResult,
    "submit_problem_response_request": SubmitProblemResponseRequest,
    "submit_problem_response_result": SubmitProblemResponseResult,
    "request_problem_expansion_request": RequestProblemExpansionRequest,
    "request_problem_expansion_result": RequestProblemExpansionResult,
}


def pir_application_schema_models() -> dict[str, type[BaseModel]]:
    return dict(PIR_APPLICATION_SCHEMA_MODELS)
