"""Fractions-compare teach must not spoil the upcoming probe (#126 A12)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from study_os.web.player.engine import check_lesson


LESSON_PATH = Path(__file__).resolve().parents[1] / "src" / "study_os" / "web" / "player" / "lessons" / "fractions-compare.v1.json"


class FractionsTeachNotProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lesson = json.loads(LESSON_PATH.read_text(encoding="utf-8"))

    def test_check_lesson_clean(self) -> None:
        self.assertEqual(check_lesson(self.lesson), [])

    def test_problem_teach_does_not_repeat_probe_question(self) -> None:
        step = next(s for s in self.lesson["steps"] if s["step_id"] == "problem")
        teach_md = step["teach"]["md"].lower()
        captions = " ".join((f.get("caption") or "") for f in step["teach"]["frames"]).lower()
        probe = (step["probe"]["prompt_md"] or "").lower()
        self.assertNotIn("which is bigger", teach_md)
        self.assertNotIn("which is bigger", captions)
        self.assertIn("which", probe)  # probe still asks the question
        # Answer labels must not appear as exact fraction tokens on teach bars.
        teach_labels = [b.get("label") for f in step["teach"]["frames"] for b in f.get("bars") or []]
        self.assertNotIn("3/4", teach_labels)
        self.assertNotIn("2/3", teach_labels)

    def test_denominator_teach_does_not_spoil_answer_four(self) -> None:
        step = next(s for s in self.lesson["steps"] if s["step_id"] == "denominator")
        teach_blob = json.dumps(step["teach"]).lower()
        self.assertNotIn("denominator = 4", teach_blob)
        self.assertNotIn("split into 4", teach_blob)
        # Teach uses a different part count than the probe's 4.
        teach_parts = [b["parts"] for f in step["teach"]["frames"] for b in f.get("bars") or []]
        probe_parts = [b["parts"] for f in step["probe"]["frames"] for b in f.get("bars") or []]
        self.assertTrue(teach_parts)
        self.assertTrue(probe_parts)
        self.assertTrue(set(teach_parts).isdisjoint(set(probe_parts)))

    def test_numerator_teach_uses_different_example(self) -> None:
        step = next(s for s in self.lesson["steps"] if s["step_id"] == "numerator")
        teach_labels = [b.get("label") for f in step["teach"]["frames"] for b in f.get("bars") or []]
        self.assertNotIn("3/4", teach_labels)


if __name__ == "__main__":
    unittest.main()
