from __future__ import annotations

from typing import Any, Protocol

from pydantic import ValidationError

from .contracts import RuntimeHealthCheck, RuntimeHealthRequest, RuntimeHealthResult


class ApplicationBoundaryError(RuntimeError):
    """Raised when a legacy runtime result cannot satisfy the canonical application contract."""


class RuntimeHealthPort(Protocol):
    def doctor(self) -> dict[str, Any]: ...


class ApplicationService:
    """Transport-independent application facade over the preserved semantic runtime."""

    def __init__(self, runtime: RuntimeHealthPort) -> None:
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
