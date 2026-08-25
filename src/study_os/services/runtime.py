"""P2 semantic overrides layered over the proven P0 runtime."""

from __future__ import annotations

from typing import Iterable

from .retention import retention_result_payload, validate_retention_probe_id, validate_scheduled_probe
from .runtime_base import StudyOSService as BaseStudyOSService
from .runtime_base import canonical_json, new_id, utc_now
from ..errors import validation


class StudyOSService(BaseStudyOSService):
    """Add bounded P2 semantics without duplicating the P0 service implementation."""

    def record_assessment(
        self,
        *,
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        capability: str,
        result: str,
        assistance_level: str,
        evidence_ids: Iterable[str],
        retention_probe_id: str | None = None,
    ) -> dict:
        for field_name, value in (("capability", capability), ("result", result), ("assistance_level", assistance_level)):
            if not isinstance(value, str) or not value.strip():
                raise validation(f"{field_name} must be a non-empty string")
        probe_id = validate_retention_probe_id(retention_probe_id)
        ids = self._as_ids(evidence_ids, "evidence_ids")
        request = {
            "session_id": session_id,
            "subject_id": subject_id,
            "capability": capability,
            "result": result,
            "assistance_level": assistance_level,
            "evidence_ids": ids,
            "retention_probe_id": probe_id,
        }
        with self.repository.transaction() as connection:
            cached = self._idempotency_check(connection, "record_assessment", idempotency_key, request)
            if cached:
                return cached
            self._session(connection, session_id, subject_id)
            resolved_ids = self._resolve_evidence(connection, ids, subject_id=subject_id)
            if probe_id is not None:
                probe = connection.execute(
                    "SELECT * FROM retention_probes WHERE retention_probe_id = ?", (probe_id,)
                ).fetchone()
                validate_scheduled_probe(
                    dict(probe) if probe is not None else None,
                    retention_probe_id=probe_id,
                    subject_id=subject_id,
                    capability=capability,
                )
            assessment_id = new_id()
            created_at = utc_now()
            connection.execute(
                "INSERT INTO assessments "
                "(assessment_id, session_id, subject_id, capability, result, assistance_level, evidence_ids_json, idempotency_key, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    assessment_id,
                    session_id,
                    subject_id,
                    capability,
                    result,
                    assistance_level,
                    canonical_json(resolved_ids),
                    idempotency_key,
                    created_at,
                ),
            )
            result_payload = {
                "assessment_id": assessment_id,
                "created": True,
                "capability": capability,
                "result": result,
            }
            if probe_id is not None:
                probe_result = retention_result_payload(
                    assessment_id=assessment_id,
                    capability=capability,
                    result=result,
                    assistance_level=assistance_level,
                    evidence_ids=resolved_ids,
                    completed_at=created_at,
                )
                updated = connection.execute(
                    "UPDATE retention_probes SET status = 'completed', result_json = ? "
                    "WHERE retention_probe_id = ? AND status = 'scheduled'",
                    (canonical_json(probe_result), probe_id),
                )
                if updated.rowcount != 1:
                    raise validation("Retention probe could not be completed atomically")
                result_payload["retention_probe_id"] = probe_id
                result_payload["retention_probe_status"] = "completed"
            self._idempotency_record(
                connection,
                operation="record_assessment",
                key=idempotency_key,
                request=request,
                result=result_payload,
                resource_type="assessment",
                resource_id=assessment_id,
            )
            return result_payload

    def resume(self, *, subject_id: str) -> dict:
        with self.repository.transaction(immediate=False) as connection:
            pointer = connection.execute(
                "SELECT checkpoint_id FROM subject_current_checkpoint WHERE subject_id = ?", (subject_id,)
            ).fetchone()
            if pointer is None:
                from ..errors import not_found

                raise not_found("Subject has no accepted checkpoint", subject_id=subject_id)
            checkpoint = self._checkpoint_payload(connection, subject_id, pointer["checkpoint_id"])
            probe = connection.execute(
                "SELECT retention_probe_id, concept_id, due_at, status, source_checkpoint_id "
                "FROM retention_probes WHERE subject_id = ? AND status = 'scheduled' "
                "ORDER BY due_at ASC, created_at ASC LIMIT 1",
                (subject_id,),
            ).fetchone()
            recent_rows = connection.execute(
                "SELECT representation_family, operation, representation_version, target_bottleneck, created_at "
                "FROM interventions WHERE subject_id = ? ORDER BY created_at DESC LIMIT 5",
                (subject_id,),
            ).fetchall()
            next_probe = None
            if probe is not None:
                next_probe = {
                    "retention_probe_id": probe["retention_probe_id"],
                    "concept_id": probe["concept_id"],
                    "due_at": probe["due_at"],
                    "status": probe["status"],
                    "source_checkpoint_id": probe["source_checkpoint_id"],
                }
            return {
                "subject_id": subject_id,
                "checkpoint_id": checkpoint["checkpoint_id"],
                "capability_state": checkpoint["capability_state"],
                "assistance_state": checkpoint["assistance_state"],
                "current_focus": checkpoint["current_focus"],
                "do_not_reteach": checkpoint["do_not_reteach"],
                "next_action": checkpoint["next_action"],
                "retention_due_at": checkpoint["retention_due_at"],
                "next_retention_probe": next_probe,
                "recent_representation_history": [
                    {
                        "representation_family": row["representation_family"],
                        "operation": row["operation"],
                        "representation_version": row["representation_version"],
                        "target_bottleneck": row["target_bottleneck"],
                        "created_at": row["created_at"],
                    }
                    for row in recent_rows
                ],
            }
