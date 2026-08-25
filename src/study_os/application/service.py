from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from pydantic import ValidationError

from .contracts import (
    RuntimeHealthCheck,
    RuntimeHealthRequest,
    RuntimeHealthResult,
    StartStudySessionRequest,
    StartStudySessionResult,
)


class ApplicationBoundaryError(RuntimeError):
    """Raised when a legacy runtime result cannot satisfy the canonical application contract."""


class ApplicationRuntimePort(Protocol):
    def doctor(self) -> dict[str, Any]: ...

    def start_session(
        self,
        *,
        idempotency_key: str,
        subject_id: str,
        project_id: str,
        domain_id: str,
        source_client: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...


class ApplicationService:
    """Transport-independent application facade over the preserved semantic runtime."""

    def __init__(self, runtime: ApplicationRuntimePort) -> None:
        self.runtime = runtime

    def inspect_runtime_health(
        self,
        request: RuntimeHealthRequest | None = None,
    ) -> RuntimeHealthResult:
        request = request or RuntimeHealthRequest()
        if request.application_contract_version != "0.1.0":
            raise ApplicationBoundaryError("unsupported application contract version")

        raw = self.runtime.doctor()
        try:
            checks: dict[str, RuntimeHealthCheck] = {}
            raw_checks = raw["checks"]
            if not isinstance(raw_checks, dict):
                raise TypeError("runtime health checks must be an object")
            for name, value in raw_checks.items():
                if not isinstance(name, str) or not isinstance(value, dict):
                    raise TypeError("runtime health check entries must be named objects")
                metadata = {
                    key: item
                    for key, item in value.items()
                    if key not in {"healthy", "detail"}
                }
                checks[name] = RuntimeHealthCheck(
                    healthy=value["healthy"],
                    detail=value["detail"],
                    metadata=metadata,
                )
            return RuntimeHealthResult(
                healthy=raw["healthy"],
                runtime_version=raw["runtime_version"],
                schema_version=raw["schema_version"],
                checks=checks,
            )
        except (KeyError, TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "legacy runtime health result does not satisfy the application contract"
            ) from exc

    def start_study_session(self, request: StartStudySessionRequest) -> StartStudySessionResult:
        raw = self.runtime.start_session(
            idempotency_key=request.idempotency_key,
            subject_id=request.subject_id,
            project_id=request.project_id,
            domain_id=request.domain_id,
            source_client=request.source_client,
            metadata=request.metadata,
        )
        try:
            started_at = raw["started_at"]
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            return StartStudySessionResult(
                session_id=raw["session_id"],
                subject_id=raw["subject_id"],
                started_at=started_at,
                created=raw["created"],
            )
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "legacy start_session result does not satisfy the application contract"
            ) from exc


def project_runtime_health_to_mcp(result: RuntimeHealthResult) -> dict[str, Any]:
    """Project the canonical application result back to the unchanged MCP v0.1 payload."""

    checks: dict[str, dict[str, Any]] = {}
    for name, check in result.checks.items():
        checks[name] = {
            "healthy": check.healthy,
            "detail": check.detail,
            **check.metadata,
        }
    return {
        "healthy": result.healthy,
        "runtime_version": result.runtime_version,
        "schema_version": result.schema_version,
        "checks": checks,
    }


def project_start_study_session_to_mcp(result: StartStudySessionResult) -> dict[str, Any]:
    """Project canonical start-session output back to the unchanged MCP v0.1 payload."""

    return {
        "session_id": result.session_id,
        "subject_id": result.subject_id,
        "started_at": result.started_at.isoformat().replace("+00:00", "Z"),
        "created": result.created,
    }
