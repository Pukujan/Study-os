import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.adaptive.baseline import InstructionCandidate, propose_instruction_baseline  # noqa: E402
from study_os.adaptive.contracts import (  # noqa: E402
    CandidateExclusion,
    DecisionProposal,
    LearnerSnapshot,
    SelectedAction,
    shadow_learning_event,
)

FIXTURE = ROOT / "tests" / "fixtures" / "p2_running_extrema_shadow.v0.1.json"


class P2AdapterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def snapshot(self) -> LearnerSnapshot:
        return LearnerSnapshot.from_mapping(self.fixture["snapshot"])

    def candidates(self) -> tuple[InstructionCandidate, ...]:
        return tuple(
            InstructionCandidate(
                candidate_id=value["candidate_id"],
                competency_id=value["competency_id"],
                prerequisites=tuple(value.get("prerequisites", [])),
                goal_relevance=value.get("goal_relevance", 1.0),
                action_type=value.get("action_type", "practice"),
                assistance_target=value.get("assistance_target"),
                representation_id=value.get("representation_id"),
                learning_operation=value.get("learning_operation"),
            )
            for value in self.fixture["candidates"]
        )

    def test_fixture_baseline_selects_expected_candidate_and_hard_exclusions(self):
        proposal = propose_instruction_baseline(self.snapshot(), self.candidates())
        self.assertIsNotNone(proposal.selected)
        self.assertEqual(
            proposal.selected.candidate_id,
            self.fixture["expected"]["selected_candidate_id"],
        )
        exclusions = {value.candidate_id: value.reason_code for value in proposal.exclusions}
        self.assertEqual(exclusions, self.fixture["expected"]["excluded_reason_by_candidate"])

    def test_snapshot_keeps_canonical_evidence_refs_and_versions(self):
        snapshot = self.snapshot()
        payload = snapshot.to_dict()
        self.assertEqual(payload["snapshot_version"], "0.1.0")
        self.assertEqual(payload["capabilities"]["algo.two_candidate_state"]["assistance_level"], "A2")
        self.assertIn("checkpoint-fixture-001", snapshot.evidence_ids())
        self.assertIn("assessment-fixture-update-order", snapshot.evidence_ids())

    def test_snapshot_rejects_noncanonical_assistance(self):
        payload = dict(self.fixture["snapshot"])
        payload["capabilities"] = dict(payload["capabilities"])
        payload["capabilities"]["algo.two_candidate_state"] = {
            "status": "partial",
            "assistance_level": "light_hint",
            "evidence_ids": ["assessment-x"],
        }
        with self.assertRaisesRegex(ValueError, "unsupported assistance level"):
            LearnerSnapshot.from_mapping(payload)

    def test_decision_proposal_cannot_select_an_excluded_candidate(self):
        with self.assertRaisesRegex(ValueError, "selected candidate cannot be excluded"):
            DecisionProposal(
                component_name="bad-selector",
                implementation="tests.bad_selector",
                component_version="0.1.0",
                mode="shadow",
                phase="instruction",
                candidates=("item-1",),
                exclusions=(CandidateExclusion("item-1", "prerequisite_not_met"),),
                selected=SelectedAction("item-1", "practice"),
                rationale="invalid fixture intentionally selects an excluded item",
            )

    def test_shadow_event_is_derived_and_references_canonical_sources(self):
        snapshot = self.snapshot()
        proposal = propose_instruction_baseline(snapshot, self.candidates())
        event = shadow_learning_event(snapshot, proposal)
        self.assertEqual(event["evidence_class"], "derived")
        self.assertEqual(event["event_type"], "controller_shadow_proposal")
        self.assertEqual(event["payload_version"], "p2-shadow-0.1.0")
        self.assertIn(snapshot.checkpoint_id, event["source_ids"])
        self.assertEqual(event["payload"]["proposal"]["mode"], "shadow")


class P2ShadowPersistenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)

    def tearDown(self):
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def test_shadow_proposal_persists_through_existing_learning_event_path(self):
        session = self.service.start_session(
            idempotency_key="p2-session",
            subject_id="subject-p2",
            project_id="dsa-python",
            domain_id="dsa",
        )
        observed = self.service.record_learning_event(
            idempotency_key="p2-observed",
            session_id=session["session_id"],
            subject_id="subject-p2",
            evidence_class="observed",
            event_type="state_prediction_attempted",
            payload={"task_id": "item-update-order-v1"},
        )
        snapshot = LearnerSnapshot.from_mapping(
            {
                "subject_id": "subject-p2",
                "checkpoint_id": None,
                "phase": "instruction",
                "current_focus": "two-candidate update order",
                "capabilities": {
                    "algo.two_candidate_update_order": {
                        "status": "partial",
                        "assistance_level": "A1",
                        "evidence_ids": [observed["event_id"]],
                    }
                },
            }
        )
        proposal = propose_instruction_baseline(
            snapshot,
            (
                InstructionCandidate(
                    candidate_id="item-update-order-v2",
                    competency_id="algo.two_candidate_update_order",
                    goal_relevance=1.0,
                    action_type="state_prediction",
                    assistance_target="A0",
                    representation_id="state-table-v1",
                    learning_operation="predict",
                ),
            ),
        )
        shadow = shadow_learning_event(snapshot, proposal)
        persisted = self.service.record_learning_event(
            idempotency_key="p2-shadow",
            session_id=session["session_id"],
            subject_id="subject-p2",
            **shadow,
        )
        self.assertTrue(persisted["created"])
        self.assertEqual(persisted["evidence_class"], "derived")

        row = self.service.repository.connection.execute(
            "SELECT event_type, payload_version, source_ids_json FROM learning_events WHERE event_id = ?",
            (persisted["event_id"],),
        ).fetchone()
        self.assertEqual(row["event_type"], "controller_shadow_proposal")
        self.assertEqual(row["payload_version"], "p2-shadow-0.1.0")
        self.assertEqual(json.loads(row["source_ids_json"]), [observed["event_id"]])


if __name__ == "__main__":
    unittest.main()
