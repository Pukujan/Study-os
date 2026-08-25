import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.adaptive.cat import (  # noqa: E402
    CatItemCandidate,
    irt_fisher_information,
    irt_probability_correct,
    propose_maximum_fisher_information,
    propose_target_success_item,
)
from study_os.adaptive.contracts import LearnerSnapshot  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "p2_cat_irt_bakeoff.v0.1.json"


class CatIrtShadowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.theta = data["ability_theta"]
        cls.target = data["target_success"]
        cls.expected = data["expected"]
        cls.diagnostic_snapshot = LearnerSnapshot.from_mapping(data["diagnostic_snapshot"])
        cls.instruction_snapshot = LearnerSnapshot.from_mapping(data["instruction_snapshot"])
        cls.items = tuple(CatItemCandidate(**item) for item in data["items"])

    def test_2pl_reference_probabilities_and_information(self):
        center = next(item for item in self.items if item.candidate_id == "item-info-center")
        target = next(item for item in self.items if item.candidate_id == "item-target-70")
        self.assertAlmostEqual(irt_probability_correct(self.theta, center), self.expected["center_probability"], places=12)
        self.assertAlmostEqual(irt_probability_correct(self.theta, target), self.expected["target_probability"], places=12)
        self.assertAlmostEqual(irt_fisher_information(self.theta, center), self.expected["center_information"], places=12)

    def test_same_bank_has_different_best_item_for_diagnostic_and_instruction(self):
        diagnostic = propose_maximum_fisher_information(
            self.diagnostic_snapshot,
            self.items,
            ability_theta=self.theta,
        )
        instruction = propose_target_success_item(
            self.instruction_snapshot,
            self.items,
            ability_theta=self.theta,
            target_success=self.target,
        )
        self.assertEqual(diagnostic.selected.candidate_id, self.expected["diagnostic_selected"])
        self.assertEqual(instruction.selected.candidate_id, self.expected["instruction_selected"])
        self.assertNotEqual(diagnostic.selected.candidate_id, instruction.selected.candidate_id)
        self.assertEqual(diagnostic.candidates, instruction.candidates)

    def test_overexposed_item_is_hard_excluded(self):
        for proposal in (
            propose_maximum_fisher_information(self.diagnostic_snapshot, self.items, ability_theta=self.theta),
            propose_target_success_item(
                self.instruction_snapshot,
                self.items,
                ability_theta=self.theta,
                target_success=self.target,
            ),
        ):
            reasons = {item.candidate_id: item.reason_code for item in proposal.exclusions}
            self.assertEqual(reasons["item-overexposed"], self.expected["overexposed_reason"])
            self.assertNotIn("item-overexposed", {score.candidate_id for score in proposal.scores})

    def test_proposals_expose_predicted_success_and_are_deterministic(self):
        first = propose_target_success_item(
            self.instruction_snapshot,
            self.items,
            ability_theta=self.theta,
            target_success=self.target,
        ).to_dict()
        second = propose_target_success_item(
            self.instruction_snapshot,
            self.items,
            ability_theta=self.theta,
            target_success=self.target,
        ).to_dict()
        self.assertEqual(first, second)
        self.assertTrue(all(math.isfinite(score["components"]["predicted_success"]) for score in first["scores"]))

    def test_target_success_validation(self):
        with self.assertRaisesRegex(ValueError, "target_success"):
            propose_target_success_item(
                self.instruction_snapshot,
                self.items,
                ability_theta=self.theta,
                target_success=1.0,
            )


if __name__ == "__main__":
    unittest.main()
