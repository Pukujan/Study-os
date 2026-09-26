"""Player service: DB-backed operations for the Study OS lesson player v2."""

from __future__ import annotations

import uuid
from typing import Any

from psycopg.types.json import Jsonb

from study_os.web.db import Conn, Database
from study_os.web.models import LLMTransport
from study_os.web.privacy import scrub
from study_os.web.service import DbGate, ServiceError

from . import content
from . import engine
from . import tutor as tutor_module
from . import presentation


class PlayerService:
    """Coordinates the pure player engine with durable player/session state."""

    def __init__(self, db: Database, settings: Any, *, llm: LLMTransport | None) -> None:
        self.db = db
        self.settings = settings
        self.llm = llm

    def _gate(self, subject_id: str | None) -> DbGate:
        return DbGate(self.db, self.settings, subject_id)

    def _session_row(
        self, conn: Conn, principal: Any, session_id: str, *, lock: bool = False
    ) -> dict[str, Any]:
        try:
            uuid.UUID(session_id)
        except ValueError as exc:
            raise ServiceError("not_found", 404) from exc
        row = conn.execute(
            "SELECT session_id, subject_id, lesson_id, lesson_revision, state, started_at, updated_at, ended_at "
            "FROM learn.player_session WHERE session_id = %s" + (" FOR UPDATE" if lock else ""),
            (session_id,),
        ).fetchone()
        if row is None or str(row["subject_id"]) != principal.subject_id:
            raise ServiceError("not_found", 404)
        return row

    def _next_seq(self, conn: Conn, session_id: str) -> int:
        row = conn.execute(
            "SELECT coalesce(max(seq), 0) + 1 AS next_seq FROM learn.player_event WHERE session_id = %s",
            (session_id,),
        ).fetchone()
        return int(row["next_seq"]) if row else 1

    def _log_event(
        self,
        conn: Conn,
        session_id: str,
        step_id: str | None,
        event: str,
        *,
        modality: str | None = None,
        outcome: str | None = None,
        response: str | None = None,
        idempotency_key: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        scrubbed = scrub(response) if response else None
        conn.execute(
            "INSERT INTO learn.player_event (session_id, seq, step_id, event, modality, outcome, "
            "response_scrubbed, idempotency_key, payload) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                session_id,
                self._next_seq(conn, session_id),
                step_id,
                event,
                modality,
                outcome,
                scrubbed,
                idempotency_key,
                Jsonb(payload or {}),
            ),
        )

    def _update_session_state(self, conn: Conn, session_id: str, state: dict[str, Any]) -> None:
        conn.execute(
            "UPDATE learn.player_session SET state = %s, updated_at = now() WHERE session_id = %s",
            (Jsonb(state), session_id),
        )

    def _view(
        self,
        lesson: dict[str, Any],
        state: dict[str, Any],
        principal: Any,
        session_id: str,
    ) -> dict[str, Any]:
        view = engine.view(lesson, state)
        view["session_id"] = session_id
        view["is_guest"] = bool(getattr(principal, "is_guest", False))
        return view

    def start_or_resume(self, principal: Any, lesson_id: str) -> dict[str, Any]:
        lesson = content.load_lesson(lesson_id)
        with self.db.tx() as conn:
            row = conn.execute(
                "SELECT session_id, state FROM learn.player_session "
                "WHERE subject_id = %s AND lesson_id = %s AND ended_at IS NULL "
                "ORDER BY started_at DESC LIMIT 1",
                (principal.subject_id, lesson_id),
            ).fetchone()
            if row is not None:
                state = dict(row["state"])
                sid = str(row["session_id"])
                self._update_session_state(conn, sid, state)
                return self._view(lesson, state, principal, sid)
            session_id = str(uuid.uuid4())
            state = engine.start(lesson)
            conn.execute(
                "INSERT INTO learn.player_session (session_id, subject_id, lesson_id, lesson_revision, state) "
                "VALUES (%s, %s, %s, %s, %s)",
                (session_id, principal.subject_id, lesson_id, lesson.get("revision", lesson_id + ".v1"), Jsonb(state)),
            )
            return self._view(lesson, state, principal, session_id)

    def get(self, principal: Any, session_id: str) -> dict[str, Any]:
        lesson, state = self._load(principal, session_id)
        return self._view(lesson, state, principal, session_id)

    def _load(self, principal: Any, session_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        with self.db.tx() as conn:
            row = self._session_row(conn, principal, session_id)
        lesson = content.load_lesson(row["lesson_id"])
        return lesson, dict(row["state"])

    def attempt(
        self, principal: Any, session_id: str, response: str, modality: str, idempotency_key: str
    ) -> dict[str, Any]:
        if not idempotency_key or len(idempotency_key) > 80:
            raise ServiceError("idempotency_key_required")
        response = (response or "")[:2000]
        lesson, state = self._load(principal, session_id)
        with self.db.tx() as conn:
            row = self._session_row(conn, principal, session_id, lock=True)
            state = dict(row["state"])
            prior = conn.execute(
                "SELECT id FROM learn.player_event WHERE session_id = %s AND idempotency_key = %s",
                (session_id, f"{principal.subject_id}:{idempotency_key}"),
            ).fetchone()
            if prior is not None:
                return self._view(lesson, state, principal, session_id)
            if state["phase"] != "probe":
                raise ServiceError("probe_not_open")
            state, feedback = engine.attempt(lesson, state, response, modality)
            self._update_session_state(conn, session_id, state)
            self._log_event(
                conn,
                session_id,
                engine._current_step(lesson, state)["step_id"],  # noqa: SLF001
                "attempt",
                modality=modality,
                outcome=feedback["outcome"],
                response=response,
                idempotency_key=f"{principal.subject_id}:{idempotency_key}",
                payload={"feedback": feedback},
            )
        return self._view(lesson, state, principal, session_id)

    def confused(self, principal: Any, session_id: str) -> dict[str, Any]:
        lesson, state = self._load(principal, session_id)
        with self.db.tx() as conn:
            row = self._session_row(conn, principal, session_id, lock=True)
            state = dict(row["state"])
            if state["phase"] != "probe":
                raise ServiceError("probe_not_open")
            state, feedback = engine.confused(lesson, state)
            self._update_session_state(conn, session_id, state)
            self._log_event(
                conn,
                session_id,
                engine._current_step(lesson, state)["step_id"],  # noqa: SLF001
                "confused",
                payload={"feedback": feedback},
            )
        return self._view(lesson, state, principal, session_id)

    def next(self, principal: Any, session_id: str) -> dict[str, Any]:
        lesson, state = self._load(principal, session_id)
        with self.db.tx() as conn:
            row = self._session_row(conn, principal, session_id, lock=True)
            state = dict(row["state"])
            state = engine.next(lesson, state)
            self._update_session_state(conn, session_id, state)
            self._log_event(
                conn,
                session_id,
                engine._current_step(lesson, state)["step_id"],  # noqa: SLF001
                "next",
                payload={},
            )
        return self._view(lesson, state, principal, session_id)

    def adapt(self, principal: Any, session_id: str, kind: str) -> dict[str, Any]:
        lesson, state = self._load(principal, session_id)
        if kind not in {"example", "easier", "harder", "back"}:
            raise ServiceError("invalid_adapt_kind")
        with self.db.tx() as conn:
            self._session_row(conn, principal, session_id, lock=True)
            state, info = engine.adapt(lesson, state, kind)
            self._update_session_state(conn, session_id, state)
            self._log_event(
                conn,
                session_id,
                engine._current_step(lesson, state)["step_id"],  # noqa: SLF001
                "adapt",
                payload={"kind": kind, "info": info},
            )
        return self._view(lesson, state, principal, session_id)

    def tutor(self, principal: Any, session_id: str, message: str) -> dict[str, Any]:
        message = (message or "")[:500]
        lesson, state = self._load(principal, session_id)
        gate = self._gate(principal.subject_id)
        result = tutor_module.reply(
            self.llm,
            self.settings,
            lesson,
            state,
            message,
            gate=gate,
            llm_enabled=self.settings.llm_enabled,
        )
        applied_update = None
        with self.db.tx() as conn:
            row = self._session_row(conn, principal, session_id, lock=True)
            locked_state = dict(row["state"])
            if (result.regenerate_presentation is not None
                    and presentation.context(lesson, locked_state) == presentation.context(lesson, state)):
                applied_update = presentation.apply(lesson, locked_state, result.regenerate_presentation, {
                    "prompt_version": result.prompt_version,
                    "model": result.model,
                    "route": result.route,
                    "served": result.served,
                })
                self._update_session_state(conn, session_id, locked_state)
                state = locked_state
            llm_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO learn.llm_interaction (id, session_id, step_id, operation, prompt_id, "
                "prompt_version, route, model, messages, response_text, served, tokens_in, tokens_out, "
                "cost_usd, latency_ms, validation_codes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    llm_id,
                    session_id,
                    engine._current_step(lesson, state)["step_id"],  # noqa: SLF001
                    "tutor_reply",
                    result.prompt_version,
                    result.prompt_version,
                    result.route,
                    result.model,
                    Jsonb(result.messages),
                    scrub(result.reply_md),
                    result.served,
                    result.tokens,
                    0,
                    result.cost,
                    result.latency,
                    list(result.validation_codes),
                ),
            )
            self._log_event(
                conn,
                session_id,
                engine._current_step(lesson, state)["step_id"],  # noqa: SLF001
                "tutor",
                payload={
                    "served": result.served,
                    "prompt_version": result.prompt_version,
                    "route": result.route,
                    "model": result.model,
                    "regenerate_presentation": applied_update,
                },
            )
        return {
            "message_id": llm_id,
            "reply_md": result.reply_md,
            "suggested_action": result.suggested_action,
            "prompt_version": result.prompt_version,
            "model": result.model,
            "served": result.served,
            "regenerate_presentation": applied_update,
        }

    def feedback(self, principal: Any, body: Any) -> dict[str, Any]:
        if body.target_kind == "step":
            return self._step_review(principal, body)
        if body.target_kind == "tutor_message":
            return self._tutor_message_feedback(principal, body)
        raise ServiceError("invalid_target_kind")

    def _tutor_message_feedback(self, principal: Any, body: Any) -> dict[str, Any]:
        if body.rating not in ("like", "dislike"):
            raise ServiceError("invalid_rating")
        allowed_reasons = {"confusing", "too_long", "too_easy", "wrong", "not_helpful", "other"}
        for reason in body.reasons or []:
            if reason not in allowed_reasons:
                raise ServiceError("invalid_reason")
        free = scrub(body.free_text) if body.free_text else None

        prompt_version: str | None = None
        model: str | None = None
        llm_id: str | None = None
        session_id: str | None = body.session_id
        if body.target_id:
            with self.db.tx() as conn:
                row = conn.execute(
                    "SELECT id, session_id, prompt_version, model FROM learn.llm_interaction WHERE id = %s",
                    (body.target_id,),
                ).fetchone()
                if row is not None:
                    llm_id = str(row["id"])
                    prompt_version = row["prompt_version"]
                    model = row["model"]
                    if session_id is None:
                        session_id = str(row["session_id"]) if row["session_id"] else None

        with self.db.tx() as conn:
            feedback_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO ux.feedback (feedback_id, subject_id, session_id, step_id, target_kind, "
                "target_id, rating, reasons, free_text_scrubbed, prompt_version, model, llm_interaction_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    feedback_id,
                    principal.subject_id,
                    session_id,
                    body.step_id,
                    body.target_kind,
                    body.target_id,
                    body.rating,
                    list(body.reasons or []),
                    free,
                    prompt_version,
                    model,
                    llm_id,
                ),
            )
        return {"ok": True, "feedback_id": feedback_id}

    def _step_review(self, principal: Any, body: Any) -> dict[str, Any]:
        """Append-only 1-5 step review bound to the served step/variant/version.

        The committed ``ux.feedback`` row is the decision record: no ``learn.*``
        event is written and a review never advances the learner path.
        """

        rating = body.rating
        if type(rating) is not int or not 1 <= rating <= 5:
            raise ServiceError("invalid_rating")
        why = (body.free_text or "").strip()
        if not why:
            raise ServiceError("why_required")
        if not body.session_id or not body.step_id or not body.target_id:
            raise ServiceError("review_target_required")
        key = (body.idempotency_key or "").strip()
        if not key:
            raise ServiceError("idempotency_key_required")
        if body.presentation_version is None:
            raise ServiceError("presentation_version_required")
        if body.reasons:
            raise ServiceError("invalid_reason")
        free = scrub(why)
        with self.db.tx() as conn:
            row = self._session_row(conn, principal, body.session_id, lock=True)
            state = dict(row["state"])
            lesson = content.load_lesson(row["lesson_id"])
            step = lesson["steps"][state["step_index"]]
            if (body.step_id != step["step_id"]
                    or body.target_id != f"{step['step_id']}:{state['variant_index']}"
                    or body.presentation_version != int(state.get("presentation_version", 0))):
                raise ServiceError("stale_review_target", 409)
            existing = self._review_by_key(conn, principal.subject_id, key)
            if existing is not None:
                return self._review_receipt(existing, body, free)
            feedback_id = str(uuid.uuid4())
            inserted = conn.execute(
                "INSERT INTO ux.feedback (feedback_id, subject_id, session_id, step_id, target_kind, "
                "target_id, rating, free_text_scrubbed, presentation_version, idempotency_key) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (subject_id, idempotency_key) WHERE idempotency_key IS NOT NULL DO NOTHING "
                "RETURNING feedback_id",
                (
                    feedback_id,
                    principal.subject_id,
                    body.session_id,
                    body.step_id,
                    "step",
                    body.target_id,
                    str(rating),
                    free,
                    body.presentation_version,
                    key,
                ),
            ).fetchone()
            if inserted is None:
                existing = self._review_by_key(conn, principal.subject_id, key)
                if existing is None:
                    raise ServiceError("review_conflict", 409)
                return self._review_receipt(existing, body, free)
        return {"ok": True, "feedback_id": feedback_id}

    @staticmethod
    def _review_by_key(conn: Conn, subject_id: str, key: str) -> dict[str, Any] | None:
        return conn.execute(
            "SELECT * FROM ux.feedback WHERE subject_id = %s AND idempotency_key = %s",
            (subject_id, key),
        ).fetchone()

    @staticmethod
    def _review_receipt(row: dict[str, Any], body: Any, free: str) -> dict[str, Any]:
        same = (
            str(row["session_id"]) == body.session_id
            and row["step_id"] == body.step_id
            and row["target_id"] == body.target_id
            and row["rating"] == str(body.rating)
            and (row["free_text_scrubbed"] or "") == free
            and row["presentation_version"] == body.presentation_version
        )
        if not same:
            raise ServiceError("review_conflict", 409)
        return {"ok": True, "feedback_id": str(row["feedback_id"])}

    def admin_feedback(self, principal: Any) -> dict[str, Any]:
        if principal.role != "admin":
            raise ServiceError("forbidden", 403)
        with self.db.tx() as conn:
            rows = conn.execute(
                "SELECT feedback_id, created_at, subject_id, session_id, step_id, target_kind, target_id, "
                "rating, reasons, free_text_scrubbed, prompt_version, model, presentation_version "
                "FROM analytics.v_feedback ORDER BY created_at DESC LIMIT 200"
            ).fetchall()
            stats = conn.execute(
                "SELECT prompt_version, rating, count(*) AS n FROM ux.feedback "
                "WHERE prompt_version IS NOT NULL AND rating IN ('like', 'dislike') "
                "GROUP BY prompt_version, rating"
            ).fetchall()
            review_stats = conn.execute(
                "SELECT presentation_version, rating, count(*) AS n FROM ux.feedback "
                "WHERE rating IN ('1', '2', '3', '4', '5') "
                "GROUP BY presentation_version, rating ORDER BY presentation_version"
            ).fetchall()
        by_version: dict[str, dict[str, Any]] = {}
        for row in stats:
            pv = row["prompt_version"]
            if pv not in by_version:
                by_version[pv] = {"likes": 0, "dislikes": 0, "top_reasons": {}}
            if row["rating"] == "like":
                by_version[pv]["likes"] += int(row["n"])
            else:
                by_version[pv]["dislikes"] += int(row["n"])
        reviews_by_version: dict[Any, dict[str, int]] = {}
        for row in review_stats:
            bucket = reviews_by_version.setdefault(row["presentation_version"], {})
            bucket[row["rating"]] = int(row["n"])
        return {
            "rows": [dict(r) for r in rows],
            "by_prompt_version": [
                {
                    "prompt_version": pv,
                    "likes": data["likes"],
                    "dislikes": data["dislikes"],
                    "top_reasons": data["top_reasons"],
                }
                for pv, data in by_version.items()
            ],
            # Ordinal 1-5 step reviews, kept separate from historical thumbs.
            "step_reviews": [
                {
                    "presentation_version": version,
                    "counts": {str(score): counts.get(str(score), 0) for score in range(1, 6)},
                    "total": sum(counts.values()),
                }
                for version, counts in sorted(
                    reviews_by_version.items(), key=lambda item: (item[0] is None, item[0])
                )
            ],
        }

    def lanes(self, principal: Any) -> dict[str, Any]:
        from . import lanes as lanes_module

        progress_by_lesson: dict[str, str] = {}
        open_sessions: dict[str, Any] = {}
        with self.db.tx() as conn:
            rows = conn.execute(
                "SELECT session_id, lesson_id, state, ended_at FROM learn.player_session "
                "WHERE subject_id = %s",
                (principal.subject_id,),
            ).fetchall()
        for row in rows:
            state = row["state"] or {}
            status = state.get("status_by_step", {})
            total = len(status)
            done = sum(1 for s in status.values() if s in {"done", "needs_review"})
            if total > 0 and done >= total:
                progress_by_lesson[row["lesson_id"]] = "done"
            elif done > 0:
                progress_by_lesson[row["lesson_id"]] = "in_progress"
            else:
                progress_by_lesson[row["lesson_id"]] = "not_started"
            if row["ended_at"] is None:
                open_sessions[row["lesson_id"]] = str(row["session_id"])
        return lanes_module.lanes_payload(progress_by_lesson, open_sessions)
