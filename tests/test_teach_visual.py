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

    def test_default_shows_curve_not_empty_table(self):
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "1"}):
            md, frames = presentation.effective(self.lesson, self.state)
        self.assertNotRegex(md, r"(?m)^\s*\d+[.)]\s")
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0]["type"], "growth_curve")
        self.assertEqual(frames[0]["n_values"], [2, 4, 8, 16])
        labels = [s["label"] for s in frames[0]["series_multi"]]
        self.assertEqual(labels, ["O(1)", "O(log n)", "O(n)", "O(n²)"])

    def test_flag_off_restores_raw_table_without_data_loss(self):
        raw = self.teach["presentation_raw"]
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "0"}):
            md, frames = presentation.effective(self.lesson, self.state)
            # resolve_teach alone still returns raw md when flag is off.
            resolved_md, resolved_frames = teach_visual.resolve_teach(self.teach)
        self.assertEqual(resolved_md, raw["md"])
        self.assertEqual(resolved_frames[0]["type"], "growth_table")
        # Flag restores the table; plain-human rewrite still numbers serve-time copy.
        self.assertIn("Big O", md)
        self.assertNotRegex(md, r"(?m)^\s*\d+[.)]\s")
        self.assertIn("how work grows", md.lower())
        self.assertEqual(frames[0]["type"], "growth_table")
        self.assertEqual(frames[0]["n_values"], [2, 4, 8, 16])
        # Upgraded frames remain in the lesson file.
        self.assertEqual(self.teach["frames"][0]["type"], "growth_curve")
        self.assertEqual(self.teach["frames"][1]["type"], "growth_workers")

    def test_worked_example_is_not_teach_duplicate(self):
        state, info = engine.adapt(self.lesson, self.state, "example")
        self.assertEqual(info["card_mode"], "worked_example")
        payload = state["worked_example"]
        teach_md = self.teach["md"]
        self.assertNotEqual(payload["solution_md"].strip(), teach_md.strip())
        self.assertNotRegex(payload["solution_md"], r"(?m)^\s*\d+[.)]\s")
        # Distinct diagram from the default teach multi-class curve.
        self.assertEqual(payload["frames"][0]["type"], "growth_workers")

    def test_worked_example_alt_rotates_diagram(self):
        state, _ = engine.adapt(self.lesson, self.state, "example")
        first_type = state["worked_example"]["frames"][0]["type"]
        state, info = engine.adapt(self.lesson, state, "example")
        self.assertEqual(info["variant_tag"], "example_alt")
        payload = state["worked_example"]
        self.assertNotEqual(payload["frames"][0]["type"], first_type)
        self.assertEqual(payload["frames"][0]["type"], "growth_curve")
        self.assertEqual(payload["frames"][0].get("highlight_label"), "O(1)")

    def test_explain_reserve_changes_frame(self):
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "1"}):
            content, codes = presentation.authored_reserve(self.lesson, self.state, ())
        self.assertEqual(codes, ())
        self.assertIsNotNone(content)
        assert content is not None
        self.assertEqual(content["teach_frames"][0]["type"], "growth_workers")

    def test_render_text_workers_and_curve(self):
        curve = frame_to_text(self.teach["frames"][0])
        workers = frame_to_text(self.teach["frames"][1])
        self.assertIn("workers", workers)
        self.assertIn("n=2", workers)
        self.assertIn("O(1)", curve)
        self.assertIn("O(n²)", curve)


if __name__ == "__main__":
    unittest.main()


class AdaptReexplainFrameTypeSwapTests(unittest.TestCase):
    """Explain again must change the visible frame *type*, not only prose."""

    def test_big_o_reexplain_swaps_curve_to_workers(self):
        lesson = load_lesson("big-o-growth-families")
        state = engine._new_state(lesson)
        before = teach_visual.resolve_teach(lesson["steps"][0]["teach"])[1]
        self.assertEqual(before[0]["type"], "growth_curve")
        state, info = engine.adapt(lesson, state, "reexplain")
        self.assertTrue(info.get("frames_changed"))
        after = presentation.effective(lesson, state)[1]
        self.assertEqual(after[0]["type"], "growth_workers")

    def test_big_o_reexplain_twice_keeps_typed_frames(self):
        """Two+ Explain again clicks must never emit a frame missing .type."""
        lesson = load_lesson("big-o-growth-families")
        state = engine._new_state(lesson)
        seen = []
        for _ in range(4):
            state, info = engine.adapt(lesson, state, "reexplain")
            self.assertFalse(info.get("refused"), info)
            frames = presentation.effective(lesson, state)[1]
            self.assertTrue(frames, "reexplain must keep at least one frame")
            for frame in frames:
                self.assertIsInstance(frame, dict)
                self.assertIsInstance(frame.get("type"), str)
                self.assertTrue(frame["type"])
            seen.append(frames[0]["type"])
        # Must actually rotate types across clicks, not stick on one diagram.
        self.assertGreaterEqual(len(set(seen)), 2, seen)
