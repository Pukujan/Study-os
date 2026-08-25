import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.adaptive.tutor_policy import (  # noqa: E402
    TutorAction,
    TutorPolicyConstraints,
    evaluate_tutor_action,
)


class TutorPolicyTests(unittest.TestCase):
    def constraints(self, **overrides):
        values = {
            "assistance_ceiling": "A1",
            "allow_full_solution": False,
            "hidden_answer_protected": True,
            "require_behavioral_advancement": True,
        }
        values.update(overrides)
        return TutorPolicyConstraints(**values)

    def codes(self, action, constraints=None):
        evaluation = evaluate_tutor_action(action, constraints or self.constraints())
        return evaluation.allowed, {violation.code for violation in evaluation.violations}

    def test_schema_is_valid(self):
        schema = json.loads((ROOT / "schemas" / "tutor-action.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)

    def test_small_hint_under_ceiling_is_allowed(self):
        action = TutorAction(
            action_id="a1",
            task_id="re.update-order.002",
            action_kind="hint",
            assistance_level="A1",
            contains_full_solution=False,
            reveals_hidden_answer=False,
        )
        allowed, codes = self.codes(action)
        self.assertTrue(allowed)
        self.assertFalse(codes)

    def test_over_assistance_and_full_solution_are_rejected(self):
        action = TutorAction(
            action_id="a2",
            task_id="re.update-order.002",
            action_kind="full_solution",
            assistance_level="A5",
            contains_full_solution=True,
            reveals_hidden_answer=False,
        )
        allowed, codes = self.codes(action)
        self.assertFalse(allowed)
        self.assertIn("assistance_ceiling_exceeded", codes)
        self.assertIn("premature_full_solution", codes)

    def test_hidden_answer_exposure_is_rejected(self):
        action = TutorAction(
            action_id="a3",
            task_id="hidden-transfer-item",
            action_kind="hint",
            assistance_level="A0",
            contains_full_solution=False,
            reveals_hidden_answer=True,
        )
        allowed, codes = self.codes(action)
        self.assertFalse(allowed)
        self.assertIn("hidden_answer_exposure", codes)

    def test_self_report_or_fluency_cannot_promote(self):
        for basis in ("self_report", "conversation_fluency"):
            action = TutorAction(
                action_id=f"advance-{basis}",
                task_id="re.update-order.002",
                action_kind="feedback",
                assistance_level="A0",
                contains_full_solution=False,
                reveals_hidden_answer=False,
                advancement_claim="pass_unaided",
                advancement_basis=basis,
                advancement_evidence_ids=(),
            )
            allowed, codes = self.codes(action)
            self.assertFalse(allowed)
            self.assertIn("nonbehavioral_advancement", codes)
            self.assertIn("missing_advancement_evidence", codes)

    def test_behavioral_advancement_with_evidence_is_allowed(self):
        action = TutorAction(
            action_id="advance-behavioral",
            task_id="re.update-order.002",
            action_kind="assessment",
            assistance_level="A0",
            contains_full_solution=False,
            reveals_hidden_answer=False,
            advancement_claim="pass_unaided",
            advancement_basis="behavioral_assessment",
            advancement_evidence_ids=("assessment-123",),
        )
        allowed, codes = self.codes(action)
        self.assertTrue(allowed)
        self.assertFalse(codes)

    def test_tutor_cannot_award_transfer_or_delayed_status(self):
        for claim in ("pass_transfer", "pass_delayed"):
            action = TutorAction(
                action_id=f"reserved-{claim}",
                task_id="re.transfer.001",
                action_kind="assessment",
                assistance_level="A0",
                contains_full_solution=False,
                reveals_hidden_answer=False,
                advancement_claim=claim,
                advancement_basis="behavioral_assessment",
                advancement_evidence_ids=("assessment-transfer",),
            )
            allowed, codes = self.codes(action)
            self.assertFalse(allowed)
            self.assertIn("reserved_capability_promotion", codes)

    def test_unvalidated_representation_is_rejected(self):
        action = TutorAction(
            action_id="rep-unvalidated",
            task_id="re.update-order.002",
            action_kind="representation",
            assistance_level="A1",
            contains_full_solution=False,
            reveals_hidden_answer=False,
            representation_id="repr.generated.v1",
            representation_semantic_validated=False,
        )
        allowed, codes = self.codes(action)
        self.assertFalse(allowed)
        self.assertIn("unvalidated_representation", codes)


if __name__ == "__main__":
    unittest.main()
