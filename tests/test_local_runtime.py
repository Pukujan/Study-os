import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.db.connection import LATEST_SCHEMA_VERSION, migrate_database  # noqa: E402
from study_os.errors import StudyOSError  # noqa: E402
from study_os.mcp.server import MCPServer  # noqa: E402


class LocalRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)

    def tearDown(self):
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def fixture_session(self):
        session = self.service.start_session(
            idempotency_key="session-1",
            subject_id="subject-001",
            project_id="dsa-python",
            domain_id="dsa",
        )
        artifact = self.service.capture_evidence(
            session_id=session["session_id"],
            subject_id="subject-001",
            content=b"synthetic public-safe evidence",
            media_type="text/plain",
        )
        event = self.service.record_learning_event(
            idempotency_key="event-1",
            session_id=session["session_id"],
            subject_id="subject-001",
            evidence_class="observed",
            event_type="confusion_reported",
            payload={"summary": "uncertain about pointer movement"},
        )
        return session, artifact, event

    def test_empty_database_migrates_and_repeat_is_safe(self):
        self.service.close()
        db_path = self.config.db_path
        db_path.unlink()
        self.assertEqual(migrate_database(db_path), LATEST_SCHEMA_VERSION)
        self.assertEqual(migrate_database(db_path), LATEST_SCHEMA_VERSION)
        connection = sqlite3.connect(db_path)
        try:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], LATEST_SCHEMA_VERSION)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM schema_meta").fetchone()[0], 2)
        finally:
            connection.close()
        self.service = StudyOSService(self.config)
        self.assertTrue(self.service.doctor()["healthy"])

    def test_idempotent_event_retry_and_conflicting_reuse(self):
        session, _, _ = self.fixture_session()
        request = dict(
            idempotency_key="retry-key",
            session_id=session["session_id"],
            subject_id="subject-001",
            evidence_class="observed",
            event_type="predict",
            payload={"prediction": "right"},
        )
        first = self.service.record_learning_event(**request)
        second = self.service.record_learning_event(**request)
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(first["event_id"], second["event_id"])
        count = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM learning_events WHERE event_id = ?", (first["event_id"],)
        ).fetchone()[0]
        self.assertEqual(count, 1)
        request["event_type"] = "assessment_passed"
        with self.assertRaises(StudyOSError) as raised:
            self.service.record_learning_event(**request)
        self.assertEqual(raised.exception.category, "conflict")

    def test_derived_claim_requires_resolvable_evidence(self):
        session, _, _ = self.fixture_session()
        with self.assertRaises(StudyOSError) as raised:
            self.service.record_learning_event(
                idempotency_key="derived-1",
                session_id=session["session_id"],
                subject_id="subject-001",
                evidence_class="derived",
                event_type="diagnosis",
                payload={"evidence_ids": ["does-not-exist"], "claim": "unsupported"},
            )
        self.assertEqual(raised.exception.category, "integrity_error")

    def test_evidence_mutation_is_detected_by_doctor(self):
        _, artifact, _ = self.fixture_session()
        evidence_path = self.config.evidence_root / artifact["storage_path"]
        evidence_path.write_bytes(b"tampered")
        health = self.service.doctor()
        self.assertFalse(health["healthy"])
        self.assertFalse(health["checks"]["raw_evidence_integrity"]["healthy"])

    def test_checkpoint_pointer_and_resume_are_durable(self):
        session, artifact, event = self.fixture_session()
        checkpoint = self.service.checkpoint(
            idempotency_key="checkpoint-1",
            subject_id="subject-001",
            source_session_ids=[session["session_id"]],
            evidence_ids=[artifact["artifact_id"], event["event_id"]],
            capability_state={"state_prediction": "not_tested", "python_implementation": "not_tested"},
            assistance_state={"level": "none"},
            resume={"current_focus": "sliding-window", "next_action": "predict the next trace"},
        )
        self.assertEqual(self.service.resume(subject_id="subject-001")["checkpoint_id"], checkpoint["checkpoint_id"])
        self.assertTrue(self.service.status(subject_id="subject-001")["current_checkpoint_id"])

        # Simulate an externally corrupted pointer; FK enforcement remains on
        # for normal writes, while this fixture models disk/admin corruption.
        self.service.close()
        connection = sqlite3.connect(self.config.db_path)
        try:
            connection.execute("PRAGMA foreign_keys = OFF")
            connection.execute(
                "UPDATE subject_current_checkpoint SET checkpoint_id = 'missing-checkpoint' WHERE subject_id = 'subject-001'"
            )
            connection.commit()
        finally:
            connection.close()
        self.service = StudyOSService(self.config)
        self.assertFalse(self.service.doctor()["healthy"])

    def test_checkpoint_advancement_requires_current_pointer_expectation(self):
        session, artifact, event = self.fixture_session()
        first = self.service.checkpoint(
            idempotency_key="checkpoint-current-1",
            subject_id="subject-001",
            source_session_ids=[session["session_id"]],
            evidence_ids=[artifact["artifact_id"], event["event_id"]],
            capability_state={"state_prediction": "not_tested"},
            assistance_state={},
            resume={"current_focus": "trace", "next_action": "retest"},
        )
        with self.assertRaises(StudyOSError) as raised:
            self.service.checkpoint(
                idempotency_key="checkpoint-current-2",
                subject_id="subject-001",
                source_session_ids=[session["session_id"]],
                evidence_ids=[artifact["artifact_id"], event["event_id"]],
                capability_state={"state_prediction": "not_tested"},
                assistance_state={},
                resume={"current_focus": "trace", "next_action": "transfer"},
            )
        self.assertEqual(raised.exception.category, "conflict")
        second = self.service.checkpoint(
            idempotency_key="checkpoint-current-3",
            subject_id="subject-001",
            source_session_ids=[session["session_id"]],
            evidence_ids=[artifact["artifact_id"], event["event_id"]],
            capability_state={"state_prediction": "not_tested"},
            assistance_state={},
            resume={
                "current_focus": "trace",
                "next_action": "transfer",
                "expected_current_checkpoint_id": first["checkpoint_id"],
            },
        )
        self.assertNotEqual(first["checkpoint_id"], second["checkpoint_id"])

    def test_all_semantic_operations_have_durable_results(self):
        session, artifact, event = self.fixture_session()
        attempt = self.service.record_attempt(
            idempotency_key="attempt-1",
            session_id=session["session_id"],
            subject_id="subject-001",
            task_id="sliding-window-trace-1",
            response={"answer": "right"},
            assistance_level="representation_visible",
        )
        assessment = self.service.record_assessment(
            idempotency_key="assessment-1",
            session_id=session["session_id"],
            subject_id="subject-001",
            capability="state_prediction",
            result="pass",
            assistance_level="none",
            evidence_ids=[attempt["attempt_id"]],
        )
        intervention = self.service.record_representation_intervention(
            idempotency_key="intervention-1",
            session_id=session["session_id"],
            subject_id="subject-001",
            representation_family="deterministic_state_trace",
            operation="predict",
            representation_version="0.1.0",
            target_bottleneck="invariant_to_control_flow",
        )
        outcome = self.service.record_representation_outcome(
            idempotency_key="outcome-1",
            intervention_id=intervention["intervention_id"],
            subject_id="subject-001",
            evidence_score=3,
            evidence_ids=[assessment["assessment_id"]],
        )
        checkpoint = self.service.checkpoint(
            idempotency_key="checkpoint-ops",
            subject_id="subject-001",
            source_session_ids=[session["session_id"]],
            evidence_ids=[artifact["artifact_id"], event["event_id"], assessment["assessment_id"], outcome["outcome_id"]],
            capability_state={"state_prediction": "pass_unaided", "python_implementation": "not_tested"},
            assistance_state={"level": "none"},
            resume={"current_focus": "sliding-window", "next_action": "implement without scaffold"},
        )
        probe = self.service.schedule_retention_probe(
            idempotency_key="probe-1",
            subject_id="subject-001",
            concept_id="sliding-window",
            due_at="2026-08-25T00:00:00Z",
            source_checkpoint_id=checkpoint["checkpoint_id"],
        )
        self.assertEqual(self.service.get_next_probe(subject_id="subject-001")["probe"]["retention_probe_id"], probe["retention_probe_id"])
        exported = self.service.export_fossil(
            idempotency_key="export-1",
            subject_id="subject-001",
            artifact_type="curated_learning_trajectory",
            source_ids=[checkpoint["checkpoint_id"]],
        )
        self.assertTrue(exported["created"])
        self.assertTrue(self.service.doctor()["healthy"])

    def test_backup_restore_reproduces_checkpoint_and_evidence(self):
        session, artifact, event = self.fixture_session()
        checkpoint = self.service.checkpoint(
            idempotency_key="checkpoint-backup",
            subject_id="subject-001",
            source_session_ids=[session["session_id"]],
            evidence_ids=[artifact["artifact_id"], event["event_id"]],
            capability_state={"state_prediction": "not_tested", "python_implementation": "not_tested"},
            assistance_state={"level": "none"},
            resume={"current_focus": "sliding-window", "next_action": "resume trace"},
        )
        backup = self.service.backup()
        self.service.close()
        os.replace(self.config.db_path, self.config.root / "db-moved.sqlite3")
        os.replace(self.config.evidence_root, self.config.root / "evidence-moved")
        self.service = StudyOSService(self.config)
        restored = self.service.restore(backup["backup_path"])
        self.assertTrue(restored["restored"])
        resumed = self.service.resume(subject_id="subject-001")
        self.assertEqual(resumed["checkpoint_id"], checkpoint["checkpoint_id"])
        self.assertTrue(self.service.evidence.verify(artifact["storage_path"], artifact["sha256"]))
        self.assertTrue(self.service.doctor()["healthy"])

    def test_mcp_exposes_exact_contract_and_no_generic_tools(self):
        server = MCPServer(self.service)
        contract = json.loads((ROOT / "contracts/study-os-mcp-tools.v0.1.json").read_text(encoding="utf-8"))
        expected = [tool["name"] for tool in contract["tools"]]
        self.assertEqual(server.list_tool_names(), expected)
        self.assertEqual(set(server.list_tool_names()), set(expected))
        self.assertFalse(any(any(fragment in name.lower() for fragment in ("sql", "shell", "exec", "write_file", "filesystem")) for name in expected))
        result = server.call_tool("doctor")
        self.assertIn("healthy", result)
        error = server.call_tool("run_sql", {})
        self.assertEqual(error["error"]["category"], "validation_error")

    def test_malformed_mcp_payload_maps_to_stable_validation_error(self):
        server = MCPServer(self.service)
        error = server.call_tool("start_session", {"subject_id": "subject-001"})
        self.assertEqual(error["error"]["category"], "validation_error")
        self.assertFalse(error["error"]["retryable"])

    def test_stale_schema_and_missing_evidence_root_are_unhealthy(self):
        self.service.db.connection.execute("PRAGMA user_version = 999")
        self.assertFalse(self.service.doctor()["healthy"])
        self.service.db.connection.execute("PRAGMA user_version = 1")
        shutil.rmtree(self.config.evidence_root)
        health = self.service.doctor()
        self.assertFalse(health["healthy"])
        self.assertFalse(health["checks"]["evidence_root"]["healthy"])

    def test_invalid_representation_version_is_rejected(self):
        session, _, _ = self.fixture_session()
        with self.assertRaises(StudyOSError) as raised:
            self.service.record_representation_intervention(
                idempotency_key="bad-version",
                session_id=session["session_id"],
                subject_id="subject-001",
                representation_family="deterministic_state_trace",
                operation="predict",
                representation_version="version-one",
                target_bottleneck="invariant",
            )
        self.assertEqual(raised.exception.category, "validation_error")

    def test_checkpoint_failure_rolls_back_checkpoint_and_pointer(self):
        session, artifact, event = self.fixture_session()
        with patch.object(self.service, "_idempotency_record", side_effect=RuntimeError("simulated interruption")):
            with self.assertRaises(RuntimeError):
                self.service.checkpoint(
                    idempotency_key="checkpoint-interrupted",
                    subject_id="subject-001",
                    source_session_ids=[session["session_id"]],
                    evidence_ids=[artifact["artifact_id"], event["event_id"]],
                    capability_state={"state_prediction": "not_tested"},
                    assistance_state={},
                    resume={"current_focus": "trace", "next_action": "retry"},
                )
        self.assertEqual(self.service.db.connection.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0], 0)
        self.assertEqual(self.service.db.connection.execute("SELECT COUNT(*) FROM subject_current_checkpoint").fetchone()[0], 0)

    def test_partial_backup_is_rejected(self):
        with tempfile.TemporaryDirectory() as partial:
            partial_path = Path(partial)
            (partial_path / "study-os.sqlite3").write_bytes(b"not a database")
            (partial_path / "evidence").mkdir()
            with self.assertRaises(StudyOSError) as raised:
                self.service.restore(partial_path)
            self.assertEqual(raised.exception.category, "validation_error")

    def test_database_busy_is_reported_as_retryable_unavailable(self):
        locker = sqlite3.connect(self.config.db_path, timeout=0.1, isolation_level=None)
        try:
            locker.execute("BEGIN EXCLUSIVE")
            self.service.db.connection.execute("PRAGMA busy_timeout = 100")
            with self.assertRaises(StudyOSError) as raised:
                self.service.start_session(
                    idempotency_key="locked-session",
                    subject_id="subject-001",
                    project_id="dsa-python",
                    domain_id="dsa",
                )
            self.assertEqual(raised.exception.category, "unavailable")
            self.assertTrue(raised.exception.retryable)
        finally:
            locker.rollback()
            locker.close()


if __name__ == "__main__":
    unittest.main()
