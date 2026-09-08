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

    def snapshot_with_statuses(self, statuses: dict[str, str]) -> LearnerSnapshot:
        payload = json.loads(json.dumps(self.fixture["snapshot"]))
        for competency_id, status in statuses.items():
            payload["capabilities"][competency_id] = {
                "status": status,
                "assistance_level": "A0" if status.startswith("pass_") else None,
                "evidence_ids": [f"assessment-{competency_id}"] if status.startswith("pass_") else [],
            }
        return LearnerSnapshot.from_mapping(payload)

    def diagnosis(self) -> DiagnosisProposal:
        return DiagnosisProposal.from_mapping(self.fixture["diagnosis_proposal"])

    def diagnosis_with_single_hypothesis(
        self,
        *,
        diagnosis_id: str,
        family: str,
        suspected_competency_ids: list[str],
        source_evidence_id: str = "learner-turn-code-confusion",
    ) -> DiagnosisProposal:
        payload = dict(self.fixture["diagnosis_proposal"])
        payload["hypotheses"] = [
            {
                "diagnosis_id": diagnosis_id,
                "family": family,
                "source_evidence_ids": [source_evidence_id],
                "suspected_competency_ids": suspected_competency_ids,
                "confidence": 0.8,
                "status": "proposed",
            }
        ]
        return DiagnosisProposal.from_mapping(payload)

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

    def route_with(self, snapshot: LearnerSnapshot, diagnosis: DiagnosisProposal):
        parent = self.fixture["parent"]
        return propose_prerequisite_sensitive_remediation(
            snapshot,
            diagnosis,
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

    def test_diagnosis_parser_rejects_malformed_array_shapes(self):
        malformed_hypotheses = dict(self.fixture["diagnosis_proposal"])
        malformed_hypotheses["hypotheses"] = ["not-an-object"]
        with self.assertRaisesRegex(ValueError, "hypotheses must contain objects"):
            DiagnosisProposal.from_mapping(malformed_hypotheses)

        malformed_sources = dict(self.fixture["diagnosis_proposal"])
        malformed_sources["source_evidence_ids"] = "learner-turn-code-confusion"
        with self.assertRaisesRegex(ValueError, "source_evidence_ids must be an array"):
            DiagnosisProposal.from_mapping(malformed_sources)

    def test_ambiguous_missing_prerequisite_fails_closed(self):
        diagnosis = self.diagnosis_with_single_hypothesis(
            diagnosis_id="diag-ambiguous",
            family="missing_prerequisite",
            suspected_competency_ids=[],
        )
        proposal = self.route_with(self.snapshot(), diagnosis)

        self.assertIsNone(proposal.selected)
        self.assertTrue(proposal.expected_evidence["progression_blocked"])
        self.assertTrue(proposal.expected_evidence["diagnostic_probe_required"])
        self.assertEqual(proposal.expected_evidence["required_next_evidence"], "diagnostic_probe")

    def test_noncanonical_suspected_prerequisite_does_not_fallback_to_only_missing(self):
        snapshot = self.snapshot_with_statuses(
            {
                "program.boolean_decision": "pass_unaided",
                "test.boundary_case": "pass_unaided",
            }
        )
        diagnosis = self.diagnosis_with_single_hypothesis(
            diagnosis_id="diag-noncanonical",
            family="missing_prerequisite",
            suspected_competency_ids=["program.not_in_canonical_graph"],
        )
        proposal = self.route_with(snapshot, diagnosis)

        self.assertIsNone(proposal.selected)
        self.assertTrue(proposal.expected_evidence["diagnostic_probe_required"])
        self.assertEqual(
            proposal.expected_evidence["noncanonical_suspected_prerequisite_ids"],
            ["program.not_in_canonical_graph"],
        )
        self.assertIsNone(proposal.expected_evidence["target_competency_id"])

    def test_already_satisfied_suspect_does_not_retarget_different_missing_prerequisite(self):
        snapshot = self.snapshot_with_statuses(
            {
                "program.comparison_semantics": "pass_unaided",
                "program.boolean_decision": "pass_unaided",
            }
        )
        diagnosis = self.diagnosis_with_single_hypothesis(
            diagnosis_id="diag-stale-suspect",
            family="missing_prerequisite",
            suspected_competency_ids=["program.comparison_semantics"],
        )
        proposal = self.route_with(snapshot, diagnosis)

        self.assertIsNone(proposal.selected)
        self.assertTrue(proposal.expected_evidence["diagnostic_probe_required"])
        self.assertEqual(proposal.expected_evidence["missing_prerequisite_ids"], ["test.boundary_case"])
        self.assertIsNone(proposal.expected_evidence["target_competency_id"])

    def test_representation_only_remediation_keeps_parent_target(self):
        diagnosis = self.diagnosis_with_single_hypothesis(
            diagnosis_id="diag-representation-only",
            family="representation_interference",
            suspected_competency_ids=[],
            source_evidence_id="learner-turn-visual-request",
        )
        parent = self.fixture["parent"]
        proposal = self.route_with(self.snapshot(), diagnosis)

        self.assertIsNotNone(proposal.selected)
        self.assertEqual(proposal.selected.candidate_id, parent["candidate_id"])
        self.assertIn(parent["candidate_id"], proposal.candidates)
        self.assertEqual(proposal.selected.learning_operation, "change_representation")
        self.assertEqual(
            proposal.expected_evidence["target_competency_id"],
            parent["competency_id"],
        )

    def test_assistance_target_never_exceeds_ceiling(self):
        parent = self.fixture["parent"]
        proposal = propose_prerequisite_sensitive_remediation(
            self.snapshot(),
            self.diagnosis(),
            parent_candidate_id=parent["candidate_id"],
            parent_competency_id=parent["competency_id"],
            ordered_prerequisite_ids=parent["ordered_prerequisite_ids"],
            assistance_ceiling="A1",
        )
        self.assertIsNotNone(proposal.selected)
        self.assertEqual(proposal.selected.assistance_target, "A1")

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
