import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.adaptive.contracts import LearnerSnapshot  # noqa: E402
from study_os.adaptive.diagnostic import (  # noqa: E402
    DiagnosticCandidate,
    bernoulli_entropy,
    bkt_information_gain,
    propose_bkt_information_gain,
    propose_uncertainty_baseline,
)

FIXTURE = ROOT / "tests" / "fixtures" / "p2_diagnostic_selector_bakeoff.v0.1.json"


class DiagnosticBakeoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.expected = data["expected"]
        cls.snapshot = LearnerSnapshot.from_mapping(data["snapshot"])
        cls.candidates = tuple(DiagnosticCandidate(**item) for item in data["candidates"])

    def test_entropy_and_bkt_reference_values(self):
        self.assertAlmostEqual(bernoulli_entropy(0.5), 1.0, places=12)
        ref = DiagnosticCandidate("reference", "kc.reference", 0.5, 0.1, 0.2)
        self.assertAlmostEqual(bkt_information_gain(ref), 0.39731260974948635, places=12)

    def test_response_noise_lowers_information_gain(self):
        low_noise = DiagnosticCandidate("low-noise", "kc", 0.5, 0.1, 0.2)
        high_noise = DiagnosticCandidate("high-noise", "kc", 0.5, 0.35, 0.35)
        self.assertLess(bkt_information_gain(high_noise), bkt_information_gain(low_noise))

    def test_same_fixture_yields_distinct_selector_choices(self):
        uncertainty = propose_uncertainty_baseline(self.snapshot, self.candidates)
        bkt = propose_bkt_information_gain(self.snapshot, self.candidates)
        self.assertEqual(uncertainty.selected.candidate_id, self.expected["uncertainty_baseline"])
        self.assertEqual(bkt.selected.candidate_id, self.expected["bkt_information_gain"])
        self.assertNotEqual(uncertainty.selected.candidate_id, bkt.selected.candidate_id)
        self.assertEqual(uncertainty.candidates, bkt.candidates)

    def test_saturated_candidate_is_hard_excluded(self):
        for proposal in (
            propose_uncertainty_baseline(self.snapshot, self.candidates),
            propose_bkt_information_gain(self.snapshot, self.candidates),
        ):
            reasons = {item.candidate_id: item.reason_code for item in proposal.exclusions}
            self.assertEqual(reasons["diag-saturated"], self.expected["saturated_exclusion"])
            self.assertNotIn("diag-saturated", {score.candidate_id for score in proposal.scores})

    def test_bkt_replay_is_deterministic_and_finite(self):
        first = propose_bkt_information_gain(self.snapshot, self.candidates).to_dict()
        second = propose_bkt_information_gain(self.snapshot, self.candidates).to_dict()
        self.assertEqual(first, second)
        self.assertTrue(all(math.isfinite(score["total"]) for score in first["scores"]))


if __name__ == "__main__":
    unittest.main()
