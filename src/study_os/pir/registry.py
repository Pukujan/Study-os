from __future__ import annotations

import re

from .contracts import (
    AssessmentKind,
    AssessmentSpec,
    CanonicalTeachingAsset,
    ExpansionKind,
    ExpansionSpec,
    LearnerOutcome,
    RepresentationSpec,
    ResponseKind,
    RunStatus,
    StepKind,
    TeachingStep,
    TransitionSpec,
)
from .controller import validate_asset


SOURCE_PIR_COMMIT = "43599ff8ed75bd7ceeab980d078e3a2570c7725d"
CANONICAL_PROBLEM_ID = "sliding-window.max-sum-k.sep4.v1"
CANONICAL_PIR_REVISION = "sep4.sliding-window.production-known-problem.v1"


def _representation(
    representation_id: str,
    markdown: str,
    *components: str,
) -> RepresentationSpec:
    return RepresentationSpec(
        representation_id=representation_id,
        learner_visible_markdown=markdown,
        visible_components=components,
    )


def _outcome(
    outcome: LearnerOutcome,
    next_step_id: str,
) -> TransitionSpec:
    return TransitionSpec(outcome=outcome, next_step_id=next_step_id)


def sliding_window_asset() -> CanonicalTeachingAsset:
    anchor_components = (
        "problem_anchor",
        "index_row",
        "numbers_row",
        "i_label",
        "k_label",
        "box_label",
    )
    recurrence_components = (*anchor_components, "sum_i_label", "recurrence")
    code_components = ("problem_anchor", "code", "variable_roles")

    asset = CanonicalTeachingAsset(
        schema_version="study-os.canonical-teaching-asset.v0",
        canonical_problem_id=CANONICAL_PROBLEM_ID,
        canonical_pir_revision=CANONICAL_PIR_REVISION,
        source_pir_repository="Pukujan/study-os-pedagogical-IR",
        source_pir_commit=SOURCE_PIR_COMMIT,
        controller_revision="study-os.pir-controller.v0",
        renderer_revision="study-os.markdown-renderer.v0",
        assessment_revision="study-os.pir-assessment.v0",
        entry_step_id="problem_anchor",
        aliases=(
            "given an array a and integer k find the maximum sum of any contiguous window of size k",
            "find the maximum sum of a contiguous subarray of size k",
            "maximum sum contiguous window size k",
            "sliding window maximum sum size k",
        ),
        representations=(
            _representation(
                "r.problem_anchor",
                "We will keep one concrete array visible while building the method.\n\n"
                "`index:  0  1  2  3  4  5`\n\n"
                "`value:  4  7  2  6  1  9`\n\n"
                "For the next check, `i = 2` and `k = 2`. The box therefore starts at "
                "index 2 and covers two values.",
                *anchor_components,
            ),
            _representation(
                "r.sum_probe",
                "`index:  0  1 [2]  3  4  5`\n\n"
                "`value:  4  7 [2] [6]  1  9`\n\n"
                "Here `i = 2`, `k = 2`. What is `sum[i]` for this box?",
                *anchor_components,
                "sum_i_label",
            ),
            _representation(
                "r.sum_partial",
                "`index:  0  1 [2]  3  4  5`\n\n"
                "`value:  4  7 [2] [6]  1  9`\n\n"
                "Those are the right values: `2` and `6`. Keep the same box and finish only "
                "the arithmetic for `sum[i]`.",
                *anchor_components,
                "sum_i_label",
            ),
            _representation(
                "r.sum_wrong",
                "`index:  0  1 [2]  3  4  5`\n\n"
                "`value:  4  7 [2] [6]  1  9`\n\n"
                "Keep `i = 2` and `k = 2` unchanged. Recheck which two values are inside the "
                "box, then compute their sum.",
                *anchor_components,
                "sum_i_label",
            ),
            _representation(
                "r.sum_why",
                "`i` tells us where the box starts. `k` tells us how many values it contains. "
                "So `sum[i]` means the sum of the values in the box that starts at `i`.",
                *anchor_components,
                "sum_i_label",
            ),
            _representation(
                "r.sum_easier",
                "Smaller example: `value: [3] [5] 9`, with `i = 0`, `k = 2`. The box is the "
                "first two values. Apply that same box-to-sum relation to the original array.",
                *anchor_components,
                "sum_i_label",
            ),
            _representation(
                "r.recurrence_bridge",
                "Now move the box one place to the right. Instead of adding every value again, "
                "start from the previous sum: remove the value that left the box and add the new "
                "value that entered. Let `j = k - 1` so the entering index is `i + j`.",
                *recurrence_components,
            ),
            _representation(
                "r.recurrence_probe",
                "Keep the roles fixed: old sum, outgoing value, incoming value. Write the update "
                "for `S[i]` using `S[i-1]`, `a[i-1]`, and `a[i+j]`.",
                *recurrence_components,
            ),
            _representation(
                "r.recurrence_repair",
                "Do not recompute the whole box. Preserve the previous sum, subtract the value at "
                "the old left edge `a[i-1]`, then add the new right-edge value `a[i+j]`.",
                *recurrence_components,
            ),
            _representation(
                "r.recurrence_why",
                "When the box moves right by one position, all middle values stay inside. Only two "
                "things change: one value leaves on the left and one value enters on the right.",
                *recurrence_components,
            ),
            _representation(
                "r.enumerate_bridge",
                "The recurrence repeats while `i` changes by one. In Python, `enumerate(a)` gives "
                "the current index `i` together with the current value `num`.",
                *code_components,
            ),
            _representation(
                "r.enumerate_probe",
                "Write only the Python loop header that gives both `i` and `num` while iterating "
                "over `a`.",
                *code_components,
            ),
            _representation(
                "r.enumerate_repair",
                "We need both the index and the value. Use Python's `enumerate` over `a`; do not "
                "replace the positional role of `i` with the array value.",
                *code_components,
            ),
            _representation(
                "r.append_bridge",
                "Each new window sum belongs at position `i` in `S`. After the first sum exists, "
                "the next sum can be appended using the recurrence directly.",
                *code_components,
            ),
            _representation(
                "r.append_probe",
                "Write only the append statement for the recurrence using `S[i-1]`, `a[i-1]`, "
                "and `a[i+j]`.",
                *code_components,
            ),
            _representation(
                "r.append_repair",
                "Keep the same recurrence and put its result into `S` with `append(...)`. Do not "
                "introduce a second formula.",
                *code_components,
            ),
            _representation(
                "r.max_bridge",
                "The loop also tracks the largest sum seen so far. The first complete window "
                "initializes `max_sum`; later windows only replace it when `S[i]` is larger.",
                *code_components,
            ),
            _representation(
                "r.max_probe",
                "Write the two-line condition that updates `max_sum` only when the current `S[i]` "
                "is larger.",
                *code_components,
            ),
            _representation(
                "r.max_repair",
                "Compare the current window sum `S[i]` with the stored `max_sum`. Only assign a new "
                "maximum inside that condition.",
                *code_components,
            ),
            _representation(
                "r.first_window",
                "The recurrence needs a previous sum, so `i == 0` is the base case. Build the first "
                "window by summing `k` values, then set `max_sum = S[i]`.",
                *code_components,
            ),
            _representation(
                "r.boundary",
                "A size-`k` window cannot start after `len(a) - k`. The loop therefore stops when "
                "`i > len(a) - k`, before constructing an incomplete box.",
                *code_components,
            ),
            _representation(
                "r.final_loop",
                "The reviewed pieces now assemble into the full loop:\n\n"
                "```python\n"
                "a = [2, 6, 4, 1, 8]\n\n"
                "k = 3\n"
                "j = k - 1\n"
                "S = []\n\n"
                "for i, num in enumerate(a):\n"
                "    if i > len(a) - k:\n"
                "        break\n\n"
                "    if i == 0:\n"
                "        S.append(0)\n"
                "        for x in range(k):\n"
                "            S[i] = S[i] + a[i+x]\n"
                "        max_sum = S[i]\n"
                "    else:\n"
                "        S.append(S[i-1] - a[i-1] + a[i+j])\n"
                "        if S[i] > max_sum:\n"
                "            max_sum = S[i]\n"
                "```\n\n"
                "This is assembled exposure from the reviewed path. Independent mastery is not "
                "established by seeing the final code.",
                *code_components,
            ),
        ),
        assessments=(
            AssessmentSpec(
                assessment_id="a.sum",
                kind=AssessmentKind.INTEGER,
                expected_values=(8,),
                partial_values=(2, 6),
            ),
            AssessmentSpec(
                assessment_id="a.arithmetic",
                kind=AssessmentKind.INTEGER,
                expected_values=(8,),
            ),
            AssessmentSpec(
                assessment_id="a.recurrence",
                kind=AssessmentKind.TEXT,
                expected_text=("S[i]=S[i-1]-a[i-1]+a[i+j]",),
            ),
            AssessmentSpec(
                assessment_id="a.enumerate",
                kind=AssessmentKind.TEXT,
                expected_text=("for i,num in enumerate(a):",),
            ),
            AssessmentSpec(
                assessment_id="a.append",
                kind=AssessmentKind.TEXT,
                expected_text=("S.append(S[i-1]-a[i-1]+a[i+j])",),
            ),
            AssessmentSpec(
                assessment_id="a.max",
                kind=AssessmentKind.TEXT,
                expected_text=(
                    "if S[i]>max_sum:max_sum=S[i]",
                    "if S[i] > max_sum:\n    max_sum = S[i]",
                ),
            ),
        ),
        steps=(
            TeachingStep(
                step_id="problem_anchor",
                kind=StepKind.EXPLAIN,
                representation_id="r.problem_anchor",
                required_components=anchor_components,
                automatic_transition=TransitionSpec(next_step_id="sum_probe"),
            ),
            TeachingStep(
                step_id="sum_probe",
                kind=StepKind.PROBE,
                representation_id="r.sum_probe",
                required_components=(*anchor_components, "sum_i_label"),
                response_kind=ResponseKind.INTEGER,
                assessment_id="a.sum",
                outcome_transitions=(
                    _outcome(LearnerOutcome.CORRECT, "recurrence_bridge"),
                    _outcome(LearnerOutcome.PARTIAL, "sum_partial"),
                    _outcome(LearnerOutcome.INCORRECT, "sum_wrong"),
                ),
            ),
            TeachingStep(
                step_id="sum_partial",
                kind=StepKind.CORRECT,
                representation_id="r.sum_partial",
                required_components=(*anchor_components, "sum_i_label"),
                automatic_transition=TransitionSpec(next_step_id="arithmetic_probe"),
            ),
            TeachingStep(
                step_id="arithmetic_probe",
                kind=StepKind.PROBE,
                representation_id="r.sum_probe",
                required_components=(*anchor_components, "sum_i_label"),
                response_kind=ResponseKind.INTEGER,
                assessment_id="a.arithmetic",
                outcome_transitions=(
                    _outcome(LearnerOutcome.CORRECT, "recurrence_bridge"),
                    _outcome(LearnerOutcome.INCORRECT, "sum_partial"),
                ),
            ),
            TeachingStep(
                step_id="sum_wrong",
                kind=StepKind.CORRECT,
                representation_id="r.sum_wrong",
                required_components=(*anchor_components, "sum_i_label"),
                automatic_transition=TransitionSpec(next_step_id="sum_probe"),
            ),
            TeachingStep(
                step_id="recurrence_bridge",
                kind=StepKind.EXPLAIN,
                representation_id="r.recurrence_bridge",
                required_components=recurrence_components,
                automatic_transition=TransitionSpec(next_step_id="recurrence_probe"),
            ),
            TeachingStep(
                step_id="recurrence_probe",
                kind=StepKind.PROBE,
                representation_id="r.recurrence_probe",
                required_components=recurrence_components,
                response_kind=ResponseKind.TEXT,
                assessment_id="a.recurrence",
                outcome_transitions=(
                    _outcome(LearnerOutcome.CORRECT, "enumerate_bridge"),
                    _outcome(LearnerOutcome.INCORRECT, "recurrence_repair"),
                ),
            ),
            TeachingStep(
                step_id="recurrence_repair",
                kind=StepKind.CORRECT,
                representation_id="r.recurrence_repair",
                required_components=recurrence_components,
                automatic_transition=TransitionSpec(next_step_id="recurrence_probe"),
            ),
            TeachingStep(
                step_id="enumerate_bridge",
                kind=StepKind.EXPLAIN,
                representation_id="r.enumerate_bridge",
                required_components=code_components,
                automatic_transition=TransitionSpec(next_step_id="enumerate_probe"),
            ),
            TeachingStep(
                step_id="enumerate_probe",
                kind=StepKind.PROBE,
                representation_id="r.enumerate_probe",
                required_components=code_components,
                response_kind=ResponseKind.CODE,
                assessment_id="a.enumerate",
                outcome_transitions=(
                    _outcome(LearnerOutcome.CORRECT, "append_bridge"),
                    _outcome(LearnerOutcome.INCORRECT, "enumerate_repair"),
                ),
            ),
            TeachingStep(
                step_id="enumerate_repair",
                kind=StepKind.CORRECT,
                representation_id="r.enumerate_repair",
                required_components=code_components,
                automatic_transition=TransitionSpec(next_step_id="enumerate_probe"),
            ),
            TeachingStep(
                step_id="append_bridge",
                kind=StepKind.EXPLAIN,
                representation_id="r.append_bridge",
                required_components=code_components,
                automatic_transition=TransitionSpec(next_step_id="append_probe"),
            ),
            TeachingStep(
                step_id="append_probe",
                kind=StepKind.PROBE,
                representation_id="r.append_probe",
                required_components=code_components,
                response_kind=ResponseKind.CODE,
                assessment_id="a.append",
                outcome_transitions=(
                    _outcome(LearnerOutcome.CORRECT, "max_bridge"),
                    _outcome(LearnerOutcome.INCORRECT, "append_repair"),
                ),
            ),
            TeachingStep(
                step_id="append_repair",
                kind=StepKind.CORRECT,
                representation_id="r.append_repair",
                required_components=code_components,
                automatic_transition=TransitionSpec(next_step_id="append_probe"),
            ),
            TeachingStep(
                step_id="max_bridge",
                kind=StepKind.EXPLAIN,
                representation_id="r.max_bridge",
                required_components=code_components,
                automatic_transition=TransitionSpec(next_step_id="max_probe"),
            ),
            TeachingStep(
                step_id="max_probe",
                kind=StepKind.PROBE,
                representation_id="r.max_probe",
                required_components=code_components,
                response_kind=ResponseKind.CODE,
                assessment_id="a.max",
                outcome_transitions=(
                    _outcome(LearnerOutcome.CORRECT, "first_window"),
                    _outcome(LearnerOutcome.INCORRECT, "max_repair"),
                ),
            ),
            TeachingStep(
                step_id="max_repair",
                kind=StepKind.CORRECT,
                representation_id="r.max_repair",
                required_components=code_components,
                automatic_transition=TransitionSpec(next_step_id="max_probe"),
            ),
            TeachingStep(
                step_id="first_window",
                kind=StepKind.EXPLAIN,
                representation_id="r.first_window",
                required_components=code_components,
                automatic_transition=TransitionSpec(next_step_id="boundary"),
            ),
            TeachingStep(
                step_id="boundary",
                kind=StepKind.EXPLAIN,
                representation_id="r.boundary",
                required_components=code_components,
                automatic_transition=TransitionSpec(next_step_id="final_loop"),
            ),
            TeachingStep(
                step_id="final_loop",
                kind=StepKind.ASSEMBLE,
                representation_id="r.final_loop",
                required_components=code_components,
                automatic_transition=TransitionSpec(
                    exit_status=RunStatus.ASSEMBLED_MASTERY_UNPROVEN
                ),
            ),
        ),
        expansions=(
            ExpansionSpec(
                step_id="sum_probe",
                kind=ExpansionKind.WHY,
                representation_id="r.sum_why",
            ),
            ExpansionSpec(
                step_id="sum_probe",
                kind=ExpansionKind.EASIER_EXAMPLE,
                representation_id="r.sum_easier",
            ),
            ExpansionSpec(
                step_id="recurrence_probe",
                kind=ExpansionKind.WHY,
                representation_id="r.recurrence_why",
            ),
        ),
    )
    violations = validate_asset(asset)
    if violations:
        codes = ", ".join(item.code.value for item in violations)
        raise RuntimeError(f"built-in canonical PIR asset is invalid: {codes}")
    return asset


_ASSETS = {CANONICAL_PROBLEM_ID: sliding_window_asset()}


def get_asset(canonical_problem_id: str) -> CanonicalTeachingAsset | None:
    return _ASSETS.get(canonical_problem_id)


def _normalize_problem_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower()).rstrip(".?!")


def resolve_known_problem(problem_text: str, domain: str) -> CanonicalTeachingAsset | None:
    if not isinstance(problem_text, str) or not problem_text.strip():
        raise ValueError("problem_text must be a non-empty string")
    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("domain must be a non-empty string")
    if domain.strip().lower() not in {"dsa", "data structures and algorithms"}:
        return None

    normalized = _normalize_problem_text(problem_text)
    asset = _ASSETS[CANONICAL_PROBLEM_ID]
    aliases = {_normalize_problem_text(alias) for alias in asset.aliases}
    return asset if normalized in aliases else None
