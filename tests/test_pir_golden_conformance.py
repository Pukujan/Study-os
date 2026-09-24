"""SOS-0002: the shipped sliding-window lesson follows the two goldens step by step.

Each negative test applies one benchmarker-style mutation to the shipped asset and
requires the conformance evaluator to report the matching violation code. The
rules mirror Pukujan/study-os-benchmarker at the commit pinned in the oracle.
"""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch

from study_os.pir import sliding_window
from study_os.pir.conformance import (
    BENCHMARKER_COMMIT,
    ConformanceViolationCode as Code,
    GoldenOracle,
    evaluate_asset,
    main_path,
)
from study_os.pir.contracts import (
    CanonicalTeachingAsset,
    LearnerOutcome,
    RunStatus,
    StepKind,
    TransitionSpec,
)
from study_os.pir.controller import start_run, submit_response
from study_os.pir.registry import CANONICAL_PROBLEM_ID, get_asset

ROOT = Path(__file__).resolve().parents[1]
ORACLE_PATH = ROOT / "domains/dsa/sliding-window/golden/conformance-oracle.v0.1.json"

GOLDEN_ORDER = (
    "problem",
    "position",
    "index",
    "box_size_k",
    "box_start_i",
    "window_sum",
    "successive_sums",
    "recurrence_repetition",
    "enumerate",
    "append",
)

# The all-correct path, one line per golden step. Wrong and partial answers add
# correction, retry, and verification steps around these.
EXPECTED_MAIN_PATH = (
    "problem.intro",
    "position.intro", "position.e0.n2", "position.e0.n2.why",
    "position.e1.n1", "position.e1.n1.why",
    "index.intro", "index.e0.n2", "index.e0.n2.why", "index.e1.n1", "index.e1.n1.why",
    "box_size_k.intro", "box_size_k.e0.n2", "box_size_k.e0.n2.why",
    "box_size_k.e1.n1", "box_size_k.e1.n1.why",
    "box_start_i.intro", "box_start_i.e0.n2", "box_start_i.e0.n2.why",
    "box_start_i.e1.n1", "box_start_i.e1.n1.why",
    "window_sum.intro", "window_sum.e0.n2", "window_sum.e0.n2.why",
    "window_sum.e1.n1", "window_sum.e1.n1.why",
    "successive_sums.intro", "successive_sums.e0.n3", "successive_sums.e0.n3.why",
    "successive_sums.e1.n2", "successive_sums.e1.n2.why",
    "successive_sums.e2.n1", "successive_sums.e2.n1.why",
    "recurrence_repetition.intro", "recurrence_repetition.e0.n2",
    "recurrence_repetition.e0.n2.why", "recurrence_repetition.e1.n1",
    "recurrence_repetition.e1.n1.why",
    "enumerate.intro", "enumerate.e0.n2", "enumerate.e0.n2.why",
    "enumerate.e1.n1", "enumerate.e1.n1.why",
    "append.intro", "append.e0.n2", "append.e0.n2.why", "append.e1.n1", "append.e1.n1.why",
    "frontier.assembled",
)  # fmt: skip


def load_oracle() -> GoldenOracle:
    return GoldenOracle.model_validate_json(ORACLE_PATH.read_text(encoding="utf-8"))


def shipped() -> CanonicalTeachingAsset:
    asset = get_asset(CANONICAL_PROBLEM_ID)
    assert asset is not None
    return asset


def replace_rep(asset: CanonicalTeachingAsset, rep_id: str, **update: object):
    found = False
    reps = []
    for rep in asset.representations:
        if rep.representation_id == rep_id:
            reps.append(rep.model_copy(update=update))
            found = True
        else:
            reps.append(rep)
    assert found, rep_id
    return asset.model_copy(update={"representations": tuple(reps)})


def rep(asset: CanonicalTeachingAsset, rep_id: str):
    return next(item for item in asset.representations if item.representation_id == rep_id)


def step(asset: CanonicalTeachingAsset, step_id: str):
    return next(item for item in asset.steps if item.step_id == step_id)


def replace_step(asset: CanonicalTeachingAsset, step_id: str, **update: object):
    steps = tuple(
        item.model_copy(update=update) if item.step_id == step_id else item
        for item in asset.steps
    )
    return asset.model_copy(update={"steps": steps})


