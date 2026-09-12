from __future__ import annotations

import re

from .contracts import (
    AssessmentKind,
    AssessmentSpec,
    CanonicalTeachingAsset,
    ExpansionKind,
    ExpansionSpec,
    LearnerOutcome,
    PresentationContract,
    RepresentationSpec,
    ResponseKind,
    RunStatus,
    StepKind,
    TeachingStep,
    TransitionSpec,
    VariableBinding,
)
from .controller import validate_asset


SOURCE_PIR_COMMIT = "43599ff8ed75bd7ceeab980d078e3a2570c7725d"
CANONICAL_PROBLEM_ID = "sliding-window.max-sum-k.sep4.v1"
CANONICAL_PIR_REVISION = "sep4.sliding-window.production-known-problem.v1"
TWO_SUM_CANONICAL_PROBLEM_ID = "two-sum.dictionary.box.v1"
TWO_SUM_CANONICAL_PIR_REVISION = "sep4.two-sum.dictionary.production-known-problem.v1"


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
            "find the maximum sum of any contiguous window of size k",
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


def two_sum_asset() -> CanonicalTeachingAsset:
    """Return the reviewed, deterministic Two Sum teaching asset.

    The visible markdown is authored here as canonical output.  The model can
    route a learner request or submit a response, but it cannot substitute a
    different variable name or rewrite the backend turn.
    """

    contract = PresentationContract(
        required_variable_map=(
            VariableBinding(name="nums", role="input list of numbers"),
            VariableBinding(name="target", role="sum to find"),
            VariableBinding(name="box", role="number to earlier-index map"),
            VariableBinding(name="i", role="current index"),
            VariableBinding(name="num", role="nums[i]"),
            VariableBinding(name="needed", role="target - num"),
        ),
        forbidden_variable_names=("seen", "lookup", "index_by_num"),
        visual_required=True,
        visual_before_explanation=True,
        max_relations_per_turn=1,
        max_nonempty_lines=12,
        tiny_check_required=True,
        render_mode="verbatim",
    )

    def rep(
        representation_id: str,
        relation_id: str,
        markdown: str,
        *components: str,
        check_question: str,
    ) -> RepresentationSpec:
        return RepresentationSpec(
            representation_id=representation_id,
            learner_visible_markdown=markdown,
            visible_components=components,
            relation_id=relation_id,
            check_question=check_question,
        )

    visual_components = ("problem_anchor", "index_row", "nums_row", "box_row")
    reps = (
        rep(
            "r.two_sum.anchor",
            "goal",
            "```text\n"
            "index | 0 | 1 | 2 | 3\n"
            "nums  | 2 | 7 | 11 | 15\n"
            "target: 9\n"
            "```\n"
            "Goal: return the two indexes whose values add to `target`.\n"
            "Check: which indexes make 2 + 7 = 9?",
            *visual_components,
            check_question="which indexes make 2 + 7 = 9?",
        ),
        rep(
            "r.two_sum.anchor_probe",
            "goal",
            "```text\n"
            "index | 0 | 1 | 2 | 3\n"
            "nums  | 2 | 7 | 11 | 15\n"
            "target: 9\n"
            "```\n"
            "Return indexes, not values.\n"
            "Which answer is correct: `[2, 7]` or `[0, 1]`?",
            *visual_components,
            check_question="which answer is correct: [2, 7] or [0, 1]?",
        ),
        rep(
            "r.two_sum.anchor_repair",
            "goal",
            "```text\n"
            "index | 0 | 1 | 2 | 3\n"
            "nums  | 2 | 7 | 11 | 15\n"
            "target: 9\n"
            "```\n"
            "The answer names positions in `nums`, so use indexes.\n"
            "Which indexes hold 2 and 7?",
            *visual_components,
            check_question="which indexes hold 2 and 7?",
        ),
        rep(
            "r.two_sum.needed",
            "needed",
            "```text\n"
            "i = 0 | num = 2 | target = 9\n"
            "needed = ?\n"
            "```\n"
            "One relation: `needed = target - num`.\n"
            "What is `needed`?",
            *visual_components,
            check_question="what is needed when target is 9 and num is 2?",
        ),
        rep(
            "r.two_sum.needed_repair",
            "needed",
            "```text\n"
            "target = 9 | num = 2\n"
            "needed = target - num = 9 - 2 = ?\n"
            "```\n"
            "Keep the subtraction order: target first.\n"
            "What number completes `2 + needed = 9`?",
            *visual_components,
            check_question="what number completes 2 + needed = 9?",
        ),
        rep(
            "r.two_sum.box",
            "box_role",
            "```text\n"
            "box = {2: 0}\n"
            "left  = number | right = index\n"
            "```\n"
            "One relation: `box` stores an earlier number with its index.\n"
            "If `needed = 2`, what value is in `box[needed]`?",
            *visual_components,
            check_question="if needed is 2, what value is in box[needed]?",
        ),
        rep(
            "r.two_sum.box_repair",
            "box_role",
            "```text\n"
            "box = {2: 0}\n"
            "box[needed] = box[2] = ?\n"
            "```\n"
            "The value on the right is the earlier index.\n"
            "What index does `box[2]` give?",
            *visual_components,
            check_question="what index does box[2] give?",
        ),
        rep(
            "r.two_sum.order",
            "check_then_add",
            "```text\n"
            "current: i | num | needed\n"
            "box: earlier numbers only\n"
            "```\n"
            "One relation: check `box` before adding the current `num`.\n"
            "Which comes first: check or add?",
            *visual_components,
            check_question="which comes first: check or add?",
        ),
        rep(
            "r.two_sum.order_repair",
            "check_then_add",
            "```text\n"
            "check box -> if absent -> box[num] = i\n"
            "```\n"
            "Checking first prevents pairing the current index with itself.\n"
            "Say the order in two words.",
            *visual_components,
            check_question="what is the two-word order?",
        ),
        rep(
            "r.two_sum.loop",
            "return_pair",
            "```text\n"
            "i, num = current index, current value\n"
            "needed = target - num\n"
            "pair = [box[needed], i]\n"
            "```\n"
            "One relation: `box[needed]` is old index and `i` is current index.\n"
            "What pair is returned?",
            *visual_components,
            check_question="what pair is returned when box[needed] is 0 and i is 1?",
        ),
        rep(
            "r.two_sum.loop_repair",
            "return_pair",
            "```text\n"
            "old index = box[needed]\n"
            "current index = i\n"
            "return = [old index, current index]\n"
            "```\n"
            "Keep both indexes; do not return the values.\n"
            "Write the return expression.",
            *visual_components,
            check_question="what expression returns both indexes?",
        ),
        rep(
            "r.two_sum.final",
            "assembled_algorithm",
            "```python\n"
            "for i, num in enumerate(nums):\n"
            "    needed = target - num\n"
            "    if needed in box:\n"
            "        return [box[needed], i]\n"
            "    box[num] = i\n"
            "```\n"
            "The reviewed path uses `nums`, `target`, `box`, `i`, `num`, and `needed`.\n"
            "Check: where is the earlier index returned from?",
            *visual_components,
            check_question="where is the earlier index returned from?",
        ),
        rep(
            "r.two_sum.needed_why",
            "needed",
            "```text\n"
            "num + needed = target\n"
            "needed = target - num\n"
            "```\n"
            "The subtraction isolates the partner value.\n"
            "Why subtract `num` from `target`?",
            *visual_components,
            check_question="why subtract num from target?",
        ),
        rep(
            "r.two_sum.box_why",
            "box_role",
            "```text\n"
            "box: number -> earlier index\n"
            "{2: 0} -> number 2 was at index 0\n"
            "```\n"
            "The map lets one check find the earlier index.\n"
            "What does the right side store?",
            *visual_components,
            check_question="what does the right side of box store?",
        ),
    )

    def route(outcome: LearnerOutcome, next_step_id: str) -> TransitionSpec:
        return TransitionSpec(outcome=outcome, next_step_id=next_step_id)

    asset = CanonicalTeachingAsset(
        schema_version="study-os.canonical-teaching-asset.v0",
        canonical_problem_id=TWO_SUM_CANONICAL_PROBLEM_ID,
        canonical_pir_revision=TWO_SUM_CANONICAL_PIR_REVISION,
        source_pir_repository="Pukujan/study-os",
        source_pir_commit="151c819e3457ae41fa1810b5060d0101f91bc12a",
        controller_revision="study-os.pir-controller.v0",
        renderer_revision="study-os.markdown-renderer.v0",
        assessment_revision="study-os.pir-assessment.v0",
        entry_step_id="two_sum_anchor",
        aliases=(
            "two sum",
            "given nums and target, return indices of two numbers whose sum is target",
            "given nums and target return indices of two numbers whose sum is target",
            "find two numbers in nums that add to target",
        ),
        representations=reps,
        assessments=(
            AssessmentSpec(
                assessment_id="a.two_sum_goal",
                kind=AssessmentKind.INTEGER_SEQUENCE,
                expected_values=(0, 1),
                partial_values=(2, 7),
            ),
            AssessmentSpec(
                assessment_id="a.two_sum_needed",
                kind=AssessmentKind.INTEGER,
                expected_values=(7,),
            ),
            AssessmentSpec(
                assessment_id="a.two_sum_box",
                kind=AssessmentKind.INTEGER,
                expected_values=(0,),
            ),
            AssessmentSpec(
                assessment_id="a.two_sum_order",
                kind=AssessmentKind.TEXT,
                expected_text=("check first then add", "check before add"),
            ),
            AssessmentSpec(
                assessment_id="a.two_sum_loop",
                kind=AssessmentKind.TEXT,
                expected_text=("return [box[needed], i]",),
            ),
        ),
        steps=(
            TeachingStep(
                step_id="two_sum_anchor",
                kind=StepKind.EXPLAIN,
                representation_id="r.two_sum.anchor",
                required_components=visual_components,
                automatic_transition=TransitionSpec(next_step_id="two_sum_goal_probe"),
            ),
            TeachingStep(
                step_id="two_sum_goal_probe",
                kind=StepKind.PROBE,
                representation_id="r.two_sum.anchor_probe",
                required_components=visual_components,
                response_kind=ResponseKind.INTEGER_SEQUENCE,
                assessment_id="a.two_sum_goal",
                outcome_transitions=(
                    route(LearnerOutcome.CORRECT, "two_sum_needed_bridge"),
                    route(LearnerOutcome.PARTIAL, "two_sum_anchor_repair"),
                    route(LearnerOutcome.INCORRECT, "two_sum_anchor_repair"),
                ),
            ),
            TeachingStep(
                step_id="two_sum_anchor_repair",
                kind=StepKind.CORRECT,
                representation_id="r.two_sum.anchor_repair",
                required_components=visual_components,
                automatic_transition=TransitionSpec(next_step_id="two_sum_goal_probe"),
            ),
            TeachingStep(
                step_id="two_sum_needed_bridge",
                kind=StepKind.EXPLAIN,
                representation_id="r.two_sum.needed",
                required_components=visual_components,
                automatic_transition=TransitionSpec(next_step_id="two_sum_needed_probe"),
            ),
            TeachingStep(
                step_id="two_sum_needed_probe",
                kind=StepKind.PROBE,
                representation_id="r.two_sum.needed",
                required_components=visual_components,
                response_kind=ResponseKind.INTEGER,
                assessment_id="a.two_sum_needed",
                outcome_transitions=(
                    route(LearnerOutcome.CORRECT, "two_sum_box_bridge"),
                    route(LearnerOutcome.INCORRECT, "two_sum_needed_repair"),
                ),
            ),
            TeachingStep(
                step_id="two_sum_needed_repair",
                kind=StepKind.CORRECT,
                representation_id="r.two_sum.needed_repair",
                required_components=visual_components,
                automatic_transition=TransitionSpec(next_step_id="two_sum_needed_probe"),
            ),
            TeachingStep(
                step_id="two_sum_box_bridge",
                kind=StepKind.EXPLAIN,
                representation_id="r.two_sum.box",
                required_components=visual_components,
                automatic_transition=TransitionSpec(next_step_id="two_sum_box_probe"),
            ),
            TeachingStep(
                step_id="two_sum_box_probe",
                kind=StepKind.PROBE,
                representation_id="r.two_sum.box",
                required_components=visual_components,
                response_kind=ResponseKind.INTEGER,
                assessment_id="a.two_sum_box",
                outcome_transitions=(
                    route(LearnerOutcome.CORRECT, "two_sum_order_bridge"),
                    route(LearnerOutcome.INCORRECT, "two_sum_box_repair"),
                ),
            ),
            TeachingStep(
                step_id="two_sum_box_repair",
                kind=StepKind.CORRECT,
                representation_id="r.two_sum.box_repair",
                required_components=visual_components,
                automatic_transition=TransitionSpec(next_step_id="two_sum_box_probe"),
            ),
            TeachingStep(
                step_id="two_sum_order_bridge",
                kind=StepKind.EXPLAIN,
                representation_id="r.two_sum.order",
                required_components=visual_components,
                automatic_transition=TransitionSpec(next_step_id="two_sum_order_probe"),
            ),
            TeachingStep(
                step_id="two_sum_order_probe",
                kind=StepKind.PROBE,
                representation_id="r.two_sum.order",
                required_components=visual_components,
                response_kind=ResponseKind.TEXT,
                assessment_id="a.two_sum_order",
                outcome_transitions=(
                    route(LearnerOutcome.CORRECT, "two_sum_loop_bridge"),
                    route(LearnerOutcome.INCORRECT, "two_sum_order_repair"),
                ),
            ),
            TeachingStep(
                step_id="two_sum_order_repair",
                kind=StepKind.CORRECT,
                representation_id="r.two_sum.order_repair",
                required_components=visual_components,
                automatic_transition=TransitionSpec(next_step_id="two_sum_order_probe"),
            ),
            TeachingStep(
                step_id="two_sum_loop_bridge",
                kind=StepKind.EXPLAIN,
                representation_id="r.two_sum.loop",
                required_components=visual_components,
                automatic_transition=TransitionSpec(next_step_id="two_sum_loop_probe"),
            ),
            TeachingStep(
                step_id="two_sum_loop_probe",
                kind=StepKind.PROBE,
                representation_id="r.two_sum.loop",
                required_components=visual_components,
                response_kind=ResponseKind.TEXT,
                assessment_id="a.two_sum_loop",
                outcome_transitions=(
                    route(LearnerOutcome.CORRECT, "two_sum_final"),
                    route(LearnerOutcome.INCORRECT, "two_sum_loop_repair"),
                ),
            ),
            TeachingStep(
                step_id="two_sum_loop_repair",
                kind=StepKind.CORRECT,
                representation_id="r.two_sum.loop_repair",
                required_components=visual_components,
                automatic_transition=TransitionSpec(next_step_id="two_sum_loop_probe"),
            ),
            TeachingStep(
                step_id="two_sum_final",
                kind=StepKind.ASSEMBLE,
                representation_id="r.two_sum.final",
                required_components=visual_components,
                automatic_transition=TransitionSpec(
                    exit_status=RunStatus.ASSEMBLED_MASTERY_UNPROVEN
                ),
            ),
        ),
        expansions=(
            ExpansionSpec(
                step_id="two_sum_needed_probe",
                kind=ExpansionKind.WHY,
                representation_id="r.two_sum.needed_why",
            ),
            ExpansionSpec(
                step_id="two_sum_box_probe",
                kind=ExpansionKind.WHY,
                representation_id="r.two_sum.box_why",
            ),
        ),
        presentation_contract=contract,
    )
    violations = validate_asset(asset)
    if violations:
        codes = ", ".join(item.code.value for item in violations)
        raise RuntimeError(f"built-in Two Sum PIR asset is invalid: {codes}")
    return asset


_ASSETS = {
    CANONICAL_PROBLEM_ID: sliding_window_asset(),
    TWO_SUM_CANONICAL_PROBLEM_ID: two_sum_asset(),
}


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
    for asset in _ASSETS.values():
        aliases = {_normalize_problem_text(alias) for alias in asset.aliases}
        if normalized in aliases:
            return asset
    return None
