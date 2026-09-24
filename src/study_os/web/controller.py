"""Web session controller (#90): a pure, deterministic state machine over PIR assets.

It wraps ``study_os.pir.controller`` and never overrides PIR transitions. It adds the
session-level states from docs/webapp/ARCHITECTURE.md §3 (START, REVIEW_DUE, PRESENT_STEP,
AWAIT_ATTEMPT, FEEDBACK, RETRY_DIFFERENT, CHECK, ADVANCE, SESSION_DONE, PAUSED, BLOCKED),
quiz flows for FSRS review and section checkpoints, and turn specs for persistence.
No I/O and no model calls happen here (P-DEC-7); grading outcomes arrive as inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from study_os.pir.contracts import (
    AssessmentSpec,
    CanonicalTeachingAsset,
    ExpansionKind,
    LearnerOutcome,
    ProblemRunState,
    RunStatus,
    StepKind,
    TeachingBundle,
    TeachingTurn,
    TransitionSpec,
)
from study_os.pir.controller import (
    build_expansion_bundle,
    build_interaction_bundle,
    classify_response,
    start_run,
)

from . import packs

WEB_CONTROLLER_REVISION = "study-os.web-controller.v1"
TOPIC_ATTEMPT_LIMIT = 10  # wheel-spinning guard per topic run
REVIEW_WARMUP_MAX = 5

ASSISTANCE = {
    StepKind.PROBE: 0,
    StepKind.EXPLAIN: 0,
    StepKind.CORRECT: 4,
    StepKind.VALIDATE: 0,
    StepKind.ASSEMBLE: 0,
    StepKind.STATUS: 0,
}


@dataclass
class TurnSpec:
    state_before: str
    event: str
    state_after: str
    operation: str
    payload: dict[str, Any]
    step_id: str | None = None
    item_id: str | None = None
    representation_id: str | None = None
    assistance_level: int = 0
    served_from: str = "canonical"


@dataclass
class CapabilityEvent:
    kc_id: str
    to_state: str
    window: str
    assistance_level: int


@dataclass
class Transition:
    state: dict[str, Any]
    turns: list[TurnSpec]
    capability: list[CapabilityEvent] = field(default_factory=list)
    review_updates: list[tuple[str, str, bool]] = field(default_factory=list)  # (item_id, kc, correct)
    rewrite_request: dict[str, Any] | None = None
    topic_state: tuple[str, str] | None = None  # (topic_id, state)


@dataclass(frozen=True)
class ProbeContext:
    track: str
    kind: str  # 'pir' | 'quiz'
    step_id: str
    concept: str
    response_kind: str
    assessment: AssessmentSpec | None
    item: packs.PackItem | None
    question_markdown: str


class ControllerError(ValueError):
    pass


def concept_of(step_id: str) -> str:
    return step_id.split(".", 1)[0]


def _probe_variant(step_id: str) -> str:
    parts = step_id.split(".")
    return parts[2] if len(parts) >= 3 else ""


def _turn_payload(turn: TeachingTurn, *, awaiting: bool, track: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "kind": turn.turn_kind.value,
        "markdown": turn.learner_visible_markdown,
        "response_kind": turn.response_kind.value if awaiting else "none",
        "awaiting": awaiting,
        "step_id": turn.canonical_step_id,
        "concept": concept_of(turn.canonical_step_id),
        "track": track,
        "allowed_actions": list(turn.allowed_actions) if awaiting else [],
    }
    if extra:
        payload.update(extra)
    return payload


def _choices_for(asset: CanonicalTeachingAsset, step_id: str) -> list[str] | None:
    step = next((s for s in asset.steps if s.step_id == step_id), None)
    if step is None or step.assessment_id is None:
        return None
    item = packs.item_for_assessment(step.assessment_id)
    return list(item.options) if item else None


def _expansion_kinds(asset: CanonicalTeachingAsset, step_id: str) -> list[str]:
    return sorted({e.kind.value for e in asset.expansions if e.step_id == step_id})


class WebController:
    """Stateless: every method takes the run state dict and returns a new one."""

    def __init__(self, assets: dict[str, CanonicalTeachingAsset]) -> None:
        self.assets = assets

    # ---------- helpers ----------
    def asset(self, asset_id: str) -> CanonicalTeachingAsset:
        asset = self.assets.get(asset_id)
        if asset is None:
            if asset_id.startswith("hesi."):
                topic = asset_id.split(".")[1]
                asset = packs.compile_topic(topic)
                self.assets[asset_id] = asset
            else:
                raise ControllerError(f"unknown asset {asset_id}")
        return asset

    def _bundle_turns(
        self,
        state: dict[str, Any],
        bundle: TeachingBundle,
        *,
        state_before: str,
        event: str,
        outcome: str | None = None,
    ) -> list[TurnSpec]:
        asset = self.asset(state["asset_id"])
        specs: list[TurnSpec] = []
        prev = state_before
        for index, turn in enumerate(bundle.turns):
            awaiting = bundle.response_turn_id == turn.turn_id
            if turn.turn_kind == StepKind.CORRECT:
                after = "FEEDBACK"
                op = "correction"
            elif turn.turn_kind == StepKind.EXPLAIN and turn.canonical_step_id.endswith(".why"):
                after = "FEEDBACK"
                op = "why"
            elif turn.turn_kind == StepKind.STATUS:
                after = "SESSION_DONE"
                op = "status"
            elif awaiting:
                after = "AWAIT_ATTEMPT"
                op = "present_probe"
            else:
                after = "PRESENT_STEP"
                op = "explain"
            if awaiting:
                variant = _probe_variant(turn.canonical_step_id)
                label = (
                    "RETRY_DIFFERENT"
                    if state.get("last_outcome") == "incorrect"
                    else "CHECK"
                    if variant == "n1"
                    else "PRESENT_STEP"
                )
                extra: dict[str, Any] = {"phase": label, "expansions": _expansion_kinds(asset, turn.canonical_step_id)}
                choices = _choices_for(asset, turn.canonical_step_id) if state["track"] == "hesi" else None
                if choices:
                    extra["choices"] = choices
            else:
                extra = {}
            if index == 0 and outcome is not None:
                extra["outcome"] = outcome
            specs.append(
                TurnSpec(
                    state_before=prev,
                    event=event if index == 0 else "auto",
                    state_after=after,
                    operation=op,
                    payload=_turn_payload(turn, awaiting=awaiting, track=state["track"], extra=extra),
                    step_id=turn.canonical_step_id,
                    representation_id=turn.representation_id,
                    assistance_level=ASSISTANCE.get(turn.turn_kind, 0),
                )
            )
            prev = after
        return specs

    # ---------- start ----------
    def start_pir(
        self,
        *,
        track: str,
        asset_id: str,
        session_id: str,
        subject_id: str,
        resume: dict[str, Any] | None = None,
        review_items: list[str] | None = None,
        topic_id: str | None = None,
    ) -> Transition:
        asset = self.asset(asset_id)
        state: dict[str, Any] = {
            "track": track,
            "asset_id": asset_id,
            "topic_id": topic_id,
            "web_state": "START",
            "last_outcome": None,
            "consecutive_incorrect": 0,
            "attempts_in_run": 0,
            "assisted": False,
            "quiz": None,
            "pir": None,
        }
        turns: list[TurnSpec] = []
        if review_items:
            quiz = {"mode": "review", "items": review_items[:REVIEW_WARMUP_MAX], "index": 0, "results": []}
            state["quiz"] = quiz
            state["web_state"] = "REVIEW_DUE"
            turns.append(self._quiz_present(state, "START", "start"))
            state["pending_pir"] = {"resume": resume, "session_id": session_id, "subject_id": subject_id}
            return Transition(state=state, turns=turns)
        return self._begin_pir(state, asset, session_id, subject_id, resume, "START", "start")

    def _begin_pir(
        self,
        state: dict[str, Any],
        asset: CanonicalTeachingAsset,
        session_id: str,
        subject_id: str,
        resume: dict[str, Any] | None,
        state_before: str,
        event: str,
    ) -> Transition:
        if resume and resume.get("status") == RunStatus.ACTIVE.value:
            pir_state = ProblemRunState.model_validate(resume, strict=False)
            pir_state = pir_state.model_copy(update={"session_id": session_id})
            pir_state, bundle = build_interaction_bundle(asset, pir_state)
            event = "resume"
        else:
            run_id = f"{session_id}:{asset.canonical_problem_id}"
            pir_state, bundle = start_run(asset, problem_run_id=run_id, subject_id=subject_id, session_id=session_id)
        state["pir"] = pir_state.model_dump(mode="json")
        state["awaiting_turn_ref"] = bundle.response_turn_id
        turns = self._bundle_turns(state, bundle, state_before=state_before, event=event)
        state["web_state"] = turns[-1].state_after if turns else "PRESENT_STEP"
        return Transition(state=state, turns=turns, topic_state=(state["topic_id"], "in_progress") if state.get("topic_id") else None)

    def start_quiz(self, *, track: str, mode: str, items: list[str], section_id: str | None = None) -> Transition:
        if not items:
            raise ControllerError("quiz has no items")
        state: dict[str, Any] = {
            "track": track,
            "asset_id": None,
            "topic_id": None,
            "section_id": section_id,
            "web_state": "START",
            "last_outcome": None,
            "consecutive_incorrect": 0,
            "attempts_in_run": 0,
            "assisted": False,
            "quiz": {"mode": mode, "items": items, "index": 0, "results": []},
            "pir": None,
        }
        turn = self._quiz_present(state, "START", "start")
        return Transition(state=state, turns=[turn])

    # ---------- quiz ----------
    def _quiz_item(self, state: dict[str, Any]) -> packs.PackItem:
        quiz = state["quiz"]
        item = packs.items_by_id().get(quiz["items"][quiz["index"]])
        if item is None:
            raise ControllerError("unknown quiz item")
        return item

    def _quiz_present(self, state: dict[str, Any], before: str, event: str) -> TurnSpec:
        item = self._quiz_item(state)
        quiz = state["quiz"]
        state["web_state"] = "AWAIT_ATTEMPT"
        state["awaiting_turn_ref"] = f"quiz:{quiz['mode']}:{quiz['index']}:{item.item_id}"
        heading = "Warm-up review" if quiz["mode"] == "review" else "Checkpoint"
        return TurnSpec(
            state_before=before,
            event=event,
            state_after="AWAIT_ATTEMPT",
            operation="present_item",
            step_id=f"{quiz['mode']}.{item.topic_id}",
            item_id=item.item_id,
            payload={
                "kind": "probe",
                "markdown": f"**{heading} {quiz['index'] + 1}/{len(quiz['items'])}**\n\n{item.stem}",
                "choices": list(item.options),
                "response_kind": "integer",
                "awaiting": True,
                "step_id": f"{quiz['mode']}.{item.topic_id}",
                "concept": item.topic_id,
                "track": state["track"],
                "phase": "REVIEW_DUE" if quiz["mode"] == "review" else "CHECK",
                "allowed_actions": ["submit_response"],
                "expansions": [],
            },
        )

    # ---------- probes ----------
    def current_probe(self, state: dict[str, Any]) -> ProbeContext:
        if state.get("web_state") != "AWAIT_ATTEMPT":
            raise ControllerError("session is not awaiting an attempt")
        if str(state.get("awaiting_turn_ref") or "").startswith("quiz:"):
            item = self._quiz_item(state)
            return ProbeContext(
                track=state["track"], kind="quiz", step_id=f"{state['quiz']['mode']}.{item.topic_id}",
                concept=item.topic_id, response_kind="integer", assessment=None, item=item,
                question_markdown=packs.probe_markdown(item),
            )
        asset = self.asset(state["asset_id"])
        pir = ProblemRunState.model_validate(state["pir"], strict=False)
        step = next(s for s in asset.steps if s.step_id == pir.current_step_id)
        assessment = next(a for a in asset.assessments if a.assessment_id == step.assessment_id)
        rep = next(r for r in asset.representations if r.representation_id == step.representation_id)
        item = packs.item_for_assessment(assessment.assessment_id) if state["track"] == "hesi" else None
        return ProbeContext(
            track=state["track"], kind="pir", step_id=step.step_id, concept=concept_of(step.step_id),
            response_kind=step.response_kind.value, assessment=assessment, item=item,
            question_markdown=rep.learner_visible_markdown,
        )

    def awaiting_ref(self, state: dict[str, Any]) -> str | None:
        return state.get("awaiting_turn_ref")

    def apply_outcome(self, state: dict[str, Any], outcome: str, *, rule_graded: bool) -> Transition:
        """Apply a graded outcome. ``unresolved`` never moves the step (P-CTL-9)."""

        if outcome not in ("correct", "partial", "incorrect", "unresolved"):
            raise ControllerError("invalid outcome")
        state = {**state}
        ctx = self.current_probe(state)
        before = "GRADE"
        if outcome == "unresolved":
            return Transition(
                state=state,
                turns=[
                    TurnSpec(
                        state_before=before, event="attempt:unresolved", state_after="AWAIT_ATTEMPT",
                        operation="ask_again", step_id=ctx.step_id,
                        payload={
                            "kind": "feedback", "markdown": "I couldn’t tell what you meant. Please answer the question above with just your answer.",
                            "response_kind": "none", "awaiting": False, "step_id": ctx.step_id,
                            "concept": ctx.concept, "track": state["track"], "outcome": "unresolved",
                        },
                    )
                ],
            )
        if ctx.kind == "quiz":
            return self._quiz_outcome(state, ctx, outcome)
        return self._pir_outcome(state, ctx, outcome, rule_graded=rule_graded)

    def _quiz_outcome(self, state: dict[str, Any], ctx: ProbeContext, outcome: str) -> Transition:
        item = ctx.item
        assert item is not None
        quiz = dict(state["quiz"])
        correct = outcome == "correct"
        quiz["results"] = [*quiz["results"], {"item_id": item.item_id, "correct": correct}]
        md = packs.why_markdown(item) if correct else packs.fix_markdown(item).replace(
            "Let’s try a different one.", "Let’s keep going."
        )
        turns = [
            TurnSpec(
                state_before="GRADE", event=f"attempt:{outcome}", state_after="FEEDBACK",
                operation="why" if correct else "correction", step_id=ctx.step_id, item_id=item.item_id,
                assistance_level=0 if correct else 4,
                payload={"kind": "explain" if correct else "correct", "markdown": md, "response_kind": "none",
                         "awaiting": False, "step_id": ctx.step_id, "concept": item.topic_id,
                         "track": state["track"], "outcome": outcome},
            )
        ]
        review_updates = [(item.item_id, item.topic_id, correct)]
        quiz["index"] += 1
        state["quiz"] = quiz
        state["last_outcome"] = outcome
        capability: list[CapabilityEvent] = []
        topic_state = None
        if quiz["index"] < len(quiz["items"]):
            turns.append(self._quiz_present(state, "FEEDBACK", "advance"))
            return Transition(state=state, turns=turns, review_updates=review_updates)
        # quiz finished
        if quiz["mode"] == "review" and state.get("pending_pir"):
            pending = state.pop("pending_pir")
            state["quiz"] = None
            asset = self.asset(state["asset_id"])
            tr = self._begin_pir(state, asset, pending["session_id"], pending["subject_id"], pending["resume"], "FEEDBACK", "advance")
            return Transition(state=tr.state, turns=turns + tr.turns, review_updates=review_updates, topic_state=tr.topic_state)
        passed = sum(1 for r in quiz["results"] if r["correct"])
        total = len(quiz["results"])
        summary = f"You answered {passed} of {total} correctly."
        if quiz["mode"] == "checkpoint":
            policy = packs.load_blueprint()["checkpoint_policy"]
            ok = total > 0 and passed / total >= float(policy["pass_fraction"])
            summary += " Checkpoint passed: strong evidence for this section today. We will re-check it on a later day." if ok else " Not passed yet. Review the topics marked in progress and try again later."
            if ok and state.get("section_id"):
                topic_state = (f"checkpoint:{state['section_id']}", "checkpoint_passed")
                for result in quiz["results"]:
                    if result["correct"]:
                        capability.append(CapabilityEvent(packs.items_by_id()[result["item_id"]].topic_id, "pass_transfer", "transfer", 0))
        state["web_state"] = "SESSION_DONE"
        turns.append(
            TurnSpec(
                state_before="FEEDBACK", event="session_done", state_after="SESSION_DONE", operation="summary",
                payload={"kind": "status", "markdown": summary, "response_kind": "none", "awaiting": False,
                         "track": state["track"], "summary": {"correct": passed, "total": total}},
            )
        )
        return Transition(state=state, turns=turns, review_updates=review_updates, capability=capability, topic_state=topic_state)

    def _route(self, asset: CanonicalTeachingAsset, pir: ProblemRunState, outcome: LearnerOutcome) -> TransitionSpec:
        step = next(s for s in asset.steps if s.step_id == pir.current_step_id)
        routes = [t for t in step.outcome_transitions if t.outcome == outcome]
        if len(routes) != 1:
            # An asset without a partial route treats partial as incorrect (keeps PIR graph legal).
            if outcome == LearnerOutcome.PARTIAL:
                return self._route(asset, pir, LearnerOutcome.INCORRECT)
            raise ControllerError(f"no unique {outcome.value} route")
        return routes[0]

    def _pir_outcome(self, state: dict[str, Any], ctx: ProbeContext, outcome: str, *, rule_graded: bool) -> Transition:
        asset = self.asset(state["asset_id"])
        pir = ProblemRunState.model_validate(state["pir"], strict=False)
        route = self._route(asset, pir, LearnerOutcome(outcome))
        if route.exit_status is not None:
            next_pir = pir.model_copy(update={"current_step_id": None, "status": route.exit_status, "transition_seq": pir.transition_seq + 1})
            bundle = None
        else:
            next_pir = pir.model_copy(update={"current_step_id": route.next_step_id, "transition_seq": pir.transition_seq + 1})
            next_pir, bundle = build_interaction_bundle(asset, next_pir) if next_pir.status == RunStatus.ACTIVE else (next_pir, None)
        prev_concept = ctx.concept
        state["attempts_in_run"] = int(state.get("attempts_in_run", 0)) + 1
        state["consecutive_incorrect"] = 0 if outcome == "correct" else int(state.get("consecutive_incorrect", 0)) + 1
        state["last_outcome"] = outcome
        capability: list[CapabilityEvent] = []
        review_updates: list[tuple[str, str, bool]] = []
        if ctx.item is not None:
            review_updates.append((ctx.item.item_id, ctx.item.topic_id, outcome == "correct"))
        variant = _probe_variant(ctx.step_id)
        assisted = bool(state.get("assisted"))
        state["assisted"] = False
        if outcome == "correct" and variant == "n1":
            # The extra check after a correct answer: capability evidence for this concept.
            level = 2 if assisted else 0
            to_state = "pass_unaided" if (rule_graded and not assisted) else "pass_supported"
            capability.append(CapabilityEvent(prev_concept, to_state, "immediate", level))
        state["pir"] = next_pir.model_dump(mode="json")
        turns: list[TurnSpec] = []
        topic_state = None
        if bundle is None or bundle.response_turn_id is None:
            state["web_state"] = "SESSION_DONE"
            state["awaiting_turn_ref"] = None
            if bundle is not None:
                # Closing turns (why for the final check, frontier status) come from the asset.
                turns = self._bundle_turns(state, bundle, state_before="GRADE", event=f"attempt:{outcome}", outcome=outcome)
            final_status = RunStatus(state["pir"]["status"])
            msg = (
                "The reviewed lesson frontier is assembled. Independent mastery remains unproven."
                if final_status == RunStatus.ASSEMBLED_MASTERY_UNPROVEN
                else f"Run status: {final_status.value}."
            )
            if state["track"] == "hesi":
                msg = "Topic assembled: you answered two in a row after the lesson. We’ll bring it back in review on a later day to check it sticks."
                topic_state = (state.get("topic_id") or prev_concept, "assembled")
            turns.append(TurnSpec("FEEDBACK" if turns else "GRADE", "session_done" if turns else f"attempt:{outcome}", "SESSION_DONE", "summary",
                                  {"kind": "status", "markdown": msg, "response_kind": "none", "awaiting": False,
                                   "track": state["track"], "outcome": outcome, "run_status": final_status.value}, step_id=ctx.step_id))
            return Transition(state=state, turns=turns, capability=capability, review_updates=review_updates, topic_state=topic_state)
        state["awaiting_turn_ref"] = bundle.response_turn_id
        turns = self._bundle_turns(state, bundle, state_before="GRADE", event=f"attempt:{outcome}", outcome=outcome)
        new_concept = concept_of(bundle.turns[-1].canonical_step_id)
        if new_concept != prev_concept and outcome == "correct":
            turns[-1].state_before = "ADVANCE"
        state["web_state"] = turns[-1].state_after
        rewrite = None
        if state["consecutive_incorrect"] >= 2 and bundle.response_turn_id is not None:
            rewrite = {"failed_step_id": ctx.step_id, "next_step_id": bundle.turns[-1].canonical_step_id, "concept": prev_concept}
        if state["track"] == "hesi" and state["attempts_in_run"] >= TOPIC_ATTEMPT_LIMIT and outcome != "correct":
            state["web_state"] = "SESSION_DONE"
            state["awaiting_turn_ref"] = None
            turns = [t for t in turns if t.operation != "present_probe"]
            turns.append(TurnSpec("FEEDBACK", "wheel_spinning", "SESSION_DONE", "summary",
                                  {"kind": "status", "markdown": "Let’s pause this topic here. That was a lot of tries, and a break or a prerequisite topic usually helps more than more drilling. It stays in progress.",
                                   "response_kind": "none", "awaiting": False, "track": "hesi", "flag": "wheel_spinning"}))
            topic_state = (state.get("topic_id") or prev_concept, "in_progress")
            rewrite = None
        return Transition(state=state, turns=turns, capability=capability, review_updates=review_updates, rewrite_request=rewrite, topic_state=topic_state)

    # ---------- expansions (hints) ----------
    def expand(self, state: dict[str, Any], kind: str) -> Transition:
        if state.get("web_state") != "AWAIT_ATTEMPT" or state.get("pir") is None or str(state.get("awaiting_turn_ref", "")).startswith("quiz:"):
            raise ControllerError("no expandable probe")
        asset = self.asset(state["asset_id"])
        pir = ProblemRunState.model_validate(state["pir"], strict=False)
        try:
            bundle = build_expansion_bundle(asset, pir, turn_id=state["awaiting_turn_ref"], kind=ExpansionKind(kind))
        except ValueError as exc:
            raise ControllerError(str(exc)) from exc
        state = {**state, "assisted": True}
        exp_turn = bundle.turns[0]
        specs = [
            TurnSpec("AWAIT_ATTEMPT", f"expand:{kind}", "AWAIT_ATTEMPT", "expansion",
                     _turn_payload(exp_turn, awaiting=False, track=state["track"], extra={"expansion": kind}),
                     step_id=exp_turn.canonical_step_id, representation_id=exp_turn.representation_id, assistance_level=2)
        ]
        specs += self._bundle_turns(state, TeachingBundle(
            schema_version=bundle.schema_version, problem_run_id=bundle.problem_run_id,
            turns=(bundle.turns[1],), response_turn_id=bundle.response_turn_id, run_status=bundle.run_status),
            state_before="AWAIT_ATTEMPT", event="auto")
        return Transition(state=state, turns=specs)

    def end(self, state: dict[str, Any]) -> Transition:
        state = {**state, "web_state": "PAUSED" if state.get("web_state") not in ("SESSION_DONE",) else "SESSION_DONE"}
        return Transition(state=state, turns=[TurnSpec(
            "AWAIT_ATTEMPT", "end", state["web_state"], "summary",
            {"kind": "status", "markdown": "Session saved. You can pick up exactly here next time.", "response_kind": "none",
             "awaiting": False, "track": state["track"]})])


def rule_grade(ctx: ProbeContext, response: str) -> str:
    """Tier-1 deterministic grading. Returns an outcome or 'unresolved' (P-GRD-1: total)."""

    text = (response or "").strip()
    if ctx.kind == "quiz" or ctx.item is not None:
        item = ctx.item
        assert item is not None
        choice = _parse_choice(text, len(item.options))
        if choice is None:
            return "unresolved"
        return "correct" if choice == item.correct_index else "incorrect"
    assert ctx.assessment is not None
    try:
        result = classify_response(ctx.assessment, text)
    except ValueError:
        return "unresolved"
    if result == LearnerOutcome.INCORRECT and ctx.assessment.kind.value == "text":
        # Free text/code that is not an exact match may still be equivalent: escalate.
        return "unresolved"
    return result.value


def _parse_choice(text: str, n: int) -> int | None:
    t = text.strip().lower().rstrip(".)")
    if t.isdigit() and 1 <= int(t) <= n:
        return int(t) - 1
    if len(t) == 1 and "a" <= t <= chr(ord("a") + n - 1):
        return ord(t) - ord("a")
    return None
