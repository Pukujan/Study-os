"""Scenario-independent deterministic boundary for model-driven tutoring.

The model may propose a diagnosis, assess learner evidence, and write one
learner-visible response.  This module owns the trust boundary around those
proposals: the active concept comes from the immutable :class:`TeachingPlan`,
progression is evidence-gated, assistance is bounded, and generated text is
checked without generating lesson prose.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .prompt_registry import (
    DEFAULT_PROMPT_REGISTRY,
    GENERATION_PROMPT_VERSION,
    PromptProvenance,
    PromptRegistry,
)
from .teaching_plan import (
    ASSISTANCE_CEILINGS,
    CompletionEvidence,
    ConceptSpec,
    RepresentationRequirement,
    SemanticInvariant,
    TeachingPlan,
    TeachingPlanProvenance,
    VariableSpec,
)


LEARNER_OUTCOMES = frozenset({"demonstrated", "not_yet", "uncertain"})

# These are transport/safety bounds for one generated turn, rather than
# concept policy.  Concept-specific policy remains in the TeachingPlan.
_MAX_RESPONSE_CHARACTERS = 4000
_MAX_RESPONSE_NONEMPTY_LINES = 20
_INTERNAL_BOUNDARY_MARKERS = (
    "needs_compilation",
    "reviewed-asset",
    "reviewed_asset",
    "path_kind",
    "prompt_hash",
    "turn_trace_schema_version",
)

_OUTCOME_ALIASES = {
    "correct": "demonstrated",
    "pass": "demonstrated",
    "incorrect": "not_yet",
    "wrong": "not_yet",
    "partial": "uncertain",
    "unclear": "uncertain",
}

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

_ASSISTANCE_ALIASES = {
    "minimal": "A1",
    "low": "A1",
    "moderate": "A2",
    "medium": "A2",
    "none": "A0",
}


class ModelTutoringError(ValueError):
    """A model proposal, plan boundary, or generated response is invalid."""


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelTutoringError(f"{field_name} must be a non-empty string")
    return value.strip()


def _assistance_rank(level: str) -> int:
    ranks = {"A0": 0, "A1": 1, "A2": 2}
    try:
        return ranks[level]
    except KeyError as exc:
        raise ModelTutoringError("assistance must be A0, A1, or A2") from exc


@dataclass(frozen=True, slots=True)
class ModelDiagnosis:
    """A model hypothesis about the current learning bottleneck."""

    diagnosis_family: str
    operation: str
    assistance_level: str
    decomposition: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "diagnosis_family", _require_text(self.diagnosis_family, "diagnosis_family"))
        object.__setattr__(self, "operation", _require_text(self.operation, "operation"))
        assistance = _require_text(self.assistance_level, "assistance_level")
        if assistance not in ASSISTANCE_CEILINGS:
            raise ModelTutoringError("assistance must be A0, A1, or A2")
        object.__setattr__(self, "assistance_level", assistance)
        if not isinstance(self.decomposition, str):
            raise ModelTutoringError("decomposition must be a string")
        object.__setattr__(self, "decomposition", self.decomposition.strip())

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
            values["diagnosis_family"].strip(), values["diagnosis_family"].strip()
        )
        values["operation"] = values["operation"].strip()
        values["assistance_level"] = _ASSISTANCE_ALIASES.get(
            values["assistance_level"].strip(), values["assistance_level"].strip()
        )
        return cls(**values)


@dataclass(frozen=True, slots=True)
class LearnerAssessment:
    """A model outcome whose demonstrated claim is bound to learner text."""

    learner_outcome: str
    evidence_quote: str = ""
    rationale: str = ""

    def __post_init__(self) -> None:
        outcome = _require_text(self.learner_outcome, "learner_outcome")
        outcome = _OUTCOME_ALIASES.get(outcome, outcome)
        if outcome not in LEARNER_OUTCOMES:
            raise ModelTutoringError("unsupported learner outcome")
        object.__setattr__(self, "learner_outcome", outcome)
        if not isinstance(self.evidence_quote, str) or not isinstance(self.rationale, str):
            raise ModelTutoringError("assessment evidence_quote and rationale must be strings")
        quote = self.evidence_quote.strip()
        if outcome == "demonstrated" and not quote:
            raise ModelTutoringError("demonstrated outcome requires verbatim learner evidence")
        object.__setattr__(self, "evidence_quote", quote)
        object.__setattr__(self, "rationale", self.rationale.strip())

    @classmethod
    def from_payload(
        cls, payload: Mapping[str, Any], *, learner_message: str
    ) -> "LearnerAssessment":
        if not isinstance(payload, Mapping):
            raise ModelTutoringError("learner assessment must be an object")
        if not isinstance(learner_message, str) or not learner_message.strip():
            raise ModelTutoringError("learner_message is required for evidence binding")
        assessment = cls(
            learner_outcome=_require_text(payload.get("learner_outcome"), "learner_outcome"),
            evidence_quote=payload.get("evidence_quote", ""),
            rationale=payload.get("rationale", ""),
        )
        if assessment.evidence_quote and assessment.evidence_quote not in learner_message:
            raise ModelTutoringError("assessment evidence_quote must be verbatim learner text")
        return assessment


@dataclass(frozen=True, slots=True)
class LearnerState:
    """Immutable position in the plan's declared concept order."""

    concept_index: int = 0
    turns_seen: int = 0

    def __post_init__(self) -> None:
        if (
            isinstance(self.concept_index, bool)
            or not isinstance(self.concept_index, int)
            or self.concept_index < 0
        ):
            raise ModelTutoringError("concept_index must be a non-negative integer")
        if (
            isinstance(self.turns_seen, bool)
            or not isinstance(self.turns_seen, int)
            or self.turns_seen < 0
        ):
            raise ModelTutoringError("turns_seen must be a non-negative integer")

    @property
    def active_concept_index(self) -> int:
        """Alias making the state meaning explicit at controller call sites."""

        return self.concept_index


