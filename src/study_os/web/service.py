"""Application service: persists controller transitions and decisions in Postgres (#85)."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fsrs import Card, Rating, Scheduler
from psycopg.types.json import Jsonb

from study_os.pir.registry import CANONICAL_PIR_REVISION, CANONICAL_PROBLEM_ID, sliding_window_asset

from . import packs
from .auth import Principal
from .config import PRICE_SNAPSHOT_ID, Settings
from .controller import WEB_CONTROLLER_REVISION, ControllerError, Transition, TurnSpec, WebController
from .db import Conn, Database
from .decisions import DecisionLayer, DecisionRecord, InterpretationRecord
from .interpreter import REWRITE_PROMPT_VERSION, rewrite_failed_step
from .models import DecisionTransport, LLMTransport
from .privacy import SCRUBBER_VERSION, scrub
from .validator import VALIDATOR_VERSION

_SCHEDULER = Scheduler()


class ServiceError(Exception):
    def __init__(self, code: str, status: int = 400) -> None:
        super().__init__(code)
        self.code = code
        self.status = status


class DbGate:
    """Budget/cache gate backed by Postgres (P-LLM-5, D018 caps, response cache)."""

    def __init__(self, db: Database, settings: Settings, subject_id: str | None) -> None:
        self.db = db
        self.settings = settings
        self.subject_id = subject_id

    def allow(self, kind: str) -> tuple[bool, str]:
        with self.db.tx() as conn:
            spend = conn.execute(
                "SELECT coalesce((SELECT sum(cost_usd) FROM learn.decision WHERE created_at >= date_trunc('day', now())), 0)"
                " + coalesce((SELECT sum(cost_usd) FROM learn.interpretation WHERE created_at >= date_trunc('day', now())), 0) AS day,"
                " coalesce((SELECT sum(cost_usd) FROM learn.decision WHERE created_at >= date_trunc('month', now())), 0)"
                " + coalesce((SELECT sum(cost_usd) FROM learn.interpretation WHERE created_at >= date_trunc('month', now())), 0) AS month"
            ).fetchone()
            assert spend is not None
            if float(spend["day"]) >= self.settings.global_daily_spend_usd:
                return False, "global_daily_spend_cap"
            if float(spend["month"]) >= self.settings.llm_spend_cap_usd:
                return False, "monthly_spend_cap"
            if self.subject_id:
                row = conn.execute(
                    "SELECT count(*) AS n FROM learn.decision d JOIN learn.turn t USING (turn_id) "
                    "JOIN learn.session s USING (session_id) WHERE s.subject_id = %s "
                    "AND d.route IN ('decision_model', 'frontier_llm') AND d.created_at >= date_trunc('day', now())",
                    (self.subject_id,),
                ).fetchone()
                if row is not None and int(row["n"]) >= self.settings.user_daily_model_calls:
                    return False, "user_daily_model_cap"
        return True, "ok"

    def cache_get(self, key: str) -> dict[str, Any] | None:
        with self.db.tx() as conn:
            row = conn.execute(
                "UPDATE cache.model_response SET hits = hits + 1 WHERE key_hash = %s RETURNING response", (key,)
            ).fetchone()
        return None if row is None else dict(row["response"])

    def cache_put(self, key: str, kind: str, model: str, response: dict[str, Any]) -> None:
        with self.db.tx() as conn:
            conn.execute(
                "INSERT INTO cache.model_response (key_hash, kind, model, response) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (key_hash) DO NOTHING",
                (key, kind, model, Jsonb(response)),
            )


def _module_versions(track: str, asset_revision: str) -> dict[str, str]:
    return {
        "controller_revision": WEB_CONTROLLER_REVISION,
        "content_revision": asset_revision,
        "interpreter_route": "inferhub:cb/glm-5.3>cb/deepseek-v4.1-flash",
        "price_snapshot_id": PRICE_SNAPSHOT_ID,
        "prompt_template_version": REWRITE_PROMPT_VERSION,
        "validator_version": VALIDATOR_VERSION,
        "scrubber_version": SCRUBBER_VERSION,
        "decision_model": "openrouter:typesafe/jev-1.13",
        "track": track,
    }


class StudyService:
    def __init__(
        self,
        db: Database,
        settings: Settings,
        *,
        jev: DecisionTransport | None,
        llm: LLMTransport | None,
        gate_factory: Any = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.jev = jev
        self.llm = llm
        self.gate_factory = gate_factory or (lambda subject_id: DbGate(db, settings, subject_id))
        self.controller = WebController({CANONICAL_PROBLEM_ID: sliding_window_asset()})

    def layer(self, subject_id: str | None) -> DecisionLayer:
        return DecisionLayer(self.settings, self.jev, self.llm, self.gate_factory(subject_id))

    # ---------- reads ----------
    def _session_row(self, conn: Conn, principal: Principal, session_id: str, *, lock: bool = False) -> dict[str, Any]:
        try:
            uuid.UUID(session_id)
        except ValueError as exc:
            raise ServiceError("not_found", 404) from exc
        row = conn.execute(
            "SELECT session_id::text AS session_id, subject_id::text AS subject_id, track, ended_at, module_version_set "
            "FROM learn.session WHERE session_id = %s" + (" FOR UPDATE" if lock else ""),
            (session_id,),
        ).fetchone()
        if row is None or row["subject_id"] != principal.subject_id:
            raise ServiceError("not_found", 404)  # P-API-2
        return row

    def _last_turn(self, conn: Conn, session_id: str) -> dict[str, Any] | None:
        return conn.execute(
            "SELECT turn_id::text AS turn_id, seq, run_state, state_after FROM learn.turn "
            "WHERE session_id = %s ORDER BY seq DESC LIMIT 1",
            (session_id,),
        ).fetchone()

    def _turns_after(self, conn: Conn, session_id: str, after_seq: int, upto: int | None = None) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT turn_id::text AS turn_id, seq, state_after, payload, served_from FROM learn.turn "
            "WHERE session_id = %s AND seq > %s AND (%s::int IS NULL OR seq <= %s::int) ORDER BY seq",
            (session_id, after_seq, upto, upto),
        ).fetchall()
        return [self._public_turn(r) for r in rows]

    @staticmethod
    def _public_turn(row: dict[str, Any]) -> dict[str, Any]:
        payload = dict(row["payload"])
        payload.update({"turn_id": row["turn_id"], "seq": row["seq"], "state": row["state_after"], "served_from": row["served_from"]})
        return payload

    def session_view(self, principal: Principal, session_id: str) -> dict[str, Any]:
        with self.db.tx() as conn:
            row = self._session_row(conn, principal, session_id)
            last = self._last_turn(conn, session_id)
            # Resume view: the most recent turns up to the last awaiting probe.
            turns = conn.execute(
                "SELECT turn_id::text AS turn_id, seq, state_after, payload, served_from FROM learn.turn "
                "WHERE session_id = %s ORDER BY seq DESC LIMIT 6",
                (session_id,),
            ).fetchall()
        public = [self._public_turn(t) for t in reversed(turns)]
        return {
            "session_id": session_id,
            "track": row["track"],
            "state": last["state_after"] if last else "START",
            "turns": public,
            "topic_id": (last["run_state"] or {}).get("topic_id") if last else None,
        }

    # ---------- writes ----------
    def _insert_turns(
        self, conn: Conn, session_id: str, start_seq: int, specs: list[TurnSpec], state: dict[str, Any]
    ) -> list[str]:
        ids: list[str] = []
        seq = start_seq
        for spec in specs:
            seq += 1
            turn_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO learn.turn (turn_id, session_id, seq, state_before, event, state_after, step_id, item_id, "
                "assistance_level, representation_id, operation, served_from, controller_revision, run_state, payload) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    turn_id, session_id, seq, spec.state_before, spec.event, spec.state_after, spec.step_id,
                    spec.item_id, spec.assistance_level, spec.representation_id, spec.operation, spec.served_from,
                    WEB_CONTROLLER_REVISION, Jsonb(state), Jsonb(spec.payload),
                ),
            )
            ids.append(turn_id)
        return ids

    def _apply_side_effects(self, conn: Conn, subject_id: str, tr: Transition, attempt_id: str | None) -> None:
        for cap in tr.capability:
            prev = conn.execute(
                "SELECT to_state FROM learn.capability_transition WHERE subject_id = %s AND kc_id = %s ORDER BY id DESC LIMIT 1",
                (subject_id, cap.kc_id),
            ).fetchone()
            conn.execute(
                "INSERT INTO learn.capability_transition (subject_id, kc_id, from_state, to_state, evidence_attempt_ids, "
                "assistance_level, \"window\") VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (subject_id, cap.kc_id, prev["to_state"] if prev else None, cap.to_state,
                 [attempt_id] if attempt_id else [], cap.assistance_level, cap.window),
            )
        now = datetime.now(timezone.utc)
        for item_id, kc, correct in tr.review_updates:
            row = conn.execute(
                "SELECT fsrs_state FROM learn.review_schedule WHERE subject_id = %s AND item_id = %s", (subject_id, item_id)
            ).fetchone()
            card = Card.from_dict(row["fsrs_state"]) if row else Card()
            card, _log = _SCHEDULER.review_card(card, Rating.Good if correct else Rating.Again, review_datetime=now)
            conn.execute(
                "INSERT INTO learn.review_schedule (subject_id, item_id, kc_id, fsrs_state, due_at, updated_at) "
                "VALUES (%s,%s,%s,%s,%s,now()) ON CONFLICT (subject_id, item_id) DO UPDATE SET "
                "fsrs_state = EXCLUDED.fsrs_state, due_at = EXCLUDED.due_at, updated_at = now()",
                (subject_id, item_id, kc, Jsonb(card.to_dict()), card.due),
            )
        if tr.topic_state:
            topic_id, state = tr.topic_state
            conn.execute(
                "INSERT INTO learn.topic_progress (subject_id, track, topic_id, state) VALUES (%s,'hesi',%s,%s) "
                "ON CONFLICT (subject_id, track, topic_id) DO UPDATE SET state = CASE "
                "WHEN learn.topic_progress.state IN ('assembled','checkpoint_passed') AND EXCLUDED.state = 'in_progress' "
                "THEN learn.topic_progress.state ELSE EXCLUDED.state END, updated_at = now()",
                (subject_id, topic_id, state),
            )

    def _record_decisions(self, conn: Conn, turn_id: str | None, decisions: list[DecisionRecord]) -> None:
        for d in decisions:
            conn.execute(
                "INSERT INTO learn.decision (decision_id, turn_id, decision_type, state_hash, question_schema, route, "
                "model_id, model_version, question_type, label, probabilities, confidence, threshold_used, acted_on, "
                "escalated, audit_sample, error, latency_ms, tokens_in, tokens_out, cost_usd) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    str(uuid.uuid4()), turn_id, d.decision_type, d.state_hash, Jsonb(d.question_schema), d.route,
                    d.model_id, d.model_version, d.question_type, d.label,
                    Jsonb(d.probabilities) if d.probabilities is not None else None, d.confidence, d.threshold_used,
                    d.acted_on, d.escalated, d.audit_sample, d.error, d.latency_ms, d.tokens_in, d.tokens_out, d.cost_usd,
                ),
            )

    def _record_interpretations(self, conn: Conn, turn_id: str | None, recs: list[InterpretationRecord]) -> None:
        for r in recs:
            iid = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO learn.interpretation (id, turn_id, operation, route, model, price_snapshot_id, "
                "prompt_template_version, input_tokens, output_tokens, cost_usd, latency_ms, validation_result, violation_codes) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (iid, turn_id, r.operation, r.route, r.model, PRICE_SNAPSHOT_ID, r.prompt_template_version,
                 r.tokens_in, r.tokens_out, r.cost_usd, r.latency_ms, r.validation_result, list(r.violation_codes)),
            )
            if r.generation is not None:
                conn.execute(
                    "INSERT INTO learn.generation (generation_id, interpretation_id, step_id, content_json, validated) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (str(uuid.uuid4()), iid, r.step_id or "", Jsonb(r.generation), bool(r.generation.get("validated"))),
                )

    def start_session(
        self, principal: Principal, *, track: str, topic_id: str | None = None, checkpoint: str | None = None
    ) -> dict[str, Any]:
        if track not in ("dsa", "hesi"):
            raise ServiceError("invalid_track")
        with self.db.tx() as conn:
            conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (principal.subject_id,))
            # Resume an open session of the same kind.
            open_rows = conn.execute(
                "SELECT s.session_id::text AS session_id, t.run_state, t.state_after FROM learn.session s "
                "JOIN LATERAL (SELECT run_state, state_after FROM learn.turn WHERE session_id = s.session_id ORDER BY seq DESC LIMIT 1) t ON true "
                "WHERE s.subject_id = %s AND s.track = %s AND s.ended_at IS NULL ORDER BY s.started_at DESC LIMIT 5",
                (principal.subject_id, track),
            ).fetchall()
            for r in open_rows:
                rs = r["run_state"] or {}
                if r["state_after"] in ("SESSION_DONE",):
                    continue
                same = (track == "dsa") or (rs.get("topic_id") == topic_id and rs.get("section_id") == checkpoint)
                if same:
                    return self.session_view(principal, r["session_id"]) | {"resumed": True}
            session_id = str(uuid.uuid4())
            if track == "dsa":
                prev = conn.execute(
                    "SELECT t.run_state FROM learn.turn t JOIN learn.session s USING (session_id) "
                    "WHERE s.subject_id = %s AND s.track = 'dsa' ORDER BY t.created_at DESC, t.seq DESC LIMIT 1",
                    (principal.subject_id,),
                ).fetchone()
                resume = (prev["run_state"] or {}).get("pir") if prev else None
                revision = CANONICAL_PIR_REVISION
                self._insert_session(conn, session_id, principal.subject_id, track, revision)
                tr = self.controller.start_pir(track="dsa", asset_id=CANONICAL_PROBLEM_ID, session_id=session_id,
                                               subject_id=principal.subject_id, resume=resume)
            elif checkpoint:
                section = next((s for s in packs.topic_graph() if s["section_id"] == checkpoint), None)
                if section is None:
                    raise ServiceError("unknown_checkpoint", 404)
                pool = [i for t in section["topics"] for i in packs.topic_items(t["topic_id"], "check")]
                if not pool:
                    raise ServiceError("checkpoint_unavailable", 409)
                n = int(packs.load_blueprint()["checkpoint_policy"]["items_per_checkpoint"])
                seed = f"{principal.subject_id}|{datetime.now(timezone.utc).date()}"
                pool.sort(key=lambda i: hashlib.sha256(f"{seed}|{i.item_id}".encode()).hexdigest())
                self._insert_session(conn, session_id, principal.subject_id, track, packs.pack_revision())
                tr = self.controller.start_quiz(track="hesi", mode="checkpoint", items=[i.item_id for i in pool[:n]], section_id=checkpoint)
            else:
                if not topic_id:
                    raise ServiceError("topic_required")
                try:
                    asset = packs.compile_topic(topic_id)
                except KeyError as exc:
                    raise ServiceError("topic_unavailable", 404) from exc
                due = conn.execute(
                    "SELECT item_id FROM learn.review_schedule WHERE subject_id = %s AND due_at <= now() "
                    "AND kc_id <> %s ORDER BY due_at LIMIT 5",
                    (principal.subject_id, topic_id),
                ).fetchall()
                review = [r["item_id"] for r in due if r["item_id"] in packs.items_by_id() and packs.items_by_id()[r["item_id"]].servable]
                self._insert_session(conn, session_id, principal.subject_id, track, asset.canonical_pir_revision)
                tr = self.controller.start_pir(track="hesi", asset_id=asset.canonical_problem_id, session_id=session_id,
                                               subject_id=principal.subject_id, review_items=review, topic_id=topic_id)
            self._insert_turns(conn, session_id, 0, tr.turns, tr.state)
            self._apply_side_effects(conn, principal.subject_id, tr, None)
        return self.session_view(principal, session_id) | {"resumed": False}

    def _insert_session(self, conn: Conn, session_id: str, subject_id: str, track: str, revision: str) -> None:
        conn.execute(
            "INSERT INTO learn.session (session_id, subject_id, track, module_version_set) VALUES (%s,%s,%s,%s)",
            (session_id, subject_id, track, Jsonb(_module_versions(track, revision))),
        )

    def _awaiting_turn(self, conn: Conn, session_id: str) -> dict[str, Any] | None:
        return conn.execute(
            "SELECT turn_id::text AS turn_id, seq FROM learn.turn WHERE session_id = %s AND (payload->>'awaiting')::boolean "
            "ORDER BY seq DESC LIMIT 1",
            (session_id,),
        ).fetchone()

    def submit_attempt(
        self, principal: Principal, session_id: str, *, turn_id: str, response: str, idempotency_key: str,
        latency_ms: int | None = None,
    ) -> dict[str, Any]:
        if not idempotency_key or len(idempotency_key) > 80:
            raise ServiceError("idempotency_key_required")
        response = (response or "")[:2000]
        with self.db.tx() as conn:
            self._session_row(conn, principal, session_id, lock=True)
            prior = conn.execute(
                "SELECT a.outcome, a.result_turn_seq, t.seq, t.session_id::text AS session_id FROM learn.attempt a "
                "JOIN learn.turn t USING (turn_id) WHERE a.idempotency_key = %s",
                (f"{principal.subject_id}:{idempotency_key}",),
            ).fetchone()
            if prior is not None:
                if prior["session_id"] != session_id:
                    raise ServiceError("idempotency_conflict", 409)
                return {"outcome": prior["outcome"], "replayed": True,
                        "turns": self._turns_after(conn, session_id, prior["seq"], prior["result_turn_seq"])}
            last = self._last_turn(conn, session_id)
            awaiting = self._awaiting_turn(conn, session_id)
            if last is None or awaiting is None or last["state_after"] not in ("AWAIT_ATTEMPT",):
                raise ServiceError("not_awaiting", 409)
            if awaiting["turn_id"] != turn_id:
                raise ServiceError("stale_turn", 409)
            state = dict(last["run_state"])
            scrubbed = scrub(response)
            try:
                ctx = self.controller.current_probe(state)
            except ControllerError as exc:
                raise ServiceError("not_awaiting", 409) from exc
            layer = self.layer(principal.subject_id)
            grade = layer.grade(ctx, scrubbed)
            decisions = list(grade.decisions)
            interps = list(grade.interpretations)
            if grade.outcome == "incorrect":
                mis = layer.misconception(ctx, scrubbed)
                if mis is not None:
                    decisions.append(mis)
            tr = self.controller.apply_outcome(state, grade.outcome, rule_graded=grade.rule_graded)
            if grade.intent == "wants_answer" and tr.turns:
                tr.turns[0].payload["markdown"] = (
                    "I won’t hand over the answer, because working it out is what makes it stick. "
                    "Look at the picture above and give your best guess. A wrong answer is fine: you’ll see the right one right after."
                )
            if tr.rewrite_request is not None:
                self._maybe_rewrite(state, tr, layer, interps)
            base_seq = int(last["seq"])
            self._insert_turns(conn, session_id, base_seq, tr.turns, tr.state)
            result_seq = base_seq + len(tr.turns)
            attempt_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO learn.attempt (attempt_id, turn_id, idempotency_key, response_kind, response_text_scrubbed, "
                "grader, outcome, latency_ms, result_turn_seq) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (attempt_id, turn_id, f"{principal.subject_id}:{idempotency_key}", ctx.response_kind, scrubbed,
                 grade.grader, grade.outcome, latency_ms, result_seq),
            )
            self._record_decisions(conn, turn_id, decisions)
            self._record_interpretations(conn, turn_id, interps)
            self._apply_side_effects(conn, principal.subject_id, tr, attempt_id)
            if tr.state.get("web_state") == "SESSION_DONE":
                conn.execute("UPDATE learn.session SET ended_at = now(), end_state = 'SESSION_DONE' WHERE session_id = %s", (session_id,))
            turns = self._turns_after(conn, session_id, base_seq, result_seq)
        return {"outcome": grade.outcome, "grader": grade.grader, "replayed": False, "turns": turns}

    def _maybe_rewrite(self, state: dict[str, Any], tr: Transition, layer: DecisionLayer, interps: list[InterpretationRecord]) -> None:
        req = tr.rewrite_request or {}
        probe_idx = next((i for i, t in enumerate(tr.turns) if t.payload.get("awaiting")), None)
        if probe_idx is None:
            return
        failed = next((t for t in tr.turns if t.operation == "correction"), None)
        next_turn = tr.turns[probe_idx]
        try:
            ctx = self.controller.current_probe(tr.state)
        except ControllerError:
            return
        forbidden: tuple[str, ...]
        if ctx.item is not None:
            forbidden = (ctx.item.options[ctx.item.correct_index],)
        elif ctx.assessment is not None:
            forbidden = tuple(ctx.assessment.expected_text) + tuple(str(v) for v in ctx.assessment.expected_values)
        else:
            forbidden = ()
        md, recs = rewrite_failed_step(
            layer, concept=str(req.get("concept")), failed_markdown=failed.payload["markdown"] if failed else "",
            next_markdown=str(next_turn.payload.get("markdown", "")), forbidden_answers=forbidden,
            step_id=str(req.get("next_step_id")),
        )
        interps.extend(recs)
        if md:
            tr.turns.insert(probe_idx, TurnSpec(
                state_before=tr.turns[probe_idx - 1].state_after if probe_idx else "FEEDBACK",
                event="rewrite_failed_step", state_after="PRESENT_STEP", operation="rewrite",
                payload={"kind": "explain", "markdown": md, "response_kind": "none", "awaiting": False,
                         "step_id": req.get("next_step_id"), "concept": req.get("concept"), "track": state["track"],
                         "generated": True},
                step_id=str(req.get("next_step_id")), served_from="generated", assistance_level=3,
            ))

    def expand(self, principal: Principal, session_id: str, *, turn_id: str, kind: str) -> dict[str, Any]:
        with self.db.tx() as conn:
            self._session_row(conn, principal, session_id, lock=True)
            last = self._last_turn(conn, session_id)
            awaiting = self._awaiting_turn(conn, session_id)
            if last is None or awaiting is None or awaiting["turn_id"] != turn_id:
                raise ServiceError("stale_turn", 409)
            try:
                tr = self.controller.expand(dict(last["run_state"]), kind)
            except ControllerError as exc:
                raise ServiceError("no_expansion", 409) from exc
            base = int(last["seq"])
            self._insert_turns(conn, session_id, base, tr.turns, tr.state)
            return {"turns": self._turns_after(conn, session_id, base)}

    def end_session(self, principal: Principal, session_id: str) -> dict[str, Any]:
        with self.db.tx() as conn:
            row = self._session_row(conn, principal, session_id, lock=True)
            last = self._last_turn(conn, session_id)
            if last is None:
                raise ServiceError("not_found", 404)
            if row["ended_at"] is None and last["state_after"] != "SESSION_DONE":
                tr = self.controller.end(dict(last["run_state"]))
                self._insert_turns(conn, session_id, int(last["seq"]), tr.turns, tr.state)
                conn.execute("UPDATE learn.session SET ended_at = now(), end_state = 'PAUSED' WHERE session_id = %s", (session_id,))
        return self.summary(principal, session_id)

    def summary(self, principal: Principal, session_id: str) -> dict[str, Any]:
        with self.db.tx() as conn:
            row = self._session_row(conn, principal, session_id)
            stats = conn.execute(
                "SELECT count(*) AS attempts, count(*) FILTER (WHERE a.outcome = 'correct') AS correct "
                "FROM learn.attempt a JOIN learn.turn t USING (turn_id) WHERE t.session_id = %s",
                (session_id,),
            ).fetchone()
            caps = conn.execute(
                "SELECT DISTINCT ON (kc_id) kc_id, to_state FROM learn.capability_transition WHERE subject_id = %s "
                "ORDER BY kc_id, id DESC",
                (principal.subject_id,),
            ).fetchall()
            due = conn.execute(
                "SELECT min(due_at) AS next_due FROM learn.review_schedule WHERE subject_id = %s AND due_at > now()",
                (principal.subject_id,),
            ).fetchone()
        assert stats is not None
        return {
            "session_id": session_id,
            "track": row["track"],
            "attempts": int(stats["attempts"]),
            "correct": int(stats["correct"]),
            "capability_states": {c["kc_id"]: c["to_state"] for c in caps},
            "next_review_at": due["next_due"].isoformat() if due and due["next_due"] else None,
            "note": "Capability states show evidence so far. They are not a mastery guarantee.",
        }

    def react(self, principal: Principal, turn_id: str, kind: str) -> None:
        if kind not in ("helped", "confused", "frustrated", "too_easy"):
            raise ServiceError("invalid_reaction")
        with self.db.tx() as conn:
            try:
                uuid.UUID(turn_id)
            except ValueError as exc:
                raise ServiceError("not_found", 404) from exc
            row = conn.execute(
                "SELECT s.subject_id::text AS subject_id FROM learn.turn t JOIN learn.session s USING (session_id) WHERE t.turn_id = %s",
                (turn_id,),
            ).fetchone()
            if row is None or row["subject_id"] != principal.subject_id:
                raise ServiceError("not_found", 404)
            # P-CTL-10: reactions are self-report; they never touch capability state.
            conn.execute("INSERT INTO ux.reaction (turn_id, kind) VALUES (%s, %s)", (turn_id, kind))

    def home(self, principal: Principal) -> dict[str, Any]:
        with self.db.tx() as conn:
            progress = conn.execute(
                "SELECT topic_id, state FROM learn.topic_progress WHERE subject_id = %s AND track = 'hesi'",
                (principal.subject_id,),
            ).fetchall()
            dsa = conn.execute(
                "SELECT t.run_state->'pir'->>'current_step_id' AS step, t.run_state->'pir'->>'status' AS status "
                "FROM learn.turn t JOIN learn.session s USING (session_id) WHERE s.subject_id = %s AND s.track = 'dsa' "
                "ORDER BY t.created_at DESC, t.seq DESC LIMIT 1",
                (principal.subject_id,),
            ).fetchone()
            days = conn.execute(
                "SELECT DISTINCT date_trunc('day', a.created_at)::date AS d FROM learn.attempt a JOIN learn.turn t USING (turn_id) "
                "JOIN learn.session s USING (session_id) WHERE s.subject_id = %s ORDER BY d DESC LIMIT 60",
                (principal.subject_id,),
            ).fetchall()
            due = conn.execute(
                "SELECT count(*) AS n FROM learn.review_schedule WHERE subject_id = %s AND due_at <= now()",
                (principal.subject_id,),
            ).fetchone()
        states = {r["topic_id"]: r["state"] for r in progress}
        sections = packs.topic_graph()
        recommended = None
        for section in sections:
            if section["exam_id"] != "a2":
                continue
            for topic in section["topics"]:
                st = states.get(topic["topic_id"], "not_started")
                topic["state"] = st
                prereq_ok = all(states.get(p) in ("assembled", "checkpoint_passed") for p in topic["prerequisites"])
                topic["prerequisites_met"] = prereq_ok
                if recommended is None and topic["available"] and st not in ("assembled", "checkpoint_passed") and prereq_ok:
                    recommended = topic["topic_id"]
            section["checkpoint_state"] = states.get(f"checkpoint:{section['section_id']}", "not_started")
        for section in sections:
            for topic in section["topics"]:
                topic.setdefault("state", states.get(topic["topic_id"], "not_started"))
                topic.setdefault("prerequisites_met", True)
        streak = 0
        today = datetime.now(timezone.utc).date()
        dates = [r["d"] for r in days]
        for offset, d in enumerate(dates):
            if (today - d).days in (offset, offset + 1) and (offset == 0 or (dates[offset - 1] - d).days == 1):
                streak += 1
            else:
                break
        return {
            "handle": principal.handle,
            "display_name": principal.display_name,
            "streak_days": streak,
            "dsa": {"current_step": dsa["step"] if dsa else None, "status": dsa["status"] if dsa else None},
            "hesi": {
                "sections": sections, "recommended_topic": recommended,
                "reviews_due": int(due["n"]) if due else 0,
                "content_status": "unreviewed draft — generated with an LLM, awaiting owner review",
                "pack_revision": packs.pack_revision(),
            },
        }

    def record_events(self, principal: Principal | None, events: list[dict[str, Any]]) -> int:
        allowed = {"page_view", "click", "step_shown", "step_answered", "hint_requested", "time_on_step",
                   "idle", "tab_hidden", "tab_visible", "error", "rating"}
        rows = []
        for e in events[:100]:
            et = e.get("type")
            if et not in allowed:
                continue
            rows.append((
                principal.subject_id if principal else None,
                _uuid_or_none(e.get("session_id")),
                _uuid_or_none(e.get("turn_id")),
                _clean(e.get("client_session"), r"^[A-Za-z0-9_-]{8,64}$") or "anonymous0",
                et,
                _clean(e.get("path"), r"^/[A-Za-z0-9/_-]{0,120}$"),
                _clean(e.get("control"), r"^[a-z0-9_.-]{1,48}$"),
                (str(e["step_id"])[:120] if e.get("step_id") else None),
                _int_or_none(e.get("value_ms"), 0, 86_400_000),
                _int_or_none(e.get("value_int"), -1_000_000, 1_000_000),
                _ts_or_none(e.get("ts")),
            ))
        if not rows:
            return 0
        with self.db.tx() as conn:
            if principal is not None:
                # Drop session/turn ids that do not belong to this learner.
                own = {r["session_id"] for r in conn.execute(
                    "SELECT session_id::text AS session_id FROM learn.session WHERE subject_id = %s", (principal.subject_id,)
                ).fetchall()}
                rows = [(r[0], r[1] if r[1] in own else None, r[2] if r[1] in own else None, *r[3:]) for r in rows]
            else:
                rows = [(None, None, None, *r[3:]) for r in rows]
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO ux.event (subject_id, session_id, turn_id, client_session, event_type, path, control, "
                    "step_id, value_ms, value_int, client_ts) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    rows,
                )
        return len(rows)


    def record_decomposer_reviews(self, principal: Principal | None, body: dict[str, Any]) -> dict[str, Any]:
        """Append-only SOS-0011 pedagogical decomposer ratings (per-step + overall)."""
        batch = _clean(body.get("review_batch_id"), r"^[A-Za-z0-9_-]{8,64}$") or _clean(
            body.get("client_session"), r"^[A-Za-z0-9_-]{8,64}$"
        )
        client = _clean(body.get("client_session"), r"^[A-Za-z0-9_-]{8,64}$") or "anonymous0"
        if not batch:
            raise ServiceError("bad_request", 400)
        problem_id = str(body.get("problem_id") or "")[:80]
        variant_id = str(body.get("variant_id") or "")[:160]
        if not problem_id or not variant_id:
            raise ServiceError("bad_request", 400)
        ratings = body.get("ratings") or []
        if not isinstance(ratings, list) or len(ratings) > 200:
            raise ServiceError("bad_request", 400)
        allowed = {"good", "bad", "prefer", "ok", "skip"}
        formats = {None, "ascii", "mermaid", "algebra", "katex", "code", "svg", "mixed", "overall"}
        rows = []
        for r in ratings:
            if not isinstance(r, dict):
                continue
            rating = str(r.get("rating") or "").lower()
            if rating not in allowed:
                continue
            note = r.get("note")
            if note is not None:
                note = str(note)[:4000]
            fmt = r.get("artifact_format")
            if fmt is not None:
                fmt = str(fmt)[:32]
            if fmt not in formats:
                fmt = None
            step_id = r.get("step_id")
            step_id = str(step_id)[:80] if step_id else None
            step_index = _int_or_none(r.get("step_index"), 0, 500)
            payload = r.get("payload") if isinstance(r.get("payload"), dict) else {}
            rows.append((
                batch, client,
                principal.subject_id if principal else None,
                problem_id, variant_id, step_id, step_index, fmt, rating, note,
                json.dumps(payload), _ts_or_none(r.get("ts") or body.get("client_ts")),
            ))
        # optional overall note as its own row
        overall = body.get("overall")
        if isinstance(overall, dict):
            rating = str(overall.get("rating") or "ok").lower()
            if rating in allowed:
                note = overall.get("note")
                note = str(note)[:4000] if note is not None else None
                rows.append((
                    batch, client,
                    principal.subject_id if principal else None,
                    problem_id, variant_id, None, None, "overall", rating, note,
                    json.dumps({"kind": "overall"}), _ts_or_none(body.get("client_ts")),
                ))
        if not rows:
            raise ServiceError("bad_request", 400)
        with self.db.tx() as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO ux.decomposer_review ("
                    "review_batch_id, client_session, subject_id, problem_id, variant_id, "
                    "step_id, step_index, artifact_format, rating, note, payload, client_ts"
                    ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)",
                    rows,
                )
        return {"stored": len(rows), "review_batch_id": batch}


def _uuid_or_none(value: Any) -> str | None:
    try:
        return str(uuid.UUID(str(value))) if value else None
    except ValueError:
        return None


def _int_or_none(value: Any, lo: int, hi: int) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    v = int(value)
    return v if lo <= v <= hi else None


def _clean(value: Any, pattern: str) -> str | None:
    import re

    if not isinstance(value, str):
        return None
    return value if re.fullmatch(pattern, value) else None


def _ts_or_none(value: Any) -> datetime | None:
    if not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def dumps(value: Any) -> str:
    return json.dumps(value, default=str)
