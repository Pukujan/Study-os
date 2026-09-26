from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from study_os.web.player import engine, presentation


class PresentationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lesson = {
            "lesson_id": "lesson",
            "revision": "lesson.v1",
            "steps": [{"step_id": "step", "kc": "concept", "teach": {"md": "old", "frames": [{"type": "box_index", "cells": [1]}]}, "probe": {}}],
        }
        self.state = {"step_index": 0, "variant_index": -1, "phase": "feedback", "scaffold": 0, "card_mode": "probe"}

    def test_validate_and_apply_is_versioned_and_same_identity(self) -> None:
        content, codes = presentation.validate_proposal({"teach_md": "A clearer view of the same position.", "frame_indices": [0]}, self.lesson, self.state, ())
        self.assertEqual(codes, ())
        update = presentation.apply(self.lesson, self.state, content or {}, {"prompt_version": "tutor.v3"})
        self.assertEqual(update["step_id"], "step")
        self.assertEqual(update["concept_id"], "concept")
        self.assertEqual(update["version"], 1)
        self.assertEqual(presentation.current(self.lesson, self.state), update)

    def test_rejects_answer_reveal_and_invalid_frames(self) -> None:
        content, codes = presentation.validate_proposal({"teach_md": "9", "frame_indices": [0]}, self.lesson, self.state, ("9",))
        self.assertIsNone(content)
        self.assertIn("ANSWER_REVEAL_FORBIDDEN", codes)
        content, codes = presentation.validate_proposal({"teach_md": "Try this.", "frame_indices": [1]}, self.lesson, self.state, ())
        self.assertIsNone(content)
        self.assertEqual(codes, ("INVALID_PRESENTATION",))

    def test_rejects_malformed_or_answer_bearing_proposals(self) -> None:
        cases = [
            ({"teach_md": "Fine.", "frame_indices": [0], "step_id": "other"}, "INVALID_PRESENTATION"),
            ({"teach_md": "Fine.", "frame_indices": [0, 0]}, "INVALID_PRESENTATION"),
            ({"teach_md": "Fine.", "frame_indices": []}, "INVALID_PRESENTATION"),
            ({"teach_md": "Fine.", "frame_indices": [True]}, "INVALID_PRESENTATION"),
            ({"teach_md": "Try ```code``` here.", "frame_indices": [0]}, "INVALID_PRESENTATION"),
            ({"teach_md": "You have mastered this.", "frame_indices": [0]}, "MASTERY_CLAIM"),
            ({"teach_md": "word " * 200, "frame_indices": [0]}, "WORD_BUDGET"),
        ]
        for proposal, expected in cases:
            with self.subTest(proposal=proposal):
                content, codes = presentation.validate_proposal(proposal, self.lesson, self.state, ())
                self.assertIsNone(content)
                self.assertIn(expected, codes)

    def test_no_proposal_is_not_a_defect(self) -> None:
        self.assertEqual(presentation.validate_proposal(None, self.lesson, self.state, ()), (None, ()))

    def test_regeneration_is_refused_once_the_lesson_is_done(self) -> None:
        state = dict(self.state, phase="done")
        content, codes = presentation.validate_proposal(
            {"teach_md": "Another view of the same position.", "frame_indices": [0]}, self.lesson, state, ()
        )
        self.assertIsNone(content)
        self.assertEqual(codes, ("PRESENTATION_NOT_ALLOWED",))

    def test_collapsed_intro_step_is_not_reopened_by_a_stale_overlay(self) -> None:
        lesson = {
            "lesson_id": "lesson",
            "revision": "lesson.v1",
            "title": "Lesson",
            "lane": "dsa",
            "representation": "box_index",
            "steps": [{"step_id": "step", "kc": "concept", "skippable": True, "teach": {"md": "old", "frames": [{"type": "box_index", "cells": [1]}]}, "probe": {}}],
        }
        state = engine.start(lesson)
        state.update({"phase": "feedback", "scaffold": 1})
        update = presentation.apply(lesson, state, {"teach_md": "Another view.", "teach_frames": [{"type": "box_index", "cells": [2]}]}, {"prompt_version": "tutor.v3"})
        self.assertEqual(update["version"], 1)
        self.assertEqual(presentation.effective(lesson, state), (None, []))
        view = engine.view(lesson, state)
        self.assertIsNone(view["step"]["teach_md"])
        self.assertEqual(view["step"]["teach_frames"], [])

    def test_overlay_only_applies_to_its_own_step_concept_and_variant(self) -> None:
        content, _ = presentation.validate_proposal(
            {"teach_md": "A clearer view of the same position.", "frame_indices": [0]}, self.lesson, self.state, ()
        )
        presentation.apply(self.lesson, self.state, content or {}, {"prompt_version": "tutor.v3"})
        self.assertEqual(presentation.effective(self.lesson, self.state)[0], "A clearer view of the same position.")

        moved = dict(self.state, step_index=0, variant_index=0)
        self.assertIsNone(presentation.current(self.lesson, moved))
        self.assertEqual(presentation.effective(self.lesson, moved)[0], "old")

    def test_versions_advance_monotonically_from_the_persisted_state(self) -> None:
        first = presentation.apply(self.lesson, self.state, {"teach_md": "One.", "teach_frames": []}, {"prompt_version": "tutor.v3"})
        second = presentation.apply(self.lesson, self.state, {"teach_md": "Two.", "teach_frames": []}, {"prompt_version": "tutor.v3"})
        self.assertEqual((first["version"], first["previous_version"]), (1, 0))
        self.assertEqual((second["version"], second["previous_version"]), (2, 1))
        self.assertEqual(presentation.effective(self.lesson, self.state)[0], "Two.")
        self.assertEqual(self.state["presentation_version"], 2)


if __name__ == "__main__":
    unittest.main()