@dataclass(frozen=True, slots=True)
class GenerationContract:
    """Deterministic input contract for one generated learner-visible turn."""

    turn_index: int
    active_concept_index: int
    active_concept: ConceptSpec
    problem_statement: str
    allowed_variables: tuple[str, ...]
    representation_requirements: tuple[RepresentationRequirement, ...]
    semantic_invariants: tuple[SemanticInvariant, ...]
    completion_evidence: tuple[CompletionEvidence, ...]
    terminal_behavior: tuple[str, ...]
    assistance_ceiling: str
    requested_assistance: str
    learner_outcome: str
    evidence_quote: str
    diagnosis_family: str
    operation: str
    advance_allowed: bool
    prompt_provenance: PromptProvenance
    plan_provenance: TeachingPlanProvenance
    variable_bindings: Mapping[str, VariableSpec] = field(default_factory=dict, repr=False)
    forbidden_terms: tuple[str, ...] = ()
    visual_required: bool = True
    visual_before_explanation: bool = True

    def __post_init__(self) -> None:
        for field_name in ("turn_index", "active_concept_index"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ModelTutoringError(f"{field_name} must be a non-negative integer")
        if not isinstance(self.active_concept, ConceptSpec):
            raise ModelTutoringError("active_concept must be a ConceptSpec")
        object.__setattr__(self, "problem_statement", _require_text(self.problem_statement, "problem_statement"))
        variables = tuple(self.allowed_variables)
        if variables != self.active_concept.allowed_variables:
            raise ModelTutoringError("generation contract variables must match active concept")
        if not variables or len(variables) != len(set(variables)):
            raise ModelTutoringError("generation contract allowed_variables must be unique")
        object.__setattr__(self, "allowed_variables", variables)

        representations = tuple(self.representation_requirements)
        invariants = tuple(self.semantic_invariants)
        evidence = tuple(self.completion_evidence)
        if any(not isinstance(item, RepresentationRequirement) for item in representations):
            raise ModelTutoringError("representation_requirements must contain plan values")
        if any(not isinstance(item, SemanticInvariant) for item in invariants):
            raise ModelTutoringError("semantic_invariants must contain plan values")
        if any(not isinstance(item, CompletionEvidence) for item in evidence):
            raise ModelTutoringError("completion_evidence must contain plan values")
        if tuple(item.id for item in representations) != tuple(
            self.active_concept.representation_requirement_ids
        ):
            raise ModelTutoringError("generation contract representations do not match active concept")
        if tuple(item.id for item in invariants) != tuple(
            self.active_concept.semantic_invariant_ids
        ):
            raise ModelTutoringError("generation contract invariants do not match active concept")
        if tuple(item.id for item in evidence) != tuple(
            self.active_concept.completion_evidence_ids
        ):
            raise ModelTutoringError("generation contract completion evidence does not match active concept")
        object.__setattr__(self, "representation_requirements", representations)
        object.__setattr__(self, "semantic_invariants", invariants)
        object.__setattr__(self, "completion_evidence", evidence)
        if not isinstance(self.variable_bindings, Mapping):
            raise ModelTutoringError("variable_bindings must be a plan mapping")
        bindings = dict(self.variable_bindings)
        if any(not isinstance(name, str) for name in bindings):
            raise ModelTutoringError("variable_bindings keys must be strings")
        if any(not isinstance(value, VariableSpec) for value in bindings.values()):
            raise ModelTutoringError("variable_bindings values must be plan values")
        if set(self.allowed_variables) - set(bindings):
            raise ModelTutoringError("variable_bindings must cover allowed variables")
        object.__setattr__(self, "variable_bindings", MappingProxyType(bindings))

        terms = tuple(_require_text(item, "forbidden_terms[]") for item in self.forbidden_terms)
        if len(terms) != len({item.casefold() for item in terms}):
            raise ModelTutoringError("forbidden_terms must contain unique values")
        object.__setattr__(self, "forbidden_terms", terms)
        if not isinstance(self.visual_required, bool):
            raise ModelTutoringError("visual_required must be boolean")
        if not isinstance(self.visual_before_explanation, bool):
            raise ModelTutoringError("visual_before_explanation must be boolean")

        terminal = tuple(_require_text(item, "terminal_behavior[]") for item in self.terminal_behavior)
        if not terminal:
            raise ModelTutoringError("terminal_behavior must not be empty")
        object.__setattr__(self, "terminal_behavior", terminal)

        if self.assistance_ceiling not in ASSISTANCE_CEILINGS:
            raise ModelTutoringError("assistance_ceiling must be A0, A1, or A2")
        if self.requested_assistance not in ASSISTANCE_CEILINGS:
            raise ModelTutoringError("requested assistance must be A0, A1, or A2")
        if _assistance_rank(self.requested_assistance) > _assistance_rank(self.assistance_ceiling):
            raise ModelTutoringError("requested assistance exceeds teaching-plan ceiling")
        if self.learner_outcome not in LEARNER_OUTCOMES:
            raise ModelTutoringError("unsupported learner outcome")
        if not isinstance(self.evidence_quote, str):
            raise ModelTutoringError("evidence_quote must be a string")
        object.__setattr__(self, "evidence_quote", self.evidence_quote.strip())
        object.__setattr__(self, "diagnosis_family", _require_text(self.diagnosis_family, "diagnosis_family"))
        object.__setattr__(self, "operation", _require_text(self.operation, "operation"))
        if not isinstance(self.advance_allowed, bool):
            raise ModelTutoringError("advance_allowed must be boolean")
        if not isinstance(self.prompt_provenance, PromptProvenance):
            raise ModelTutoringError("prompt_provenance must be PromptProvenance")
        if not isinstance(self.plan_provenance, TeachingPlanProvenance):
            raise ModelTutoringError("plan_provenance must be TeachingPlanProvenance")

    @property
    def active_concept_id(self) -> str:
        return self.active_concept.id

    @property
    def concept_index(self) -> int:
        return self.active_concept_index

    @property
    def prompt_version(self) -> str:
        return self.prompt_provenance.prompt_version

    @property
    def prompt_hash(self) -> str:
        return self.prompt_provenance.prompt_hash

    @property
    def model_identifier(self) -> str:
        return self.prompt_provenance.model_identifier

    @property
    def representation_requirement_ids(self) -> tuple[str, ...]:
        return tuple(item.id for item in self.representation_requirements)

    @property
    def semantic_invariant_ids(self) -> tuple[str, ...]:
        return tuple(item.id for item in self.semantic_invariants)

    @property
    def completion_evidence_ids(self) -> tuple[str, ...]:
        return tuple(item.id for item in self.completion_evidence)

    @property
    def forbidden_variables(self) -> tuple[str, ...]:
        """Declared plan variables outside the active concept binding."""

        return tuple(
            name for name in self.variable_bindings
            if name not in self.allowed_variables
        )

    def trace(
        self, diagnosis: ModelDiagnosis, assessment: LearnerAssessment, *, advance: bool
    ) -> dict[str, Any]:
        return {
            "schema_version": self.plan_provenance.turn_trace_schema_version,
            "path_kind": "model_generated",
            "turn_index": self.turn_index,
            "active_concept_index": self.active_concept_index,
            "active_concept_id": self.active_concept_id,
            "diagnosis_family": diagnosis.diagnosis_family,
            "operation": diagnosis.operation,
            "assistance_level": diagnosis.assistance_level,
            "assistance_ceiling": self.assistance_ceiling,
            "learner_outcome": assessment.learner_outcome,
            "evidence_quote": assessment.evidence_quote,
            "advance": advance,
            "allowed_variables": list(self.allowed_variables),
            "representation_requirement_ids": list(self.representation_requirement_ids),
            "semantic_invariant_ids": list(self.semantic_invariant_ids),
            "completion_evidence_ids": list(self.completion_evidence_ids),
            "prompt_version": self.prompt_provenance.prompt_version,
            "prompt_hash": self.prompt_provenance.prompt_hash,
            "model_identifier": self.prompt_provenance.model_identifier,
            "teaching_plan_schema_version": self.plan_provenance.teaching_plan_schema_version,
            "run_id": self.prompt_provenance.run_id,
            "source_problem_id": self.prompt_provenance.source_problem_id,
            "prompt_provenance": self.prompt_provenance.to_payload(),
            "plan_provenance": _plan_provenance_payload(self.plan_provenance),
            "forbidden_terms": list(self.forbidden_terms),
            "visual_required": self.visual_required,
            "visual_before_explanation": self.visual_before_explanation,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return a serializable contract view without lesson content."""

        return {
            "turn_index": self.turn_index,
            "active_concept_index": self.active_concept_index,
            "active_concept_id": self.active_concept_id,
            "problem_statement": self.problem_statement,
            "allowed_variables": list(self.allowed_variables),
            "representation_requirements": [
                {
                    "id": item.id,
                    "kind": item.kind,
                    "operation": item.operation,
                    "description": item.description,
                    "required": item.required,
                }
                for item in self.representation_requirements
            ],
            "semantic_invariants": [
                {"id": item.id, "concept_id": item.concept_id, "statement": item.statement}
                for item in self.semantic_invariants
            ],
            "completion_evidence": [
                {
                    "id": item.id,
                    "concept_id": item.concept_id,
                    "evidence_type": item.evidence_type,
                    "description": item.description,
                }
                for item in self.completion_evidence
            ],
            "terminal_behavior": list(self.terminal_behavior),
            "assistance_ceiling": self.assistance_ceiling,
            "requested_assistance": self.requested_assistance,
            "learner_outcome": self.learner_outcome,
            "evidence_quote": self.evidence_quote,
            "advance_allowed": self.advance_allowed,
            "forbidden_terms": list(self.forbidden_terms),
            "prompt_provenance": self.prompt_provenance.to_payload(),
            "plan_provenance": _plan_provenance_payload(self.plan_provenance),
        }


@dataclass(frozen=True, slots=True)
class Authorization:
    """A proposed turn plus the immutable state to commit if accepted."""

    contract: GenerationContract
    diagnosis: ModelDiagnosis
    assessment: LearnerAssessment
    trace: dict[str, Any]
    next_state: LearnerState

    @property
    def completion_candidate(self) -> bool:
        """Whether this turn demonstrated the plan's final concept.

        The generic controller has no mastery flag and therefore never marks a
        learner complete.  A completion-driven runner may use this signal only
        as a candidate terminal event, after independently validating terminal
        and integration evidence.
        """

        return (
            self.assessment.learner_outcome == "demonstrated"
            and not self.contract.advance_allowed
        )


def _plan_provenance_payload(provenance: TeachingPlanProvenance) -> dict[str, str]:
    return {
        "prompt_version": provenance.prompt_version,
        "prompt_hash": provenance.prompt_hash,
        "model_identifier": provenance.model_identifier,
        "teaching_plan_schema_version": provenance.teaching_plan_schema_version,
        "turn_trace_schema_version": provenance.turn_trace_schema_version,
        "run_id": provenance.run_id,
        "source_problem_id": provenance.source_problem_id,
    }


def _contains_identifier(text: str, identifier: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9_]){re.escape(identifier)}(?![A-Za-z0-9_])",
        text,
        flags=re.IGNORECASE,
    ) is not None


def _representation_present(text: str, requirement: RepresentationRequirement) -> bool:
    lowered = text.casefold()
    if requirement.id.casefold() in lowered:
        return True
    kind = requirement.kind.casefold()
    operation = requirement.operation.casefold()
    if kind in lowered and operation in lowered:
        return True

    # A model is allowed to render the requested representation in ordinary
    # learner language rather than echoing the internal requirement id or both
    # metadata labels.  Use the generated description as a small deterministic
    # semantic anchor: require at least two meaningful description terms, plus
    # the visual boundary checked by the caller.  This keeps the validator from
    # authoring a chart while avoiding brittle dependence on labels such as
    # ``predict`` that a learner would never see.
    stop_words = {
        "a", "an", "and", "as", "at", "be", "by", "for", "from", "in",
        "of", "on", "or", "the", "to", "with", "each", "show", "represent",
    }
    terms = {
        term
        for term in re.findall(r"[a-z][a-z0-9_]*", requirement.description.casefold())
        if term not in stop_words and len(term) > 2
    }
    return len(terms & set(re.findall(r"[a-z][a-z0-9_]*", lowered))) >= min(2, len(terms))


def _looks_visual(text: str) -> bool:
    """Recognize a small learner-visible chart/trace without authoring one."""

    return (
        "```" in text
        or "|" in text
        or "→" in text
        or "->" in text
        or ("[" in text and "]" in text and "\n" in text)
    )


def validate_generated_response(text: str, contract: GenerationContract) -> None:
    """Validate one bounded response; this function never creates response text."""

    if not isinstance(contract, GenerationContract):
        raise ModelTutoringError("contract must be a GenerationContract")
    if not isinstance(text, str) or not text.strip():
        raise ModelTutoringError("generated response is empty")
    if len(text) > _MAX_RESPONSE_CHARACTERS:
        raise ModelTutoringError("response exceeds the character boundary")
    if sum(bool(line.strip()) for line in text.splitlines()) > _MAX_RESPONSE_NONEMPTY_LINES:
        raise ModelTutoringError("response exceeds the non-empty-line boundary")

    lowered = text.casefold()
    leaked = [marker for marker in _INTERNAL_BOUNDARY_MARKERS if marker in lowered]
    if leaked:
        raise ModelTutoringError(f"internal routing/provenance marker leaked: {leaked}")

    missing_representations = [
        requirement.id
        for requirement in contract.representation_requirements
        if requirement.required and not _representation_present(text, requirement)
    ]
    if missing_representations:
        raise ModelTutoringError(
            f"required representation requirements are missing: {missing_representations}"
        )

    forbidden_terms = [
        term
        for term in contract.forbidden_terms
        if (
            _contains_identifier(text, term)
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", term)
            else term.casefold() in lowered
        )
    ]
    if forbidden_terms:
        raise ModelTutoringError(f"forbidden source terms leaked: {forbidden_terms}")

    if contract.visual_required and not _looks_visual(text):
        raise ModelTutoringError("required visual is missing")
    if contract.visual_before_explanation:
        first = next((line.strip() for line in text.splitlines() if line.strip()), "")
        variable_header = any(
            re.match(rf"^{re.escape(name)}\s*[:=]", first, flags=re.IGNORECASE)
            for name in contract.allowed_variables
        )
        table_header = "|" in first
        if not first.startswith(("```", "|", "[", "index:", "nums:", "value:")) and not variable_header and not table_header:
            raise ModelTutoringError("visual must precede explanation")

    forbidden = [
        name for name in contract.forbidden_variables
        if _contains_identifier(text, name)
    ]
    if forbidden:
        raise ModelTutoringError(f"variables outside the active concept leaked: {forbidden}")


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


def parse_model_decision(
    raw: str, *, learner_message: str
) -> tuple[ModelDiagnosis, LearnerAssessment]:
    payload = _json_object(raw, label="model decision")
    diagnosis_payload = payload.get("diagnosis", payload)
    diagnosis = ModelDiagnosis.from_payload(diagnosis_payload)
    # Luna occasionally nests the assessment alongside its diagnosis.  Treat
    # that as a transport-shape variation, not as learner evidence: the same
    # deterministic evidence binding still runs below.
    assessment_payload = payload.get("assessment")
    if assessment_payload is None and isinstance(diagnosis_payload, Mapping):
        assessment_payload = diagnosis_payload.get("assessment")
    if assessment_payload is None:
        assessment_payload = payload
    assessment = LearnerAssessment.from_payload(
        assessment_payload, learner_message=learner_message
    )
    return diagnosis, assessment


def parse_model_diagnosis(raw: str) -> ModelDiagnosis:
    payload = _json_object(raw, label="model diagnosis")
    return ModelDiagnosis.from_payload(payload.get("diagnosis", payload))


def parse_generation_response(raw: str) -> str:
    payload = _json_object(raw, label="model generation")
    response = payload.get("response")
    if not isinstance(response, str) or not response.strip():
        raise ModelTutoringError("model generation requires response")
    return response.strip()


class GenericModelTutoringController:
    """Authorize exactly one generic plan-constrained tutoring operation."""

    def __init__(
        self,
        plan: TeachingPlan,
        state: LearnerState | None = None,
        *,
        prompt_registry: PromptRegistry = DEFAULT_PROMPT_REGISTRY,
        generation_prompt_version: str = GENERATION_PROMPT_VERSION,
        model_identifier: str | None = None,
        forbidden_terms: Sequence[str] = (),
        visual_required: bool = True,
        visual_before_explanation: bool = True,
    ) -> None:
        if not isinstance(plan, TeachingPlan):
            raise ModelTutoringError("controller requires a validated TeachingPlan")
        if not isinstance(prompt_registry, PromptRegistry):
            raise ModelTutoringError("prompt_registry must be a PromptRegistry")
        self._validate_concept_order(plan)
        current_state = state or LearnerState()
        if current_state.concept_index >= len(plan.concepts):
            raise ModelTutoringError("state concept_index is outside the plan concept order")
        if model_identifier is None:
            model_identifier = plan.provenance.model_identifier
        model_identifier = _require_text(model_identifier, "model_identifier")
        try:
            generation_prompt = prompt_registry.for_role(
                "generation", version=generation_prompt_version
            )
        except (KeyError, ValueError) as exc:
            raise ModelTutoringError("generation prompt provenance is not registered") from exc

        self.plan = plan
        self.state = current_state
        self.prompt_registry = prompt_registry
        self.model_identifier = model_identifier
        self._generation_prompt = generation_prompt
        normalized_terms = tuple(_require_text(item, "forbidden_terms[]") for item in forbidden_terms)
        if len(normalized_terms) != len({item.casefold() for item in normalized_terms}):
            raise ModelTutoringError("forbidden_terms must contain unique values")
        self.forbidden_terms = normalized_terms
        if not isinstance(visual_required, bool):
            raise ModelTutoringError("visual_required must be boolean")
        if not isinstance(visual_before_explanation, bool):
            raise ModelTutoringError("visual_before_explanation must be boolean")
        self.visual_required = visual_required
        self.visual_before_explanation = visual_before_explanation

    @staticmethod
    def _validate_concept_order(plan: TeachingPlan) -> None:
        completed_ids: set[str] = set()
        for concept in plan.concepts:
            missing = sorted(set(concept.prerequisites) - completed_ids)
            if missing:
                raise ModelTutoringError(
                    f"plan concept order violates prerequisites for {concept.id}: {missing}"
                )
            completed_ids.add(concept.id)

    @property
    def active_concept(self) -> ConceptSpec:
        return self.plan.concepts[self.state.concept_index]

    def _prompt_provenance(self) -> PromptProvenance:
        return self._generation_prompt.provenance(
            model_identifier=self.model_identifier,
            teaching_plan_schema_version=self.plan.schema_version,
            turn_trace_schema_version=self.plan.provenance.turn_trace_schema_version,
            run_id=self.plan.provenance.run_id,
            source_problem_id=self.plan.provenance.source_problem_id,
        )

    def _generation_contract(
        self,
        diagnosis: ModelDiagnosis,
        assessment: LearnerAssessment,
        *,
        turn_index: int,
        advance: bool,
    ) -> GenerationContract:
        concept = self.active_concept
        requirements_by_id = {
            item.id: item for item in self.plan.representation_requirements
        }
        invariants_by_id = {item.id: item for item in self.plan.semantic_invariants}
        evidence_by_id = {item.id: item for item in self.plan.completion_evidence}
        return GenerationContract(
            turn_index=turn_index,
            active_concept_index=self.state.concept_index,
            active_concept=concept,
            problem_statement=self.plan.problem.statement,
            allowed_variables=concept.allowed_variables,
            representation_requirements=tuple(
                requirements_by_id[item_id]
                for item_id in concept.representation_requirement_ids
            ),
            semantic_invariants=tuple(
                invariants_by_id[item_id] for item_id in concept.semantic_invariant_ids
            ),
            completion_evidence=tuple(
                evidence_by_id[item_id] for item_id in concept.completion_evidence_ids
            ),
            terminal_behavior=self.plan.terminal_behavior,
            assistance_ceiling=self.plan.assistance_ceiling,
            requested_assistance=diagnosis.assistance_level,
            learner_outcome=assessment.learner_outcome,
            evidence_quote=assessment.evidence_quote,
            diagnosis_family=diagnosis.diagnosis_family,
            operation=diagnosis.operation,
            advance_allowed=advance,
            prompt_provenance=self._prompt_provenance(),
            plan_provenance=self.plan.provenance,
            variable_bindings=self.plan.variables,
            forbidden_terms=self.forbidden_terms,
            visual_required=self.visual_required,
            visual_before_explanation=self.visual_before_explanation,
        )

    def authorize(
        self,
        diagnosis: ModelDiagnosis,
        assessment: LearnerAssessment,
        *,
        learner_message: str,
        turn_index: int | None = None,
    ) -> Authorization:
        if not isinstance(diagnosis, ModelDiagnosis):
            raise ModelTutoringError("diagnosis must be a ModelDiagnosis")
        if not isinstance(assessment, LearnerAssessment):
            raise ModelTutoringError("assessment must be a LearnerAssessment")
        if not isinstance(learner_message, str) or not learner_message.strip():
            raise ModelTutoringError("learner_message is required for evidence binding")
        if assessment.evidence_quote and assessment.evidence_quote not in learner_message:
            raise ModelTutoringError("assessment evidence_quote must be verbatim learner text")
        if assessment.learner_outcome == "demonstrated" and not assessment.evidence_quote:
            raise ModelTutoringError("demonstrated outcome requires verbatim learner evidence")
        if _assistance_rank(diagnosis.assistance_level) > _assistance_rank(
            self.plan.assistance_ceiling
        ):
            raise ModelTutoringError("model assistance exceeds teaching-plan ceiling")
        if turn_index is None:
            turn_index = self.state.turns_seen
        if isinstance(turn_index, bool) or not isinstance(turn_index, int) or turn_index < 0:
            raise ModelTutoringError("turn_index must be a non-negative integer")

        # This is deliberately one boolean transition.  It cannot skip a
        # concept, and the final concept remains active after its evidence is
        # demonstrated because the state has no unproven mastery flag.
        advance = (
            assessment.learner_outcome == "demonstrated"
            and self.state.concept_index < len(self.plan.concepts) - 1
        )
        contract = self._generation_contract(
            diagnosis, assessment, turn_index=turn_index, advance=advance
        )
        next_state = LearnerState(
            concept_index=self.state.concept_index + (1 if advance else 0),
            turns_seen=self.state.turns_seen + 1,
        )
        return Authorization(
            contract=contract,
            diagnosis=diagnosis,
            assessment=assessment,
            trace=contract.trace(diagnosis, assessment, advance=advance),
            next_state=next_state,
        )

    def authorize_model_decision(
        self,
        raw: str,
        *,
        learner_message: str,
        turn_index: int | None = None,
    ) -> Authorization:
        diagnosis, assessment = parse_model_decision(
            raw, learner_message=learner_message
        )
        return self.authorize(
            diagnosis,
            assessment,
            learner_message=learner_message,
            turn_index=turn_index,
        )

    def commit(self, authorization: Authorization) -> None:
        if not isinstance(authorization, Authorization):
            raise ModelTutoringError("authorization must be an Authorization")
        self.state = authorization.next_state


def build_generation_prompt(
    contract: GenerationContract,
    *,
    learner_message: str,
    history: Sequence[Mapping[str, str]] | None = None,
    prompt_registry: PromptRegistry = DEFAULT_PROMPT_REGISTRY,
) -> str:
    """Build model instructions from a contract; never author lesson prose."""

    if not isinstance(contract, GenerationContract):
        raise ModelTutoringError("contract must be a GenerationContract")
    if not isinstance(learner_message, str) or not learner_message.strip():
        raise ModelTutoringError("learner_message is required")
    if not isinstance(prompt_registry, PromptRegistry):
        raise ModelTutoringError("prompt_registry must be a PromptRegistry")
    try:
        prompt_definition = prompt_registry.verify(
            version=contract.prompt_provenance.prompt_version,
            prompt_hash=contract.prompt_provenance.prompt_hash,
        )
    except (KeyError, ValueError) as exc:
        raise ModelTutoringError("contract prompt provenance cannot be resolved") from exc

    recent_history = []
    for item in (history or ())[-6:]:
        if not isinstance(item, Mapping):
            raise ModelTutoringError("history entries must be objects")
        recent_history.append(dict(item))
    requirements = [
        {
            "id": item.id,
            "kind": item.kind,
            "operation": item.operation,
            "required": item.required,
        }
        for item in contract.representation_requirements
    ]
    invariants = [
        {"id": item.id, "statement": item.statement}
        for item in contract.semantic_invariants
    ]
    completion = [
        {"id": item.id, "evidence_type": item.evidence_type}
        for item in contract.completion_evidence
    ]
    return (
        f"{prompt_definition.content}\n\n"
        "Return JSON only with key `response`. The controller owns progression; "
        "do not claim mastery, change the active concept, or expose internal routing. "
        "Use only the active contract and keep the response within the deterministic "
        "response boundary.\n"
        f"Active concept: {contract.active_concept_id}\n"
        f"Allowed variables: {list(contract.allowed_variables)}\n"
        f"Forbidden source terms: {list(contract.forbidden_terms)}\n"
        f"Visual required: {contract.visual_required}; visual must precede explanation: "
        f"{contract.visual_before_explanation}\n"
        f"Representation requirements: {json.dumps(requirements, ensure_ascii=False)}\n"
        f"Semantic invariants: {json.dumps(invariants, ensure_ascii=False)}\n"
        f"Completion evidence: {json.dumps(completion, ensure_ascii=False)}\n"
        f"Terminal behavior: {list(contract.terminal_behavior)}\n"
        f"Assistance ceiling: {contract.assistance_ceiling}; requested assistance: "
        f"{contract.requested_assistance}\n"
        f"Assessed learner outcome: {contract.learner_outcome}; evidence quote: "
        f"{contract.evidence_quote!r}\n"
        f"Prompt provenance: {json.dumps(contract.prompt_provenance.to_payload(), ensure_ascii=False)}\n\n"
        "Learner message:\n"
        f"{learner_message}\n\n"
        "Recent conversation:\n"
        f"{json.dumps(recent_history, ensure_ascii=False)}"
    )


# Compatibility aliases keep the generic API easy to discover without
# reintroducing the legacy scenario-specific implementation.
GenericTutoringState = LearnerState
ModelTutoringState = LearnerState
GenericModelTutoringError = ModelTutoringError
ModelTutoringController = GenericModelTutoringController


__all__ = [
    "Authorization",
    "GenerationContract",
    "GenericModelTutoringController",
    "GenericModelTutoringError",
    "GenericTutoringState",
    "LEARNER_OUTCOMES",
    "LearnerAssessment",
    "LearnerState",
    "ModelDiagnosis",
    "ModelTutoringController",
    "ModelTutoringError",
    "ModelTutoringState",
    "build_generation_prompt",
    "parse_generation_response",
    "parse_model_decision",
    "parse_model_diagnosis",
    "validate_generated_response",
]
