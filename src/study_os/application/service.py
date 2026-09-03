from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from pydantic import ValidationError

from .contracts import (
    AppendConversationTurnRequest,
    AppendConversationTurnResult,
    NextRetentionProbeRequest,
    NextRetentionProbeResult,
    RecentRepresentationSummary,
    RecordAssessmentRequest,
    RecordAssessmentResult,
    RecordAttemptRequest,
    RecordAttemptResult,
    RecordLearningEventRequest,
    RecordLearningEventResult,
    RecordRepresentationInterventionRequest,
    RecordRepresentationInterventionResult,
    RecordRepresentationOutcomeRequest,
    RecordRepresentationOutcomeResult,
    ResumeRetentionProbeSummary,
    ResumeLearningContextRequest,
    ResumeLearningContextResult,
    ResumeSubjectRequest,
    ResumeSubjectResult,
    RetentionProbeSummary,
    RuntimeHealthCheck,
    RuntimeHealthRequest,
    RuntimeHealthResult,
    ScheduleRetentionProbeRequest,
    ScheduleRetentionProbeResult,
    StartStudySessionRequest,
    StartStudySessionResult,
    SubjectStatusRequest,
    SubjectStatusResult,
)


class ApplicationBoundaryError(RuntimeError):
    """Raised when a legacy runtime result cannot satisfy the canonical application contract."""


