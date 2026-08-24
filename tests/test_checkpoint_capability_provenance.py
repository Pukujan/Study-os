import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.errors import StudyOSError  # noqa: E402


class CheckpointCapabilityProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)
        self.session = self.service.start_session(
            idempotency_key="session-1",
            subject_id="subject-001",
            project_id="dsa-python",
            domain_id="dsa",
        )
        self.event = self.service.record_learning_event(
            idempotency_key="event-1",
            session_id=self.session["session_id"],
            subject_id="subject-001",
            evidence_class="observed",
            event_type="prediction",
            payload={"result": "synthetic"},
        )

    def tearDown(self):
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def checkpoint(self, *, key: str, evidence_ids: list[str]) -> dict:
        return self.service.checkpoint(
            idempotency_key=key,
            subject_id="subject-001",
            source_session_ids=[self.session["session_id"]],
            evidence_ids=evidence_ids,
            capability_state={"state_prediction": "pass_unaided", "python_implementation": "not_tested"},
            assistance_state={"level": "none"},
            resume={"current_focus": "sliding-window", "next_action": "continue"},
        )

    def test_pass_unaided_requires_cited_unaided_assessment(self):
        with self.assertRaises(StudyOSError) as raised:
            self.checkpoint(key="checkpoint-no-assessment", evidence_ids=[self.event["event_id"]])
        self.assertEqual(raised.exception.category, "integrity_error")
        self.assertEqual(self.service.db.connection.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0], 0)
        self.assertEqual(
            self.service.db.connection.execute(
                "SELECT COUNT(*) FROM idempotency_records WHERE operation_name = 'checkpoint'"
            ).fetchone()[0],
            0,
        )

        assisted = self.service.record_assessment(
            idempotency_key="assessment-assisted",
            session_id=self.session["session_id"],
            subject_id="subject-001",
            capability="state_prediction",
            result="pass",
            assistance_level="representation_visible",
            evidence_ids=[self.event["event_id"]],
        )
        with self.assertRaises(StudyOSError) as raised:
            self.checkpoint(key="checkpoint-assisted", evidence_ids=[assisted["assessment_id"]])
        self.assertEqual(raised.exception.category, "integrity_error")
        self.assertEqual(self.service.db.connection.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0], 0)

        unaided = self.service.record_assessment(
            idempotency_key="assessment-unaided",
            session_id=self.session["session_id"],
            subject_id="subject-001",
            capability="state_prediction",
            result="pass",
            assistance_level="none",
            evidence_ids=[self.event["event_id"]],
        )
        checkpoint = self.checkpoint(key="checkpoint-unaided", evidence_ids=[unaided["assessment_id"]])
        self.assertTrue(checkpoint["accepted"])
        self.assertEqual(self.service.resume(subject_id="subject-001")["capability_state"]["state_prediction"], "pass_unaided")


if __name__ == "__main__":
    unittest.main()
