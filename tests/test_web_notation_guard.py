from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from study_os.web.notation_guard import notation_violations, approved_symbols
from study_os.web.validator import validate_generated
from study_os.web.player import presentation


class NotationGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lesson = {
            "lesson_id": "demo",
            "revision": "demo.v1",
            "steps": [{
                "step_id": "one", "kc": "linear",
                "teach": {"md": "One stick for each box.", "frames": []},
            }],
        }
        self.state = {"step_index": 0, "phase": "feedback", "variant_index": -1, "scaffold": 0}

    def test_rejects_fresh_function_and_index_symbols(self):
        self.assertEqual(notation_violations("W(n) = 3 and T(4) = 5 and S[i] is 2.", ()),
                         ("UNAPPROVED_NOTATION:S", "UNAPPROVED_NOTATION:T", "UNAPPROVED_NOTATION:W"))
        self.assertEqual(notation_violations("3 boxes used 3 sticks.", ()), ())
        self.assertEqual(notation_violations("O(n) is the linear pattern.", ("O",)), ())

    def test_only_authored_nonempty_definitions_grant_approval(self):
        lesson = copy.deepcopy(self.lesson)
        lesson["steps"][0]["teach"]["approved_notation"] = [
            {"symbol": "W", "definition": "The exact stick placements in this game."},
            {"symbol": "T", "definition": ""},
            {"symbol": "S", "definition": 12},
        ]
        self.assertEqual(approved_symbols(lesson, self.state), ("W",))
        self.assertEqual(notation_violations("W(3) = 3 and T(3) = 4", ("W",)), ("UNAPPROVED_NOTATION:T",))

    def test_general_generated_prose_needs_explicit_lesson_allowlist(self):
        result = validate_generated("W(3) = 3.", forbidden_answers=(), required_blocks=(),
                                    allowed_notation=approved_symbols(self.lesson, self.state))
        self.assertFalse(result.ok)
        self.assertIn("UNAPPROVED_NOTATION:W", result.codes)

    def test_presentation_rejects_notation_before_rewrite_can_hide_it(self):
        update, codes = presentation.validate_proposal(
            {"teach_md": "Each box gets a stick. W(n) = n.", "frame_indices": []},
            self.lesson, self.state, (),
        )
        self.assertIsNone(update)
        self.assertIn("UNAPPROVED_NOTATION:W", codes)

    def test_presentation_accepts_plain_words(self):
        update, codes = presentation.validate_proposal(
            {"teach_md": "Three boxes need three sticks.", "frame_indices": []},
            self.lesson, self.state, (),
        )
        self.assertEqual(codes, ())
        self.assertIsNotNone(update)


if __name__ == "__main__":
    unittest.main()
