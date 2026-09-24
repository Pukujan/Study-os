"""Golden-conformance evaluator for canonical PIR teaching assets.

The rules mirror ``Pukujan/study-os-benchmarker`` at commit
``d438988fda12e9df902caabbcb6a639834452d5d``:

- ``specs/VERIFICATION.md`` BINV-001..005 (legal next node, required bridges,
  required representation, forbidden concepts, answer-reveal policy);
- ``src/study_os_benchmarker/evaluator.py`` (proposal violation codes and their order);
- ``src/study_os_benchmarker/decomposition.py`` (missing concept, ordering,
  representation attachment, and the new-concept budget per step).

The benchmarker scores one proposed tutor move. Here the same rules run over every
step of a shipped asset, projected the way the benchmarker projects a decomposition:
the main path (entry, automatic transitions, and CORRECT routes) gives the order in
which relations are introduced, and each representation's ``relation:<concept>``
components give what a step introduces. Two Study OS golden rules the benchmarker
does not encode are added as named codes: ``FEEDBACK_DISCIPLINE`` (correct, wrong,
and partial routing) and ``MASTERY_CLAIM`` (the benchmarker's ``mastery_claim``
forbidden concept, applied to learner-visible text and exit states).

Nothing here is imported from the benchmarker at runtime. Violation order is part of
the report semantics and must stay stable.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    AssessmentKind,
    AssessmentSpec,
    CanonicalTeachingAsset,
    LearnerOutcome,
    RepresentationSpec,
    RunStatus,
    StepKind,
    TeachingStep,
)

BENCHMARKER_REPOSITORY = "Pukujan/study-os-benchmarker"
BENCHMARKER_COMMIT = "d438988fda12e9df902caabbcb6a639834452d5d"
EVALUATOR_VERSION = "study-os.pir-golden-conformance.v0.1.0"
RELATION_PREFIX = "relation:"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ConformanceViolationCode(StrEnum):
    ILLEGAL_STEP = "ILLEGAL_STEP"
    MISSING_REQUIRED_BRIDGE = "MISSING_REQUIRED_BRIDGE"
    ORDERING_VIOLATION = "ORDERING_VIOLATION"
    TOO_MANY_NEW_CONCEPTS = "TOO_MANY_NEW_CONCEPTS"
    MISSING_REPRESENTATION = "MISSING_REPRESENTATION"
    FORBIDDEN_REPRESENTATION_PRESENT = "FORBIDDEN_REPRESENTATION_PRESENT"
    FORBIDDEN_CONCEPT_DISCLOSED = "FORBIDDEN_CONCEPT_DISCLOSED"
    ANSWER_REVEAL_FORBIDDEN = "ANSWER_REVEAL_FORBIDDEN"
    FEEDBACK_DISCIPLINE = "FEEDBACK_DISCIPLINE"
    MASTERY_CLAIM = "MASTERY_CLAIM"


class GoldenSource(_Strict):
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class GoldenBridge(_Strict):
    concept_id: str = Field(min_length=1)
    golden_step: str = Field(min_length=1)


class ConceptRepresentationRule(_Strict):
    concept_id: str = Field(min_length=1)
    all_steps: tuple[str, ...] = ()
    intro: tuple[str, ...] = ()
    probe_required: tuple[str, ...] = ()
    probe_forbidden: tuple[str, ...] = ()


class ForbiddenConcept(_Strict):
    concept_id: str = Field(min_length=1)
    text_markers: tuple[str, ...] = ()


class GoldenOracle(_Strict):
    schema_version: str = Field(pattern=r"^study-os\.pir-golden-oracle\.v0$")
    canonical_problem_id: str = Field(min_length=1)
    benchmarker_repository: str = Field(min_length=1)
    benchmarker_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    golden_sources: tuple[GoldenSource, ...] = Field(min_length=1)
    required_bridges: tuple[GoldenBridge, ...] = Field(min_length=1)
    terminal_concepts: tuple[str, ...] = ()
    max_new_concepts_per_step: int = Field(ge=1)
    feedback_required: tuple[str, ...] = ()
    fix_required: tuple[str, ...] = ()
    partial_required: tuple[str, ...] = ()
    representation_rules: tuple[ConceptRepresentationRule, ...] = ()
    forbidden_concepts: tuple[ForbiddenConcept, ...] = ()
    probe_forbidden_glyph_patterns: tuple[str, ...] = ()
    structural_glyph_lines: tuple[str, ...] = ()
    mastery_patterns: tuple[str, ...] = ()
    mastery_allowed_phrases: tuple[str, ...] = ()
    allowed_exit_statuses: tuple[RunStatus, ...] = Field(min_length=1)


class ConformanceViolation(_Strict):
    code: ConformanceViolationCode
    detail: str = Field(min_length=1)


class ConformanceReport(_Strict):
    evaluator_version: str
    benchmarker_commit: str
    canonical_problem_id: str
    canonical_pir_revision: str
    passed: bool
    main_path_concepts: tuple[str, ...]
    violations: tuple[ConformanceViolation, ...]


def concept_of(step_id: str) -> str:
    return step_id.split(".", 1)[0]


def _relations(representation: RepresentationSpec) -> tuple[str, ...]:
    return tuple(
        component[len(RELATION_PREFIX) :]
        for component in representation.visible_components
        if component.startswith(RELATION_PREFIX)
    )


def _route(step: TeachingStep, outcome: LearnerOutcome) -> str | None:
    for transition in step.outcome_transitions:
        if transition.outcome == outcome:
            return transition.next_step_id
    return None


def main_path(asset: CanonicalTeachingAsset) -> tuple[TeachingStep, ...]:
    """Entry, automatic transitions, and CORRECT routes until exit or a repeat."""

    steps = {step.step_id: step for step in asset.steps}
    path: list[TeachingStep] = []
    seen: set[str] = set()
    current: str | None = asset.entry_step_id
    while current is not None and current in steps and current not in seen:
        seen.add(current)
        step = steps[current]
        path.append(step)
        if step.kind == StepKind.PROBE:
            current = _route(step, LearnerOutcome.CORRECT)
        elif step.automatic_transition is not None:
            current = step.automatic_transition.next_step_id
        else:
            current = None
    return tuple(path)


def _answer_literals(assessment: AssessmentSpec) -> tuple[str, ...]:
    if assessment.kind == AssessmentKind.TEXT:
        return tuple(re.sub(r"\s+", "", text) for text in assessment.expected_text)
    if assessment.kind == AssessmentKind.INTEGER_SEQUENCE and len(assessment.expected_values) > 1:
        values = assessment.expected_values
        return (
            "(" + ",".join(str(value) for value in values) + ")",
            "(" + ", ".join(str(value) for value in values) + ")",
        )
    return ()


def _strip_structural_lines(markdown: str, structural: tuple[str, ...]) -> str:
    lines = markdown.splitlines()
    kept: list[str] = []
    skip_next = False
    for line in lines:
        if skip_next:
            skip_next = False
            continue
        if line.strip() in structural:
            skip_next = True
            kept.append(line)
            continue
        kept.append(line)
    return "\n".join(kept)


def evaluate_asset(
    oracle: GoldenOracle,
    asset: CanonicalTeachingAsset,
) -> ConformanceReport:
    violations: list[ConformanceViolation] = []

    def add(code: ConformanceViolationCode, detail: str) -> None:
        violations.append(ConformanceViolation(code=code, detail=detail))

    steps = {step.step_id: step for step in asset.steps}
    representations = {item.representation_id: item for item in asset.representations}
    assessments = {item.assessment_id: item for item in asset.assessments}
    golden_order = tuple(bridge.concept_id for bridge in oracle.required_bridges)
    legal_concepts = set(golden_order).union(oracle.terminal_concepts)
    rules = {rule.concept_id: rule for rule in oracle.representation_rules}

    def rep_of(step: TeachingStep) -> RepresentationSpec | None:
        return representations.get(step.representation_id)

    # BINV-001: every step belongs to a golden concept (no invented steps).
    illegal = sorted(
        step.step_id for step in asset.steps if concept_of(step.step_id) not in legal_concepts
    )
    if illegal:
        add(
            ConformanceViolationCode.ILLEGAL_STEP,
            "step(s) outside the golden concepts: " + ", ".join(illegal),
        )

    # Decomposition projection over the main path.
    path = main_path(asset)
    introduced_at: dict[str, int] = {}
    oversized: list[str] = []
    for position, step in enumerate(path):
        representation = rep_of(step)
        if representation is None:
            continue
        new = [
            relation
            for relation in dict.fromkeys(_relations(representation))
            if relation not in introduced_at
        ]
        for relation in new:
            introduced_at[relation] = position
        if len(new) > oracle.max_new_concepts_per_step:
            oversized.append(f"{step.step_id} ({', '.join(new)})")
    main_concepts = tuple(sorted(introduced_at, key=lambda item: introduced_at[item]))

    # BINV-002 / decomposition MISSING_CONCEPT: every golden step is introduced.
    missing = [
        f"{bridge.concept_id} ({bridge.golden_step})"
        for bridge in oracle.required_bridges
        if bridge.concept_id not in introduced_at
    ]
    if missing:
        add(
            ConformanceViolationCode.MISSING_REQUIRED_BRIDGE,
            "golden step(s) missing from the main path: " + ", ".join(missing),
        )

    # Decomposition ORDERING_VIOLATION over consecutive golden steps.
    bad_orderings: list[str] = []
    for before, after in zip(golden_order, golden_order[1:]):
        first, second = introduced_at.get(before), introduced_at.get(after)
        if first is not None and second is not None and first >= second:
            bad_orderings.append(f"{before}->{after}")
    if bad_orderings:
        add(
            ConformanceViolationCode.ORDERING_VIOLATION,
            "golden order violated: " + ", ".join(sorted(bad_orderings)),
        )

    # Decomposition TOO_MANY_NEW_CONCEPTS.
    if oversized:
        add(
            ConformanceViolationCode.TOO_MANY_NEW_CONCEPTS,
            "step(s) introduce more than "
            f"{oracle.max_new_concepts_per_step} relation(s): " + "; ".join(oversized),
        )

    # BINV-003: required representation persists; BINV-005 companion: forbidden
    # (answer-revealing) representation absent from exercises.
    missing_representation: list[str] = []
    forbidden_representation: list[str] = []
    for step in asset.steps:
        representation = rep_of(step)
        rule = rules.get(concept_of(step.step_id))
        if representation is None or rule is None:
            continue
        visible = set(representation.visible_components)
        required = list(rule.all_steps)
        if step.step_id == f"{rule.concept_id}.intro":
            required.extend(rule.intro)
        if step.kind == StepKind.PROBE:
            required.extend(rule.probe_required)
        for component in dict.fromkeys(required):
            if component not in visible:
                missing_representation.append(f"{step.step_id}:{component}")
        if step.kind == StepKind.PROBE:
            for component in rule.probe_forbidden:
                if component in visible:
                    forbidden_representation.append(f"{step.step_id}:{component}")
    if missing_representation:
        add(
            ConformanceViolationCode.MISSING_REPRESENTATION,
            "missing required representation: " + ", ".join(sorted(missing_representation)),
        )
    if forbidden_representation:
        add(
            ConformanceViolationCode.FORBIDDEN_REPRESENTATION_PRESENT,
            "answer-revealing representation in exercise: "
            + ", ".join(sorted(forbidden_representation)),
        )

    # BINV-004: forbidden future concepts stay absent (components and text markers).
    disclosed: list[str] = []
    forbidden_ids = {item.concept_id for item in oracle.forbidden_concepts}
    for representation in asset.representations:
        for relation in _relations(representation):
            if relation in forbidden_ids:
                disclosed.append(f"{representation.representation_id}:{relation}")
        for concept in oracle.forbidden_concepts:
            for marker in concept.text_markers:
                if marker in representation.learner_visible_markdown:
                    disclosed.append(
                        f"{representation.representation_id}:{concept.concept_id}"
                        f" ({marker!r})"
                    )
    if disclosed:
        add(
            ConformanceViolationCode.FORBIDDEN_CONCEPT_DISCLOSED,
            "forbidden concept(s) disclosed: " + ", ".join(sorted(set(disclosed))),
        )

    # BINV-005: exercise text must not reveal the answer (literal or highlight glyph).
    leaks: list[str] = []
    for step in asset.steps:
        if step.kind != StepKind.PROBE:
            continue
        representation = rep_of(step)
        assessment = assessments.get(step.assessment_id or "")
        if representation is None or assessment is None:
            continue
        markdown = representation.learner_visible_markdown
        compact = re.sub(r"\s+", "", markdown)
        for literal in _answer_literals(assessment):
            if literal in markdown or re.sub(r"\s+", "", literal) in compact:
                leaks.append(f"{step.step_id}: answer literal {literal!r}")
        checked = _strip_structural_lines(markdown, oracle.structural_glyph_lines)
        for pattern in oracle.probe_forbidden_glyph_patterns:
            if re.search(pattern, checked):
                leaks.append(f"{step.step_id}: highlight glyph {pattern!r}")
    if leaks:
        add(
            ConformanceViolationCode.ANSWER_REVEAL_FORBIDDEN,
            "exercise reveals its answer: " + "; ".join(sorted(set(leaks))),
        )

    # Golden feedback rules (Study OS addition).
    feedback: list[str] = []
    for step in asset.steps:
        if step.kind != StepKind.PROBE:
            continue
        concept = concept_of(step.step_id)
        correct_target = steps.get(_route(step, LearnerOutcome.CORRECT) or "")
        wrong_target = steps.get(_route(step, LearnerOutcome.INCORRECT) or "")
        partial_route = _route(step, LearnerOutcome.PARTIAL)

        if correct_target is None or correct_target.kind != StepKind.EXPLAIN:
            feedback.append(f"{step.step_id}: correct answer is not followed by an explanation")
        else:
            why = rep_of(correct_target)
            if (
                concept_of(correct_target.step_id) != concept
                or why is None
                or not set(oracle.feedback_required).issubset(why.visible_components)
            ):
                feedback.append(f"{step.step_id}: correct answer lacks why on the same chart")

        if wrong_target is None or wrong_target.kind != StepKind.CORRECT:
            feedback.append(f"{step.step_id}: wrong answer is not followed by a correction")
        else:
            fix = rep_of(wrong_target)
            required = set(oracle.feedback_required).union(oracle.fix_required)
            if fix is None or not required.issubset(fix.visible_components):
                feedback.append(
                    f"{step.step_id}: correction lacks the answer on the chart or reassurance"
                )
            retry_id = (
                wrong_target.automatic_transition.next_step_id
                if wrong_target.automatic_transition is not None
                else None
            )
            retry = steps.get(retry_id or "")
            if retry is None or retry.kind != StepKind.PROBE or concept_of(retry.step_id) != concept:
                feedback.append(f"{step.step_id}: correction does not lead to a retry")
            else:
                if retry.representation_id == step.representation_id:
                    feedback.append(f"{step.step_id}: retry repeats the same example")
                after = steps.get(_route(retry, LearnerOutcome.CORRECT) or "")
                follow_id = (
                    after.automatic_transition.next_step_id
                    if after is not None and after.automatic_transition is not None
                    else None
                )
                follow = steps.get(follow_id or "")
                if (
                    follow is None
                    or follow.kind != StepKind.PROBE
                    or concept_of(follow.step_id) != concept
                ):
                    feedback.append(
                        f"{step.step_id}: no extra check after a correct retry before advancing"
                    )

        if partial_route is not None:
            partial = steps.get(partial_route)
            partial_rep = rep_of(partial) if partial is not None else None
            nxt = (
                steps.get(partial.automatic_transition.next_step_id or "")
                if partial is not None and partial.automatic_transition is not None
                else None
            )
            if (
                partial is None
                or partial.kind != StepKind.CORRECT
                or partial_rep is None
                or not set(oracle.partial_required).issubset(partial_rep.visible_components)
                or nxt is None
                or nxt.kind != StepKind.PROBE
                or concept_of(nxt.step_id) != concept
            ):
                feedback.append(
                    f"{step.step_id}: partial answer does not keep the correct part and "
                    "isolate the missing step"
                )
    if feedback:
        add(ConformanceViolationCode.FEEDBACK_DISCIPLINE, "; ".join(sorted(feedback)))

    # Mastery is never claimed (benchmarker forbidden concept ``mastery_claim``).
    claims: list[str] = []
    for representation in asset.representations:
        text = representation.learner_visible_markdown
        for phrase in oracle.mastery_allowed_phrases:
            text = text.replace(phrase, "")
        for pattern in oracle.mastery_patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                claims.append(f"{representation.representation_id}: {pattern!r}")
    exits = [
        (step.step_id, step.automatic_transition.exit_status)
        for step in asset.steps
        if step.automatic_transition is not None
        and step.automatic_transition.exit_status is not None
    ] + [
        (step.step_id, transition.exit_status)
        for step in asset.steps
        for transition in step.outcome_transitions
        if transition.exit_status is not None
    ]
    for step_id, status in exits:
        if status not in oracle.allowed_exit_statuses:
            claims.append(f"{step_id}: exits with {status}")
    if not exits:
        claims.append("asset has no exit, so the unproven-mastery end state is unreachable")
    if claims:
        add(ConformanceViolationCode.MASTERY_CLAIM, "; ".join(sorted(claims)))

    return ConformanceReport(
        evaluator_version=EVALUATOR_VERSION,
        benchmarker_commit=oracle.benchmarker_commit,
        canonical_problem_id=asset.canonical_problem_id,
        canonical_pir_revision=asset.canonical_pir_revision,
        passed=not violations,
        main_path_concepts=main_concepts,
        violations=tuple(violations),
    )
