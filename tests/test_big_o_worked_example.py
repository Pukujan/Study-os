"""Big O teach-only Worked example must differ and stay continuable (#126)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from study_os.web.player import content, engine


class BigOWorkedExampleTests(unittest.TestCase):
    def test_why_care_example_differs_from_teach(self) -> None:
        lesson = content.load_lesson("big-o-growth-families")
        state = engine.start(lesson)
        view = engine.view(lesson, state)
        self.assertEqual(view["step"]["step_id"], "why_care")
        self.assertIsNone(view["step"]["probe"])
        teach_md = view["step"]["teach_md"]
        teach_types = [f["type"] for f in view["step"]["teach_frames"]]

        state, info = engine.adapt(lesson, state, "example")
        self.assertEqual(info.get("card_mode"), "worked_example")
        view2 = engine.view(lesson, state)
        example = view2["worked_example"]
        self.assertIsNotNone(example)
        assert example is not None
        self.assertNotEqual(example["md"], teach_md)
        self.assertTrue(example["md"].startswith("1)"))
        example_types = [f["type"] for f in example["frames"]]
        self.assertNotEqual(example_types, teach_types)
        # Teach-only steps remain in probe phase so Continue stays available.
        self.assertEqual(view2["phase"], "probe")
        self.assertIsNone(view2["step"]["probe"])
        self.assertEqual(view2["card_mode"], "worked_example")

    def test_why_care_example_alternate_rotates(self) -> None:
        lesson = content.load_lesson("big-o-growth-families")
        state = engine.start(lesson)
        state, _ = engine.adapt(lesson, state, "example")
        first = engine.view(lesson, state)["worked_example"]["md"]
        state, _ = engine.adapt(lesson, state, "example")
        second = engine.view(lesson, state)["worked_example"]["md"]
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
