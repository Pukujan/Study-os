"""teach_visual_v1 + Big O multi-class curve + catalog interactives."""
from __future__ import annotations
import os, unittest
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

    def test_default_shows_curve_not_empty_table(self):
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "1"}):
            md, frames = presentation.effective(self.lesson, self.state)
        self.assertNotRegex(md, r"(?m)^\s*\d+[.)]\s")
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0]["type"], "growth_curve")
        labels = [s["label"] for s in frames[0]["series_multi"]]
        self.assertEqual(labels, ["O(1)", "O(log n)", "O(n)", "O(n²)"])

    def test_flag_off_restores_raw_table_without_data_loss(self):
        raw = self.teach["presentation_raw"]
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "0"}):
            md, frames = presentation.effective(self.lesson, self.state)
            resolved_md, resolved_frames = teach_visual.resolve_teach(self.teach)
        self.assertEqual(resolved_md, raw["md"])
        self.assertEqual(resolved_frames[0]["type"], "growth_table")
        self.assertEqual(frames[0]["type"], "growth_table")
        self.assertEqual(self.teach["frames"][0]["type"], "growth_curve")
        self.assertEqual(self.teach["frames"][1]["type"], "curated_diagram")

    def test_worked_example_is_not_teach_duplicate(self):
        state, info = engine.adapt(self.lesson, self.state, "example")
        payload = state["worked_example"]
        self.assertNotEqual(payload["solution_md"].strip(), self.teach["md"].strip())
        self.assertEqual(payload["frames"][0]["type"], "interactive_visual")
        self.assertEqual(payload["frames"][0].get("exercise_kind"), "match_curves")

    def test_worked_example_alt_rotates_diagram(self):
        state, _ = engine.adapt(self.lesson, self.state, "example")
        first_type = state["worked_example"]["frames"][0]["type"]
        state, info = engine.adapt(self.lesson, state, "example")
        self.assertEqual(info["variant_tag"], "example_alt")
        self.assertNotEqual(state["worked_example"]["frames"][0]["type"], first_type)
        self.assertEqual(state["worked_example"]["frames"][0]["type"], "growth_curve")

    def test_explain_reserve_changes_frame(self):
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "1"}):
            content, codes = presentation.authored_reserve(self.lesson, self.state, ())
        self.assertEqual(codes, ())
        self.assertEqual(content["teach_frames"][0]["type"], "curated_diagram")

    def test_render_text_curve(self):
        curve = frame_to_text(self.teach["frames"][0])
        self.assertIn("O(1)", curve)
        self.assertIn("O(n²)", curve)

class AdaptReexplainFrameTypeSwapTests(unittest.TestCase):
    def test_big_o_reexplain_swaps_curve_to_curated(self):
        lesson = load_lesson("big-o-growth-families")
        state = engine._new_state(lesson)
        before = teach_visual.resolve_teach(lesson["steps"][0]["teach"])[1]
        self.assertEqual(before[0]["type"], "growth_curve")
        state, info = engine.adapt(lesson, state, "reexplain")
        self.assertTrue(info.get("frames_changed"))
        after = presentation.effective(lesson, state)[1]
        self.assertEqual(after[0]["type"], "curated_diagram")

if __name__ == "__main__":
    unittest.main()
