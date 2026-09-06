from __future__ import annotations

import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from study_os import RuntimeConfig, StudyOSService
from study_os.db.connection import LATEST_SCHEMA_VERSION
from study_os.errors import StudyOSError
from study_os.mcp.server import MCPServer
from study_os.pir.registry import CANONICAL_PROBLEM_ID


class PIRRuntimeIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)
        self.session = self.service.start_session(
            idempotency_key="pir-session",
            subject_id="subject-001",
            project_id="dsa-python",
            domain_id="dsa",
        )

    def tearDown(self) -> None:
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def start_problem(self, key: str = "pir-start") -> dict[str, object]:
        return self.service.start_problem(
            idempotency_key=key,
            session_id=str(self.session["session_id"]),
            subject_id="subject-001",
            canonical_problem_id=CANONICAL_PROBLEM_ID,
        )

    @staticmethod
    def response_turn_id(result: dict[str, object]) -> str:
        bundle = result["turn"]
        if not isinstance(bundle, dict):
            raise AssertionError("expected teaching bundle")
        turn_id = bundle.get("response_turn_id")
        if not isinstance(turn_id, str):
            raise AssertionError("expected response turn id")
        return turn_id

    def test_known_problem_resolution_is_conservative(self) -> None:
        known = self.service.resolve_problem(
            problem_text="maximum sum contiguous window size k",
            domain="dsa",
        )
        self.assertEqual(known["status"], "known")
        self.assertEqual(known["canonical_problem_id"], CANONICAL_PROBLEM_ID)

        unknown = self.service.resolve_problem(
            problem_text="find the shortest path in an unweighted graph",
            domain="dsa",
        )
        self.assertEqual(unknown["status"], "needs_compilation")
        self.assertIsNone(unknown["canonical_problem_id"])

    def test_start_problem_pins_asset_and_retries_idempotently(self) -> None:
        first = self.start_problem()
        second = self.start_problem()
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(first["problem_run_id"], second["problem_run_id"])
        self.assertEqual(first["canonical_problem_id"], CANONICAL_PROBLEM_ID)
        self.assertEqual(first["run_status"], "active")
        self.assertEqual(self.response_turn_id(first), self.response_turn_id(second))

        count = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM problem_runs WHERE problem_run_id = ?",
            (first["problem_run_id"],),
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_historical_box_values_are_partial_not_incorrect(self) -> None:
        started = self.start_problem()
        result = self.service.submit_problem_response(
            idempotency_key="pir-partial",
            problem_run_id=str(started["problem_run_id"]),
            subject_id="subject-001",
            turn_id=self.response_turn_id(started),
            response="2 6",
        )
        self.assertEqual(result["outcome"], "partial")
        bundle = result["turn"]
        self.assertIsInstance(bundle, dict)
        turns = bundle["turns"]
        self.assertEqual(turns[0]["canonical_step_id"], "sum_partial")
        self.assertEqual(turns[-1]["canonical_step_id"], "arithmetic_probe")
        self.assertIn("right values", turns[0]["learner_visible_markdown"])

    def test_expansion_is_durable_and_does_not_advance(self) -> None:
        started = self.start_problem()
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)
        before = self.service.db.connection.execute(
            "SELECT current_step_id, transition_seq FROM problem_runs WHERE problem_run_id = ?",
            (run_id,),
        ).fetchone()

        expansion = self.service.request_problem_expansion(
            idempotency_key="pir-expand",
            problem_run_id=run_id,
            subject_id="subject-001",
            turn_id=turn_id,
            request_kind="why",
            learner_request="why is i the start of the box?",
        )
        after = self.service.db.connection.execute(
            "SELECT current_step_id, transition_seq FROM problem_runs WHERE problem_run_id = ?",
            (run_id,),
        ).fetchone()
        self.assertEqual(tuple(before), tuple(after))
        self.assertEqual(expansion["turn"]["response_turn_id"], turn_id)
        self.assertEqual(expansion["turn"]["turns"][-1]["turn_id"], turn_id)

        event = self.service.db.connection.execute(
            "SELECT event_type FROM learning_events WHERE event_type = 'pir_expansion_request'"
        ).fetchone()
        self.assertIsNotNone(event)

    def test_response_retry_is_exact_and_does_not_duplicate_evidence(self) -> None:
        started = self.start_problem()
        request = dict(
            idempotency_key="pir-submit-retry",
            problem_run_id=str(started["problem_run_id"]),
            subject_id="subject-001",
            turn_id=self.response_turn_id(started),
            response="8",
        )
        first = self.service.submit_problem_response(**request)
        second = self.service.submit_problem_response(**request)
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(first["outcome"], second["outcome"])
        self.assertEqual(first["turn"], second["turn"])

        attempts = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM attempts WHERE idempotency_key = ?",
            ("pir:pir-submit-retry:attempt",),
        ).fetchone()[0]
        events = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM learning_events WHERE idempotency_key = ?",
            ("pir:pir-submit-retry:outcome",),
        ).fetchone()[0]
        self.assertEqual(attempts, 1)
        self.assertEqual(events, 1)

    def test_conflicting_idempotency_and_stale_turn_fail_closed(self) -> None:
        started = self.start_problem()
        run_id = str(started["problem_run_id"])
        old_turn = self.response_turn_id(started)
        self.service.submit_problem_response(
            idempotency_key="pir-submit-conflict",
            problem_run_id=run_id,
            subject_id="subject-001",
            turn_id=old_turn,
            response="8",
        )

        with self.assertRaises(StudyOSError) as conflict_error:
            self.service.submit_problem_response(
                idempotency_key="pir-submit-conflict",
                problem_run_id=run_id,
                subject_id="subject-001",
                turn_id=old_turn,
                response="7",
            )
        self.assertEqual(conflict_error.exception.category, "conflict")

        with self.assertRaises(StudyOSError) as stale_error:
            self.service.submit_problem_response(
                idempotency_key="pir-submit-stale",
                problem_run_id=run_id,
                subject_id="subject-001",
                turn_id=old_turn,
                response="8",
            )
        self.assertEqual(stale_error.exception.category, "conflict")

    def test_restart_reconstructs_exact_current_turn(self) -> None:
        started = self.start_problem()
        run_id = str(started["problem_run_id"])
        advanced = self.service.submit_problem_response(
            idempotency_key="pir-before-restart",
            problem_run_id=run_id,
            subject_id="subject-001",
            turn_id=self.response_turn_id(started),
            response="8",
        )
        expected = self.service.get_problem_turn(
            problem_run_id=run_id,
            subject_id="subject-001",
        )
        self.assertEqual(expected["turn"]["response_turn_id"], advanced["turn"]["response_turn_id"])

        self.service.close()
        self.service = StudyOSService(self.config)
        resumed = self.service.get_problem_turn(
            problem_run_id=run_id,
            subject_id="subject-001",
        )
        self.assertEqual(resumed, expected)

    def test_subject_boundary_and_missing_pinned_asset_fail_closed(self) -> None:
        started = self.start_problem()
        run_id = str(started["problem_run_id"])
        with self.assertRaises(StudyOSError) as wrong_subject:
            self.service.get_problem_turn(
                problem_run_id=run_id,
                subject_id="subject-999",
            )
        self.assertEqual(wrong_subject.exception.category, "not_found")

        with patch("study_os.services.pir_runtime.get_asset", return_value=None):
            with self.assertRaises(StudyOSError) as missing_asset:
                self.service.get_problem_turn(
                    problem_run_id=run_id,
                    subject_id="subject-001",
                )
        self.assertEqual(missing_asset.exception.category, "integrity_error")

    def test_all_correct_path_ends_assembled_without_mastery(self) -> None:
        current = self.start_problem()
        run_id = str(current["problem_run_id"])
        answers = (
            "8",
            "S[i]=S[i-1]-a[i-1]+a[i+j]",
            "for i,num in enumerate(a):",
            "S.append(S[i-1]-a[i-1]+a[i+j])",
            "if S[i] > max_sum:\n    max_sum = S[i]",
        )
        for index, answer in enumerate(answers):
            current = self.service.submit_problem_response(
                idempotency_key=f"pir-complete-{index}",
                problem_run_id=run_id,
                subject_id="subject-001",
                turn_id=self.response_turn_id(current),
                response=answer,
            )

        self.assertEqual(current["run_status"], "assembled_mastery_unproven")
        self.assertIsNone(current["turn"]["response_turn_id"])
        rendered = "\n".join(
            turn["learner_visible_markdown"] for turn in current["turn"]["turns"]
        )
        self.assertIn("Independent mastery is not established", rendered)
        self.assertNotIn("completed_validated", rendered)

    def test_mcp_v04_exposes_exactly_twenty_semantic_tools(self) -> None:
        server = MCPServer(self.service)
        names = server.list_tool_names()
        self.assertEqual(len(names), 20)
        for name in (
            "resolve_problem",
            "start_problem",
            "get_problem_turn",
            "submit_problem_response",
            "request_problem_expansion",
        ):
            self.assertIn(name, names)

        resolution = server.call_tool(
            "resolve_problem",
            {
                "problem_text": "maximum sum contiguous window size k",
                "domain": "dsa",
            },
        )
        self.assertEqual(resolution["status"], "known")

    def test_schema_v1_to_v2_migration_preserves_existing_session(self) -> None:
        session_id = str(self.session["session_id"])
        self.service.close()
        connection = sqlite3.connect(self.config.db_path)
        try:
            connection.execute("PRAGMA foreign_keys = OFF")
            connection.execute("DROP TABLE problem_run_operations")
            connection.execute("DROP TABLE problem_runs")
            connection.execute("PRAGMA user_version = 1")
            connection.execute(
                "UPDATE schema_meta SET value = '1' WHERE key = 'schema_version'"
            )
            connection.commit()
        finally:
            connection.close()

        self.service = StudyOSService(self.config)
        self.assertEqual(LATEST_SCHEMA_VERSION, 2)
        self.assertEqual(
            self.service.db.connection.execute("PRAGMA user_version").fetchone()[0],
            2,
        )
        preserved = self.service.db.connection.execute(
            "SELECT session_id FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        self.assertIsNotNone(preserved)
        tables = {
            row[0]
            for row in self.service.db.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        self.assertIn("problem_runs", tables)
        self.assertIn("problem_run_operations", tables)


if __name__ == "__main__":
    unittest.main()
