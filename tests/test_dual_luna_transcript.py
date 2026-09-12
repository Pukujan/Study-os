from __future__ import annotations

import importlib.util
import json
import sys
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
    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "student_message": (
                f"student {payload['scenario_id']} turn {payload['turn_index']} "
                f"{payload['learner_signal']}"
            )
        }

    def close(self) -> None:
        return None


class FakeTeacher:
    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
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
