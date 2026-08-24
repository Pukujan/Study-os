"""Project-agnostic semantic service over SQLite and private evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .. import CONTRACT_VERSION, RUNTIME_VERSION
from ..config import RuntimeConfig
from ..db.connection import Database, LATEST_SCHEMA_VERSION
from ..db.repositories import SQLiteRepository
from ..errors import StudyOSError, conflict, integrity, not_found, unsupported, validation
from ..evidence.store import EvidenceStore


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_id() -> str:
    return str(uuid.uuid4())


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise validation("Request contains a value that is not JSON serializable") from exc


def request_fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def json_load(value: str, default: Any = None) -> Any:
    return json.loads(value) if value is not None else default


class StudyOSService:
    """The only layer allowed to implement semantic persistence behavior."""

    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self.config = config or RuntimeConfig.from_env()
        self.config.ensure_directories()
        self.db = Database(self.config)
        self.repository = SQLiteRepository(self.db)
        self.evidence = EvidenceStore(self.config)

    def close(self) -> None:
        self.repository.close()

    def _idempotency_check(self, connection: sqlite3.Connection, operation: str, key: str, request: Any) -> dict | None:
        if not isinstance(key, str) or not key.strip():
            raise validation("idempotency_key must be a non-empty string")
        fingerprint = request_fingerprint(request)
        row = connection.execute(
            "SELECT request_fingerprint, result_json FROM idempotency_records "
            "WHERE operation_name = ? AND idempotency_key = ?",
            (operation, key),
        ).fetchone()
        if row is None:
            return None
        if row["request_fingerprint"] != fingerprint:
            raise conflict(
                "Idempotency key was already used for a different request",
                operation=operation,
                idempotency_key=key,
            )
        result = json.loads(row["result_json"])
        result["created"] = False
        return result

    def _idempotency_record(
        self,
        connection: sqlite3.Connection,
        *,
        operation: str,
        key: str,
        request: Any,
        result: dict,
        resource_type: str,
        resource_id: str | None,
    ) -> None:
        connection.execute(
            "INSERT INTO idempotency_records "
            "(operation_name, idempotency_key, request_fingerprint, resource_type, resource_id, result_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (operation, key, request_fingerprint(request), resource_type, resource_id, canonical_json(result), utc_now()),
        )

    def _ensure_subject(self, connection: sqlite3.Connection, subject_id: str) -> None:
        connection.execute(
            "INSERT OR IGNORE INTO subjects(subject_id, created_at) VALUES (?, ?)",
            (subject_id, utc_now()),
        )

    def _ensure_project_domain(self, connection: sqlite3.Connection, project_id: str, domain_id: str) -> None:
        connection.execute(
            "INSERT OR IGNORE INTO projects(project_id, created_at) VALUES (?, ?)",
            (project_id, utc_now()),
        )
        existing = connection.execute("SELECT project_id FROM domains WHERE domain_id = ?", (domain_id,)).fetchone()
        if existing is not None and existing["project_id"] != project_id:
            raise conflict("Domain is already associated with a different project", domain_id=domain_id)
        connection.execute(
            "INSERT OR IGNORE INTO domains(domain_id, project_id, created_at) VALUES (?, ?, ?)",
            (domain_id, project_id, utc_now()),
        )

    def _session(self, connection: sqlite3.Connection, session_id: str, subject_id: str) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM sessions WHERE session_id = ? AND subject_id = ?",
            (session_id, subject_id),
        ).fetchone()
        if row is None:
            raise not_found("Session does not exist for subject", session_id=session_id, subject_id=subject_id)
        return row

    @staticmethod
    def _as_ids(values: Iterable[str] | None, field_name: str, *, required: bool = True) -> list[str]:
        if values is None:
            if required:
                raise validation(f"{field_name} is required")
            return []
        if isinstance(values, (str, bytes)):
            raise validation(f"{field_name} must be an array of strings")
        result = list(values)
        if required and not result:
            raise validation(f"{field_name} must not be empty")
        if any(not isinstance(value, str) or not value for value in result):
            raise validation(f"{field_name} must contain non-empty strings")
        return result

    def _resolve_evidence(self, connection: sqlite3.Connection, evidence_ids: Iterable[str] | None) -> list[str]:
        ids = self._as_ids(evidence_ids, "evidence_ids")
        tables = (
            "raw_artifacts",
            "learning_events",
            "attempts",
            "assessments",
            "representation_outcomes",
            "checkpoints",
        )
        columns = {
            "raw_artifacts": "artifact_id",
            "learning_events": "event_id",
            "attempts": "attempt_id",
            "assessments": "assessment_id",
            "representation_outcomes": "outcome_id",
            "checkpoints": "checkpoint_id",
        }
        missing: list[str] = []
        for evidence_id in ids:
            found = False
            for table in tables:
                if connection.execute(
                    f"SELECT 1 FROM {table} WHERE {columns[table]} = ?", (evidence_id,)
                ).fetchone():
                    found = True
                    break
            if not found:
                missing.append(evidence_id)
        if missing:
            raise integrity("Evidence/source IDs do not resolve", missing_evidence_ids=missing)
        return ids

    def capture_evidence(
        self,
        *,
        session_id: str,
        subject_id: str,
        content: bytes | bytearray | memoryview | str | Path,
        media_type: str | None = None,
        capture_method: str = "local",
        source_metadata: dict | None = None,
    ) -> dict:
        with self.repository.transaction() as connection:
            self._session(connection, session_id, subject_id)
            artifact_id, sha256, storage_path = self.evidence.capture(
                session_id=session_id,
                content=content,
                media_type=media_type,
                capture_method=capture_method,
                source_metadata=source_metadata,
            )
            try:
                connection.execute(
                    "INSERT INTO raw_artifacts "
                    "(artifact_id, session_id, sha256, storage_path, media_type, captured_at, capture_method, source_metadata_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        artifact_id,
                        session_id,
                        sha256,
                        storage_path,
                        media_type,
                        utc_now(),
                        capture_method,
                        canonical_json(source_metadata or {}),
                    ),
                )
            except Exception:
                try:
                    self.evidence.resolve(storage_path).unlink(missing_ok=True)
                finally:
                    raise
        return {"artifact_id": artifact_id, "sha256": sha256, "storage_path": storage_path}

    def start_session(
        self,
        *,
        idempotency_key: str,
        subject_id: str,
        project_id: str,
        domain_id: str,
        source_client: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        request = {
            "subject_id": subject_id,
            "project_id": project_id,
            "domain_id": domain_id,
            "source_client": source_client,
            "metadata": metadata or {},
        }
        with self.repository.transaction() as connection:
            cached = self._idempotency_check(connection, "start_session", idempotency_key, request)
            if cached:
                return cached
            for name, value in (("subject_id", subject_id), ("project_id", project_id), ("domain_id", domain_id)):
                if not isinstance(value, str) or not value.strip():
                    raise validation(f"{name} must be a non-empty string")
            self._ensure_subject(connection, subject_id)
            self._ensure_project_domain(connection, project_id, domain_id)
            session_id = new_id()
            started_at = utc_now()
            connection.execute(
                "INSERT INTO sessions(session_id, subject_id, project_id, domain_id, started_at, source_client, metadata_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, subject_id, project_id, domain_id, started_at, source_client, canonical_json(metadata or {})),
            )
            result = {"session_id": session_id, "subject_id": subject_id, "started_at": started_at, "created": True}
            self._idempotency_record(
                connection,
                operation="start_session",
                key=idempotency_key,
                request=request,
                result=result,
                resource_type="session",
                resource_id=session_id,
            )
            return result

    def record_learning_event(
        self,
        *,
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        evidence_class: str,
        event_type: str,
        payload: dict,
        source_ids: Iterable[str] | None = None,
        payload_version: str = "0.1.0",
    ) -> dict:
        if evidence_class not in {"observed", "self_reported", "derived"}:
            raise validation("evidence_class must be observed, self_reported, or derived")
        if not isinstance(payload, dict):
            raise validation("payload must be an object")
        payload_source_ids = payload.get("evidence_ids") if source_ids is None else list(source_ids)
        request = {
            "session_id": session_id,
            "subject_id": subject_id,
            "evidence_class": evidence_class,
            "event_type": event_type,
            "payload": payload,
            "source_ids": list(payload_source_ids or []),
            "payload_version": payload_version,
        }
        with self.repository.transaction() as connection:
            cached = self._idempotency_check(connection, "record_learning_event", idempotency_key, request)
            if cached:
                return cached
            self._session(connection, session_id, subject_id)
            if not isinstance(event_type, str) or not event_type.strip():
                raise validation("event_type must be a non-empty string")
            resolved_source_ids = self._as_ids(payload_source_ids, "source_ids", required=evidence_class == "derived")
            if resolved_source_ids:
                self._resolve_evidence(connection, resolved_source_ids)
            event_id = new_id()
            connection.execute(
                "INSERT INTO learning_events "
                "(event_id, session_id, subject_id, evidence_class, event_type, payload_json, payload_version, source_ids_json, idempotency_key, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    session_id,
                    subject_id,
                    evidence_class,
                    event_type,
                    canonical_json(payload),
                    payload_version,
                    canonical_json(resolved_source_ids),
                    idempotency_key,
                    utc_now(),
                ),
            )
            result = {"event_id": event_id, "created": True, "evidence_class": evidence_class}
            self._idempotency_record(
                connection,
                operation="record_learning_event",
                key=idempotency_key,
                request=request,
                result=result,
                resource_type="learning_event",
                resource_id=event_id,
            )
            return result

    def record_attempt(
        self,
        *,
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        task_id: str,
        response: Any,
        assistance_level: str = "none",
        context: dict | None = None,
    ) -> dict:
        if not isinstance(response, (dict, list, str, int, float, bool)) and response is not None:
            raise validation("response must be JSON serializable")
        if not isinstance(task_id, str) or not task_id.strip():
            raise validation("task_id must be a non-empty string")
        if not isinstance(assistance_level, str) or not assistance_level.strip():
            raise validation("assistance_level must be a non-empty string")
        request = {
            "session_id": session_id,
            "subject_id": subject_id,
            "task_id": task_id,
            "response": response,
            "assistance_level": assistance_level,
            "context": context or {},
        }
        with self.repository.transaction() as connection:
            cached = self._idempotency_check(connection, "record_attempt", idempotency_key, request)
            if cached:
                return cached
            self._session(connection, session_id, subject_id)
            attempt_id = new_id()
            connection.execute(
                "INSERT INTO attempts "
                "(attempt_id, session_id, subject_id, task_id, response_json, assistance_level, context_json, idempotency_key, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    attempt_id,
                    session_id,
                    subject_id,
                    task_id,
                    canonical_json(response),
                    assistance_level,
                    canonical_json(context or {}),
                    idempotency_key,
                    utc_now(),
                ),
            )
            result = {"attempt_id": attempt_id, "created": True}
            self._idempotency_record(
                connection,
                operation="record_attempt",
                key=idempotency_key,
                request=request,
                result=result,
                resource_type="attempt",
                resource_id=attempt_id,
            )
            return result

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
    ) -> dict:
        for field_name, value in (("capability", capability), ("result", result), ("assistance_level", assistance_level)):
            if not isinstance(value, str) or not value.strip():
                raise validation(f"{field_name} must be a non-empty string")
        ids = self._as_ids(evidence_ids, "evidence_ids")
        request = {
            "session_id": session_id,
            "subject_id": subject_id,
            "capability": capability,
            "result": result,
            "assistance_level": assistance_level,
            "evidence_ids": ids,
        }
        with self.repository.transaction() as connection:
            cached = self._idempotency_check(connection, "record_assessment", idempotency_key, request)
            if cached:
                return cached
            self._session(connection, session_id, subject_id)
            resolved_ids = self._resolve_evidence(connection, ids)
            assessment_id = new_id()
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
                    utc_now(),
                ),
            )
            result_payload = {
                "assessment_id": assessment_id,
                "created": True,
                "capability": capability,
                "result": result,
            }
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
    ) -> dict:
        for field_name, value in (
            ("representation_family", representation_family),
            ("operation", operation),
            ("representation_version", representation_version),
            ("target_bottleneck", target_bottleneck),
        ):
            if not isinstance(value, str) or not value.strip():
                raise validation(f"{field_name} must be a non-empty string")
        if not SEMVER_RE.fullmatch(representation_version):
            raise validation("representation_version must use semantic version form MAJOR.MINOR.PATCH")
        request = {
            "session_id": session_id,
            "subject_id": subject_id,
            "representation_family": representation_family,
            "operation": operation,
            "representation_version": representation_version,
            "target_bottleneck": target_bottleneck,
        }
        with self.repository.transaction() as connection:
            cached = self._idempotency_check(connection, "record_representation_intervention", idempotency_key, request)
            if cached:
                return cached
            self._session(connection, session_id, subject_id)
            representation = connection.execute(
                "SELECT representation_id FROM representations WHERE family = ? AND semantic_version = ?",
                (representation_family, representation_version),
            ).fetchone()
            representation_id = representation["representation_id"] if representation else new_id()
            if representation is None:
                connection.execute(
                    "INSERT INTO representations(representation_id, family, semantic_version) VALUES (?, ?, ?)",
                    (representation_id, representation_family, representation_version),
                )
            intervention_id = new_id()
            connection.execute(
                "INSERT INTO interventions "
                "(intervention_id, session_id, subject_id, representation_id, representation_family, operation, representation_version, target_bottleneck, idempotency_key, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    intervention_id,
                    session_id,
                    subject_id,
                    representation_id,
                    representation_family,
                    operation,
                    representation_version,
                    target_bottleneck,
                    idempotency_key,
                    utc_now(),
                ),
            )
            result = {"intervention_id": intervention_id, "created": True}
            self._idempotency_record(
                connection,
                operation="record_representation_intervention",
                key=idempotency_key,
                request=request,
                result=result,
                resource_type="intervention",
                resource_id=intervention_id,
            )
            return result

    def record_representation_outcome(
        self,
        *,
        idempotency_key: str,
        intervention_id: str,
        subject_id: str,
        evidence_score: int,
        evidence_ids: Iterable[str],
    ) -> dict:
        if not isinstance(evidence_score, int) or isinstance(evidence_score, bool) or not 0 <= evidence_score <= 5:
            raise validation("evidence_score must be an integer from 0 to 5")
        ids = self._as_ids(evidence_ids, "evidence_ids")
        request = {
            "intervention_id": intervention_id,
            "subject_id": subject_id,
            "evidence_score": evidence_score,
            "evidence_ids": ids,
        }
        with self.repository.transaction() as connection:
            cached = self._idempotency_check(connection, "record_representation_outcome", idempotency_key, request)
            if cached:
                return cached
            intervention = connection.execute(
                "SELECT subject_id FROM interventions WHERE intervention_id = ?", (intervention_id,)
            ).fetchone()
            if intervention is None:
                raise not_found("Intervention does not exist", intervention_id=intervention_id)
            if intervention["subject_id"] != subject_id:
                raise integrity("Intervention belongs to a different subject", intervention_id=intervention_id)
            resolved_ids = self._resolve_evidence(connection, ids)
            outcome_id = new_id()
            connection.execute(
                "INSERT INTO representation_outcomes "
                "(outcome_id, intervention_id, subject_id, evidence_score, evidence_ids_json, idempotency_key, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (outcome_id, intervention_id, subject_id, evidence_score, canonical_json(resolved_ids), idempotency_key, utc_now()),
            )
            result = {"outcome_id": outcome_id, "created": True, "evidence_score": evidence_score}
            self._idempotency_record(
                connection,
                operation="record_representation_outcome",
                key=idempotency_key,
                request=request,
                result=result,
                resource_type="representation_outcome",
                resource_id=outcome_id,
            )
            return result

    def checkpoint(
        self,
        *,
        idempotency_key: str,
        subject_id: str,
        source_session_ids: Iterable[str],
        evidence_ids: Iterable[str],
        capability_state: dict,
        assistance_state: dict,
        resume: dict,
        retention_due_at: str | None = None,
        derivation_version: str = "0.1.0",
    ) -> dict:
        if not isinstance(capability_state, dict) or not capability_state:
            raise validation("capability_state must be a non-empty object")
        if not isinstance(assistance_state, dict):
            raise validation("assistance_state must be an object")
        if not isinstance(resume, dict):
            raise validation("resume must be an object")
        expected_current_checkpoint_id = resume.get("expected_current_checkpoint_id")
        if expected_current_checkpoint_id is not None and (
            not isinstance(expected_current_checkpoint_id, str) or not expected_current_checkpoint_id.strip()
        ):
            raise validation("resume.expected_current_checkpoint_id must be a non-empty string when supplied")
        current_focus = resume.get("current_focus")
        next_action = resume.get("next_action")
        if not isinstance(current_focus, str) or not current_focus.strip():
            raise validation("resume.current_focus must be a non-empty string")
        if not isinstance(next_action, str) or not next_action.strip():
            raise validation("resume.next_action must be a non-empty string")
        session_ids = self._as_ids(source_session_ids, "source_session_ids")
        ids = self._as_ids(evidence_ids, "evidence_ids")
        request = {
            "subject_id": subject_id,
            "source_session_ids": session_ids,
            "evidence_ids": ids,
            "capability_state": capability_state,
            "assistance_state": assistance_state,
            "resume": resume,
            "retention_due_at": retention_due_at,
            "derivation_version": derivation_version,
        }
        with self.repository.transaction() as connection:
            cached = self._idempotency_check(connection, "checkpoint", idempotency_key, request)
            if cached:
                return cached
            subject = connection.execute("SELECT 1 FROM subjects WHERE subject_id = ?", (subject_id,)).fetchone()
            if subject is None:
                raise not_found("Subject does not exist", subject_id=subject_id)
            for session_id in session_ids:
                self._session(connection, session_id, subject_id)
            resolved_ids = self._resolve_evidence(connection, ids)
            current_pointer = connection.execute(
                "SELECT checkpoint_id FROM subject_current_checkpoint WHERE subject_id = ?", (subject_id,)
            ).fetchone()
            if current_pointer is None:
                if expected_current_checkpoint_id is not None:
                    raise conflict("Checkpoint expected an existing current pointer, but none exists", subject_id=subject_id)
            elif expected_current_checkpoint_id != current_pointer["checkpoint_id"]:
                raise conflict(
                    "Checkpoint would overwrite a newer current pointer; resume and retry with the accepted checkpoint",
                    subject_id=subject_id,
                    expected_current_checkpoint_id=expected_current_checkpoint_id,
                    actual_current_checkpoint_id=current_pointer["checkpoint_id"],
                )
            checkpoint_id = new_id()
            connection.execute(
                "INSERT INTO checkpoints "
                "(checkpoint_id, subject_id, source_session_ids_json, evidence_ids_json, capability_state_json, assistance_state_json, current_focus, do_not_reteach_json, next_action, retention_due_at, derivation_version, idempotency_key, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    checkpoint_id,
                    subject_id,
                    canonical_json(session_ids),
                    canonical_json(resolved_ids),
                    canonical_json(capability_state),
                    canonical_json(assistance_state),
                    current_focus,
                    canonical_json(resume.get("do_not_reteach", [])),
                    next_action,
                    retention_due_at,
                    derivation_version,
                    idempotency_key,
                    utc_now(),
                ),
            )
            # This pointer write is in the same transaction as checkpoint insert.
            connection.execute(
                "INSERT INTO subject_current_checkpoint(subject_id, checkpoint_id, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(subject_id) DO UPDATE SET checkpoint_id = excluded.checkpoint_id, updated_at = excluded.updated_at",
                (subject_id, checkpoint_id, utc_now()),
            )
            result = {
                "checkpoint_id": checkpoint_id,
                "accepted": True,
                "subject_id": subject_id,
                "next_action": next_action,
            }
            self._idempotency_record(
                connection,
                operation="checkpoint",
                key=idempotency_key,
                request=request,
                result=result,
                resource_type="checkpoint",
                resource_id=checkpoint_id,
            )
            return result

    def _checkpoint_payload(self, connection: sqlite3.Connection, subject_id: str, checkpoint_id: str) -> dict:
        row = connection.execute(
            "SELECT * FROM checkpoints WHERE checkpoint_id = ? AND subject_id = ?", (checkpoint_id, subject_id)
        ).fetchone()
        if row is None:
            raise integrity("Current checkpoint pointer does not resolve", subject_id=subject_id, checkpoint_id=checkpoint_id)
        return {
            "checkpoint_id": row["checkpoint_id"],
            "subject_id": row["subject_id"],
            "source_session_ids": json_load(row["source_session_ids_json"], []),
            "evidence_ids": json_load(row["evidence_ids_json"], []),
            "capability_state": json_load(row["capability_state_json"], {}),
            "assistance_state": json_load(row["assistance_state_json"], {}),
            "current_focus": row["current_focus"],
            "do_not_reteach": json_load(row["do_not_reteach_json"], []),
            "next_action": row["next_action"],
            "retention_due_at": row["retention_due_at"],
            "derivation_version": row["derivation_version"],
            "created_at": row["created_at"],
        }

    def resume(self, *, subject_id: str) -> dict:
        with self.repository.transaction(immediate=False) as connection:
            pointer = connection.execute(
                "SELECT checkpoint_id FROM subject_current_checkpoint WHERE subject_id = ?", (subject_id,)
            ).fetchone()
            if pointer is None:
                raise not_found("Subject has no accepted checkpoint", subject_id=subject_id)
            checkpoint = self._checkpoint_payload(connection, subject_id, pointer["checkpoint_id"])
            return {
                "subject_id": subject_id,
                "checkpoint_id": checkpoint["checkpoint_id"],
                "capability_state": checkpoint["capability_state"],
                "assistance_state": checkpoint["assistance_state"],
                "current_focus": checkpoint["current_focus"],
                "next_action": checkpoint["next_action"],
            }

    def status(self, *, subject_id: str) -> dict:
        with self.repository.transaction(immediate=False) as connection:
            if connection.execute("SELECT 1 FROM subjects WHERE subject_id = ?", (subject_id,)).fetchone() is None:
                raise not_found("Subject does not exist", subject_id=subject_id)
            session = connection.execute(
                "SELECT session_id FROM sessions WHERE subject_id = ? ORDER BY started_at DESC LIMIT 1", (subject_id,)
            ).fetchone()
            pointer = connection.execute(
                "SELECT checkpoint_id FROM subject_current_checkpoint WHERE subject_id = ?", (subject_id,)
            ).fetchone()
            current_checkpoint_id = pointer["checkpoint_id"] if pointer else None
            current_focus = None
            next_action = None
            if current_checkpoint_id:
                checkpoint = self._checkpoint_payload(connection, subject_id, current_checkpoint_id)
                current_focus = checkpoint["current_focus"]
                next_action = checkpoint["next_action"]
            return {
                "subject_id": subject_id,
                "current_session_id": session["session_id"] if session else None,
                "current_checkpoint_id": current_checkpoint_id,
                "current_focus": current_focus,
                "next_action": next_action,
            }

    def schedule_retention_probe(
        self,
        *,
        idempotency_key: str,
        subject_id: str,
        concept_id: str,
        due_at: str,
        source_checkpoint_id: str,
    ) -> dict:
        for field_name, value in (("subject_id", subject_id), ("concept_id", concept_id), ("due_at", due_at), ("source_checkpoint_id", source_checkpoint_id)):
            if not isinstance(value, str) or not value.strip():
                raise validation(f"{field_name} must be a non-empty string")
        request = {
            "subject_id": subject_id,
            "concept_id": concept_id,
            "due_at": due_at,
            "source_checkpoint_id": source_checkpoint_id,
        }
        with self.repository.transaction() as connection:
            cached = self._idempotency_check(connection, "schedule_retention_probe", idempotency_key, request)
            if cached:
                return cached
            self._ensure_subject(connection, subject_id)
            checkpoint = connection.execute(
                "SELECT subject_id FROM checkpoints WHERE checkpoint_id = ?", (source_checkpoint_id,)
            ).fetchone()
            if checkpoint is None:
                raise not_found("Source checkpoint does not exist", source_checkpoint_id=source_checkpoint_id)
            if checkpoint["subject_id"] != subject_id:
                raise integrity("Source checkpoint belongs to a different subject")
            connection.execute(
                "INSERT OR IGNORE INTO concepts(concept_id, created_at) VALUES (?, ?)", (concept_id, utc_now())
            )
            probe_id = new_id()
            connection.execute(
                "INSERT INTO retention_probes "
                "(retention_probe_id, subject_id, concept_id, due_at, source_checkpoint_id, idempotency_key, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (probe_id, subject_id, concept_id, due_at, source_checkpoint_id, idempotency_key, utc_now()),
            )
            result = {"retention_probe_id": probe_id, "created": True, "due_at": due_at}
            self._idempotency_record(
                connection,
                operation="schedule_retention_probe",
                key=idempotency_key,
                request=request,
                result=result,
                resource_type="retention_probe",
                resource_id=probe_id,
            )
            return result

    def get_next_probe(self, *, subject_id: str) -> dict:
        with self.repository.transaction(immediate=False) as connection:
            if connection.execute("SELECT 1 FROM subjects WHERE subject_id = ?", (subject_id,)).fetchone() is None:
                raise not_found("Subject does not exist", subject_id=subject_id)
            row = connection.execute(
                "SELECT * FROM retention_probes WHERE subject_id = ? AND status = 'scheduled' "
                "ORDER BY due_at ASC, created_at ASC LIMIT 1",
                (subject_id,),
            ).fetchone()
            probe = None
            source_checkpoint_id = None
            reason = "no_scheduled_probe"
            if row:
                source_checkpoint_id = row["source_checkpoint_id"]
                probe = {
                    "retention_probe_id": row["retention_probe_id"],
                    "concept_id": row["concept_id"],
                    "due_at": row["due_at"],
                    "status": row["status"],
                }
                reason = "scheduled_retention_probe"
            return {
                "subject_id": subject_id,
                "probe": probe,
                "reason": reason,
                "source_checkpoint_id": source_checkpoint_id,
            }

    def export_fossil(
        self,
        *,
        idempotency_key: str,
        subject_id: str,
        artifact_type: str,
        source_ids: Iterable[str],
    ) -> dict:
        if not isinstance(artifact_type, str) or not artifact_type.strip():
            raise validation("artifact_type must be a non-empty string")
        ids = self._as_ids(source_ids, "source_ids")
        request = {"subject_id": subject_id, "artifact_type": artifact_type, "source_ids": ids}
        with self.repository.transaction() as connection:
            cached = self._idempotency_check(connection, "export_fossil", idempotency_key, request)
            if cached:
                return cached
            if connection.execute("SELECT 1 FROM subjects WHERE subject_id = ?", (subject_id,)).fetchone() is None:
                raise not_found("Subject does not exist", subject_id=subject_id)
            resolved_ids = self._resolve_evidence(connection, ids)
            export_id = new_id()
            export_dir = self.config.exports_root / "fossil"
            export_dir.mkdir(parents=True, exist_ok=True)
            storage_path = (export_dir / f"{export_id}.json").relative_to(self.config.root).as_posix()
            export_payload = {
                "export_version": CONTRACT_VERSION,
                "export_id": export_id,
                "subject_id": subject_id,
                "artifact_type": artifact_type,
                "source_ids": resolved_ids,
                "created_at": utc_now(),
            }
            (self.config.root / storage_path).write_text(json.dumps(export_payload, indent=2) + "\n", encoding="utf-8")
            connection.execute(
                "INSERT INTO fossil_exports(export_id, subject_id, artifact_type, source_ids_json, storage_path, idempotency_key, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (export_id, subject_id, artifact_type, canonical_json(resolved_ids), storage_path, idempotency_key, export_payload["created_at"]),
            )
            result = {"export_id": export_id, "created": True, "artifact_type": artifact_type, "source_ids": resolved_ids}
            self._idempotency_record(
                connection,
                operation="export_fossil",
                key=idempotency_key,
                request=request,
                result=result,
                resource_type="fossil_export",
                resource_id=export_id,
            )
            return result

    def doctor(self) -> dict:
        checks: dict[str, dict[str, Any]] = {}

        def check(name: str, healthy: bool, detail: str = "ok", **extra: Any) -> None:
            checks[name] = {"healthy": bool(healthy), "detail": detail, **extra}

        connection = self.repository.connection
        try:
            schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            check(
                "schema_version",
                schema_version == LATEST_SCHEMA_VERSION,
                "ok" if schema_version == LATEST_SCHEMA_VERSION else "unsupported schema version",
                expected=LATEST_SCHEMA_VERSION,
                actual=schema_version,
            )
        except sqlite3.DatabaseError as exc:
            schema_version = None
            check("schema_version", False, "database could not be read", error=str(exc))

        try:
            foreign_keys = int(connection.execute("PRAGMA foreign_keys").fetchone()[0])
            fk_violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            check("foreign_keys", foreign_keys == 1 and not fk_violations, "ok" if foreign_keys == 1 and not fk_violations else "foreign-key enforcement/check failed", violations=len(fk_violations))
        except sqlite3.DatabaseError as exc:
            check("foreign_keys", False, "foreign-key check failed", error=str(exc))

        required_tables = {
            "subjects", "projects", "domains", "concepts", "sessions", "raw_artifacts", "messages",
            "learning_events", "episodes", "attempts", "assessments", "representations", "interventions",
            "representation_outcomes", "checkpoints", "subject_current_checkpoint", "retention_probes",
            "fossil_exports", "idempotency_records",
        }
        try:
            actual_tables = {
                row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            missing = sorted(required_tables - actual_tables)
            check("required_tables", not missing, "ok" if not missing else "required tables are missing", missing=missing)
        except sqlite3.DatabaseError as exc:
            check("required_tables", False, "table inspection failed", error=str(exc))

        try:
            meta = {
                row["key"]: row["value"] for row in connection.execute("SELECT key, value FROM schema_meta")
            }
            compatible = meta.get("schema_version") == str(LATEST_SCHEMA_VERSION) and meta.get("contract_version") == CONTRACT_VERSION
            check("contract_runtime_version", compatible, "ok" if compatible else "contract/runtime version mismatch", expected_contract=CONTRACT_VERSION, actual_contract=meta.get("contract_version"), runtime_version=RUNTIME_VERSION)
        except sqlite3.DatabaseError as exc:
            check("contract_runtime_version", False, "version metadata is unavailable", error=str(exc))

        check("evidence_root", self.config.evidence_root.is_dir(), "ok" if self.config.evidence_root.is_dir() else "configured evidence root is unavailable")

        pointer_failures: list[dict[str, str]] = []
        evidence_failures: list[dict[str, str]] = []
        try:
            pointers = connection.execute("SELECT subject_id, checkpoint_id FROM subject_current_checkpoint").fetchall()
            for pointer in pointers:
                checkpoint = connection.execute(
                    "SELECT evidence_ids_json FROM checkpoints WHERE checkpoint_id = ? AND subject_id = ?",
                    (pointer["checkpoint_id"], pointer["subject_id"]),
                ).fetchone()
                if checkpoint is None:
                    pointer_failures.append({"subject_id": pointer["subject_id"], "checkpoint_id": pointer["checkpoint_id"]})
                    continue
                try:
                    self._resolve_evidence(connection, json_load(checkpoint["evidence_ids_json"], []))
                except StudyOSError as exc:
                    evidence_failures.append({"checkpoint_id": pointer["checkpoint_id"], "detail": exc.message})
            check("current_checkpoint_pointers", not pointer_failures, "ok" if not pointer_failures else "current checkpoint pointer is broken", failures=pointer_failures)
            check("checkpoint_evidence", not evidence_failures, "ok" if not evidence_failures else "checkpoint evidence is unresolved", failures=evidence_failures)
        except sqlite3.DatabaseError as exc:
            check("current_checkpoint_pointers", False, "checkpoint inspection failed", error=str(exc))
            check("checkpoint_evidence", False, "checkpoint inspection failed", error=str(exc))

        artifact_failures: list[dict[str, str]] = []
        try:
            for artifact in connection.execute("SELECT artifact_id, storage_path, sha256 FROM raw_artifacts"):
                try:
                    if not self.evidence.verify(artifact["storage_path"], artifact["sha256"]):
                        artifact_failures.append({"artifact_id": artifact["artifact_id"], "reason": "missing_or_hash_mismatch"})
                except StudyOSError as exc:
                    artifact_failures.append({"artifact_id": artifact["artifact_id"], "reason": exc.message})
            check("raw_evidence_integrity", not artifact_failures, "ok" if not artifact_failures else "raw evidence hash verification failed", failures=artifact_failures)
        except sqlite3.DatabaseError as exc:
            check("raw_evidence_integrity", False, "artifact inspection failed", error=str(exc))

        healthy = all(item["healthy"] for item in checks.values())
        return {
            "healthy": healthy,
            "runtime_version": RUNTIME_VERSION,
            "schema_version": schema_version,
            "checks": checks,
        }

    def _record_counts(self, connection: sqlite3.Connection) -> dict[str, int]:
        tables = (
            "subjects", "projects", "domains", "concepts", "sessions", "raw_artifacts", "learning_events",
            "episodes", "attempts", "assessments", "representations", "interventions", "representation_outcomes",
            "checkpoints", "subject_current_checkpoint", "retention_probes", "fossil_exports", "idempotency_records",
        )
        return {table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in tables}

    @staticmethod
    def _file_hashes(root: Path) -> dict[str, str]:
        if not root.exists():
            return {}
        files: dict[str, str] = {}
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            files[path.relative_to(root).as_posix()] = EvidenceStore.sha256_file(path)
        return files

    def backup(self, destination: str | Path | None = None) -> dict:
        backup_dir = Path(destination).expanduser().resolve() if destination else self.config.backups_root / f"backup-{uuid.uuid4().hex}"
        if backup_dir.exists():
            raise validation("Backup destination already exists", destination=str(backup_dir))
        backup_dir.mkdir(parents=True, exist_ok=False)
        evidence_backup = backup_dir / "evidence"
        evidence_backup.mkdir()
        target_db = backup_dir / "study-os.sqlite3"
        target_connection = sqlite3.connect(target_db)
        try:
            self.repository.connection.backup(target_connection)
            target_connection.commit()
        finally:
            target_connection.close()
        for source in sorted(item for item in self.config.evidence_root.rglob("*") if item.is_file()):
            relative = source.relative_to(self.config.evidence_root)
            target = evidence_backup / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        with self.repository.transaction(immediate=False) as connection:
            manifest = {
                "backup_version": "0.1.0",
                "schema_version": int(connection.execute("PRAGMA user_version").fetchone()[0]),
                "contract_version": CONTRACT_VERSION,
                "created_at": utc_now(),
                "database_sha256": EvidenceStore.sha256_file(target_db),
                "evidence_sha256": self._file_hashes(evidence_backup),
                "record_counts": self._record_counts(connection),
            }
        (backup_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return {"backup_path": str(backup_dir), "manifest": manifest}

    def restore(self, backup_path: str | Path) -> dict:
        source = Path(backup_path).expanduser().resolve()
        manifest_path = source / "manifest.json"
        source_db = source / "study-os.sqlite3"
        source_evidence = source / "evidence"
        if not manifest_path.is_file() or not source_db.is_file() or not source_evidence.is_dir():
            raise validation("Backup is incomplete", backup_path=str(source))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("contract_version") != CONTRACT_VERSION:
            raise unsupported("Backup contract version is incompatible", backup_contract=manifest.get("contract_version"))
        if int(manifest.get("schema_version", -1)) != LATEST_SCHEMA_VERSION:
            raise unsupported("Backup schema version is incompatible", backup_schema=manifest.get("schema_version"))
        if EvidenceStore.sha256_file(source_db) != manifest.get("database_sha256"):
            raise integrity("Backup database hash does not match its manifest")
        if self._file_hashes(source_evidence) != manifest.get("evidence_sha256", {}):
            raise integrity("Backup evidence hashes do not match its manifest")

        staging = self.config.root / f".restore-staging-{uuid.uuid4().hex}"
        staging.mkdir(parents=True)
        try:
            shutil.copy2(source_db, staging / "study-os.sqlite3")
            shutil.copytree(source_evidence, staging / "evidence")
            old_db = self.config.db_path.with_name(f"study-os.sqlite3.restore-previous-{uuid.uuid4().hex}")
            old_evidence = self.config.evidence_root.with_name(f"evidence.restore-previous-{uuid.uuid4().hex}")
            self.repository.close()
            if self.config.db_path.exists():
                os.replace(self.config.db_path, old_db)
            if self.config.evidence_root.exists():
                os.replace(self.config.evidence_root, old_evidence)
            os.replace(staging / "study-os.sqlite3", self.config.db_path)
            os.replace(staging / "evidence", self.config.evidence_root)
            self.db = Database(self.config)
            self.repository = SQLiteRepository(self.db)
            self.evidence = EvidenceStore(self.config)
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
        with self.repository.transaction(immediate=False) as connection:
            restored_counts = self._record_counts(connection)
        expected_counts = manifest.get("record_counts", {})
        if expected_counts and restored_counts != expected_counts:
            raise integrity(
                "Restored database record counts do not match the backup manifest",
                expected_counts=expected_counts,
                actual_counts=restored_counts,
            )
        health = self.doctor()
        if not health["healthy"]:
            raise integrity("Restored runtime failed doctor", checks=health["checks"])
        return {
            "restored": True,
            "backup_path": str(source),
            "schema_version": LATEST_SCHEMA_VERSION,
            "record_counts": manifest.get("record_counts", {}),
            "doctor": health,
        }
