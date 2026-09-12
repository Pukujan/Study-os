from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "tools" / "replay_dsa_conversations.py"
CORPUS_PATH = ROOT / "datasets" / "dsa-conversation-replay.v0.1.json"

spec = importlib.util.spec_from_file_location("dsa_replay", HARNESS_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("unable to load DSA replay harness")
dsa_replay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dsa_replay
spec.loader.exec_module(dsa_replay)


class DSAConversationReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = dsa_replay.load_corpus(CORPUS_PATH)

    def test_corpus_is_large_and_realistic(self) -> None:
        errors = dsa_replay.validate_corpus(self.corpus)
        self.assertEqual(errors, [])
        problem_count, turn_count = dsa_replay.corpus_counts(self.corpus)
        self.assertGreaterEqual(problem_count, 10)
        self.assertGreaterEqual(turn_count, 150)

        for scenario in self.corpus["scenarios"]:
            signals = {turn["learner_signal"] for turn in scenario["turns"]}
            self.assertIn("clarification", signals)
            self.assertIn("wrong_or_uncertain", signals)
            self.assertIn("recovery_or_check", signals)
            self.assertTrue(
                any(turn["expected"]["visual_required"] for turn in scenario["turns"])
            )

    def test_actor_payload_does_not_leak_hidden_assertions_or_stage(self) -> None:
        scenario = self.corpus["scenarios"][0]
        turn = scenario["turns"][0]
        payload = dsa_replay._actor_payload(scenario, turn, 0, [])
        serialized = json.dumps(payload)
        self.assertNotIn("expected", payload)
        self.assertNotIn("stage", payload)
        self.assertNotIn("must_include_any", serialized)
        self.assertNotIn("must_not_include", serialized)
        self.assertNotIn(str(turn["stage"]), serialized)

    def test_evaluator_accepts_stage_aligned_visual_question(self) -> None:
        turn = {
            "expected": {
                "must_include_any": ["needed", "target", "num"],
                "must_not_include": ["seen", "return"],
                "visual_required": True,
                "max_nonempty_lines": 12,
                "must_ask_question": True,
            }
        }
        message = (
            "| target | 9 |\n"
            "| num | 3 |\n"
            "| needed | 6 |\n\n"
            "`needed = target - num`\n"
            "What is needed when num = 4?"
        )
        self.assertEqual(dsa_replay.evaluate_response(turn, message), [])

    def test_evaluator_catches_the_failures_we_keep_seeing(self) -> None:
        turn = {
            "expected": {
                "must_include_any": ["box", "needed"],
                "must_not_include": ["seen", "full code", "return"],
                "visual_required": True,
                "max_nonempty_lines": 6,
                "must_ask_question": True,
            }
        }
        message = (
            "Use seen as the hash map and return immediately if the complement exists. "
            "Then here is the full code implementation with enumerate and a final return."
        )
        codes = {
            violation.code
            for violation in dsa_replay.evaluate_response(turn, message)
        }
        self.assertIn("FUTURE_OR_RENAMED_CONCEPT", codes)
        self.assertIn("REPRESENTATION_DROPPED", codes)
        self.assertIn("BACK_AND_FORTH_DROPPED", codes)

    def test_grade_lane_finds_first_visible_divergence(self) -> None:
        scenario = self.corpus["scenarios"][0]
        records = [
            {
                "scenario_id": scenario["id"],
                "turn_index": 0,
                "assistant_message": "Here is a long prose answer with no chart and no question.",
            }
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript = Path(temp_dir) / "transcript.jsonl"
            transcript.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            report = dsa_replay.grade_transcript(self.corpus, transcript)
        self.assertEqual(report["executed_turns"], 1)
        self.assertEqual(report["failed_turns"], 1)
        self.assertEqual(
            report["first_divergence"]["scenario_id"],
            scenario["id"],
        )


if __name__ == "__main__":
    unittest.main()
