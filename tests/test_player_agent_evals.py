"""Focused tests for the synthetic live-player A2A harness."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_player_agent_evals as harness  # noqa: E402


class PlayerAgentEvalTests(unittest.TestCase):
    def test_oracle_prefix_is_pinned_to_player_slice(self) -> None:
        prefix, digest, conforms = harness.golden_prefix()
        self.assertEqual(prefix, ["problem", "position", "index", "box_size_k", "box_start_i", "window_sum"])
        self.assertEqual(len(digest), 64)
        self.assertIsInstance(conforms, bool)

    def test_scripted_personas_are_deterministic(self) -> None:
        self.assertEqual(harness.learner_response("golden", "window-sum", 0), "9")
        self.assertEqual(harness.learner_response("wrong_then_right", "window-sum", 0), "not this")
        self.assertEqual(harness.learner_response("wrong_then_right", "window-sum", 1), "9")
        self.assertEqual(harness.learner_response("partial_then_right", "window-sum", 0), "2 6 1")

    def test_missing_render_capability_is_a_failure(self) -> None:
        violations = harness.capability_detector(
            {"reply_md": "Try an example", "suggested_action": "example"},
            {"step": {"step_id": "position"}},
            {"step": {"step_id": "position"}},
        )
        self.assertEqual(violations[0]["code"], "MISSING_REGENERATE_PRESENTATION")

    def test_scorecard_is_synthetic_and_machine_readable(self) -> None:
        card = harness.build_scorecard(
            [{"persona": "golden", "seed": 0, "observed_path": [], "events": [], "violations": [], "end_phase": "done"}],
            live=False,
        )
        self.assertEqual(card["schema_version"], harness.SCORECARD_VERSION)
        self.assertTrue(card["synthetic_only"])
        self.assertIn("transcripts", card)
        json.dumps(card)


if __name__ == "__main__":
    unittest.main()
