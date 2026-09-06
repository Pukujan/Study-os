from __future__ import annotations

import json
import sqlite3
from typing import Any

from ..errors import conflict, integrity, not_found, validation
from ..pir.contracts import (
    ExpansionKind,
    ProblemRunState,
    ResponseKind,
    RunStatus,
    StepKind,
    TeachingBundle,
    TeachingTurn,
)
from ..pir.controller import (
    build_expansion_bundle,
    build_interaction_bundle,
    start_run,
    submit_response,
)
from ..pir.registry import get_asset, resolve_known_problem
from .runtime_base import canonical_json, new_id, request_fingerprint, utc_now


class PIRRuntimeMixin:
    """Durable known-problem PIR semantics layered onto StudyOSService."""

    def _problem_operation_check(
        self,
        connection: sqlite3.Connection,
        operation_kind: str,
        idempotency_key: str,
        request: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise validation("idempotency_key must be a non-empty string")
        row = connection.execute(
            "SELECT request_fingerprint, result_json FROM problem_run_operations "
            "WHERE operation_kind = ? AND idempotency_key = ?",
            (operation_kind, idempotency_key),
        ).fetchone()
        if row is None:
            return None
        if row["request_fingerprint"] != request_fingerprint(request):
            raise conflict(
                "Idempotency key was already used for a different PIR request",
                operation=operation_kind,
                idempotency_key=idempotency_key,
            )
        result = json.loads(row["result_json"])
        if "created" in result:
            result["created"] = False
        return result

    def _problem_operation_record(
        self,
        connection: sqlite3.Connection,
        *,
        operation_kind: str,
        idempotency_key: str,
        request: dict[str, Any],
        problem_run_id: str,
        result: dict[str, Any],
    ) -> None:
        connection.execute(
            "INSERT INTO problem_run_operations "
            "(operation_id, operation_kind, idempotency_key, request_fingerprint, "
            "problem_run_id, result_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                new_id(),
                operation_kind,
                idempotency_key,
                request_fingerprint(request),
                problem_run_id,
                canonical_json(result),
                utc_now(),
            ),
        )

    @staticmethod
    def _state_from_row(row: sqlite3.Row) -> ProblemRunState:
        return ProblemRunState(
            schema_version="study-os.problem-run-state.v0",
            problem_run_id=row["problem_run_id"],
            subject_id=row["subject_id"],
            session_id=row["session_id"],
            canonical_problem_id=row["canonical_problem_id"],
            canonical_pir_revision=row["canonical_pir_revision"],
            controller_revision=row["controller_revision"],
            renderer_revision=row["renderer_revision"],
            assessment_revision=row["assessment_revision"],
            current_step_id=row["current_step_id"],
            status=RunStatus(row["status"]),
            transition_seq=row["transition_seq"],
        )

    def _load_problem_run(
        self,
        connection: sqlite3.Connection,
        problem_run_id: str,
        subject_id: str,
    ) -> ProblemRunState:
        row = connection.execute(
            "SELECT * FROM problem_runs WHERE problem_run_id = ? AND subject_id = ?",
            (problem_run_id, subject_id),
        ).fetchone()
        if row is None:
            raise not_found(
                "Problem run does not exist for subject",
                problem_run_id=problem_run_id,
                subject_id=subject_id,
            )
        return self._state_from_row(row)

    @staticmethod
    def _asset_for_state(state: ProblemRunState):
        asset = get_asset(state.canonical_problem_id)
        if asset is None:
            raise integrity(
                "Pinned canonical PIR asset is unavailable",
                canonical_problem_id=state.canonical_problem_id,
            )
        expected = (
            asset.canonical_pir_revision,
            asset.controller_revision,
            asset.renderer_revision,
            asset.assessment_revision,
        )
        observed = (
            state.canonical_pir_revision,
            state.controller_revision,
            state.renderer_revision,
            state.assessment_revision,
        )
        if expected != observed:
            raise integrity(
                "Persisted problem-run revision tuple does not match installed asset",
                problem_run_id=state.problem_run_id,
            )
        return asset

    @staticmethod
    def _bundle_payload(bundle: TeachingBundle) -> dict[str, Any]:
        return bundle.model_dump(mode="json")

    @staticmethod
    def _terminal_bundle(state: ProblemRunState) -> TeachingBundle:
        turn = TeachingTurn(
            schema_version="study-os.teaching-turn.v0",
            problem_run_id=state.problem_run_id,
            turn_id=f"{state.problem_run_id}:{state.transition_seq}:status",
            canonical_step_id="status",
            turn_kind=StepKind.STATUS,
            representation_id="status",
            learner_visible_markdown=(
                "The reviewed lesson frontier is assembled. Independent mastery remains unproven."
                if state.status == RunStatus.ASSEMBLED_MASTERY_UNPROVEN
                else f"Problem run status: {state.status.value}."
            ),
            response_kind=ResponseKind.NONE,
            allowed_actions=(),
            run_status=state.status,
        )
        return TeachingBundle(
            schema_version="study-os.teaching-bundle.v0",
            problem_run_id=state.problem_run_id,
            turns=(turn,),
            response_turn_id=None,
            run_status=state.status,
        )

    def _current_problem_bundle(self, state: ProblemRunState) -> TeachingBundle:
        if state.status != RunStatus.ACTIVE:
            return self._terminal_bundle(state)
        asset = self._asset_for_state(state)
        reconstructed, bundle = build_interaction_bundle(asset, state)
        if reconstructed != state:
            raise integrity(
                "Persisted problem run is not at an interaction boundary",
                problem_run_id=state.problem_run_id,
            )
        return bundle

    @staticmethod
    def _persist_problem_run(
        connection: sqlite3.Connection,
        previous: ProblemRunState,
        updated: ProblemRunState,
    ) -> None:
        changed = connection.execute(
            "UPDATE problem_runs SET current_step_id = ?, status = ?, transition_seq = ?, "
            "updated_at = ? WHERE problem_run_id = ? AND transition_seq = ?",
            (
                updated.current_step_id,
                updated.status.value,
                updated.transition_seq,
                utc_now(),
                updated.problem_run_id,
                previous.transition_seq,
            ),
        )
        if changed.rowcount != 1:
            raise conflict(
                "Problem run changed before the transition could commit",
                problem_run_id=updated.problem_run_id,
            )

    def resolve_problem(self, *, problem_text: str, domain: str) -> dict[str, Any]:
        try:
            asset = resolve_known_problem(problem_text, domain)
        except ValueError as exc:
            raise validation(str(exc)) from exc
        if asset is None:
            return {
                "status": "needs_compilation",
                "canonical_problem_id": None,
                "canonical_pir_revision": None,
                "reason": "No reviewed known-problem PIR asset matched this exact problem alias.",
            }
        return {
            "status": "known",
            "canonical_problem_id": asset.canonical_problem_id,
            "canonical_pir_revision": asset.canonical_pir_revision,
            "reason": "Matched a reviewed, pinned known-problem PIR asset.",
        }

    def start_problem(
        self,
        *,
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        canonical_problem_id: str,
    ) -> dict[str, Any]:
        request = {
            "session_id": session_id,
            "subject_id": subject_id,
            "canonical_problem_id": canonical_problem_id,
        }
        with self.repository.transaction() as connection:
            cached = self._problem_operation_check(
                connection,
                "start_problem",
                idempotency_key,
                request,
            )
            if cached is not None:
                return cached
            self._session(connection, session_id, subject_id)
            asset = get_asset(canonical_problem_id)
            if asset is None:
                raise not_found(
                    "Canonical problem is not installed as a reviewed known asset",
                    canonical_problem_id=canonical_problem_id,
                )
            problem_run_id = new_id()
            state, bundle = start_run(
                asset,
                problem_run_id=problem_run_id,
                subject_id=subject_id,
                session_id=session_id,
            )
            now = utc_now()
            connection.execute(
                "INSERT INTO problem_runs "
                "(problem_run_id, subject_id, session_id, canonical_problem_id, "
                "canonical_pir_revision, controller_revision, renderer_revision, "
                "assessment_revision, current_step_id, status, transition_seq, "
                "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    state.problem_run_id,
                    state.subject_id,
                    state.session_id,
                    state.canonical_problem_id,
                    state.canonical_pir_revision,
                    state.controller_revision,
                    state.renderer_revision,
                    state.assessment_revision,
                    state.current_step_id,
                    state.status.value,
                    state.transition_seq,
                    now,
                    now,
                ),
            )
            result = {
                "problem_run_id": problem_run_id,
                "canonical_problem_id": state.canonical_problem_id,
                "canonical_pir_revision": state.canonical_pir_revision,
                "run_status": state.status.value,
                "turn": self._bundle_payload(bundle),
                "created": True,
            }
            self._problem_operation_record(
                connection,
                operation_kind="start_problem",
                idempotency_key=idempotency_key,
                request=request,
                problem_run_id=problem_run_id,
                result=result,
            )
            return result

    def get_problem_turn(
        self,
        *,
        problem_run_id: str,
        subject_id: str,
    ) -> dict[str, Any]:
        with self.repository.transaction(immediate=False) as connection:
            state = self._load_problem_run(connection, problem_run_id, subject_id)
            self._asset_for_state(state)
            bundle = self._current_problem_bundle(state)
            return {
                "problem_run_id": state.problem_run_id,
                "run_status": state.status.value,
                "turn": self._bundle_payload(bundle),
            }

    def submit_problem_response(
        self,
        *,
        idempotency_key: str,
        problem_run_id: str,
        subject_id: str,
        turn_id: str,
        response: str,
    ) -> dict[str, Any]:
        if not isinstance(response, str) or not response.strip():
            raise validation("response must be a non-empty string")
        request = {
            "problem_run_id": problem_run_id,
            "subject_id": subject_id,
            "turn_id": turn_id,
            "response": response,
        }
        with self.repository.transaction() as connection:
            cached = self._problem_operation_check(
                connection,
                "submit_problem_response",
                idempotency_key,
                request,
            )
            if cached is not None:
                return cached
            state = self._load_problem_run(connection, problem_run_id, subject_id)
            asset = self._asset_for_state(state)
            step_id = state.current_step_id
            try:
                transition = submit_response(
                    asset,
                    state,
                    turn_id=turn_id,
                    response=response,
                )
            except ValueError as exc:
                if "stale" in str(exc) or "current step" in str(exc):
                    raise conflict(str(exc), problem_run_id=problem_run_id) from exc
                raise validation(str(exc)) from exc

            attempt_id = new_id()
            created_at = utc_now()
            attempt_context = {
                "problem_run_id": problem_run_id,
                "canonical_problem_id": state.canonical_problem_id,
                "canonical_pir_revision": state.canonical_pir_revision,
                "canonical_step_id": step_id,
                "turn_id": turn_id,
                "controller_revision": state.controller_revision,
                "renderer_revision": state.renderer_revision,
                "assessment_revision": state.assessment_revision,
            }
            connection.execute(
                "INSERT INTO attempts "
                "(attempt_id, session_id, subject_id, task_id, response_json, "
                "assistance_level, context_json, idempotency_key, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    attempt_id,
                    state.session_id,
                    subject_id,
                    f"pir:{state.canonical_problem_id}:{step_id}",
                    canonical_json(response),
                    "none",
                    canonical_json(attempt_context),
                    f"pir:{idempotency_key}:attempt",
                    created_at,
                ),
            )
            event_id = new_id()
            event_payload = {
                **attempt_context,
                "attempt_id": attempt_id,
                "outcome": transition.outcome.value,
            }
            connection.execute(
                "INSERT INTO learning_events "
                "(event_id, session_id, subject_id, evidence_class, event_type, payload_json, "
                "payload_version, source_ids_json, idempotency_key, created_at) "
                "VALUES (?, ?, ?, 'observed', 'pir_response_outcome', ?, ?, ?, ?, ?)",
                (
                    event_id,
                    state.session_id,
                    subject_id,
                    canonical_json(event_payload),
                    "0.1.0",
                    canonical_json([attempt_id]),
                    f"pir:{idempotency_key}:outcome",
                    created_at,
                ),
            )
            self._persist_problem_run(connection, state, transition.state)
            result = {
                "problem_run_id": problem_run_id,
                "outcome": transition.outcome.value,
                "run_status": transition.state.status.value,
                "turn": self._bundle_payload(transition.bundle),
                "created": True,
            }
            self._problem_operation_record(
                connection,
                operation_kind="submit_problem_response",
                idempotency_key=idempotency_key,
                request=request,
                problem_run_id=problem_run_id,
                result=result,
            )
            return result

    def request_problem_expansion(
        self,
        *,
        idempotency_key: str,
        problem_run_id: str,
        subject_id: str,
        turn_id: str,
        request_kind: str,
        learner_request: str,
    ) -> dict[str, Any]:
        if not isinstance(learner_request, str) or not learner_request.strip():
            raise validation("learner_request must be a non-empty string")
        try:
            kind = ExpansionKind(request_kind)
        except ValueError as exc:
            raise validation("request_kind is not a supported expansion kind") from exc
        request = {
            "problem_run_id": problem_run_id,
            "subject_id": subject_id,
            "turn_id": turn_id,
            "request_kind": kind.value,
            "learner_request": learner_request,
        }
        with self.repository.transaction() as connection:
            cached = self._problem_operation_check(
                connection,
                "request_problem_expansion",
                idempotency_key,
                request,
            )
            if cached is not None:
                return cached
            state = self._load_problem_run(connection, problem_run_id, subject_id)
            asset = self._asset_for_state(state)
            try:
                bundle = build_expansion_bundle(
                    asset,
                    state,
                    turn_id=turn_id,
                    kind=kind,
                )
            except ValueError as exc:
                if "stale" in str(exc) or "current step" in str(exc):
                    raise conflict(str(exc), problem_run_id=problem_run_id) from exc
                raise validation(str(exc)) from exc

            event_id = new_id()
            created_at = utc_now()
            payload = {
                "problem_run_id": problem_run_id,
                "canonical_problem_id": state.canonical_problem_id,
                "canonical_pir_revision": state.canonical_pir_revision,
                "canonical_step_id": state.current_step_id,
                "turn_id": turn_id,
                "request_kind": kind.value,
                "learner_request": learner_request,
                "transition_seq": state.transition_seq,
            }
            connection.execute(
                "INSERT INTO learning_events "
                "(event_id, session_id, subject_id, evidence_class, event_type, payload_json, "
                "payload_version, source_ids_json, idempotency_key, created_at) "
                "VALUES (?, ?, ?, 'observed', 'pir_expansion_request', ?, ?, '[]', ?, ?)",
                (
                    event_id,
                    state.session_id,
                    subject_id,
                    canonical_json(payload),
                    "0.1.0",
                    f"pir:{idempotency_key}:expansion",
                    created_at,
                ),
            )
            connection.execute(
                "UPDATE problem_runs SET updated_at = ? WHERE problem_run_id = ?",
                (created_at, problem_run_id),
            )
            result = {
                "problem_run_id": problem_run_id,
                "run_status": state.status.value,
                "turn": self._bundle_payload(bundle),
                "created": True,
            }
            self._problem_operation_record(
                connection,
                operation_kind="request_problem_expansion",
                idempotency_key=idempotency_key,
                request=request,
                problem_run_id=problem_run_id,
                result=result,
            )
            return result
