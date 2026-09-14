"""Bounded model/schema tutoring kernel for the Contains Duplicate pilot.

The model proposes diagnosis, learner-outcome evidence, and learner-visible prose.
Deterministic code owns stage transitions, assistance ceilings, provenance, and
presentation invariants. No canonical lesson prose lives here.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping


TRACE_SCHEMA_VERSION = "study-os.model-tutoring-trace.v0.2"
PROMPT_VERSION = "study-os.model-tutoring-pilot.v2"
SCENARIO_ID = "contains-duplicate-set"
MODEL_VARIABLES = ("nums", "box", "num")
FORBIDDEN_VARIABLES = ("seen",)
STAGE_ORDER = ("anchor", "box-meaning", "membership", "order", "loop")
STAGE_TO_CONCEPT = {
    "anchor": "duplicate_meaning",
    "box-meaning": "box_meaning",
    "membership": "membership",
    "order": "check_before_add",
    "loop": "loop_assembly",
}
STAGE_REQUIRED_VARIABLES = {
    "anchor": ("nums",),
    "box-meaning": ("nums", "box", "num"),
    "membership": ("nums", "box", "num"),
    "order": ("nums", "box", "num"),
    "loop": ("nums", "box", "num"),
}
STAGE_ANCHORS = {
    "anchor": ("nums", "duplicate"),
    "box-meaning": ("box", "num"),
    "membership": ("num", "box"),
    "order": ("check", "add", "box"),
    "loop": ("num", "box"),
}
STAGE_FORBIDDEN = {
    "anchor": ("seen", "set", "loop"),
    "box-meaning": ("seen", "return", "full code"),
    "membership": ("seen", "add", "full code"),
    "order": ("seen", "full code"),
    "loop": ("seen",),
}
DIAGNOSIS_FAMILIES = {
    "none",
    "missing_prerequisite",
    "concept_failure",
    "representation_interference",
    "identifier_interference",
    "information_overload",
    "information_underload",
    "decomposition_too_coarse",
    "over_decomposition",
    "over_help",
    "uncertain_mixed",
}
OPERATIONS = {
    "explain",
    "clarify",
    "probe",
    "smaller_step",
    "show_trace",
    "change_representation",
    "give_hint",
    "assemble",
}
ASSISTANCE_LEVELS = {"A0", "A1", "A2"}
LEARNER_OUTCOMES = {"demonstrated", "not_yet", "uncertain"}

_DIAGNOSIS_ALIASES = {
    "mental_model": "concept_failure",
    "concept_gap": "concept_failure",
    "conceptual": "concept_failure",
    "recognition": "concept_failure",
    "confusion": "concept_failure",
    "representation": "representation_interference",
    "identifier_confusion": "identifier_interference",
    "mixed": "uncertain_mixed",
}
_OPERATION_ALIASES = {
    "contrast": "change_representation",
    "teach": "explain",
    "explain_concept": "explain",
    "question": "probe",
    "guide": "probe",
    "small_step": "smaller_step",
    "trace": "show_trace",
    "hint": "give_hint",
    "identify_required_state": "probe",
    "seen_set_membership": "probe",
}
_ASSISTANCE_ALIASES = {
    "minimal": "A1",
    "low": "A1",
    "moderate": "A2",
    "medium": "A2",
    "none": "A0",
}
_OUTCOME_ALIASES = {
    "correct": "demonstrated",
    "pass": "demonstrated",
    "incorrect": "not_yet",
    "wrong": "not_yet",
    "partial": "uncertain",
    "unclear": "uncertain",
}


class ModelTutoringError(ValueError):
    """A model proposal or generated response violates the pilot boundary."""


@dataclass(frozen=True)
class ModelDiagnosis:
    diagnosis_family: str
    operation: str
    assistance_level: str
    decomposition: str = ""

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ModelDiagnosis":
        if not isinstance(payload, Mapping):
            raise ModelTutoringError("model diagnosis must be an object")
        values = {
            "diagnosis_family": payload.get("diagnosis_family"),
            "operation": payload.get("operation"),
            "assistance_level": payload.get("assistance_level"),
            "decomposition": payload.get("decomposition", ""),
        }
        for field_name in ("diagnosis_family", "operation", "assistance_level"):
            if not isinstance(values[field_name], str) or not values[field_name].strip():
                raise ModelTutoringError(f"model diagnosis requires {field_name}")
        values["diagnosis_family"] = _DIAGNOSIS_ALIASES.get(
            values["diagnosis_family"], values["diagnosis_family"]
        )
        values["operation"] = _OPERATION_ALIASES.get(values["operation"], values["operation"])
        values["assistance_level"] = _ASSISTANCE_ALIASES.get(
            values["assistance_level"], values["assistance_level"]
        )
        if values["diagnosis_family"] not in DIAGNOSIS_FAMILIES:
            raise ModelTutoringError("unsupported diagnosis family")
        if values["operation"] not in OPERATIONS:
            raise ModelTutoringError("unsupported pedagogical operation")
        if values["assistance_level"] not in ASSISTANCE_LEVELS:
            raise ModelTutoringError("assistance must be A0, A1, or A2")
        if not isinstance(values["decomposition"], str):
            raise ModelTutoringError("decomposition must be a string")
        return cls(**values)


@dataclass(frozen=True)
class LearnerAssessment:
    """Model-proposed outcome tied to verbatim learner evidence."""

    learner_outcome: str
    evidence_quote: str = ""
    rationale: str = ""

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
        *,
        learner_message: str,
    ) -> "LearnerAssessment":
        if not isinstance(payload, Mapping):
            raise ModelTutoringError("learner assessment must be an object")
        outcome = payload.get("learner_outcome")
        quote = payload.get("evidence_quote", "")
        rationale = payload.get("rationale", "")
        if not isinstance(outcome, str) or not outcome.strip():
            raise ModelTutoringError("learner assessment requires learner_outcome")
        outcome = _OUTCOME_ALIASES.get(outcome, outcome)
        if outcome not in LEARNER_OUTCOMES:
            raise ModelTutoringError("unsupported learner outcome")
        if not isinstance(quote, str) or not isinstance(rationale, str):
            raise ModelTutoringError("assessment evidence_quote and rationale must be strings")
        quote = quote.strip()
        if quote and quote.casefold() not in learner_message.casefold():
            raise ModelTutoringError("assessment evidence_quote must be verbatim learner text")
        if outcome == "demonstrated" and not quote:
            raise ModelTutoringError("demonstrated outcome requires verbatim learner evidence")
        return cls(outcome, quote, rationale.strip())


@dataclass(frozen=True)
class ModelTutoringState:
    """Deterministic state; model output is never stored as authority."""

    stage_index: int = 0
    mastery_proven: bool = False
    turns_seen: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.stage_index < len(STAGE_ORDER):
            raise ModelTutoringError("stage_index is outside the pilot progression")
        if self.mastery_proven:
            raise ModelTutoringError("pilot cannot claim mastery from model tutoring")

    @property
    def stage(self) -> str:
        return STAGE_ORDER[self.stage_index]


@dataclass(frozen=True)
class GenerationContract:
    scenario_id: str
    turn_index: int
    learner_signal: str
    learner_outcome: str
    evidence_quote: str
    stage: str
    target_concept: str
    allowed_variables: tuple[str, ...]
    forbidden_variables: tuple[str, ...]
    required_anchors: tuple[str, ...]
    forbidden_terms: tuple[str, ...]
    required_completion_terms: tuple[str, ...] = ()
    visual_required: bool = True
    visual_before_explanation: bool = True
    max_nonempty_lines: int = 12
    must_ask_question: bool = True
    max_relations: int = 1
    advance_allowed: bool = False
    prompt_version: str = PROMPT_VERSION
    model_identifier: str = "gpt-5.6-luna"

    def trace(
        self,
        diagnosis: ModelDiagnosis,
        assessment: LearnerAssessment,
        *,
        advance: bool,
    ) -> dict[str, Any]:
        return {
            "schema_version": TRACE_SCHEMA_VERSION,
            "scenario_id": self.scenario_id,
            "turn_index": self.turn_index,
            "path_kind": "model_generated",
            "target_concept": self.target_concept,
            "diagnosis_family": diagnosis.diagnosis_family,
            "operation": diagnosis.operation,
            "assistance_level": diagnosis.assistance_level,
            "learner_outcome": assessment.learner_outcome,
            "evidence_quote": assessment.evidence_quote,
            "advance": advance,
            "allowed_variables": list(self.allowed_variables),
            "forbidden_variables": list(self.forbidden_variables),
            "visual_required": self.visual_required,
            "prompt_version": self.prompt_version,
            "model_identifier": self.model_identifier,
        }


@dataclass(frozen=True)
class Authorization:
    contract: GenerationContract
    diagnosis: ModelDiagnosis
    assessment: LearnerAssessment
    trace: dict[str, Any]
    next_state: ModelTutoringState


def _contains_identifier(text: str, identifier: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9_]){re.escape(identifier)}(?![A-Za-z0-9_])",
        text,
        flags=re.IGNORECASE,
    ) is not None


def _has_visual(text: str) -> bool:
    return (
        "```" in text
        or "|" in text
        or "→" in text
        or "->" in text
        or ("[" in text and "]" in text and "\n" in text)
    )


def _nonempty_lines(text: str) -> int:
    return sum(bool(line.strip()) for line in text.splitlines())


def _relation_count(text: str) -> int:
    return sum(
        1
        for line in text.splitlines()
        if re.match(r"^\s*(?:one\s+)?relation\s*:", line, flags=re.IGNORECASE)
    )


def validate_generated_response(text: str, contract: GenerationContract) -> None:
    if not isinstance(text, str) or not text.strip():
        raise ModelTutoringError("generated response is empty")
    lowered = text.lower()
    missing = [term for term in contract.required_anchors if term.lower() not in lowered]
    if missing:
        raise ModelTutoringError(f"missing required anchors: {missing}")
    completion_missing = [
        term for term in contract.required_completion_terms if term.lower() not in lowered
    ]
    if completion_missing:
        raise ModelTutoringError(f"missing required loop completion: {completion_missing}")
    if contract.required_completion_terms and "return false" not in lowered:
        raise ModelTutoringError("final loop turn must explicitly establish `return False`")
    forbidden = [
        term for term in contract.forbidden_terms if term and term.lower() in lowered
    ]
    if forbidden:
        raise ModelTutoringError(f"forbidden concept or alias exposed: {forbidden}")
    if contract.visual_required and not _has_visual(text):
        raise ModelTutoringError("required visual is missing")
    if contract.visual_before_explanation:
        first = next((line.strip() for line in text.splitlines() if line.strip()), "")
        if not first.startswith(("```", "|", "index:", "nums:", "value:", "[")):
            raise ModelTutoringError("visual must precede explanation")
    if contract.must_ask_question and "?" not in text:
        raise ModelTutoringError("learner-sized check question is missing")
    if _nonempty_lines(text) > contract.max_nonempty_lines:
        raise ModelTutoringError("response exceeds the prose budget")
    if _relation_count(text) != contract.max_relations:
        raise ModelTutoringError("response must contain exactly one relation")
    for name in contract.forbidden_variables:
        if _contains_identifier(text, name):
            raise ModelTutoringError(f"forbidden variable alias exposed: {name}")
    if contract.stage != "loop" and ("def " in lowered or "class " in lowered):
        raise ModelTutoringError("full implementation leaked before loop assembly")


def _json_object(raw: str, *, label: str) -> dict[str, Any]:
    if not isinstance(raw, str):
        raise ModelTutoringError(f"{label} must be text")
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ModelTutoringError(f"{label} must be a JSON object") from exc
    if not isinstance(payload, dict):
        raise ModelTutoringError(f"{label} must be a JSON object")
    return payload


def parse_model_decision(raw: str, *, learner_message: str) -> tuple[ModelDiagnosis, LearnerAssessment]:
    payload = _json_object(raw, label="model diagnosis")
    diagnosis_payload = payload.get("diagnosis", payload)
    assessment_payload = payload.get("assessment", payload)
    diagnosis = ModelDiagnosis.from_payload(diagnosis_payload)
    assessment = LearnerAssessment.from_payload(
        assessment_payload,
        learner_message=learner_message,
    )
    return diagnosis, assessment


def parse_model_diagnosis(raw: str) -> ModelDiagnosis:
    """Backward-compatible diagnosis parser; progression code must use parse_model_decision."""

    payload = _json_object(raw, label="model diagnosis")
    return ModelDiagnosis.from_payload(payload.get("diagnosis", payload))


def parse_model_turn(raw: str) -> tuple[ModelDiagnosis, str]:
    payload = _json_object(raw, label="model turn")
    diagnosis = ModelDiagnosis.from_payload(payload.get("diagnosis", payload))
    response = payload.get("response")
    if not isinstance(response, str) or not response.strip():
        raise ModelTutoringError("model turn requires a learner-visible response")
    return diagnosis, response.strip()


def parse_generation_response(raw: str) -> str:
    payload = _json_object(raw, label="model generation")
    response = payload.get("response")
    if not isinstance(response, str) or not response.strip():
        raise ModelTutoringError("model generation requires response")
    return response.strip()


class ModelTutoringController:
    """Deterministic authorization for exactly one Contains Duplicate run."""

    def __init__(
        self,
        state: ModelTutoringState | None = None,
        *,
        prompt_version: str = PROMPT_VERSION,
        model_identifier: str = "gpt-5.6-luna",
    ) -> None:
        self.state = state or ModelTutoringState()
        self.prompt_version = prompt_version
        self.model_identifier = model_identifier

    def authorize(
        self,
        diagnosis: ModelDiagnosis,
        assessment: LearnerAssessment,
        *,
        learner_message: str,
        scenario_id: str = SCENARIO_ID,
        turn_index: int,
        learner_signal: str = "unspecified",
    ) -> Authorization:
        if scenario_id != SCENARIO_ID:
            raise ModelTutoringError("pilot controller only accepts contains-duplicate-set")
        if turn_index < 0:
            raise ModelTutoringError("turn_index must be non-negative")
        if not isinstance(learner_message, str) or not learner_message.strip():
            raise ModelTutoringError("learner_message is required for progression evidence")
        if assessment.evidence_quote and assessment.evidence_quote.casefold() not in learner_message.casefold():
            raise ModelTutoringError("progression evidence is not present in learner message")
        if assessment.learner_outcome == "demonstrated" and not assessment.evidence_quote:
            raise ModelTutoringError("demonstrated outcome requires learner evidence")

        stage = self.state.stage
        advance = (
            assessment.learner_outcome == "demonstrated"
            and self.state.stage_index < len(STAGE_ORDER) - 1
        )
        final_loop_turn = stage == "loop" and turn_index >= 14
        contract = GenerationContract(
            scenario_id=scenario_id,
            turn_index=turn_index,
            learner_signal=learner_signal,
            learner_outcome=assessment.learner_outcome,
            evidence_quote=assessment.evidence_quote,
            stage=stage,
            target_concept=STAGE_TO_CONCEPT[stage],
            allowed_variables=STAGE_REQUIRED_VARIABLES[stage],
            forbidden_variables=FORBIDDEN_VARIABLES,
            required_anchors=STAGE_ANCHORS[stage],
            forbidden_terms=STAGE_FORBIDDEN[stage],
            required_completion_terms=("return", "false") if final_loop_turn else (),
            advance_allowed=advance,
            prompt_version=self.prompt_version,
            model_identifier=self.model_identifier,
        )
        next_index = self.state.stage_index + (1 if advance else 0)
        next_state = ModelTutoringState(
            stage_index=next_index,
            mastery_proven=False,
            turns_seen=self.state.turns_seen + 1,
        )
        return Authorization(
            contract=contract,
            diagnosis=diagnosis,
            assessment=assessment,
            trace=contract.trace(diagnosis, assessment, advance=advance),
            next_state=next_state,
        )

    def commit(self, authorization: Authorization) -> None:
        self.state = authorization.next_state


def build_generation_prompt(
    contract: GenerationContract,
    *,
    learner_message: str,
    history: list[Mapping[str, str]] | None = None,
) -> str:
    """Build a bounded prompt; it contains policy, never a canonical lesson."""

    history = history or []
    completion = (
        " This is the final loop turn: explicitly teach/check the no-duplicate completion `return False`."
        if contract.required_completion_terms
        else ""
    )
    return (
        "Generate one bounded Study OS tutoring turn. Return JSON only with key `response` "
        "containing learner-visible markdown. The controller already assessed the learner; "
        "do not change progression or claim mastery. Start with a small visual, contain "
        "exactly one line beginning `Relation:`, use only the allowed variables "
        f"{list(contract.allowed_variables)}, never use {list(contract.forbidden_variables)}, "
        f"include {list(contract.required_anchors)}, avoid {list(contract.forbidden_terms)}, "
        f"ask one tiny question, and stay within {contract.max_nonempty_lines} non-empty lines. "
        f"Current concept: {contract.target_concept}; stage: {contract.stage}; "
        f"assessed learner outcome: {contract.learner_outcome}; evidence quote: {contract.evidence_quote!r}."
        + completion
        + "\n\nLearner message:\n"
        + learner_message
        + "\n\nRecent conversation:\n"
        + json.dumps(history[-6:], ensure_ascii=False)
    )


__all__ = [
    "ASSISTANCE_LEVELS",
    "Authorization",
    "DIAGNOSIS_FAMILIES",
    "FORBIDDEN_VARIABLES",
    "GenerationContract",
    "LEARNER_OUTCOMES",
    "LearnerAssessment",
    "ModelDiagnosis",
    "ModelTutoringController",
    "ModelTutoringError",
    "ModelTutoringState",
    "OPERATIONS",
    "PROMPT_VERSION",
    "SCENARIO_ID",
    "STAGE_ANCHORS",
    "STAGE_ORDER",
    "STAGE_REQUIRED_VARIABLES",
    "STAGE_TO_CONCEPT",
    "build_generation_prompt",
    "parse_generation_response",
    "parse_model_decision",
    "parse_model_diagnosis",
    "parse_model_turn",
    "validate_generated_response",
]