def rebuilt(concepts) -> CanonicalTeachingAsset:
    with patch.object(sliding_window, "GOLDEN_CONCEPTS", concepts):
        entry, reps, assessments, steps, expansions = sliding_window.build_sliding_window_graph()
    return shipped().model_copy(
        update={
            "entry_step_id": entry,
            "representations": reps,
            "assessments": assessments,
            "steps": steps,
            "expansions": expansions,
        }
    )


def correct_response(asset: CanonicalTeachingAsset, step_id: str) -> str:
    spec = next(
        item for item in asset.assessments if item.assessment_id == step(asset, step_id).assessment_id
    )
    if spec.expected_text:
        return spec.expected_text[0]
    return " ".join(str(value) for value in spec.expected_values)


class GoldenConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.oracle = load_oracle()
        self.asset = shipped()

    def codes(self, asset: CanonicalTeachingAsset) -> set[Code]:
        return {violation.code for violation in evaluate_asset(self.oracle, asset).violations}

    def detail(self, asset: CanonicalTeachingAsset, code: Code) -> str:
        report = evaluate_asset(self.oracle, asset)
        return next(item.detail for item in report.violations if item.code == code)

    # -- positive ---------------------------------------------------------------

    def test_shipped_lesson_conforms_to_both_goldens(self) -> None:
        report = evaluate_asset(self.oracle, self.asset)
        self.assertEqual(report.violations, ())
        self.assertTrue(report.passed)
        self.assertEqual(report.main_path_concepts, GOLDEN_ORDER)
        self.assertEqual(
            tuple(bridge.concept_id for bridge in self.oracle.required_bridges), GOLDEN_ORDER
        )

    def test_main_path_is_the_reviewed_step_list(self) -> None:
        self.assertEqual(tuple(item.step_id for item in main_path(self.asset)), EXPECTED_MAIN_PATH)

    def test_oracle_pins_goldens_and_benchmarker(self) -> None:
        self.assertEqual(self.oracle.benchmarker_commit, BENCHMARKER_COMMIT)
        self.assertEqual(self.oracle.canonical_problem_id, CANONICAL_PROBLEM_ID)
        for source in self.oracle.golden_sources:
            digest = hashlib.sha256((ROOT / source.path).read_bytes()).hexdigest()
            self.assertEqual(digest, source.sha256, f"{source.path} changed; re-review the oracle")

    def test_builder_probe_rules_match_the_oracle(self) -> None:
        for rule in self.oracle.representation_rules:
            if rule.probe_forbidden:
                self.assertEqual(
                    set(sliding_window.PROBE_FORBIDDEN[rule.concept_id]),
                    set(rule.probe_forbidden),
                    rule.concept_id,
                )

    def test_report_is_deterministic(self) -> None:
        mutated = replace_rep(
            self.asset,
            "r.frontier.assembled",
            learner_visible_markdown="You have mastered it. max_sum = S[i]",
        )
        first = evaluate_asset(self.oracle, mutated).model_dump_json()
        second = evaluate_asset(self.oracle, mutated).model_dump_json()
        self.assertEqual(first, second)
        codes = [item.code for item in evaluate_asset(self.oracle, mutated).violations]
        self.assertEqual(codes, [Code.FORBIDDEN_CONCEPT_DISCLOSED, Code.MASTERY_CLAIM])

    # -- BINV-002: missing golden step --------------------------------------------

    def test_missing_golden_step_is_rejected(self) -> None:
        without_index = tuple(
            factory for factory in sliding_window.GOLDEN_CONCEPTS if factory.__name__ != "_index"
        )
        mutated = rebuilt(without_index)
        self.assertIn(Code.MISSING_REQUIRED_BRIDGE, self.codes(mutated))
        self.assertIn("index", self.detail(mutated, Code.MISSING_REQUIRED_BRIDGE))

    def test_skipping_successive_sums_before_recurrence_is_rejected(self) -> None:
        # The shipped v1 lesson jumped from sum[i] straight to the recurrence.
        mutated = replace_step(
            self.asset,
            "window_sum.e1.n1.why",
            automatic_transition=TransitionSpec(next_step_id="recurrence_repetition.intro"),
        )
        self.assertIn(Code.MISSING_REQUIRED_BRIDGE, self.codes(mutated))
        self.assertIn("successive_sums", self.detail(mutated, Code.MISSING_REQUIRED_BRIDGE))

    # -- decomposition ORDERING_VIOLATION --------------------------------------------

    def test_moving_i_before_k_is_an_ordering_violation(self) -> None:
        concepts = list(sliding_window.GOLDEN_CONCEPTS)
        k_index = concepts.index(sliding_window._box_size)
        i_index = concepts.index(sliding_window._box_start)
        concepts[k_index], concepts[i_index] = concepts[i_index], concepts[k_index]
        mutated = rebuilt(tuple(concepts))
        self.assertIn(Code.ORDERING_VIOLATION, self.codes(mutated))
        self.assertIn("box_size_k->box_start_i", self.detail(mutated, Code.ORDERING_VIOLATION))

    # -- decomposition TOO_MANY_NEW_CONCEPTS ----------------------------------------

    def test_two_new_relations_in_one_step_is_rejected(self) -> None:
        intro = rep(self.asset, "r.position.intro")
        mutated = replace_rep(
            self.asset,
            "r.position.intro",
            visible_components=(*intro.visible_components, "relation:index"),
        )
        self.assertIn(Code.TOO_MANY_NEW_CONCEPTS, self.codes(mutated))
        self.assertIn("position.intro", self.detail(mutated, Code.TOO_MANY_NEW_CONCEPTS))

    # -- BINV-003: box chart persists into code steps -------------------------------

    def test_code_step_without_box_chart_is_rejected(self) -> None:
        mutated = self.asset
        for item in self.asset.representations:
            if item.representation_id.startswith(("r.append.", "r.recurrence_repetition.")):
                mutated = replace_rep(
                    mutated,
                    item.representation_id,
                    visible_components=tuple(
                        component
                        for component in item.visible_components
                        if component not in {"window_box", "index_row", "numbers_row"}
                    ),
                )
        detail = self.detail(mutated, Code.MISSING_REPRESENTATION)
        self.assertIn("append.e0.n2:window_box", detail)
        self.assertIn("recurrence_repetition.e0.n2:index_row", detail)

    def test_old_code_phase_components_are_rejected(self) -> None:
        # v1 replaced the chart with problem_anchor/code/variable_roles in code steps.
        mutated = replace_rep(
            self.asset,
            "r.append.e0.probe",
            visible_components=("problem_anchor", "code", "variable_roles", "relation:append"),
        )
        self.assertIn(Code.MISSING_REPRESENTATION, self.codes(mutated))

    # -- BINV-005: exercise charts omit answer-revealing parts ----------------------

    def test_enumerate_pair_row_in_exercise_is_rejected(self) -> None:
        probe = rep(self.asset, "r.enumerate.e0.probe")
        mutated = replace_rep(
            self.asset,
            "r.enumerate.e0.probe",
            visible_components=(*probe.visible_components, "pair_row"),
        )
        self.assertIn(Code.FORBIDDEN_REPRESENTATION_PRESENT, self.codes(mutated))
        self.assertIn(
            "enumerate.e0.n2:pair_row", self.detail(mutated, Code.FORBIDDEN_REPRESENTATION_PRESENT)
        )

    def test_answer_literal_in_exercise_text_is_rejected(self) -> None:
        probe = rep(self.asset, "r.enumerate.e0.probe")
        mutated = replace_rep(
            self.asset,
            "r.enumerate.e0.probe",
            learner_visible_markdown=probe.learner_visible_markdown
            + "\n\npair: (0,4) (1,7) (2,2) (3,6) (4,1) (5,9)",
        )
        self.assertIn(Code.ANSWER_REVEAL_FORBIDDEN, self.codes(mutated))

    def test_answer_arrow_in_exercise_chart_is_rejected(self) -> None:
        why = rep(self.asset, "r.position.e0.why")
        mutated = replace_rep(
            self.asset,
            "r.position.e0.probe",
            learner_visible_markdown=why.learner_visible_markdown.split("\n", 2)[2],
        )
        self.assertIn(Code.ANSWER_REVEAL_FORBIDDEN, self.codes(mutated))

    def test_append_answer_in_exercise_is_rejected(self) -> None:
        probe = rep(self.asset, "r.append.e0.probe")
        mutated = replace_rep(
            self.asset,
            "r.append.e0.probe",
            learner_visible_markdown=probe.learner_visible_markdown
            + "\n\nHint: S.append( S[i-1] + a[i] )",
        )
        self.assertIn(Code.ANSWER_REVEAL_FORBIDDEN, self.codes(mutated))

    # -- BINV-004: parts 06-08 stay out of this lesson ------------------------------

    def test_future_concepts_are_rejected(self) -> None:
        for marker in ("max_sum = S[i]", "for x in range(k):", "    break", "else:"):
            with self.subTest(marker=marker):
                frontier = rep(self.asset, "r.frontier.assembled")
                mutated = replace_rep(
                    self.asset,
                    "r.frontier.assembled",
                    learner_visible_markdown=frontier.learner_visible_markdown
                    + f"\n\n```python\n{marker}\n```",
                )
                self.assertIn(Code.FORBIDDEN_CONCEPT_DISCLOSED, self.codes(mutated))

    def test_invented_step_is_rejected(self) -> None:
        extra = step(self.asset, "frontier.assembled").model_copy(update={"step_id": "max.intro"})
        mutated = self.asset.model_copy(update={"steps": (*self.asset.steps, extra)})
        self.assertIn(Code.ILLEGAL_STEP, self.codes(mutated))

    # -- mastery ------------------------------------------------------------------

    def test_mastery_claim_in_text_is_rejected(self) -> None:
        for claim in ("You have mastered sliding windows.", "Mastery achieved.", "You now know it."):
            with self.subTest(claim=claim):
                mutated = replace_rep(
                    self.asset, "r.frontier.assembled", learner_visible_markdown=claim
                )
                self.assertIn(Code.MASTERY_CLAIM, self.codes(mutated))

    def test_validated_exit_is_a_mastery_claim(self) -> None:
        mutated = replace_step(
            self.asset,
            "frontier.assembled",
            automatic_transition=TransitionSpec(exit_status=RunStatus.COMPLETED_VALIDATED),
        )
        self.assertIn(Code.MASTERY_CLAIM, self.codes(mutated))

    def test_disclaimer_is_not_a_claim(self) -> None:
        self.assertIn(
            sliding_window.MASTERY_DISCLAIMER,
            rep(self.asset, "r.frontier.assembled").learner_visible_markdown,
        )
        self.assertNotIn(Code.MASTERY_CLAIM, self.codes(self.asset))

    # -- golden feedback rules ------------------------------------------------------

    def test_retrying_the_same_example_is_rejected(self) -> None:
        # v1 behaviour: after a correction, ask the identical probe again.
        mutated = replace_step(
            self.asset,
            "position.e0.n2.fix",
            automatic_transition=TransitionSpec(next_step_id="position.e0.n2"),
        )
        self.assertIn("same example", self.detail(mutated, Code.FEEDBACK_DISCIPLINE))

    def test_advancing_after_one_correct_retry_is_rejected(self) -> None:
        mutated = replace_step(
            self.asset,
            "position.e1.n2.why",
            automatic_transition=TransitionSpec(next_step_id="index.intro"),
        )
        self.assertIn("no extra check", self.detail(mutated, Code.FEEDBACK_DISCIPLINE))

    def test_correct_answer_without_why_is_rejected(self) -> None:
        probe = step(self.asset, "index.e0.n2")
        routes = tuple(
            route.model_copy(update={"next_step_id": "index.e1.n1"})
            if route.outcome == LearnerOutcome.CORRECT
            else route
            for route in probe.outcome_transitions
        )
        mutated = replace_step(self.asset, "index.e0.n2", outcome_transitions=routes)
        self.assertIn(Code.FEEDBACK_DISCIPLINE, self.codes(mutated))

    def test_correction_without_reassurance_is_rejected(self) -> None:
        fix = rep(self.asset, "r.box_size_k.e0.fix")
        mutated = replace_rep(
            self.asset,
            "r.box_size_k.e0.fix",
            visible_components=tuple(
                item for item in fix.visible_components if item != "reassurance"
            ),
        )
        self.assertIn(Code.FEEDBACK_DISCIPLINE, self.codes(mutated))

    def test_partial_that_drops_the_correct_part_is_rejected(self) -> None:
        mutated = replace_step(
            self.asset,
            "window_sum.e1.n1.partial",
            automatic_transition=TransitionSpec(next_step_id="successive_sums.intro"),
        )
        self.assertIn("partial answer", self.detail(mutated, Code.FEEDBACK_DISCIPLINE))


