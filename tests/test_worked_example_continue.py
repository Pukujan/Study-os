"""Continue after Worked example must unstick probe and teach-only steps."""

from __future__ import annotations

import unittest

from study_os.web.player import engine
from study_os.web.player.content import load_lesson


class WorkedExampleContinueTests(unittest.TestCase):
    def test_fractions_continue_leaves_worked_example_to_probe(self):
        lesson = load_lesson("fractions-compare")
        state = engine._new_state(lesson)
        state, info = engine.adapt(lesson, state, "example")
        self.assertEqual(info["card_mode"], "worked_example")
        state = engine.next(lesson, state)
        self.assertEqual(state["card_mode"], "probe")
        self.assertIsNone(state.get("worked_example"))
        self.assertEqual(state["phase"], "probe")
        # Still on the same step — ready to answer.
        self.assertEqual(lesson["steps"][state["step_index"]]["step_id"], "problem")

    def test_big_o_why_continue_advances_past_teach_only(self):
        lesson = load_lesson("big-o-growth-families")
        state = engine._new_state(lesson)
        state, _ = engine.adapt(lesson, state, "example")
        self.assertEqual(state["card_mode"], "worked_example")
        state = engine.next(lesson, state)
        # Teach-only why_care advances after leaving the example.
        self.assertEqual(lesson["steps"][state["step_index"]]["step_id"], "o1_constant")


if __name__ == "__main__":
    unittest.main()
