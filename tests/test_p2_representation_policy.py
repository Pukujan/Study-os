import copy
import json
import sys
import unittest
from dataclasses import fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.adaptive.contracts import LearnerSnapshot  # noqa: E402
from study_os.adaptive.representation_policy import (  # noqa: E402
    RepresentationCandidate,
    RepresentationOutcomeSummary,
    propose_representation_intervention,
)
from study_os.curriculum import load_curriculum_slice  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "p2_representation_policy.v0.1.json"


class RepresentationPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.snapshot = LearnerSnapshot.from_mapping(cls.fixture["snapshot"])
        cls.candidates = tuple(RepresentationCandidate.from_mapping(value) for value in cls.fixture["candidates"])
        cls.curriculum = load_curriculum_slice(ROOT, "domains/dsa/running-extrema")
        cls.task = cls.curriculum.item_by_id[cls.fixture["selection"]["selected_task_id"]]

    def propose(self, candidates=None, snapshot=None):
        selection = self.fixture["selection"]
        return propose_representation_intervention(
            snapshot or self.snapshot,
            candidates or self.candidates,
            selected_task_id=selection["selected_task_id"],
            target_competency_id=selection["target_competency_id"],
            assistance_ceiling=selection["assistance_ceiling"],
            allowed_representation_families=self.task["representation_families"],
        )

    def test_persistent_behavioral_effect_beats_immediate_only_high_score(self):
        proposal = self.propose()
        self.assertEqual(proposal.selected.candidate_id, "rep.state-table.trace.a1")
        self.assertEqual(proposal.selected.representation_id, "repr.state-table.v1")
        self.assertEqual(proposal.selected.learning_operation, "trace")
        self.assertEqual(proposal.expected_evidence["representation_family"], "state_table")
        score_by_id = {score.candidate_id: score for score in proposal.scores}
        persistent = score_by_id["rep.state-table.trace.a1"]
        immediate_only = score_by_id["rep.python-code.debug.a0"]
        self.assertGreater(persistent.components["observed_window_coverage"], immediate_only.components["observed_window_coverage"])
        self.assertGreater(persistent.total, immediate_only.total)

    def test_hard_gates_preserve_upstream_task_and_assistance_authority(self):
        proposal = self.propose()
        exclusions = {value.candidate_id: value.reason_code for value in proposal.exclusions}
        self.assertEqual(exclusions["rep.generated-visual.a1"], "representation_not_allowed_for_task")
        self.assertEqual(exclusions["rep.state-table.a2-over-ceiling"], "assistance_ceiling_exceeded")
        self.assertEqual(exclusions["rep.other-task"], "different_task")

    def test_semantic_validation_is_a_hard_gate_even_for_allowed_family(self):
        candidate = copy.deepcopy(self.fixture["candidates"][0])
        candidate["candidate_id"] = "rep.state-table.unvalidated"
        candidate["semantic_validated"] = False
        proposal = self.propose(candidates=(RepresentationCandidate.from_mapping(candidate),))
        self.assertIsNone(proposal.selected)
        self.assertEqual(proposal.exclusions[0].reason_code, "semantic_not_validated")

    def test_behavioral_scores_require_canonical_evidence(self):
        with self.assertRaisesRegex(ValueError, "canonical evidence_ids"):
            RepresentationOutcomeSummary(immediate=0.8)

    def test_untested_candidate_gets_small_exploration_bonus_not_fake_effect(self):
        proposal = self.propose()
        score_by_id = {score.candidate_id: score for score in proposal.scores}
        exploratory = score_by_id["rep.state-table.predict.a0"]
        self.assertEqual(exploratory.components["persistent_behavioral_effect"], 0.0)
        self.assertGreater(exploratory.components["exploration_bonus"], 0.0)
        self.assertLess(exploratory.total, score_by_id["rep.state-table.trace.a1"].total)

    def test_recent_representation_exposure_is_penalized(self):
        proposal = self.propose()
        score_by_id = {score.candidate_id: score for score in proposal.scores}
        code_score = score_by_id["rep.python-code.debug.a0"]
        self.assertLess(code_score.components["recent_exposure_penalty"], 0.0)

    def test_policy_has_no_fixed_learning_style_field(self):
        candidate_fields = {field.name for field in fields(RepresentationCandidate)}
        forbidden = {"learning_style", "visual_learner", "auditory_learner", "preferred_modality"}
        self.assertTrue(candidate_fields.isdisjoint(forbidden))

    def test_policy_is_shadow_only_and_phase_bounded(self):
        proposal = self.propose()
        self.assertEqual(proposal.mode, "shadow")
        transfer_snapshot = LearnerSnapshot(
            subject_id="subject-representation-shadow",
            checkpoint_id="checkpoint-representation-shadow",
            phase="transfer",
        )
        with self.assertRaisesRegex(ValueError, "instruction/fading"):
            self.propose(snapshot=transfer_snapshot)


if __name__ == "__main__":
    unittest.main()
