from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pydantic import ValidationError  # noqa: E402

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.application.contracts import (  # noqa: E402
    AppendConversationTurnRequest,
    AppendConversationTurnResult,
)
from study_os.application.service import (  # noqa: E402
    ApplicationService,
    project_append_conversation_turn_to_mcp,
)
from study_os.errors import StudyOSError  # noqa: E402
from study_os.mcp.server import MCPServer  # noqa: E402


class SourceTurnDurabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)
        self.session = self.service.start_session(
            idempotency_key="session-source-turns",
            subject_id="subject-source-turns",
            project_id="project-source-turns",
            domain_id="domain-source-turns",
        )

    def tearDown(self) -> None:
        self.service.close()
        self.temp_dir.cleanup()

    def append_request(self, **overrides: object) -> dict:
        request = {
            "idempotency_key": "turn-user-1",
            "session_id": self.session["session_id"],
            "subject_id": "subject-source-turns",
            "role": "user",
            "content": "What does cache[7] return?",
        }
        request.update(overrides)
        return request

    def test_user_and_assistant_turns_are_raw_artifact_backed_occurrences(self) -> None:
        user = self.service.append_conversation_turn(**self.append_request())
        assistant = self.service.append_conversation_turn(
            **self.append_request(
                idempotency_key="turn-assistant-1",
                role="assistant",
                content="It returns the value stored under key 7.",
            )
        )

        rows = self.service.db.connection.execute(
            "SELECT message_id, role, artifact_id, content_sha256, metadata_json "
            "FROM messages ORDER BY created_at"
        ).fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual({row["role"] for row in rows}, {"user", "assistant"})
        for result, row, content in zip(
            (user, assistant),
            rows,
            ("What does cache[7] return?", "It returns the value stored under key 7."),
        ):
            self.assertEqual(result["message_id"], row["message_id"])
            self.assertEqual(result["artifact_id"], row["artifact_id"])
            self.assertEqual(result["sha256"], hashlib.sha256(content.encode()).hexdigest())
            self.assertEqual(row["content_sha256"], result["sha256"])
            artifact = self.service.db.connection.execute(
                "SELECT storage_path, sha256, capture_method FROM raw_artifacts WHERE artifact_id = ?",
                (row["artifact_id"],),
            ).fetchone()
            self.assertEqual(artifact["sha256"], result["sha256"])
            self.assertTrue(self.config.evidence_root.joinpath(artifact["storage_path"]).read_bytes() == content.encode())
            self.assertEqual(json.loads(row["metadata_json"])["capture_origin"], "live")
            self.assertTrue(result["created"])

    def test_exact_retry_is_one_occurrence_and_conflicting_reuse_fails(self) -> None:
        first = self.service.append_conversation_turn(**self.append_request())
        second = self.service.append_conversation_turn(**self.append_request())
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(first["message_id"], second["message_id"])
        self.assertEqual(
            self.service.db.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
            1,
        )

        with self.assertRaises(StudyOSError) as raised:
            self.service.append_conversation_turn(
                **self.append_request(content="changed content")
            )
        self.assertEqual(raised.exception.category, "conflict")
        self.assertEqual(
            self.service.db.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
            1,
        )

    def test_identical_content_with_new_identity_is_a_new_occurrence(self) -> None:
        first = self.service.append_conversation_turn(**self.append_request())
        second = self.service.append_conversation_turn(
            **self.append_request(idempotency_key="turn-user-2")
        )
        self.assertNotEqual(first["message_id"], second["message_id"])
        self.assertEqual(
            self.service.db.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
            2,
        )

    def test_source_metadata_and_two_clocks_are_preserved(self) -> None:
        result = self.service.append_conversation_turn(
            **self.append_request(
                source_conversation_ref="conversation-1",
                source_message_ref="message-1",
                source_parent_ref="message-0",
                source_timestamp="2024-01-01T00:00:00Z",
                source_sequence=7,
                source_client="chatgpt",
            )
        )
        metadata = json.loads(
            self.service.db.connection.execute(
                "SELECT metadata_json FROM messages WHERE message_id = ?",
                (result["message_id"],),
            ).fetchone()[0]
        )
        self.assertEqual(metadata["source_timestamp"], "2024-01-01T00:00:00Z")
        self.assertEqual(metadata["source_sequence"], 7)
        self.assertEqual(metadata["source_message_ref"], "message-1")
        self.assertNotEqual(metadata["source_timestamp"], result["local_captured_at"])

    def test_precommit_failure_does_not_false_ack_or_leave_canonical_rows(self) -> None:
        with patch.object(self.service.evidence, "capture", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.service.append_conversation_turn(**self.append_request())
        self.assertEqual(self.service.db.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0], 0)
        self.assertEqual(self.service.db.connection.execute("SELECT COUNT(*) FROM raw_artifacts").fetchone()[0], 0)
        self.assertEqual(self.service.db.connection.execute("SELECT COUNT(*) FROM idempotency_records").fetchone()[0], 1)
        # Only the session idempotency record exists; the failed append was not acknowledged.
        self.assertIsNone(
            self.service.db.connection.execute(
                "SELECT 1 FROM idempotency_records WHERE operation_name = 'append_conversation_turn'"
            ).fetchone()
        )

    def test_postcommit_response_loss_retries_original_result(self) -> None:
        first_call = True

        def lose_response(_: dict) -> None:
            nonlocal first_call
            if first_call:
                first_call = False
                raise ConnectionError("response lost after commit")

        self.service._after_append_commit_hook = lose_response
        with self.assertRaises(ConnectionError):
            self.service.append_conversation_turn(**self.append_request())
        self.service._after_append_commit_hook = None
        retry = self.service.append_conversation_turn(**self.append_request())
        self.assertFalse(retry["created"])
        self.assertEqual(
            self.service.db.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
            1,
        )

    def test_restart_preserves_source_turns_and_exact_retry(self) -> None:
        self.service.append_conversation_turn(**self.append_request())
        self.service.append_conversation_turn(
            **self.append_request(
                idempotency_key="turn-assistant-restart-1",
                role="assistant",
                content="Synthetic restart response.",
            )
        )
        self.service.close()
        self.service = StudyOSService(self.config)
        retry = self.service.append_conversation_turn(**self.append_request())
        self.assertFalse(retry["created"])
        self.assertEqual(self.service.db.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0], 2)
        self.assertTrue(self.service.doctor()["healthy"])

    def test_application_and_mcp_projection_are_bounded(self) -> None:
        request = AppendConversationTurnRequest(**self.append_request(idempotency_key="turn-app-1"))
        application = ApplicationService(self.service).append_conversation_turn(request)
        projected = project_append_conversation_turn_to_mcp(application)
        self.assertEqual(projected["created"], True)
        self.assertEqual(projected["sha256"], application.sha256)
        mcp = MCPServer(self.service).call_tool(
            "append_conversation_turn",
            self.append_request(idempotency_key="turn-mcp-1"),
        )
        self.assertEqual(mcp["created"], True)
        self.assertEqual(mcp["capture_origin"], "live")
        self.assertEqual(len(MCPServer(self.service).list_tool_names()), 14)

    def test_application_contract_rejects_invalid_turns(self) -> None:
        with self.assertRaises(ValidationError):
            AppendConversationTurnRequest(**self.append_request(content=""))
        with self.assertRaises(ValidationError):
            AppendConversationTurnRequest(**self.append_request(role="tool"))
        with self.assertRaises(ValidationError):
            AppendConversationTurnRequest(**self.append_request(invented=True))

    def test_doctor_detects_message_artifact_corruption(self) -> None:
        result = self.service.append_conversation_turn(**self.append_request())
        self.service.db.connection.execute(
            "UPDATE messages SET content_sha256 = 'bad' WHERE message_id = ?",
            (result["message_id"],),
        )
        health = self.service.doctor()
        self.assertFalse(health["healthy"])
        self.assertFalse(health["checks"]["message_evidence_integrity"]["healthy"])

    def transcript_file(self, turns: list[dict]) -> Path:
        path = Path(self.temp_dir.name) / "reviewed-transcript.json"
        path.write_text(
            json.dumps(
                {"conversation_id": "conversation-1", "source_client": "chatgpt", "turns": turns}
            ),
            encoding="utf-8",
        )
        return path

    def test_reviewed_reconciliation_backfills_missing_turn_and_is_idempotent(self) -> None:
        live = self.service.append_conversation_turn(
            **self.append_request(
                idempotency_key="live-m1",
                source_conversation_ref="conversation-1",
                source_message_ref="m1",
                source_sequence=0,
            )
        )
        transcript = self.transcript_file(
            [
                {
                    "source_message_id": "m1",
                    "role": "user",
                    "content": "What does cache[7] return?",
                    "source_timestamp": "2024-01-01T00:00:00Z",
                    "source_sequence": 0,
                },
                {
                    "source_message_id": "m2",
                    "role": "assistant",
                    "content": "It returns the value stored under key 7.",
                    "source_timestamp": "2024-01-01T00:00:02Z",
                    "source_sequence": 1,
                },
            ]
        )
        first = self.service.reconcile_conversation(
            session_id=self.session["session_id"],
            subject_id="subject-source-turns",
            transcript_path=transcript,
        )
        self.assertEqual(first["status"], "backfilled_missing")
        self.assertEqual(
            [item["outcome"] for item in first["outcomes"]],
            ["already_present_exact", "backfilled_missing"],
        )
        backfilled = self.service.db.connection.execute(
            "SELECT metadata_json FROM messages WHERE role = 'assistant'"
        ).fetchone()
        self.assertEqual(json.loads(backfilled[0])["capture_origin"], "reconciliation")
        second = self.service.reconcile_conversation(
            session_id=self.session["session_id"],
            subject_id="subject-source-turns",
            transcript_path=transcript,
        )
        self.assertEqual(
            [item["outcome"] for item in second["outcomes"]],
            ["already_present_exact", "already_present_exact"],
        )
        self.assertEqual(
            self.service.db.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
            2,
        )
        self.assertEqual(live["capture_origin"], "live")

    def test_ambiguous_reconciliation_fails_closed(self) -> None:
        self.service.append_conversation_turn(**self.append_request(idempotency_key="same-1"))
        self.service.append_conversation_turn(**self.append_request(idempotency_key="same-2"))
        result = self.service.reconcile_conversation(
            session_id=self.session["session_id"],
            subject_id="subject-source-turns",
            transcript_path=self.transcript_file(
                [{"role": "user", "content": "What does cache[7] return?"}]
            ),
        )
        self.assertEqual(result["status"], "ambiguous_review_required")
        self.assertEqual(result["outcomes"][0]["outcome"], "ambiguous_review_required")
        self.assertEqual(
            self.service.db.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
            2,
        )

    def test_backup_restore_preserves_source_turn_substrate(self) -> None:
        self.service.append_conversation_turn(**self.append_request())
        backup_path = Path(self.temp_dir.name) / "backup"
        backup = self.service.backup(backup_path)
        self.service.restore(backup["backup_path"])
        rows = self.service.db.connection.execute(
            "SELECT message_id, artifact_id, content_sha256 FROM messages"
        ).fetchall()
        self.assertEqual(len(rows), 1)
        retry = self.service.append_conversation_turn(**self.append_request())
        self.assertFalse(retry["created"])
        self.assertEqual(retry["message_id"], rows[0]["message_id"])
        self.assertTrue(self.service.doctor()["healthy"])

    def test_backup_restore_preserves_reconciled_source_turn(self) -> None:
        first = self.service.reconcile_conversation(
            session_id=self.session["session_id"],
            subject_id="subject-source-turns",
            transcript_path=self.transcript_file(
                [{
                    "source_message_id": "reconciled-1",
                    "role": "assistant",
                    "content": "Synthetic reconciled response.",
                    "source_timestamp": "2024-01-01T00:00:02Z",
                    "source_sequence": 1,
                }]
            ),
        )
        self.assertEqual(first["status"], "backfilled_missing")
        backup = self.service.backup(Path(self.temp_dir.name) / "reconciled-backup")
        self.service.restore(backup["backup_path"])
        row = self.service.db.connection.execute(
            "SELECT artifact_id, metadata_json FROM messages"
        ).fetchone()
        metadata = json.loads(row["metadata_json"])
        self.assertEqual(metadata["capture_origin"], "reconciliation")
        self.assertEqual(metadata["source_message_ref"], "reconciled-1")
        self.assertTrue(self.service.doctor()["healthy"])


if __name__ == "__main__":
    unittest.main()
