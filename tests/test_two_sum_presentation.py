from __future__ import annotations

import unittest

from study_os.pir import (
    AssetViolationCode,
    PresentationContract,
    build_interaction_bundle,
    start_run,
    validate_asset,
)
from study_os.pir.registry import (
    TWO_SUM_CANONICAL_PROBLEM_ID,
    resolve_known_problem,
    two_sum_asset,
)


class TwoSumPresentationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.asset = two_sum_asset()

    def test_exact_problem_alias_resolves_to_reviewed_asset(self) -> None:
        resolved = resolve_known_problem(
            "Given nums and target, return indices of two numbers whose sum is target.",
            "dsa",
        )
        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.canonical_problem_id, TWO_SUM_CANONICAL_PROBLEM_ID)

    def test_required_variable_map_is_exact_and_forbids_renames(self) -> None:
        contract = self.asset.presentation_contract
        self.assertIsInstance(contract, PresentationContract)
        assert contract is not None
        self.assertEqual(
            tuple(item.name for item in contract.required_variable_map),
            ("nums", "target", "box", "i", "num", "needed"),
        )
        self.assertEqual(
            contract.forbidden_variable_names,
            ("seen", "lookup", "index_by_num"),
        )
        rendered = "\n".join(
            representation.learner_visible_markdown
            for representation in self.asset.representations
        )
        self.assertNotIn("seen", rendered)
        self.assertNotIn("lookup", rendered)
        self.assertNotIn("index_by_num", rendered)

    def test_box_needed_turn_is_visual_and_verbatim(self) -> None:
        state, _ = start_run(
            self.asset,
            problem_run_id="two-sum-box-run",
            subject_id="subject-001",
            session_id="session-001",
        )
        # Walk the deterministic graph with approved answers to the box probe.
        from study_os.pir.controller import submit_response

        current = state
        answers = (("two-sum-box-goal", "[0, 1]"), ("two-sum-box-needed", "7"))
        for key, answer in answers:
            _, bundle = build_interaction_bundle(self.asset, current)
            result = submit_response(
                self.asset,
                current,
                turn_id=bundle.response_turn_id or "",
                response=answer,
            )
            current = result.state
        _, bundle = build_interaction_bundle(self.asset, current)
        self.assertEqual(bundle.turns[-1].canonical_step_id, "two_sum_box_probe")
        turn = bundle.turns[-1]
        self.assertEqual(turn.render_mode, "verbatim")
        self.assertIn("box[needed]", turn.learner_visible_markdown)
        self.assertIn("```text", turn.learner_visible_markdown)
        self.assertIsNotNone(bundle.presentation_contract)

    def test_validator_rejects_forbidden_rename_and_missing_chart(self) -> None:
        forbidden = self.asset.representations[6].model_copy(
            update={
                "learner_visible_markdown": "```text\nseen = {}\n```\nWhat is next?"
            }
        )
        renamed = self.asset.model_copy(
            update={
                "representations": (
                    *self.asset.representations[:6],
                    forbidden,
                    *self.asset.representations[7:],
                )
            }
        )
        codes = {violation.code for violation in validate_asset(renamed)}
        self.assertIn(AssetViolationCode.PRESENTATION_FORBIDDEN_TERM, codes)

        no_chart = self.asset.representations[6].model_copy(
            update={"learner_visible_markdown": "Explain box[needed]."}
        )
        broken = self.asset.model_copy(
            update={
                "representations": (
                    *self.asset.representations[:6],
                    no_chart,
                    *self.asset.representations[7:],
                )
            }
        )
        codes = {violation.code for violation in validate_asset(broken)}
        self.assertIn(AssetViolationCode.PRESENTATION_VISUAL_MISSING, codes)

    def test_validator_rejects_contract_without_tiny_check(self) -> None:
        missing_check = self.asset.representations[6].model_copy(
            update={"check_question": None}
        )
        broken = self.asset.model_copy(
            update={
                "representations": (
                    *self.asset.representations[:6],
                    missing_check,
                    *self.asset.representations[7:],
                )
            }
        )
        codes = {violation.code for violation in validate_asset(broken)}
        self.assertIn(AssetViolationCode.PRESENTATION_CHECK_MISSING, codes)


if __name__ == "__main__":
    unittest.main()
