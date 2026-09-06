from __future__ import annotations

from typing import Any, Protocol

from pydantic import ValidationError

from .pir_contracts import (
    GetProblemTurnRequest,
    GetProblemTurnResult,
    RequestProblemExpansionRequest,
    RequestProblemExpansionResult,
    ResolveProblemRequest,
    ResolveProblemResult,
    StartProblemRequest,
    StartProblemResult,
    SubmitProblemResponseRequest,
    SubmitProblemResponseResult,
)
from .service import ApplicationBoundaryError, ApplicationRuntimePort, ApplicationService


class PIRApplicationRuntimePort(ApplicationRuntimePort, Protocol):
    def resolve_problem(self, *, problem_text: str, domain: str) -> dict[str, Any]: ...

    def start_problem(
        self,
        *,
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        canonical_problem_id: str,
    ) -> dict[str, Any]: ...

    def get_problem_turn(
        self,
        *,
        problem_run_id: str,
        subject_id: str,
    ) -> dict[str, Any]: ...

    def submit_problem_response(
        self,
        *,
        idempotency_key: str,
        problem_run_id: str,
        subject_id: str,
        turn_id: str,
        response: str,
    ) -> dict[str, Any]: ...

    def request_problem_expansion(
        self,
        *,
        idempotency_key: str,
        problem_run_id: str,
        subject_id: str,
        turn_id: str,
        request_kind: str,
        learner_request: str,
    ) -> dict[str, Any]: ...


class PIRApplicationService(ApplicationService):
    """Application facade extended with deterministic PIR teaching operations."""

    runtime: PIRApplicationRuntimePort

    def __init__(self, runtime: PIRApplicationRuntimePort) -> None:
        super().__init__(runtime)
        self.runtime = runtime

    def resolve_problem(self, request: ResolveProblemRequest) -> ResolveProblemResult:
        raw = self.runtime.resolve_problem(
            problem_text=request.problem_text,
            domain=request.domain,
        )
        try:
            return ResolveProblemResult(**raw)
        except (TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "runtime resolve_problem result does not satisfy the application contract"
            ) from exc

    def start_problem(self, request: StartProblemRequest) -> StartProblemResult:
        raw = self.runtime.start_problem(
            idempotency_key=request.idempotency_key,
            session_id=request.session_id,
            subject_id=request.subject_id,
            canonical_problem_id=request.canonical_problem_id,
        )
        try:
            return StartProblemResult(**raw)
        except (TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "runtime start_problem result does not satisfy the application contract"
            ) from exc

    def get_problem_turn(self, request: GetProblemTurnRequest) -> GetProblemTurnResult:
        raw = self.runtime.get_problem_turn(
            problem_run_id=request.problem_run_id,
            subject_id=request.subject_id,
        )
        try:
            return GetProblemTurnResult(**raw)
        except (TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "runtime get_problem_turn result does not satisfy the application contract"
            ) from exc

    def submit_problem_response(
        self,
        request: SubmitProblemResponseRequest,
    ) -> SubmitProblemResponseResult:
        raw = self.runtime.submit_problem_response(
            idempotency_key=request.idempotency_key,
            problem_run_id=request.problem_run_id,
            subject_id=request.subject_id,
            turn_id=request.turn_id,
            response=request.response,
        )
        try:
            return SubmitProblemResponseResult(**raw)
        except (TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "runtime submit_problem_response result does not satisfy the application contract"
            ) from exc

    def request_problem_expansion(
        self,
        request: RequestProblemExpansionRequest,
    ) -> RequestProblemExpansionResult:
        raw = self.runtime.request_problem_expansion(
            idempotency_key=request.idempotency_key,
            problem_run_id=request.problem_run_id,
            subject_id=request.subject_id,
            turn_id=request.turn_id,
            request_kind=request.request_kind,
            learner_request=request.learner_request,
        )
        try:
            return RequestProblemExpansionResult(**raw)
        except (TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "runtime request_problem_expansion result does not satisfy the application contract"
            ) from exc


def _project(result: Any) -> dict[str, Any]:
    return result.model_dump(
        mode="json",
        exclude={"application_contract_version"},
        exclude_none=False,
    )


def project_resolve_problem_to_mcp(result: ResolveProblemResult) -> dict[str, Any]:
    return _project(result)


def project_start_problem_to_mcp(result: StartProblemResult) -> dict[str, Any]:
    return _project(result)


def project_get_problem_turn_to_mcp(result: GetProblemTurnResult) -> dict[str, Any]:
    return _project(result)


def project_submit_problem_response_to_mcp(
    result: SubmitProblemResponseResult,
) -> dict[str, Any]:
    return _project(result)


def project_request_problem_expansion_to_mcp(
    result: RequestProblemExpansionResult,
) -> dict[str, Any]:
    return _project(result)