class ApplicationRuntimePort(Protocol):
    def doctor(self) -> dict[str, Any]: ...

    def status(self, *, subject_id: str) -> dict[str, Any]: ...

    def resume(self, *, subject_id: str) -> dict[str, Any]: ...

    def resume_learning_context(self, *, subject_id: str) -> dict[str, Any]: ...

    def get_next_probe(self, *, subject_id: str) -> dict[str, Any]: ...

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

    def append_conversation_turn(
        self,
        *,
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        role: str,
        content: str,
        source_conversation_ref: str | None = None,
        source_message_ref: str | None = None,
        source_parent_ref: str | None = None,
        source_timestamp: str | None = None,
        source_sequence: int | None = None,
        source_client: str | None = None,
    ) -> dict[str, Any]: ...

    def record_attempt(
        self,
        *,
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        task_id: str,
        response: Any,
        assistance_level: str = "none",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    def record_learning_event(
        self,
        *,
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        evidence_class: str,
        event_type: str,
        payload: dict[str, Any],
        source_ids: list[str] | None = None,
        payload_version: str = "0.1.0",
    ) -> dict[str, Any]: ...

    def record_assessment(
        self,
        *,
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        capability: str,
        result: str,
        assistance_level: str,
        evidence_ids: list[str],
        retention_probe_id: str | None = None,
    ) -> dict[str, Any]: ...

    def record_representation_intervention(
        self,
        *,
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        representation_family: str,
        operation: str,
        representation_version: str,
        target_bottleneck: str,
    ) -> dict[str, Any]: ...

    def record_representation_outcome(
        self,
        *,
        idempotency_key: str,
        intervention_id: str,
        subject_id: str,
        evidence_score: int,
        evidence_ids: list[str],
    ) -> dict[str, Any]: ...

    def schedule_retention_probe(
        self,
        *,
        idempotency_key: str,
        subject_id: str,
        concept_id: str,
        due_at: str,
        source_checkpoint_id: str,
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

    def get_subject_status(self, request: SubjectStatusRequest) -> SubjectStatusResult:
        raw = self.runtime.status(subject_id=request.subject_id)
        try:
            return SubjectStatusResult(
                subject_id=raw["subject_id"],
                current_session_id=raw["current_session_id"],
                current_checkpoint_id=raw["current_checkpoint_id"],
                current_focus=raw["current_focus"],
                next_action=raw["next_action"],
            )
        except (KeyError, TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "legacy status result does not satisfy the application contract"
            ) from exc

    def resume_subject(self, request: ResumeSubjectRequest) -> ResumeSubjectResult:
        raw = self.runtime.resume(subject_id=request.subject_id)
        try:
            raw_probe = raw["next_retention_probe"]
            next_retention_probe = None
            if raw_probe is not None:
                if not isinstance(raw_probe, dict):
                    raise TypeError("resume retention probe summary must be an object or null")
                next_retention_probe = ResumeRetentionProbeSummary(
                    retention_probe_id=raw_probe["retention_probe_id"],
                    concept_id=raw_probe["concept_id"],
                    due_at=raw_probe["due_at"],
                    status=raw_probe["status"],
                    source_checkpoint_id=raw_probe["source_checkpoint_id"],
                )

            raw_history = raw["recent_representation_history"]
            if not isinstance(raw_history, list):
                raise TypeError("recent representation history must be an array")
            recent_representation_history = []
            for item in raw_history:
                if not isinstance(item, dict):
                    raise TypeError("recent representation entries must be objects")
                recent_representation_history.append(
                    RecentRepresentationSummary(
                        representation_family=item["representation_family"],
                        operation=item["operation"],
                        representation_version=item["representation_version"],
                        target_bottleneck=item["target_bottleneck"],
                        created_at=item["created_at"],
                    )
                )

            return ResumeSubjectResult(
                subject_id=raw["subject_id"],
                checkpoint_id=raw["checkpoint_id"],
                capability_state=raw["capability_state"],
                assistance_state=raw["assistance_state"],
                current_focus=raw["current_focus"],
                do_not_reteach=raw["do_not_reteach"],
                next_action=raw["next_action"],
                retention_due_at=raw["retention_due_at"],
                next_retention_probe=next_retention_probe,
                recent_representation_history=recent_representation_history,
            )
        except (KeyError, TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "legacy resume result does not satisfy the application contract"
            ) from exc

    def resume_learning_context(
        self, request: ResumeLearningContextRequest
    ) -> ResumeLearningContextResult:
        raw = self.runtime.resume_learning_context(subject_id=request.subject_id)
        try:
            return ResumeLearningContextResult(
                subject_id=raw["subject_id"],
                continuity_status=raw["continuity_status"],
                checkpoint=raw["checkpoint"],
                recent_evidence=raw["recent_evidence"],
                evidence_boundary=raw["evidence_boundary"],
                identity_diagnostic=raw["identity_diagnostic"],
            )
        except (KeyError, TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "runtime continuity result does not satisfy the application contract"
            ) from exc

    def get_next_retention_probe(
        self,
        request: NextRetentionProbeRequest,
    ) -> NextRetentionProbeResult:
        raw = self.runtime.get_next_probe(subject_id=request.subject_id)
        try:
            raw_probe = raw["probe"]
            probe = None
            if raw_probe is not None:
                if not isinstance(raw_probe, dict):
                    raise TypeError("retention probe summary must be an object or null")
                probe = RetentionProbeSummary(
                    retention_probe_id=raw_probe["retention_probe_id"],
                    concept_id=raw_probe["concept_id"],
                    due_at=raw_probe["due_at"],
                    status=raw_probe["status"],
                )
            return NextRetentionProbeResult(
                subject_id=raw["subject_id"],
                probe=probe,
                reason=raw["reason"],
                source_checkpoint_id=raw["source_checkpoint_id"],
            )
        except (KeyError, TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "legacy get_next_probe result does not satisfy the application contract"
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

    def append_conversation_turn(
        self,
        request: AppendConversationTurnRequest,
    ) -> AppendConversationTurnResult:
        raw = self.runtime.append_conversation_turn(
            idempotency_key=request.idempotency_key,
            session_id=request.session_id,
            subject_id=request.subject_id,
            role=request.role,
            content=request.content,
            source_conversation_ref=request.source_conversation_ref,
            source_message_ref=request.source_message_ref,
            source_parent_ref=request.source_parent_ref,
            source_timestamp=request.source_timestamp,
            source_sequence=request.source_sequence,
            source_client=request.source_client,
        )
        try:
            local_captured_at = raw["local_captured_at"]
            if isinstance(local_captured_at, str):
                local_captured_at = datetime.fromisoformat(local_captured_at.replace("Z", "+00:00"))
            return AppendConversationTurnResult(
                message_id=raw["message_id"],
                artifact_id=raw["artifact_id"],
                sha256=raw["sha256"],
                created=raw["created"],
                capture_origin=raw["capture_origin"],
                local_captured_at=local_captured_at,
            )
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "runtime append_conversation_turn result does not satisfy the application contract"
            ) from exc

    def record_attempt(self, request: RecordAttemptRequest) -> RecordAttemptResult:
        raw = self.runtime.record_attempt(
            idempotency_key=request.idempotency_key,
            session_id=request.session_id,
            subject_id=request.subject_id,
            task_id=request.task_id,
            response=request.response,
            assistance_level=request.assistance_level,
            context=request.context,
        )
        try:
            return RecordAttemptResult(
                attempt_id=raw["attempt_id"],
                created=raw["created"],
            )
        except (KeyError, TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "legacy record_attempt result does not satisfy the application contract"
            ) from exc

    def record_learning_event(
        self,
        request: RecordLearningEventRequest,
    ) -> RecordLearningEventResult:
        raw = self.runtime.record_learning_event(
            idempotency_key=request.idempotency_key,
            session_id=request.session_id,
            subject_id=request.subject_id,
            evidence_class=request.evidence_class,
            event_type=request.event_type,
            payload=request.payload,
            source_ids=request.source_ids,
            payload_version=request.payload_version,
        )
        try:
            return RecordLearningEventResult(
                event_id=raw["event_id"],
                created=raw["created"],
                evidence_class=raw["evidence_class"],
            )
        except (KeyError, TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "legacy record_learning_event result does not satisfy the application contract"
            ) from exc

    def record_assessment(self, request: RecordAssessmentRequest) -> RecordAssessmentResult:
        raw = self.runtime.record_assessment(
            idempotency_key=request.idempotency_key,
            session_id=request.session_id,
            subject_id=request.subject_id,
            capability=request.capability,
            result=request.result,
            assistance_level=request.assistance_level,
            evidence_ids=request.evidence_ids,
            retention_probe_id=request.retention_probe_id,
        )
        try:
            payload: dict[str, Any] = {
                "assessment_id": raw["assessment_id"],
                "created": raw["created"],
                "capability": raw["capability"],
                "result": raw["result"],
            }
            if "retention_probe_id" in raw:
                payload["retention_probe_id"] = raw["retention_probe_id"]
            if "retention_probe_status" in raw:
                payload["retention_probe_status"] = raw["retention_probe_status"]
            return RecordAssessmentResult(**payload)
        except (KeyError, TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "legacy record_assessment result does not satisfy the application contract"
            ) from exc

    def record_representation_intervention(
        self,
        request: RecordRepresentationInterventionRequest,
    ) -> RecordRepresentationInterventionResult:
        raw = self.runtime.record_representation_intervention(
            idempotency_key=request.idempotency_key,
            session_id=request.session_id,
            subject_id=request.subject_id,
            representation_family=request.representation_family,
            operation=request.operation,
            representation_version=request.representation_version,
            target_bottleneck=request.target_bottleneck,
        )
        try:
            return RecordRepresentationInterventionResult(
                intervention_id=raw["intervention_id"],
                created=raw["created"],
            )
        except (KeyError, TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "legacy record_representation_intervention result does not satisfy the application contract"
            ) from exc

    def record_representation_outcome(
        self,
        request: RecordRepresentationOutcomeRequest,
    ) -> RecordRepresentationOutcomeResult:
        raw = self.runtime.record_representation_outcome(
            idempotency_key=request.idempotency_key,
            intervention_id=request.intervention_id,
            subject_id=request.subject_id,
            evidence_score=request.evidence_score,
            evidence_ids=request.evidence_ids,
        )
        try:
            return RecordRepresentationOutcomeResult(
                outcome_id=raw["outcome_id"],
                created=raw["created"],
                evidence_score=raw["evidence_score"],
            )
        except (KeyError, TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "legacy record_representation_outcome result does not satisfy the application contract"
            ) from exc

    def schedule_retention_probe(
        self,
        request: ScheduleRetentionProbeRequest,
    ) -> ScheduleRetentionProbeResult:
        raw = self.runtime.schedule_retention_probe(
            idempotency_key=request.idempotency_key,
            subject_id=request.subject_id,
            concept_id=request.concept_id,
            due_at=request.due_at,
            source_checkpoint_id=request.source_checkpoint_id,
        )
        try:
            return ScheduleRetentionProbeResult(
                retention_probe_id=raw["retention_probe_id"],
                created=raw["created"],
                due_at=raw["due_at"],
            )
        except (KeyError, TypeError, ValidationError) as exc:
            raise ApplicationBoundaryError(
                "legacy schedule_retention_probe result does not satisfy the application contract"
            ) from exc


def project_runtime_health_to_mcp(result: RuntimeHealthResult) -> dict[str, Any]:
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


def project_subject_status_to_mcp(result: SubjectStatusResult) -> dict[str, Any]:
    return {
        "subject_id": result.subject_id,
        "current_session_id": result.current_session_id,
        "current_checkpoint_id": result.current_checkpoint_id,
        "current_focus": result.current_focus,
        "next_action": result.next_action,
    }


def project_resume_subject_to_mcp(result: ResumeSubjectResult) -> dict[str, Any]:
    next_retention_probe = None
    if result.next_retention_probe is not None:
        next_retention_probe = {
            "retention_probe_id": result.next_retention_probe.retention_probe_id,
            "concept_id": result.next_retention_probe.concept_id,
            "due_at": result.next_retention_probe.due_at,
            "status": result.next_retention_probe.status,
            "source_checkpoint_id": result.next_retention_probe.source_checkpoint_id,
        }
    return {
        "subject_id": result.subject_id,
        "checkpoint_id": result.checkpoint_id,
        "capability_state": result.capability_state,
        "assistance_state": result.assistance_state,
        "current_focus": result.current_focus,
        "do_not_reteach": result.do_not_reteach,
        "next_action": result.next_action,
        "retention_due_at": result.retention_due_at,
        "next_retention_probe": next_retention_probe,
        "recent_representation_history": [
            {
                "representation_family": item.representation_family,
                "operation": item.operation,
                "representation_version": item.representation_version,
                "target_bottleneck": item.target_bottleneck,
                "created_at": item.created_at,
            }
            for item in result.recent_representation_history
        ],
    }


def project_next_retention_probe_to_mcp(result: NextRetentionProbeResult) -> dict[str, Any]:
    probe = None
    if result.probe is not None:
        probe = {
            "retention_probe_id": result.probe.retention_probe_id,
            "concept_id": result.probe.concept_id,
            "due_at": result.probe.due_at,
            "status": result.probe.status,
        }
    return {
        "subject_id": result.subject_id,
        "probe": probe,
        "reason": result.reason,
        "source_checkpoint_id": result.source_checkpoint_id,
    }


def project_start_study_session_to_mcp(result: StartStudySessionResult) -> dict[str, Any]:
    return {
        "session_id": result.session_id,
        "subject_id": result.subject_id,
        "started_at": result.started_at.isoformat().replace("+00:00", "Z"),
        "created": result.created,
    }


def project_resume_learning_context_to_mcp(
    result: ResumeLearningContextResult,
) -> dict[str, Any]:
    return {
        "subject_id": result.subject_id,
        "continuity_status": result.continuity_status,
        "checkpoint": result.checkpoint,
        "recent_evidence": result.recent_evidence,
        "evidence_boundary": result.evidence_boundary,
        "identity_diagnostic": result.identity_diagnostic,
    }


def project_append_conversation_turn_to_mcp(
    result: AppendConversationTurnResult,
) -> dict[str, Any]:
    return {
        "message_id": result.message_id,
        "artifact_id": result.artifact_id,
        "sha256": result.sha256,
        "created": result.created,
        "capture_origin": result.capture_origin,
        "local_captured_at": result.local_captured_at.isoformat().replace("+00:00", "Z"),
    }


def project_record_attempt_to_mcp(result: RecordAttemptResult) -> dict[str, Any]:
    return {
        "attempt_id": result.attempt_id,
        "created": result.created,
    }


def project_record_learning_event_to_mcp(
    result: RecordLearningEventResult,
) -> dict[str, Any]:
    return {
        "event_id": result.event_id,
        "created": result.created,
        "evidence_class": result.evidence_class,
    }


def project_record_assessment_to_mcp(result: RecordAssessmentResult) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "assessment_id": result.assessment_id,
        "created": result.created,
        "capability": result.capability,
        "result": result.result,
    }
    if "retention_probe_id" in result.model_fields_set:
        payload["retention_probe_id"] = result.retention_probe_id
    if "retention_probe_status" in result.model_fields_set:
        payload["retention_probe_status"] = result.retention_probe_status
    return payload


def project_record_representation_intervention_to_mcp(
    result: RecordRepresentationInterventionResult,
) -> dict[str, Any]:
    return {
        "intervention_id": result.intervention_id,
        "created": result.created,
    }


def project_record_representation_outcome_to_mcp(
    result: RecordRepresentationOutcomeResult,
) -> dict[str, Any]:
    return {
        "outcome_id": result.outcome_id,
        "created": result.created,
        "evidence_score": result.evidence_score,
    }


def project_schedule_retention_probe_to_mcp(
    result: ScheduleRetentionProbeResult,
) -> dict[str, Any]:
    return {
        "retention_probe_id": result.retention_probe_id,
        "created": result.created,
        "due_at": result.due_at,
    }
