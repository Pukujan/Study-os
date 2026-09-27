"""teach_visual_v1 flag + Big O step-1 metaphor selection."""

from __future__ import annotations

import os
import unittest
from unittest import mock

from study_os.web.player import engine, presentation, teach_visual
from study_os.web.player.content import load_lesson
from study_os.web.player.render_text import frame_to_text


class TeachVisualFlagTests(unittest.TestCase):
    def test_enabled_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(teach_visual.FLAG_ENV, None)
            self.assertTrue(teach_visual.enabled())

    def test_disabled_by_zero(self):
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "0"}):
            self.assertFalse(teach_visual.enabled())


class BigOWhyVisualTests(unittest.TestCase):
    def setUp(self):
        self.lesson = load_lesson("big-o-growth-families")
        self.step = self.lesson["steps"][0]
        self.teach = self.step["teach"]
        self.state = engine._new_state(self.lesson)

    def test_default_shows_workers_not_empty_table(self):
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "1"}):
            md, frames = presentation.effective(self.lesson, self.state)
        self.assertIn("1)", md)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0]["type"], "growth_workers")
        self.assertEqual(frames[0]["n_values"], [2, 4, 8, 16])

    def test_flag_off_restores_raw_table_without_data_loss(self):
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "0"}):
            md, frames = presentation.effective(self.lesson, self.state)
        raw = self.teach["presentation_raw"]
        self.assertEqual(md, raw["md"])
        self.assertEqual(frames[0]["type"], "growth_table")
        self.assertEqual(frames[0]["n_values"], [2, 4, 8, 16])
        # Upgraded frames remain in the lesson file.
        self.assertEqual(self.teach["frames"][0]["type"], "growth_workers")

    def test_worked_example_is_not_teach_duplicate(self):
        state, info = engine.adapt(self.lesson, self.state, "example")
        self.assertEqual(info["card_mode"], "worked_example")
        payload = state["worked_example"]
        teach_md = self.teach["md"]
        self.assertNotEqual(payload["solution_md"].strip(), teach_md.strip())
        self.assertIn("1)", payload["solution_md"])
        # Distinct diagram from the default teach workers pile.
        self.assertEqual(payload["frames"][0]["type"], "growth_curve")

    def test_worked_example_alt_rotates_diagram(self):
        state, _ = engine.adapt(self.lesson, self.state, "example")
        first_type = state["worked_example"]["frames"][0]["type"]
        state, info = engine.adapt(self.lesson, state, "example")
        self.assertEqual(info["variant_tag"], "example_alt")
        payload = state["worked_example"]
        self.assertNotEqual(payload["frames"][0]["type"], first_type)
        self.assertEqual(payload["frames"][0]["type"], "growth_workers")

    def test_explain_reserve_changes_frame(self):
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "1"}):
            content, codes = presentation.authored_reserve(self.lesson, self.state, ())
        self.assertEqual(codes, ())
        self.assertIsNotNone(content)
        assert content is not None
        self.assertEqual(content["teach_frames"][0]["type"], "growth_curve")

    def test_render_text_workers_and_curve(self):
        workers = frame_to_text(self.teach["frames"][0])
        curve = frame_to_text(self.teach["frames"][1])
        self.assertIn("workers", workers)
        self.assertIn("n=2", workers)
        self.assertIn("slow growth", curve)


if __name__ == "__main__":
    unittest.main()
