import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.adaptive.contracts import LearnerSnapshot  # noqa: E402
from study_os.adaptive.scaffold import (  # noqa: E402
    EpisodePlan,
    StepAssessment,
    propose_scaffold_action,
)
from study_os.curriculum import load_curriculum_slice  # noqa: E402

PLAN_PATH = ROOT / "domains" / "dsa" / "running-extrema" / "episode-plan.v0.1.json"
SCHEMA_PATH = ROOT / "schemas" / "episode-plan.schema.json"


class ScaffoldControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan_data = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.plan = EpisodePlan.from_mapping(cls.plan_data)
        cls.curriculum = load_curriculum_slice(ROOT, "domains/dsa/running-extrema")

    def snapshot(self, phase: str = "instruction") -> LearnerSnapshot:
        return LearnerSnapshot(
            subject_id="subject-scaffold",
            checkpoint_id="checkpoint-scaffold",
            phase=phase,
            current_focus="running extrema",
        )

    def assessment(self, step_index: int, result: str, assistance: str = "A2") -> StepAssessment:
        step = self.plan.steps[step_index]
        return StepAssessment(
            assessment_id=f"assessment-{step_index}-{result}",
            competency_id=step.competency_id,
            result=result,
            assistance_level=assistance,
            evidence_ids=(f"attempt-{step_index}",),
        )

    def test_real_plan_matches_schema_and_curriculum(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(self.plan_data)

        self.assertEqual(len(self.plan.steps), 7)
        self.assertEqual([step.complexity_stage for step in self.plan.steps], [1, 2, 3, 4, 5, 5, 6])
        for step in self.plan.steps:
            self.assertIn(step.competency_id, self.curriculum.competency_by_id)
            for item_id in step.item_ids:
                item = self.curriculum.item_by_id[item_id]
                self.assertIn(step.competency_id, item["competency_ids"])
                self.assertNotIn(item["exposure_class"], {"transfer_public_fixture", "retention_public_fixture"})

    def test_missing_assessment_probes_current_step(self):
        proposal = propose_scaffold_action(
            self.snapshot(), self.plan, current_step_id="step.two-candidates"
        )
        self.assertEqual(proposal.selected.candidate_id, "step.two-candidates")
        self.assertEqual(proposal.selected.action_type, "probe_step")
        self.assertEqual(proposal.selected.assistance_target, "A0")

    def test_failure_remediates_same_atomic_target(self):
        proposal = propose_scaffold_action(
            self.snapshot(),
            self.plan,
            current_step_id="step.update-order-scaffolded",
            assessment=self.assessment(4, "fail", "A2"),
        )
        self.assertEqual(proposal.selected.candidate_id, "step.update-order-scaffolded")
        self.assertEqual(proposal.selected.action_type, "remediate_step")
        self.assertEqual(proposal.selected.assistance_target, "A3")

    def test_supported_success_fades_instead_of_advancing(self):
        proposal = propose_scaffold_action(
            self.snapshot(),
            self.plan,
            current_step_id="step.update-order-scaffolded",
            assessment=self.assessment(4, "pass_supported", "A2"),
        )
        self.assertEqual(proposal.selected.candidate_id, "step.update-order-scaffolded")
        self.assertEqual(proposal.selected.action_type, "fade_same_step")
        self.assertEqual(proposal.selected.assistance_target, "A1")

    def test_unaided_success_advances_exactly_one_step(self):
        proposal = propose_scaffold_action(
            self.snapshot(),
            self.plan,
            current_step_id="step.update-order-scaffolded",
            assessment=self.assessment(4, "pass_unaided", "A0"),
        )
        self.assertEqual(proposal.selected.candidate_id, "step.update-order-faded")
        self.assertEqual(proposal.selected.action_type, "advance_one_step")
        self.assertNotEqual(proposal.selected.candidate_id, "step.blank-implementation")

    def test_final_step_only_signals_completion_candidate(self):
        proposal = propose_scaffold_action(
            self.snapshot(),
            self.plan,
            current_step_id="step.blank-implementation",
            assessment=self.assessment(6, "pass_unaided", "A0"),
        )
        self.assertEqual(proposal.selected.action_type, "episode_complete_candidate")
        self.assertTrue(proposal.expected_evidence["requires_separate_transfer_or_retention_evidence"])
        self.assertNotIn("pass_transfer", json.dumps(proposal.to_dict()))
        self.assertNotIn("pass_delayed", json.dumps(proposal.to_dict()))

    def test_mismatched_or_nonbehavioral_assessment_cannot_advance(self):
        wrong = StepAssessment(
            assessment_id="assessment-wrong",
            competency_id="dsa.compare.values",
            result="pass_unaided",
            assistance_level="A0",
            evidence_ids=("attempt-wrong",),
        )
        with self.assertRaisesRegex(ValueError, "must match"):
            propose_scaffold_action(
                self.snapshot(),
                self.plan,
                current_step_id="step.blank-implementation",
                assessment=wrong,
            )
        with self.assertRaisesRegex(ValueError, "accepts only"):
            StepAssessment(
                assessment_id="assessment-self-report",
                competency_id="dsa.extrema.update_order",
                result="pass_transfer",
                assistance_level="A0",
                evidence_ids=("self-report-1",),
            )

    def test_controller_rejects_transfer_or_maintenance_phase(self):
        with self.assertRaisesRegex(ValueError, "instruction/fading"):
            propose_scaffold_action(
                self.snapshot("transfer"), self.plan, current_step_id="step.compare-values"
            )


if __name__ == "__main__":
    unittest.main()
