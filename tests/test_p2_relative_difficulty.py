import sys
import unittest
from dataclasses import fields, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.adaptive.complexity import (  # noqa: E402
    ComplexityItemCandidate,
    ItemComplexity,
    LearnerDifficultyProfile,
    estimate_relative_load,
    propose_relative_difficulty_fit,
)
from study_os.adaptive.contracts import LearnerSnapshot  # noqa: E402
from study_os.curriculum import load_curriculum_slice  # noqa: E402


class RelativeDifficultyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curriculum = load_curriculum_slice(ROOT, "domains/dsa/running-extrema")

    def complexity(self, item_id: str) -> ItemComplexity:
        return ItemComplexity.from_mapping(self.curriculum.item_by_id[item_id]["complexity"])

    def snapshot(self) -> LearnerSnapshot:
        return LearnerSnapshot(
            subject_id="subject-relative-load",
            checkpoint_id="checkpoint-relative-load",
            phase="instruction",
        )

    def test_same_authored_items_reverse_relative_order_for_different_profiles(self):
        index_item = self.complexity("re.index-value.001")
        state_item = self.complexity("re.two-candidate.001")

        syntax_weak = LearnerDifficultyProfile(
            prerequisite_readiness=0.9,
            state_reasoning=0.9,
            control_flow_fluency=0.9,
            syntax_fluency=0.1,
            representation_translation=0.8,
            novelty_tolerance=0.8,
            transfer_fluency=0.8,
            scaffold_support_effectiveness=0.5,
        )
        state_weak = LearnerDifficultyProfile(
            prerequisite_readiness=0.9,
            state_reasoning=0.1,
            control_flow_fluency=0.2,
            syntax_fluency=0.9,
            representation_translation=0.8,
            novelty_tolerance=0.8,
            transfer_fluency=0.8,
            scaffold_support_effectiveness=0.5,
        )

        self.assertGreater(
            estimate_relative_load(index_item, syntax_weak).relative_load,
            estimate_relative_load(state_item, syntax_weak).relative_load,
        )
        self.assertGreater(
            estimate_relative_load(state_item, state_weak).relative_load,
            estimate_relative_load(index_item, state_weak).relative_load,
        )

    def test_scaffold_is_relief_not_fake_mastery(self):
        profile = LearnerDifficultyProfile(
            prerequisite_readiness=0.5,
            state_reasoning=0.5,
            control_flow_fluency=0.5,
            syntax_fluency=0.5,
            representation_translation=0.5,
            novelty_tolerance=0.5,
            transfer_fluency=0.5,
            scaffold_support_effectiveness=1.0,
        )
        original = self.complexity("re.running-max.001")
        unscaffolded = replace(original, scaffold_amount=0)
        supported = estimate_relative_load(original, profile)
        unsupported = estimate_relative_load(unscaffolded, profile)
        self.assertLess(supported.relative_load, unsupported.relative_load)
        self.assertLess(supported.components["scaffold_relief"], 0.0)

    def test_fit_selector_retains_component_breakdown(self):
        profile = LearnerDifficultyProfile(
            prerequisite_readiness=0.8,
            state_reasoning=0.5,
            control_flow_fluency=0.5,
            syntax_fluency=0.4,
            representation_translation=0.6,
            novelty_tolerance=0.6,
            transfer_fluency=0.5,
            scaffold_support_effectiveness=0.7,
        )
        candidates = tuple(
            ComplexityItemCandidate(item_id, self.complexity(item_id))
            for item_id in ("re.compare.001", "re.two-candidate.001", "re.implement.001")
        )
        proposal = propose_relative_difficulty_fit(
            self.snapshot(), candidates, profile=profile, target_relative_load=0.10
        )
        self.assertEqual(proposal.mode, "shadow")
        self.assertFalse(proposal.expected_evidence["psychometric_probability_claimed"])
        self.assertTrue(proposal.expected_evidence["requires_behavioral_calibration"])
        for score in proposal.scores:
            self.assertIn("state_load", score.components)
            self.assertIn("syntax_load", score.components)
            self.assertIn("translation_load", score.components)
            self.assertIn("scaffold_relief", score.components)

    def test_model_does_not_collapse_authoring_to_easy_medium_hard(self):
        item_fields = {field.name for field in fields(ItemComplexity)}
        self.assertNotIn("difficulty", item_fields)
        self.assertNotIn("difficulty_label", item_fields)
        self.assertGreaterEqual(len(item_fields), 8)

    def test_invalid_strength_or_complexity_is_rejected(self):
        with self.assertRaises(ValueError):
            LearnerDifficultyProfile(
                prerequisite_readiness=1.1,
                state_reasoning=0.5,
                control_flow_fluency=0.5,
                syntax_fluency=0.5,
                representation_translation=0.5,
                novelty_tolerance=0.5,
                transfer_fluency=0.5,
                scaffold_support_effectiveness=0.5,
            )
        with self.assertRaises(ValueError):
            ItemComplexity(6, 1, 1, 1, 1, 1, 1, 1)


if __name__ == "__main__":
    unittest.main()
