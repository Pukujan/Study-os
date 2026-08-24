import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.errors import StudyOSError  # noqa: E402


class P0ReviewIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)

    def tearDown(self):
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def start_session(self, subject_id: str, key: str) -> dict:
        return self.service.start_session(
            idempotency_key=key,
            subject_id=subject_id,
            project_id="dsa-python",
            domain_id="dsa",
        )

    def observed_event(self, session_id: str, subject_id: str, key: str) -> dict:
        return self.service.record_learning_event(
            idempotency_key=key,
            session_id=session_id,
            subject_id=subject_id,
            evidence_class="observed",
            event_type="prediction",
            payload={"result": "synthetic"},
        )

    def test_cross_subject_evidence_cannot_support_derived_state(self):
        session_a = self.start_session("subject-a", "session-a")
        session_b = self.start_session("subject-b", "session-b")
        event_a = self.observed_event(session_a["session_id"], "subject-a", "event-a")

        with self.assertRaises(StudyOSError) as raised:
            self.service.record_learning_event(
                idempotency_key="derived-b",
                session_id=session_b["session_id"],
                subject_id="subject-b",
                evidence_class="derived",
                event_type="diagnosis",
                payload={"evidence_ids": [event_a["event_id"]], "claim": "wrong subject"},
            )

        self.assertEqual(raised.exception.category, "integrity_error")
        self.assertEqual(
            self.service.db.connection.execute(
                "SELECT COUNT(*) FROM learning_events WHERE subject_id = 'subject-b' AND evidence_class = 'derived'"
            ).fetchone()[0],
            0,
        )

    def test_assessment_can_reference_same_subject_intervention(self):
        session = self.start_session("subject-001", "session-1")
        event = self.observed_event(session["session_id"], "subject-001", "event-1")
        intervention = self.service.record_representation_intervention(
            idempotency_key="intervention-1",
            session_id=session["session_id"],
            subject_id="subject-001",
            representation_family="deterministic_state_trace",
            operation="predict",
            representation_version="0.1.0",
            target_bottleneck="problem_to_state",
        )

        assessment = self.service.record_assessment(
            idempotency_key="assessment-1",
            session_id=session["session_id"],
            subject_id="subject-001",
            capability="state_prediction",
            result="pass",
            assistance_level="representation_visible",
            evidence_ids=[event["event_id"], intervention["intervention_id"]],
        )

        self.assertTrue(assessment["created"])

    def test_representation_outcome_requires_behavioral_assessment(self):
        session = self.start_session("subject-001", "session-1")
        event = self.observed_event(session["session_id"], "subject-001", "event-1")
        intervention = self.service.record_representation_intervention(
            idempotency_key="intervention-1",
            session_id=session["session_id"],
            subject_id="subject-001",
            representation_family="deterministic_state_trace",
            operation="predict",
            representation_version="0.1.0",
            target_bottleneck="problem_to_state",
        )

        with self.assertRaises(StudyOSError) as raised:
            self.service.record_representation_outcome(
                idempotency_key="outcome-without-assessment",
                intervention_id=intervention["intervention_id"],
                subject_id="subject-001",
                evidence_score=3,
                evidence_ids=[event["event_id"]],
            )
        self.assertEqual(raised.exception.category, "integrity_error")

        assessment = self.service.record_assessment(
            idempotency_key="assessment-1",
            session_id=session["session_id"],
            subject_id="subject-001",
            capability="state_prediction",
            result="pass",
            assistance_level="none",
            evidence_ids=[event["event_id"]],
        )
        outcome = self.service.record_representation_outcome(
            idempotency_key="outcome-with-assessment",
            intervention_id=intervention["intervention_id"],
            subject_id="subject-001",
            evidence_score=3,
            evidence_ids=[assessment["assessment_id"]],
        )
        self.assertTrue(outcome["created"])

    def test_doctor_detects_missing_checkpoint_source_session(self):
        session = self.start_session("subject-001", "session-1")
        event = self.observed_event(session["session_id"], "subject-001", "event-1")
        checkpoint = self.service.checkpoint(
            idempotency_key="checkpoint-1",
            subject_id="subject-001",
            source_session_ids=[session["session_id"]],
            evidence_ids=[event["event_id"]],
            capability_state={"state_prediction": "not_tested"},
            assistance_state={},
            resume={"current_focus": "sliding-window", "next_action": "run baseline probe"},
        )
        self.assertTrue(checkpoint["accepted"])

        self.service.db.connection.execute(
            "UPDATE checkpoints SET source_session_ids_json = '[\"missing-session\"]' WHERE checkpoint_id = ?",
            (checkpoint["checkpoint_id"],),
        )
        health = self.service.doctor()
        self.assertFalse(health["healthy"])
        self.assertFalse(health["checks"]["checkpoint_sources"]["healthy"])

    def test_restore_swap_failure_recovers_previous_runtime(self):
        first = self.start_session("subject-001", "session-before-backup")
        self.observed_event(first["session_id"], "subject-001", "event-before-backup")
        backup = self.service.backup()
        second = self.start_session("subject-001", "session-after-backup")
        before_count = self.service.db.connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

        real_replace = os.replace
        calls = {"count": 0}

        def fail_fourth_replace(src, dst):
            calls["count"] += 1
            if calls["count"] == 4:
                raise OSError("simulated restore swap interruption")
            return real_replace(src, dst)

        with patch("study_os.services.runtime.os.replace", side_effect=fail_fourth_replace):
            with self.assertRaises(OSError):
                self.service.restore(backup["backup_path"])

        self.assertEqual(
            self.service.db.connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0],
            before_count,
        )
        self.assertEqual(self.service.status(subject_id="subject-001")["current_session_id"], second["session_id"])
        self.assertTrue(self.service.doctor()["healthy"])

    def test_export_failure_leaves_no_orphan_artifact_and_retry_succeeds(self):
        session = self.start_session("subject-001", "session-1")
        event = self.observed_event(session["session_id"], "subject-001", "event-1")
        export_dir = self.config.exports_root / "fossil"

        with patch.object(self.service, "_idempotency_record", side_effect=RuntimeError("simulated commit path failure")):
            with self.assertRaises(RuntimeError):
                self.service.export_fossil(
                    idempotency_key="export-1",
                    subject_id="subject-001",
                    artifact_type="curated_learning_trajectory",
                    source_ids=[event["event_id"]],
                )

        self.assertEqual(self.service.db.connection.execute("SELECT COUNT(*) FROM fossil_exports").fetchone()[0], 0)
        self.assertEqual(list(export_dir.glob("*.json")) if export_dir.exists() else [], [])

        exported = self.service.export_fossil(
            idempotency_key="export-1",
            subject_id="subject-001",
            artifact_type="curated_learning_trajectory",
            source_ids=[event["event_id"]],
        )
        self.assertTrue(exported["created"])
        self.assertEqual(self.service.db.connection.execute("SELECT COUNT(*) FROM fossil_exports").fetchone()[0], 1)
        self.assertEqual(len(list(export_dir.glob("*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
