"""Decision layer v1 (#97): rules → hosted Jev (typesafe/jev-1.13) → frontier LLM.

Every decision, including rule decisions, becomes a ``DecisionRecord`` that the service
writes to ``learn.decision`` (P-DEC-3). A tier-2 decision acts only when its confidence
reaches τ (P-DEC-2); a ``correct`` grade from tier 2 needs τ_mastery or agreement with
tier 3. Affect/intent signals never change grades or steps (P-DEC-4).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from .config import Settings
from .controller import ProbeContext, rule_grade
from .models import DecisionTransport, LLMTransport, ModelUnavailable

GRADE_TEMPLATE = "study-os.grade-choice.v1"
MISCONCEPTION_TEMPLATE = "study-os.misconception-choice.v1"
GRADE_LABELS = ("pass", "partial", "fail")  # fixed order, logged with each decision
LABEL_TO_OUTCOME = {"pass": "correct", "partial": "partial", "fail": "incorrect"}

# Repository-owned misconception catalogs per DSA concept (derived hypotheses only).
DSA_MISCONCEPTIONS: dict[str, dict[str, str]] = {
    "position": {"counted_from_zero": "Counted positions starting at 0 instead of 1", "read_value_not_position": "Gave the number itself instead of its position"},
    "index": {"used_position_not_index": "Gave the 1-based position instead of the 0-based index", "off_by_one_other": "Shifted by one in the other direction"},
    "box_size_k": {"box_too_long": "Put k+1 numbers in the box", "box_too_short": "Put k-1 numbers in the box"},
    "box_start_i": {"started_at_position": "Started the box at position i instead of index i", "box_wrong_length": "Used the wrong box length"},
    "window_sum": {"window_too_long": "Summed k+1 numbers", "window_too_short": "Summed k-1 numbers", "started_at_wrong_index": "Summed a window starting at the wrong index", "arithmetic_slip": "Right numbers, arithmetic mistake"},
    "successive_sums": {"recomputed_wrong_window": "Used a wrong window for one of the sums", "arithmetic_slip": "Right numbers, arithmetic mistake"},
}

WANTS_ANSWER_RE = re.compile(
    r"(?i)\b(just tell me|give me the answer|what(?:'s| is) the answer|tell me the answer|show me the answer|i give up)\b"
)
INJECTION_RE = re.compile(r"(?i)(ignore (?:all |the )?(?:previous|prior) instructions|mark me (?:as )?master|system prompt)")


@dataclass
class DecisionRecord:
    decision_type: str
    state_hash: str
    question_schema: dict[str, Any]
    route: str
    label: str | None
    confidence: float | None
    acted_on: bool
    escalated: bool = False
    threshold_used: float | None = None
    model_id: str | None = None
    model_version: str | None = None
    question_type: str | None = None
    probabilities: dict[str, float] | None = None
    audit_sample: bool = False
    error: str | None = None
    latency_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


@dataclass
class InterpretationRecord:
    operation: str
    route: str
    model: str
    prompt_template_version: str
    validation_result: str
    violation_codes: tuple[str, ...] = ()
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    generation: dict[str, Any] | None = None
    step_id: str | None = None


@dataclass
class GradeResult:
    outcome: str
    grader: str  # deterministic | decision_model | interpreter | none
    rule_graded: bool
    decisions: list[DecisionRecord] = field(default_factory=list)
    interpretations: list[InterpretationRecord] = field(default_factory=list)
    intent: str | None = None


class ModelGate(Protocol):
    def allow(self, kind: str) -> tuple[bool, str]: ...

    def cache_get(self, key: str) -> dict[str, Any] | None: ...

    def cache_put(self, key: str, kind: str, model: str, response: dict[str, Any]) -> None: ...


class OpenGate:
    """Gate that always allows and never caches (tests)."""

    def allow(self, kind: str) -> tuple[bool, str]:
        return True, "ok"

    def cache_get(self, key: str) -> dict[str, Any] | None:
        return None

    def cache_put(self, key: str, kind: str, model: str, response: dict[str, Any]) -> None:
        return None


def cache_key(model: str, template: str, payload: Any) -> str:
    raw = json.dumps([model, template, payload], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _state_hash(ctx: ProbeContext) -> str:
    return hashlib.sha256(f"{ctx.track}|{ctx.step_id}".encode()).hexdigest()[:32]


def _expected_text(ctx: ProbeContext) -> str:
    if ctx.item is not None:
        return f"option {ctx.item.correct_index + 1}: {ctx.item.options[ctx.item.correct_index]}"
    a = ctx.assessment
    assert a is not None
    if a.expected_text:
        return " or ".join(a.expected_text)
    return ", ".join(str(v) for v in a.expected_values)


def _audit(decision_seed: str, rate: float) -> bool:
    if rate <= 0:
        return False
    bucket = int(hashlib.sha256(decision_seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return bucket < rate


class DecisionLayer:
    def __init__(
        self,
        settings: Settings,
        jev: DecisionTransport | None,
        llm: LLMTransport | None,
        gate: ModelGate | None = None,
    ) -> None:
        self.settings = settings
        self.jev = jev if settings.decision_model_enabled else None
        self.llm = llm if settings.llm_enabled else None
        self.gate = gate or OpenGate()

    # ---- tier 2 plumbing ----
    def _jev(self, dtype: str, template: str, state: str, questions: dict[str, Any], ctx: ProbeContext) -> tuple[DecisionRecord, dict[str, Any] | None]:
        qkey = next(iter(questions))
        qtype = questions[qkey]["type"]
        record = DecisionRecord(
            decision_type=dtype, state_hash=_state_hash(ctx), question_schema={"template": template, "questions": questions},
            route="decision_model", label=None, confidence=None, acted_on=False,
            model_id=self.settings.jev_model, question_type=qtype,
        )
        if self.jev is None:
            record.error = "decision_model_disabled"
            return record, None
        allowed, why = self.gate.allow("decision")
        if not allowed:
            record.error = why
            return record, None
        key = cache_key(self.jev.model, template, [state, questions])
        cached = self.gate.cache_get(key)
        if cached is not None:
            record.route = "cache"
            answer = cached.get("answer")
            record.model_version = cached.get("model_version")
        else:
            try:
                resp = self.jev.decide(state, questions)
            except ModelUnavailable as exc:
                record.error = exc.reason
                return record, None
            answer = resp.answers.get(qkey)
            record.model_version = resp.model_version
            record.latency_ms, record.tokens_in, record.tokens_out, record.cost_usd = (
                resp.latency_ms, resp.tokens_in, resp.tokens_out, resp.cost_usd,
            )
            if isinstance(answer, dict):
                self.gate.cache_put(key, "decision", self.jev.model, {"answer": answer, "model_version": resp.model_version})
        if not isinstance(answer, dict):
            record.error = "no_answer"
            return record, None
        record.label = answer.get("choice") if qtype == "choice" else str(answer.get("score"))
        probs = answer.get("probabilities")
        record.probabilities = {str(k): float(v) for k, v in probs.items()} if isinstance(probs, dict) else None
        conf = answer.get("confidence")
        record.confidence = float(conf) if isinstance(conf, (int, float)) else None
        return record, answer

    # ---- grading cascade ----
    def grade(self, ctx: ProbeContext, response: str) -> GradeResult:
        started = time.monotonic()
        outcome = rule_grade(ctx, response)
        rule_record = DecisionRecord(
            decision_type="grade", state_hash=_state_hash(ctx),
            question_schema={"template": "rule", "kind": ctx.kind, "response_kind": ctx.response_kind},
            route="rule", label=outcome, confidence=1.0 if outcome != "unresolved" else None,
            acted_on=outcome != "unresolved", escalated=outcome == "unresolved",
            latency_ms=int((time.monotonic() - started) * 1000),
        )
        result = GradeResult(outcome=outcome, grader="deterministic", rule_graded=True, decisions=[rule_record])
        if outcome != "unresolved":
            return result  # P-DEC-1: rules first, no model call
        result.rule_graded = False
        result.grader = "none"
        if WANTS_ANSWER_RE.search(response) or INJECTION_RE.search(response):
            intent = "wants_answer" if WANTS_ANSWER_RE.search(response) else "prompt_injection"
            result.intent = intent
            result.decisions.append(DecisionRecord(
                decision_type="intent", state_hash=_state_hash(ctx), question_schema={"template": "rule.intent.v1"},
                route="rule", label=intent, confidence=1.0, acted_on=False,
            ))
            result.outcome = "unresolved"
            return result
        if ctx.item is not None:
            return result  # MCQ input that is not a choice: ask again, no model needed
        state = (
            f"Tutor question (step {ctx.step_id}):\n{ctx.question_markdown}\n\n"
            f"Expected answer: {_expected_text(ctx)}\n"
            f"Learner answer: {response}"
        )
        questions = {
            "grade": {
                "type": "choice",
                "instructions": "Grade the learner answer against the expected answer. pass = gives the expected answer (any wording, working shown is fine); partial = part of it is right; fail = wrong or no answer.",
                "criteria": {
                    "pass": "The learner's final answer matches the expected answer",
                    "partial": "The learner has a correct part but the final answer is incomplete",
                    "fail": "The final answer is wrong, missing, or unrelated",
                },
            }
        }
        record, answer = self._jev("grade", GRADE_TEMPLATE, state, questions, ctx)
        result.decisions.append(record)
        tier2_label = record.label if answer is not None else None
        conf = record.confidence or 0.0
        need = self.settings.tau_mastery if tier2_label == "pass" else self.settings.tau_grade
        record.threshold_used = need
        if tier2_label in LABEL_TO_OUTCOME and conf >= need:
            record.acted_on = True
            result.outcome = LABEL_TO_OUTCOME[tier2_label]
            result.grader = "decision_model"
            seed = f"{record.state_hash}|{response}"
            if _audit(seed, self.settings.audit_rate):
                record.audit_sample = True
                self._llm_grade(ctx, response, result, act=False)
            return result
        record.escalated = True
        llm_outcome = self._llm_grade(ctx, response, result, act=True)
        if llm_outcome is not None:
            if llm_outcome == "correct" and tier2_label is not None and tier2_label != "pass":
                result.outcome = "unresolved"  # disagreement on a mastery-bearing grade
            else:
                result.outcome = llm_outcome
                result.grader = "interpreter"
        return result

    def _llm_grade(self, ctx: ProbeContext, response: str, result: GradeResult, *, act: bool) -> str | None:
        from .interpreter import grade_free_text

        rec, interp = grade_free_text(self, ctx, response)
        result.decisions.append(rec)
        if interp is not None:
            result.interpretations.append(interp)
        rec.acted_on = act and rec.label in ("correct", "partial", "incorrect") and (rec.confidence or 0) >= 0.7
        rec.threshold_used = 0.7
        return rec.label if rec.acted_on else None

    # ---- misconception (derived hypothesis; never gates) ----
    def misconception(self, ctx: ProbeContext, response: str) -> DecisionRecord | None:
        catalog: dict[str, str]
        if ctx.item is not None:
            return None  # MCQ: the chosen distractor is itself the deterministic signal
        catalog = DSA_MISCONCEPTIONS.get(ctx.concept, {})
        if not catalog:
            return None
        criteria = {**catalog, "none_of_these": "None of the listed misconceptions explains the answer"}
        state = (
            f"Tutor question (step {ctx.step_id}):\n{ctx.question_markdown}\n\n"
            f"Expected answer: {_expected_text(ctx)}\nLearner answer (incorrect): {response}"
        )
        questions = {"misconception": {"type": "choice", "instructions": "Which misconception best explains the learner's wrong answer?", "criteria": criteria}}
        record, answer = self._jev("misconception", MISCONCEPTION_TEMPLATE, state, questions, ctx)
        record.threshold_used = self.settings.tau_misconception
        record.acted_on = False  # stored as a derived hypothesis only
        if answer is None and record.error == "decision_model_disabled":
            return None
        return record
