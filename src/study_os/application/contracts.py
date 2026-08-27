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


def _validate_json_value(value: JsonValue) -> JsonValue:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite numbers are not allowed in application contract JSON")
    if isinstance(value, list):
        for item in value:
            _validate_json_value(item)
    elif isinstance(value, dict):
        for item in value.values():
            _validate_json_value(item)
    return value


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


class SubjectStatusRequest(ApplicationContractModel):
    subject_id: NonEmptyString


class SubjectStatusResult(ApplicationContractModel):
    subject_id: NonEmptyString
    current_session_id: NonEmptyString | None
    current_checkpoint_id: NonEmptyString | None
    current_focus: NonEmptyString | None
    next_action: NonEmptyString | None


class NextRetentionProbeRequest(ApplicationContractModel):
    subject_id: NonEmptyString


class RetentionProbeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    retention_probe_id: NonEmptyString
    concept_id: NonEmptyString
    due_at: NonEmptyString
    status: Literal["scheduled"]


class NextRetentionProbeResult(ApplicationContractModel):
    subject_id: NonEmptyString
    probe: RetentionProbeSummary | None
    reason: Literal["no_scheduled_probe", "scheduled_retention_probe"]
    source_checkpoint_id: NonEmptyString | None

    @field_validator("source_checkpoint_id")
    @classmethod
    def validate_probe_state(cls, value: str | None, info: Any) -> str | None:
        probe = info.data.get("probe")
        reason = info.data.get("reason")
        if probe is None:
            if reason != "no_scheduled_probe" or value is not None:
                raise ValueError("no scheduled probe must not expose a source checkpoint")
        elif reason != "scheduled_retention_probe" or value is None:
            raise ValueError("scheduled probe must expose its source checkpoint")
        return value


class ResumeSubjectRequest(ApplicationContractModel):
    subject_id: NonEmptyString


class ResumeRetentionProbeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    retention_probe_id: NonEmptyString
    concept_id: NonEmptyString
    due_at: NonEmptyString
    status: Literal["scheduled"]
    source_checkpoint_id: NonEmptyString


class RecentRepresentationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    representation_family: NonEmptyString
    operation: NonEmptyString
    representation_version: NonEmptyString
    target_bottleneck: NonEmptyString
    created_at: NonEmptyString


class ResumeSubjectResult(ApplicationContractModel):
    subject_id: NonEmptyString
    checkpoint_id: NonEmptyString
    capability_state: dict[str, JsonValue]
    assistance_state: dict[str, JsonValue]
    current_focus: NonEmptyString
    do_not_reteach: list[NonEmptyString]
    next_action: NonEmptyString
    retention_due_at: NonEmptyString | None
    next_retention_probe: ResumeRetentionProbeSummary | None
    recent_representation_history: list[RecentRepresentationSummary]

    @field_validator("capability_state")
    @classmethod
    def validate_capability_state(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if not value:
            raise ValueError("capability_state must not be empty")
        _validate_public_json(value)
        return value

    @field_validator("assistance_state")
    @classmethod
    def validate_assistance_state(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        _validate_public_json(value)
        return value


class StartStudySessionRequest(ApplicationContractModel):
    idempotency_key: NonEmptyString
    subject_id: NonEmptyString
    project_id: NonEmptyString
    domain_id: NonEmptyString
    source_client: str | None = None
    metadata: dict[str, JsonValue] = Field(default_factory=dict)

    @field_validator("metadata", mode="before")
    @classmethod
    def normalize_legacy_null_metadata(cls, value: object) -> object:
        # The existing runtime fingerprints absent/None metadata as an empty object.
        # Preserve that compatibility before MCP is migrated onto this model.
        return {} if value is None else value

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        _validate_public_json(value)
        return value


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


class RecordAttemptRequest(ApplicationContractModel):
    idempotency_key: NonEmptyString
    session_id: NonEmptyString
    subject_id: NonEmptyString
    task_id: NonEmptyString
    response: JsonValue
    assistance_level: NonEmptyString = "none"
    context: dict[str, JsonValue] = Field(default_factory=dict)

    @field_validator("context", mode="before")
    @classmethod
    def normalize_legacy_null_context(cls, value: object) -> object:
        # The preserved runtime fingerprints absent/None context as an empty object.
        return {} if value is None else value

    @field_validator("response")
    @classmethod
    def validate_response_json(cls, value: JsonValue) -> JsonValue:
        # Learner responses may legitimately contain arbitrary JSON keys, so use the
        # generic JSON safety check rather than the public error/detail key filter.
        _validate_json_value(value)
        return value

    @field_validator("context")
    @classmethod
    def validate_context_json(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        # Context currently carries versioned attempt telemetry and remains stored as
        # one JSON object; this adapter must not silently reinterpret its vocabulary.
        _validate_json_value(value)
        return value


class RecordAttemptResult(ApplicationContractModel):
    attempt_id: NonEmptyString
    created: bool


CORE_SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "application_error_envelope": ApplicationErrorEnvelope,
    "get_next_retention_probe_request": NextRetentionProbeRequest,
    "get_next_retention_probe_result": NextRetentionProbeResult,
    "get_subject_status_request": SubjectStatusRequest,
    "get_subject_status_result": SubjectStatusResult,
    "inspect_runtime_health_request": RuntimeHealthRequest,
    "inspect_runtime_health_result": RuntimeHealthResult,
    "record_attempt_request": RecordAttemptRequest,
    "record_attempt_result": RecordAttemptResult,
    "resume_subject_request": ResumeSubjectRequest,
    "resume_subject_result": ResumeSubjectResult,
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
