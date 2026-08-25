import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.adaptive.baseline import InstructionCandidate, propose_instruction_baseline  # noqa: E402
from study_os.adaptive.contracts import CapabilityState, LearnerSnapshot, shadow_learning_event  # noqa: E402
from study_os.adaptive.shadow_audit import shadow_outcome_learning_event  # noqa: E402


class ShadowOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.service = StudyOSService(RuntimeConfig.from_env(self.temp_dir.name))

    def tearDown(self):
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def test_proposal_and_actual_assessment_are_linked_without_new_schema(self):
        session = self.service.start_session(
            idempotency_key="shadow-outcome-session",
            subject_id="subject-shadow-outcome",
            project_id="dsa-python",
            domain_id="dsa",
        )
        attempt = self.service.record_attempt(
            idempotency_key="shadow-outcome-attempt-1",
            session_id=session["session_id"],
            subject_id="subject-shadow-outcome",
            task_id="re.update-order.002",
            response="old largest should move to second first",
            assistance_level="A0",
        )
        assessment = self.service.record_assessment(
            idempotency_key="shadow-outcome-assessment-1",
            session_id=session["session_id"],
            subject_id="subject-shadow-outcome",
            capability="dsa.extrema.update_order",
            result="pass_unaided",
            assistance_level="A0",
            evidence_ids=[attempt["attempt_id"]],
        )
        snapshot = LearnerSnapshot(
            subject_id="subject-shadow-outcome",
            checkpoint_id=None,
            phase="instruction",
            current_focus="update ordering",
            capabilities={
                "dsa.extrema.update_order": CapabilityState(
                    status="pass_unaided",
                    assistance_level="A0",
                    evidence_ids=(assessment["assessment_id"],),
                )
            },
        )
        proposal = propose_instruction_baseline(
            snapshot,
            (
                InstructionCandidate(
                    candidate_id="re.implement.001",
                    competency_id="dsa.extrema.second_largest_implement",
                    prerequisites=("dsa.extrema.update_order",),
                    goal_relevance=1.0,
                    action_type="manual_code_blank",
                    assistance_target="A1",
                    representation_id="python_code",
                    learning_operation="translate",
                ),
            ),
        )
        proposal_event = self.service.record_learning_event(
            idempotency_key="shadow-outcome-proposal-event",
            session_id=session["session_id"],
            subject_id="subject-shadow-outcome",
            **shadow_learning_event(snapshot, proposal),
        )

        outcome_args = shadow_outcome_learning_event(
            proposal,
            proposal_event_id=proposal_event["event_id"],
            assessment_id=assessment["assessment_id"],
            actual_candidate_id="re.update-order.002",
            capability="dsa.extrema.update_order",
            result="pass_unaided",
            assistance_level="A0",
        )
        outcome_event = self.service.record_learning_event(
            idempotency_key="shadow-outcome-actual-event",
            session_id=session["session_id"],
            subject_id="subject-shadow-outcome",
            **outcome_args,
        )

        row = self.service.repository.connection.execute(
            "SELECT event_type, payload_json, source_ids_json FROM learning_events WHERE event_id = ?",
            (outcome_event["event_id"],),
        ).fetchone()
        payload = json.loads(row["payload_json"])
        sources = json.loads(row["source_ids_json"])
        self.assertEqual(row["event_type"], "controller_shadow_outcome")
        self.assertEqual(sources, [proposal_event["event_id"], assessment["assessment_id"]])
        self.assertEqual(payload["proposed_candidate_id"], "re.implement.001")
        self.assertEqual(payload["actual_candidate_id"], "re.update-order.002")
        self.assertFalse(payload["proposal_followed"])
        self.assertEqual(payload["result"], "pass_unaided")

    def test_non_shadow_proposal_cannot_be_logged_as_shadow_outcome(self):
        snapshot = LearnerSnapshot(subject_id="s", checkpoint_id=None, phase="instruction")
        proposal = propose_instruction_baseline(
            snapshot,
            (InstructionCandidate(candidate_id="i", competency_id="c", goal_relevance=1.0),),
        )
        live_like = type(proposal)(
            component_name=proposal.component_name,
            implementation=proposal.implementation,
            component_version=proposal.component_version,
            mode="advisory",
            phase=proposal.phase,
            candidates=proposal.candidates,
            exclusions=proposal.exclusions,
            scores=proposal.scores,
            selected=proposal.selected,
            rationale=proposal.rationale,
            expected_evidence=proposal.expected_evidence,
        )
        with self.assertRaisesRegex(ValueError, "shadow proposal"):
            shadow_outcome_learning_event(
                live_like,
                proposal_event_id="event-1",
                assessment_id="assessment-1",
                actual_candidate_id="i",
                capability="c",
                result="pass_unaided",
                assistance_level="A0",
            )


if __name__ == "__main__":
    unittest.main()
