from __future__ import annotations

import json
import math
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    field_serializer,
    field_validator,
)

APPLICATION_CONTRACT_VERSION = "0.1.0"
NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ErrorCode = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, pattern=r"^[a-z][a-z0-9_.-]*$"),
]
FORBIDDEN_PUBLIC_DETAIL_KEYS = frozenset(
    {
        "raw_private_evidence",
        "private_transcript_body",
        "secret",
        "credential",
        "hidden_holdout_answer",
    }
)


class ApplicationErrorCategory(StrEnum):
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    INTEGRITY_ERROR = "integrity_error"
    UNSUPPORTED_VERSION = "unsupported_version"
    UNAVAILABLE = "unavailable"
    INTERNAL_ERROR = "internal_error"


def _validate_public_json(value: JsonValue) -> JsonValue:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite numbers are not allowed in application contract JSON")
    if isinstance(value, list):
        for item in value:
            _validate_public_json(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_DETAIL_KEYS:
                raise ValueError(f"public application detail may not contain {key!r}")
            _validate_public_json(item)
    return value


class ApplicationContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    application_contract_version: Literal["0.1.0"] = APPLICATION_CONTRACT_VERSION


class ApplicationError(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    category: ApplicationErrorCategory
    code: ErrorCode
    message: NonEmptyString
    retryable: bool = False
    details: dict[str, JsonValue] = Field(default_factory=dict)

    @field_validator("details")
    @classmethod
    def validate_safe_details(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        _validate_public_json(value)
        return value


class ApplicationErrorEnvelope(ApplicationContractModel):
    error: ApplicationError


class RuntimeHealthRequest(ApplicationContractModel):
    pass


class RuntimeHealthCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    healthy: bool
    detail: NonEmptyString
    metadata: dict[str, JsonValue] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        _validate_public_json(value)
        return value


class RuntimeHealthResult(ApplicationContractModel):
    healthy: bool
    runtime_version: NonEmptyString
    schema_version: int | None
    checks: dict[NonEmptyString, RuntimeHealthCheck]


class StartStudySessionRequest(ApplicationContractModel):
    idempotency_key: NonEmptyString
    subject_id: NonEmptyString
    project_id: NonEmptyString
    domain_id: NonEmptyString


class StartStudySessionResult(ApplicationContractModel):
    session_id: NonEmptyString
    subject_id: NonEmptyString
    started_at: datetime
    created: bool

    @field_validator("started_at")
    @classmethod
    def require_utc_timestamp(cls, value: datetime) -> datetime:
        offset = value.utcoffset()
        if value.tzinfo is None or offset is None:
            raise ValueError("started_at must include timezone information")
        if offset.total_seconds() != 0:
            raise ValueError("started_at must be UTC")
        return value

    @field_serializer("started_at", when_used="json")
    def serialize_started_at(self, value: datetime) -> str:
        return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


CORE_SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "application_error_envelope": ApplicationErrorEnvelope,
    "inspect_runtime_health_request": RuntimeHealthRequest,
    "inspect_runtime_health_result": RuntimeHealthResult,
    "start_study_session_request": StartStudySessionRequest,
    "start_study_session_result": StartStudySessionResult,
}


def canonical_model_json(model: BaseModel) -> str:
    payload = model.model_dump(mode="json", exclude_none=False)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def application_contract_core_schema_bundle() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Study OS Application Contract Core",
        "application_contract_version": APPLICATION_CONTRACT_VERSION,
        "models": {
            name: model.model_json_schema(mode="validation")
            for name, model in sorted(CORE_SCHEMA_MODELS.items())
        },
    }


def render_application_contract_core_schema() -> str:
    return json.dumps(
        application_contract_core_schema_bundle(),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