class GoldenBehaviourTests(unittest.TestCase):
    """Drive the real controller through the golden's correct, wrong, and partial paths."""

    def setUp(self) -> None:
        self.asset = shipped()

    def run_answers(self, answers: dict[str, str]) -> list[str]:
        state, bundle = start_run(
            self.asset, problem_run_id="golden", subject_id="subject-001", session_id="s"
        )
        visited = [turn.canonical_step_id for turn in bundle.turns]
        for _ in range(200):
            if bundle.response_turn_id is None:
                break
            current = state.current_step_id
            assert current is not None
            response = answers.pop(current, None) or correct_response(self.asset, current)
            result = submit_response(
                self.asset, state, turn_id=bundle.response_turn_id, response=response
            )
            state, bundle = result.state, result.bundle
            visited.extend(turn.canonical_step_id for turn in bundle.turns)
        self.assertEqual(state.status, RunStatus.ASSEMBLED_MASTERY_UNPROVEN)
        return visited

    def test_wrong_answer_corrects_reassures_retries_differently_and_checks_again(self) -> None:
        visited = self.run_answers({"position.e0.n2": "9"})
        start = visited.index("position.e0.n2")
        self.assertEqual(
            visited[start : start + 7],
            [
                "position.e0.n2",
                "position.e0.n2.fix",
                "position.e1.n2",
                "position.e1.n2.why",
                "position.e2.n1",
                "position.e2.n1.why",
                "index.intro",
            ],
        )
        fix = rep(self.asset, "r.position.e0.fix").learner_visible_markdown
        self.assertIn("The right answer is **4**.", fix)
        self.assertIn(sliding_window.REASSURANCE, fix)

    def test_partial_keeps_the_numbers_and_asks_only_for_the_addition(self) -> None:
        visited = self.run_answers({"window_sum.e1.n1": "2 6"})
        start = visited.index("window_sum.e1.n1")
        self.assertEqual(
            visited[start : start + 6],
            [
                "window_sum.e1.n1",
                "window_sum.e1.n1.partial",
                "window_sum.e1.n1.finish",
                "window_sum.e1.n1.finish.why",
                "window_sum.e2.n1",
                "window_sum.e2.n1.why",
            ],
        )
        self.assertIn(
            "Those are the right numbers: **2 and 6**.",
            rep(self.asset, "r.window_sum.e1.partial").learner_visible_markdown,
        )
        self.assertIn("`sum[i=3]`", rep(self.asset, "r.window_sum.e2.probe").learner_visible_markdown)

    def test_append_partial_keeps_the_value_and_isolates_storage(self) -> None:
        visited = self.run_answers({"append.e0.n2": "S[i-1] + a[i]"})
        self.assertIn("append.e0.n2.partial", visited)
        self.assertIn("append.e0.n2.finish", visited)

    def test_enumerate_needs_exactly_two_checks_on_the_correct_path(self) -> None:
        visited = self.run_answers({})
        probes = [item for item in visited if item.startswith("enumerate.") and ".n" in item]
        probes = [item for item in probes if not item.endswith(".why")]
        self.assertEqual(probes, ["enumerate.e0.n2", "enumerate.e1.n1"])

    def test_successive_sums_are_all_traversed_before_the_recurrence(self) -> None:
        visited = self.run_answers({})
        recurrence = visited.index("recurrence_repetition.intro")
        for probe in ("successive_sums.e0.n3", "successive_sums.e1.n2", "successive_sums.e2.n1"):
            self.assertLess(visited.index(probe), recurrence)

    def test_every_probe_is_one_tiny_question(self) -> None:
        by_id = {item.representation_id: item for item in self.asset.representations}
        for item in self.asset.steps:
            if item.kind != StepKind.PROBE:
                continue
            markdown = by_id[item.representation_id].learner_visible_markdown
            questions = [line for line in markdown.splitlines() if line.startswith("**")]
            self.assertEqual(len(questions), 1, item.step_id)
            self.assertTrue(questions[0].rstrip("*").rstrip("`").endswith("?"), item.step_id)


if __name__ == "__main__":
    unittest.main()
