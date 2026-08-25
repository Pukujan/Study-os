import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.config import RuntimeConfig
from study_os.services.runtime import StudyOSService


class SemanticRuntimeOverrideTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.service = StudyOSService(RuntimeConfig(root=root))
        self.subject = "learner-1"
        started = self.service.start_session(
            idempotency_key="start-1", subject_id=self.subject, project_id="p", domain_id="d"
        )
        self.session = started["session_id"]
        attempt = self.service.record_attempt(
            idempotency_key="attempt-1", session_id=self.session, subject_id=self.subject,
            task_id="task-1", response={"answer": 1}, assistance_level="none"
        )
        self.attempt_id = attempt["attempt_id"]
        baseline = self.service.record_assessment(
            idempotency_key="baseline-assessment", session_id=self.session, subject_id=self.subject,
            capability="cap-1", result="pass_unaided", assistance_level="none", evidence_ids=[self.attempt_id]
        )
        self.baseline_assessment_id = baseline["assessment_id"]
        checkpoint = self.service.checkpoint(
            idempotency_key="checkpoint-1", subject_id=self.subject,
            source_session_ids=[self.session], evidence_ids=[self.baseline_assessment_id],
            capability_state={"cap-1": "pass_unaided"}, assistance_state={"cap-1": "A0"},
            resume={"current_focus": "cap-1", "do_not_reteach": ["cap-0"], "next_action": "probe cap-1"},
            retention_due_at="2026-08-26T06:00:00Z"
        )
        self.checkpoint_id = checkpoint["checkpoint_id"]

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def test_assessment_atomically_completes_scheduled_probe(self):
        probe = self.service.schedule_retention_probe(
            idempotency_key="probe-1", subject_id=self.subject, concept_id="cap-1",
            due_at="2026-08-26T06:00:00Z", source_checkpoint_id=self.checkpoint_id
        )
        result = self.service.record_assessment(
            idempotency_key="assessment-1", session_id=self.session, subject_id=self.subject,
            capability="cap-1", result="pass_delayed", assistance_level="none",
            evidence_ids=[self.attempt_id], retention_probe_id=probe["retention_probe_id"]
        )
        self.assertEqual(result["retention_probe_status"], "completed")
        self.assertIsNone(self.service.get_next_probe(subject_id=self.subject)["probe"])
        with self.service.repository.transaction(immediate=False) as connection:
            row = connection.execute(
                "SELECT status, result_json FROM retention_probes WHERE retention_probe_id = ?",
                (probe["retention_probe_id"],),
            ).fetchone()
            self.assertEqual(row["status"], "completed")
            self.assertIn(result["assessment_id"], row["result_json"])

    def test_probe_mismatch_rolls_back_assessment(self):
        probe = self.service.schedule_retention_probe(
            idempotency_key="probe-2", subject_id=self.subject, concept_id="cap-1",
            due_at="2026-08-26T06:00:00Z", source_checkpoint_id=self.checkpoint_id
        )
        with self.assertRaises(Exception):
            self.service.record_assessment(
                idempotency_key="assessment-bad", session_id=self.session, subject_id=self.subject,
                capability="other-cap", result="pass_delayed", assistance_level="none",
                evidence_ids=[self.attempt_id], retention_probe_id=probe["retention_probe_id"]
            )
        with self.service.repository.transaction(immediate=False) as connection:
            count = connection.execute("SELECT COUNT(*) AS n FROM assessments WHERE idempotency_key = 'assessment-bad'").fetchone()["n"]
            status = connection.execute(
                "SELECT status FROM retention_probes WHERE retention_probe_id = ?", (probe["retention_probe_id"],)
            ).fetchone()["status"]
        self.assertEqual(count, 0)
        self.assertEqual(status, "scheduled")

    def test_resume_projects_checkpoint_and_live_retention_context(self):
        self.service.record_representation_intervention(
            idempotency_key="repr-1", session_id=self.session, subject_id=self.subject,
            representation_family="state_table", operation="compare", representation_version="1.0.0",
            target_bottleneck="state_tracking"
        )
        probe = self.service.schedule_retention_probe(
            idempotency_key="probe-3", subject_id=self.subject, concept_id="cap-1",
            due_at="2026-08-26T06:00:00Z", source_checkpoint_id=self.checkpoint_id
        )
        resumed = self.service.resume(subject_id=self.subject)
        self.assertEqual(resumed["do_not_reteach"], ["cap-0"])
        self.assertEqual(resumed["retention_due_at"], "2026-08-26T06:00:00Z")
        self.assertEqual(resumed["next_retention_probe"]["retention_probe_id"], probe["retention_probe_id"])
        self.assertEqual(resumed["recent_representation_history"][0]["representation_family"], "state_table")


if __name__ == "__main__":
    unittest.main()
