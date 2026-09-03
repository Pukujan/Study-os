from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.application.contracts import ResumeLearningContextRequest  # noqa: E402
from study_os.application.service import ApplicationService  # noqa: E402
from study_os.mcp.server import MCPServer  # noqa: E402


class CrossChatContinuityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)

    def tearDown(self) -> None:
        self.service.close()
        self.temp_dir.cleanup()

    def session(self, subject_id: str, key: str) -> dict:
        return self.service.start_session(
            idempotency_key=key,
            subject_id=subject_id,
            project_id=f"project-{subject_id}",
            domain_id=f"domain-{subject_id}",
        )

    def turn(self, session: dict, subject_id: str, key: str, role: str, content: str) -> dict:
        return self.service.append_conversation_turn(
            idempotency_key=key,
            session_id=session["session_id"],
            subject_id=subject_id,
            role=role,
            content=content,
        )

    def checkpoint(self, session: dict, subject_id: str, evidence_id: str, key: str) -> dict:
        return self.service.checkpoint(
            idempotency_key=key,
            subject_id=subject_id,
            source_session_ids=[session["session_id"]],
            evidence_ids=[evidence_id],
            capability_state={"state_prediction": "not_yet_assessed"},
            assistance_state={"level": "guided"},
            resume={"current_focus": "dictionaries", "next_action": "try Two Sum"},
        )

    def test_ct1_existing_checkpoint_resumes_normally(self) -> None:
        session = self.session("subject-a", "session-a")
        turn = self.turn(session, "subject-a", "turn-a", "user", "Dictionaries map keys to values.")
        self.checkpoint(session, "subject-a", turn["artifact_id"], "checkpoint-a")

        result = self.service.resume_learning_context(subject_id="subject-a")

        self.assertEqual(result["continuity_status"], "checkpoint_only")
        self.assertEqual(result["checkpoint"]["current_focus"], "dictionaries")
        self.assertEqual(result["recent_evidence"]["messages"], [])

    def test_ct2_no_checkpoint_uses_durable_prior_turns(self) -> None:
        session = self.session("subject-a", "session-a")
        user = self.turn(session, "subject-a", "turn-a", "user", "I am working on Two Sum dictionaries.")
        assistant = self.turn(session, "subject-a", "turn-b", "assistant", "Use a map from value to index.")

        result = self.service.resume_learning_context(subject_id="subject-a")

        self.assertEqual(result["continuity_status"], "evidence_only")
        self.assertEqual([item["message_id"] for item in result["recent_evidence"]["messages"]], [user["message_id"], assistant["message_id"]])
        self.assertIn("Two Sum", result["recent_evidence"]["messages"][0]["content_excerpt"])
        self.assertNotIn("capability_state", result)

    def test_ct3_checkpoint_and_newer_turns_are_separate(self) -> None:
        session = self.session("subject-a", "session-a")
        before = self.turn(session, "subject-a", "turn-a", "user", "Checkpoint context")
        checkpoint = self.checkpoint(session, "subject-a", before["artifact_id"], "checkpoint-a")
        after = self.turn(session, "subject-a", "turn-b", "user", "After checkpoint, consider duplicates.")

        result = self.service.resume_learning_context(subject_id="subject-a")

        self.assertEqual(result["continuity_status"], "checkpoint_plus_recent_evidence")
        self.assertEqual(result["checkpoint"]["checkpoint_id"], checkpoint["checkpoint_id"])
        self.assertEqual(result["recent_evidence"]["messages"][0]["message_id"], after["message_id"])
        self.assertTrue(result["evidence_boundary"]["recent_evidence_is_not_mastery"])

    def test_ct4_transcript_is_not_capability_or_mastery(self) -> None:
        session = self.session("subject-a", "session-a")
        self.turn(session, "subject-a", "turn-a", "user", "I mastered dictionaries.")

        result = self.service.resume_learning_context(subject_id="subject-a")

        self.assertNotIn("capability_state", result)
        self.assertNotIn("mastery", result)
        self.assertTrue(result["evidence_boundary"]["transcript_is_source_evidence_only"])

    def test_ct5_subject_isolation(self) -> None:
        session = self.session("subject-a", "session-a")
        self.turn(session, "subject-a", "turn-a", "user", "private subject A context")
        self.session("subject-b", "session-b")

        result = self.service.resume_learning_context(subject_id="subject-b")

        self.assertEqual(result["continuity_status"], "no_durable_context")
        self.assertEqual(result["recent_evidence"]["messages"], [])

    def test_ct6_unknown_identity_is_explicit(self) -> None:
        result = self.service.resume_learning_context(subject_id="subject-not-bound")
        self.assertEqual(result["continuity_status"], "identity_or_runtime_unverified")
        self.assertEqual(result["identity_diagnostic"], "subject_not_found_in_runtime")

    def test_ct7_restart_preserves_continuity(self) -> None:
        session = self.session("subject-a", "session-a")
        turn = self.turn(session, "subject-a", "turn-a", "user", "restart-safe context")
        first = self.service.resume_learning_context(subject_id="subject-a")
        self.service.close()
        self.service = StudyOSService(self.config)

        second = self.service.resume_learning_context(subject_id="subject-a")

        self.assertEqual(first, second)
        self.assertEqual(second["recent_evidence"]["messages"][0]["artifact_id"], turn["artifact_id"])

    def test_ct8_backup_restore_preserves_continuity(self) -> None:
        session = self.session("subject-a", "session-a")
        self.turn(session, "subject-a", "turn-a", "user", "backup-safe context")
        expected = self.service.resume_learning_context(subject_id="subject-a")
        backup = self.service.backup()
        restored_dir = tempfile.TemporaryDirectory()
        try:
            restored = RuntimeConfig.from_env(restored_dir.name)
            restored_service = StudyOSService(restored)
            try:
                restored_service.restore(backup["backup_path"])
                self.assertEqual(restored_service.resume_learning_context(subject_id="subject-a"), expected)
            finally:
                restored_service.close()
        finally:
            restored_dir.cleanup()

    def test_ct9_hashes_remain_valid(self) -> None:
        session = self.session("subject-a", "session-a")
        turn = self.turn(session, "subject-a", "turn-a", "user", "hash-safe context")
        row = self.service.db.connection.execute(
            "SELECT storage_path, sha256 FROM raw_artifacts WHERE artifact_id = ?", (turn["artifact_id"],)
        ).fetchone()
        self.assertEqual(hashlib.sha256(self.config.evidence_root.joinpath(row["storage_path"]).read_bytes()).hexdigest(), row["sha256"])
        self.assertTrue(self.service.doctor()["healthy"])

    def test_application_and_mcp_expose_continuity_query(self) -> None:
        session = self.session("subject-a", "session-a")
        self.turn(session, "subject-a", "turn-a", "user", "application boundary context")
        result = ApplicationService(self.service).resume_learning_context(ResumeLearningContextRequest(subject_id="subject-a"))
        self.assertEqual(result.continuity_status, "evidence_only")
        mcp = MCPServer(self.service).call_tool("resume_learning_context", {"subject_id": "subject-a"})
        self.assertEqual(mcp["continuity_status"], "evidence_only")


if __name__ == "__main__":
    unittest.main()
