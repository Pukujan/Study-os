from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "tools" / "run_dual_luna_transcript.py"
CORPUS_PATH = ROOT / "datasets" / "dsa-conversation-replay.v0.1.json"

spec = importlib.util.spec_from_file_location("dual_luna_transcript", HARNESS_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("unable to load dual-Luna transcript runner")
dual_luna = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dual_luna
spec.loader.exec_module(dual_luna)


class FakeStudent:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(payload)
        return {
            "student_message": (
                f"student {payload['scenario_id']} turn {payload['turn_index']} "
                f"{payload['learner_signal']}"
            )
        }

    def close(self) -> None:
        return None


class FakeTeacher:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(payload)
        return {
            "teacher_message": (
                f"teacher {payload['scenario_id']} turn {payload['turn_index']}"
            )
        }

    def close(self) -> None:
        return None


class DualLunaTranscriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = dual_luna.load_corpus(CORPUS_PATH)

    def test_student_payload_has_behavioral_guidance_not_hidden_rubric(self) -> None:
        scenario = self.corpus["scenarios"][0]
        payload = dual_luna.build_student_payload(
            scenario,
            turn_index=0,
            conversation=[],
        )
        serialized = json.dumps(payload)
        self.assertNotIn("expected", serialized)
        self.assertNotIn("must_include_any", serialized)
        self.assertNotIn("must_not_include", serialized)
        self.assertNotIn("stage", payload)
        self.assertEqual(payload["learner_signal"], "clarification")

    def test_teacher_payload_does_not_receive_dataset_answer_key(self) -> None:
        scenario = self.corpus["scenarios"][0]
        payload = dual_luna.build_teacher_payload(
            scenario,
            turn_index=0,
            learner_message="wait what are we finding?",
            conversation=[{"role": "learner", "content": "wait what are we finding?"}],
        )
        serialized = json.dumps(payload)
        self.assertNotIn("expected", serialized)
        self.assertNotIn("learner_signal", payload)
        self.assertNotIn("variables", payload)
        self.assertNotIn("stage", payload)

    def test_full_problem_conversation_is_preserved_for_restart_recovery(self) -> None:
        scenario = self.corpus["scenarios"][0]
        conversation = [
            {"role": "teacher" if index % 2 else "learner", "content": str(index)}
            for index in range(30)
        ]
        payload = dual_luna.build_student_payload(
            scenario,
            turn_index=14,
            conversation=conversation,
        )
        self.assertEqual(payload["conversation"], conversation)
        self.assertEqual(len(payload["conversation"]), 30)

    def test_default_full_run_is_14_problems_and_210_exchanges(self) -> None:
        records = dual_luna.run_transcript(
            self.corpus,
            FakeStudent(),
            FakeTeacher(),
        )
        self.assertEqual(len(records), 210)
        self.assertEqual(len({item["scenario_id"] for item in records}), 14)
        dual_luna.validate_run_size(records)

    def test_raw_transcript_contains_no_judge_fields(self) -> None:
        records = dual_luna.run_transcript(
            self.corpus,
            FakeStudent(),
            FakeTeacher(),
            scenario_ids={"two-sum-dictionary"},
            turns_per_problem=2,
        )
        self.assertEqual(len(records), 2)
        for record in records:
            self.assertNotIn("violations", record)
            self.assertNotIn("score", record)
            self.assertNotIn("passed", record)
            self.assertNotIn("expected", record)
            self.assertTrue(record["learner_message"])
            self.assertTrue(record["teacher_message"])

    def test_resume_continues_from_next_uncaptured_exchange(self) -> None:
        first_student = FakeStudent()
        first_teacher = FakeTeacher()
        initial = dual_luna.run_transcript(
            self.corpus,
            first_student,
            first_teacher,
            scenario_ids={"two-sum-dictionary"},
            turns_per_problem=1,
        )
        self.assertEqual(len(initial), 1)

        student = FakeStudent()
        teacher = FakeTeacher()
        resumed = dual_luna.run_transcript(
            self.corpus,
            student,
            teacher,
            scenario_ids={"two-sum-dictionary"},
            turns_per_problem=3,
            existing_records=initial,
        )

        self.assertEqual(len(resumed), 3)
        self.assertEqual([call["turn_index"] for call in student.calls], [1, 2])
        self.assertEqual([call["turn_index"] for call in teacher.calls], [1, 2])
        self.assertEqual(len(student.calls[0]["conversation"]), 2)
        self.assertEqual(len(student.calls[1]["conversation"]), 4)

    def test_checkpoint_callback_runs_after_every_completed_exchange(self) -> None:
        snapshots: list[int] = []
        records = dual_luna.run_transcript(
            self.corpus,
            FakeStudent(),
            FakeTeacher(),
            scenario_ids={"two-sum-dictionary"},
            turns_per_problem=3,
            on_record=lambda _record, all_records: snapshots.append(len(all_records)),
        )
        self.assertEqual(len(records), 3)
        self.assertEqual(snapshots, [1, 2, 3])

    def test_jsonl_round_trip_supports_resume(self) -> None:
        records = dual_luna.run_transcript(
            self.corpus,
            FakeStudent(),
            FakeTeacher(),
            scenario_ids={"two-sum-dictionary"},
            turns_per_problem=2,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "transcript.jsonl"
            dual_luna.write_jsonl(records, path)
            restored = dual_luna.load_jsonl(path)
        self.assertEqual(restored, records)

    def test_markdown_is_readable_full_conversation(self) -> None:
        records = dual_luna.run_transcript(
            self.corpus,
            FakeStudent(),
            FakeTeacher(),
            scenario_ids={"two-sum-dictionary"},
            turns_per_problem=2,
        )
        markdown = dual_luna.render_markdown(records)
        self.assertIn("# Dual-Luna DSA raw transcript", markdown)
        self.assertIn("## Two Sum", markdown)
        self.assertIn("**Learner**", markdown)
        self.assertIn("**Study OS teacher**", markdown)
        self.assertIn("student two-sum-dictionary turn 0", markdown)
        self.assertIn("teacher two-sum-dictionary turn 0", markdown)


if __name__ == "__main__":
    unittest.main()
