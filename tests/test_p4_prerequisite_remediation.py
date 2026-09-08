import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.adaptive.contracts import LearnerSnapshot  # noqa: E402
from study_os.adaptive.diagnosis import DiagnosisProposal  # noqa: E402
from study_os.adaptive.prerequisite_remediation import (  # noqa: E402
    propose_prerequisite_sensitive_remediation,
)
from study_os.adaptive.representation_policy import (  # noqa: E402
    RepresentationCandidate,
    propose_representation_intervention,
)

FIXTURE = ROOT / "tests" / "fixtures" / "p4_mutation_lab_representation_failure.v0.1.json"


class P4PrerequisiteRemediationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def snapshot(self) -> LearnerSnapshot:
        return LearnerSnapshot.from_mapping(self.fixture["snapshot"])

    def diagnosis(self) -> DiagnosisProposal:
        return DiagnosisProposal.from_mapping(self.fixture["diagnosis_proposal"])

    def route(self):
        parent = self.fixture["parent"]
        return propose_prerequisite_sensitive_remediation(
            self.snapshot(),
            self.diagnosis(),
            parent_candidate_id=parent["candidate_id"],
            parent_competency_id=parent["competency_id"],
            ordered_prerequisite_ids=parent["ordered_prerequisite_ids"],
            assistance_ceiling="A2",
        )

    def test_failed_mutation_lab_routes_to_missing_prerequisite(self):
        proposal = self.route()
        expected = self.fixture["expected"]

        self.assertIsNotNone(proposal.selected)
        self.assertEqual(proposal.selected.action_type, "remediate_prerequisite")
        self.assertEqual(
            proposal.expected_evidence["target_competency_id"],
            expected["target_competency_id"],
        )
        self.assertTrue(proposal.expected_evidence["progression_blocked"])
        self.assertEqual(
            proposal.expected_evidence["required_next_evidence"],
            expected["required_next_evidence"],
        )
        self.assertEqual(
            proposal.expected_evidence["authorized_operations"],
            expected["authorized_operations"],
        )

    def test_confusion_does_not_become_parent_task_failure(self):
        proposal = self.route()
        self.assertEqual(
            proposal.expected_evidence["canonical_parent_attempt_recording"],
            "forbidden_until_parent_behavioral_probe",
        )
        self.assertTrue(proposal.expected_evidence["progression_blocked"])
        self.assertFalse(proposal.expected_evidence["diagnostic_probe_required"])

    def test_diagnosis_contract_is_strict_and_versioned(self):
        payload = dict(self.fixture["diagnosis_proposal"])
        payload["can_advance"] = True
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            DiagnosisProposal.from_mapping(payload)

        diagnosis = self.diagnosis()
        self.assertEqual(diagnosis.schema_version, "0.1.0")
        self.assertEqual(diagnosis.prompt_version, "p4-diagnosis-proposal.v0.1")

    def test_ambiguous_missing_prerequisite_fails_closed(self):
        payload = dict(self.fixture["diagnosis_proposal"])
        payload["hypotheses"] = [
            {
                "diagnosis_id": "diag-ambiguous",
                "family": "missing_prerequisite",
                "source_evidence_ids": ["learner-turn-code-confusion"],
                "suspected_competency_ids": [],
                "confidence": 0.5,
                "status": "proposed",
            }
        ]
        diagnosis = DiagnosisProposal.from_mapping(payload)
        parent = self.fixture["parent"]
        proposal = propose_prerequisite_sensitive_remediation(
            self.snapshot(),
            diagnosis,
            parent_candidate_id=parent["candidate_id"],
            parent_competency_id=parent["competency_id"],
            ordered_prerequisite_ids=parent["ordered_prerequisite_ids"],
        )

        self.assertIsNone(proposal.selected)
        self.assertTrue(proposal.expected_evidence["progression_blocked"])
        self.assertTrue(proposal.expected_evidence["diagnostic_probe_required"])
        self.assertEqual(proposal.expected_evidence["required_next_evidence"], "diagnostic_probe")

    def test_representation_only_remediation_keeps_parent_target(self):
        payload = dict(self.fixture["diagnosis_proposal"])
        payload["hypotheses"] = [
            {
                "diagnosis_id": "diag-representation-only",
                "family": "representation_interference",
                "source_evidence_ids": ["learner-turn-visual-request"],
                "suspected_competency_ids": [],
                "confidence": 0.9,
                "status": "proposed",
            }
        ]
        diagnosis = DiagnosisProposal.from_mapping(payload)
        parent = self.fixture["parent"]
        proposal = propose_prerequisite_sensitive_remediation(
            self.snapshot(),
            diagnosis,
            parent_candidate_id=parent["candidate_id"],
            parent_competency_id=parent["competency_id"],
            ordered_prerequisite_ids=parent["ordered_prerequisite_ids"],
        )

        self.assertIsNotNone(proposal.selected)
        self.assertEqual(proposal.selected.candidate_id, parent["candidate_id"])
        self.assertEqual(proposal.selected.learning_operation, "change_representation")
        self.assertEqual(
            proposal.expected_evidence["target_competency_id"],
            parent["competency_id"],
        )

    def test_representation_contract_surfaces_visual_intent_to_renderer(self):
        candidate = RepresentationCandidate.from_mapping(self.fixture["representation_candidate"])
        proposal = propose_representation_intervention(
            self.snapshot(),
            (candidate,),
            selected_task_id=candidate.task_id,
            target_competency_id=candidate.competency_id,
            assistance_ceiling="A2",
            allowed_representation_families=("decision_tree",),
        )
        expected = self.fixture["expected"]

        self.assertIsNotNone(proposal.selected)
        self.assertEqual(
            proposal.expected_evidence["representation_family"],
            expected["selected_representation_family"],
        )
        constraints = proposal.expected_evidence["representation_constraints"]
        self.assertEqual(constraints["code_visibility"], expected["code_visibility"])
        self.assertEqual(
            constraints["interaction_granularity"],
            expected["interaction_granularity"],
        )
        self.assertIn("explicit_boundary_state", constraints["required_structure"])
        self.assertIn("source_code_primary", constraints["forbidden_features"])

    def test_same_inputs_produce_same_route(self):
        first = self.route().to_dict()
        second = self.route().to_dict()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
