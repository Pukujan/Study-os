from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from study_os.experimental.mutation_study import (
    PROBES,
    StudySliceError,
    get_status,
    get_turn,
    start_run,
    submit_choice,
)


class MutationStudySliceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "mutation-study.sqlite"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_start_is_deterministic(self) -> None:
        started = start_run(self.db_path, "subject-001")
        turn = started["turn"]
        self.assertEqual(turn["node_id"], "survivor_meaning")
        self.assertEqual(turn["lesson_id"], "mutation-testing.v0")
        self.assertEqual(started["status"]["run_status"], "active")
        self.assertTrue(self.db_path.exists())

    def test_incorrect_records_attempt_and_does_not_advance(self) -> None:
        started = start_run(self.db_path, "subject-001")
        run_id = started["run_id"]
        result = submit_choice(self.db_path, run_id, "A", "A1")
        self.assertEqual(result["outcome"], "incorrect")
        self.assertFalse(result["advanced"])
        self.assertEqual(result["turn"]["node_id"], "survivor_meaning")
        node = result["status"]["nodes"][0]
        self.assertEqual(node["attempts"], 1)
        self.assertEqual(node["correct"], 0)
        self.assertFalse(node["mastered"])

        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT assistance_level FROM study_attempts WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        self.assertEqual(row[0], "A1")

    def test_invalid_choice_fails_closed_without_evidence(self) -> None:
        started = start_run(self.db_path, "subject-001")
        run_id = started["run_id"]
        with self.assertRaises(StudySliceError):
            submit_choice(self.db_path, run_id, "Z")
        status = get_status(self.db_path, run_id)
        self.assertEqual(status["nodes"][0]["attempts"], 0)
        self.assertEqual(status["current_node_id"], "survivor_meaning")

    def test_correct_advances_exactly_one_node(self) -> None:
        started = start_run(self.db_path, "subject-001")
        run_id = started["run_id"]
        result = submit_choice(self.db_path, run_id, PROBES[0].correct_choice)
        self.assertTrue(result["advanced"])
        self.assertEqual(result["turn"]["node_id"], PROBES[1].node_id)
        self.assertTrue(result["status"]["nodes"][0]["mastered"])
        self.assertFalse(result["status"]["nodes"][1]["mastered"])

    def test_restart_resume_uses_sqlite_state(self) -> None:
        started = start_run(self.db_path, "subject-001")
        run_id = started["run_id"]
        submit_choice(self.db_path, run_id, PROBES[0].correct_choice, "A2")

        resumed = get_turn(self.db_path, run_id)
        self.assertEqual(resumed["turn"]["node_id"], PROBES[1].node_id)
        first = resumed["status"]["nodes"][0]
        self.assertEqual(first["attempts"], 1)
        self.assertEqual(first["correct"], 1)
        self.assertTrue(first["mastered"])

    def test_final_completion_is_exact_and_rejects_more_answers(self) -> None:
        started = start_run(self.db_path, "subject-001")
        run_id = started["run_id"]
        result = None
        for probe in PROBES:
            result = submit_choice(self.db_path, run_id, probe.correct_choice)

        assert result is not None
        self.assertIsNone(result["turn"])
        status = result["status"]
        self.assertEqual(status["run_status"], "complete")
        self.assertIsNone(status["current_node_id"])
        self.assertEqual(status["mastered_nodes"], len(PROBES))
        self.assertTrue(all(node["mastered"] for node in status["nodes"]))

        with self.assertRaises(StudySliceError):
            submit_choice(self.db_path, run_id, "A")

    def test_assistance_is_validated_before_write(self) -> None:
        started = start_run(self.db_path, "subject-001")
        run_id = started["run_id"]
        with self.assertRaises(StudySliceError):
            submit_choice(self.db_path, run_id, "B", "A9")
        status = get_status(self.db_path, run_id)
        self.assertEqual(status["nodes"][0]["attempts"], 0)


if __name__ == "__main__":
    unittest.main()
