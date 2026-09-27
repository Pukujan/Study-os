"""teach_visual_v1 flag + curated multi-class Big O visuals (Refs #161 #126)."""

from __future__ import annotations

import os
import unittest
from unittest import mock

from study_os.web.player import engine, presentation, teach_visual
import json
from pathlib import Path

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

    def test_default_shows_multi_class_curve(self):
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "1"}):
            md, frames = presentation.effective(self.lesson, self.state)
        self.assertNotRegex(md, r"(?m)^\s*\d+[.)]\s")
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0]["type"], "growth_curve")
        self.assertEqual(frames[0]["n_values"], [1, 2, 4, 8, 16])
        labels = [s["label"] for s in frames[0]["series_multi"]]
        self.assertEqual(labels, ["O(1)", "O(log n)", "O(n)", "O(n²)"])
        self.assertEqual(frames[0].get("y_scale"), "log")

    def test_flag_off_restores_raw_table_without_data_loss(self):
        raw = self.teach["presentation_raw"]
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "0"}):
            md, frames = presentation.effective(self.lesson, self.state)
            resolved_md, resolved_frames = teach_visual.resolve_teach(self.teach)
        self.assertEqual(resolved_md, raw["md"])
        self.assertEqual(resolved_frames[0]["type"], "growth_table")
        self.assertIn("Big O", md)
        self.assertNotRegex(md, r"(?m)^\s*\d+[.)]\s")
        self.assertIn("how work grows", md.lower())
        self.assertEqual(frames[0]["type"], "growth_table")
        self.assertEqual(self.teach["frames"][0]["type"], "growth_curve")
        self.assertEqual(self.teach["frames"][1]["type"], "curated_diagram")

    def test_worked_example_is_not_teach_duplicate(self):
        state, info = engine.adapt(self.lesson, self.state, "example")
        self.assertEqual(info["card_mode"], "worked_example")
        payload = state["worked_example"]
        teach_md = self.teach["md"]
        self.assertNotEqual(payload["solution_md"].strip(), teach_md.strip())
        self.assertNotRegex(payload["solution_md"], r"(?m)^\s*\d+[.)]\s")
        self.assertEqual(payload["frames"][0]["type"], "curated_diagram")
        self.assertEqual(
            payload["frames"][0]["asset_id"],
            "big-o.comparison-computational-complexity",
        )

    def test_worked_example_alt_rotates_diagram(self):
        state, _ = engine.adapt(self.lesson, self.state, "example")
        first_type = state["worked_example"]["frames"][0]["type"]
        state, info = engine.adapt(self.lesson, state, "example")
        self.assertEqual(info["variant_tag"], "example_alt")
        payload = state["worked_example"]
        self.assertNotEqual(payload["frames"][0]["type"], first_type)
        self.assertEqual(payload["frames"][0]["type"], "growth_curve")
        self.assertEqual(payload["frames"][0].get("highlight_label"), "O(1)")
        self.assertEqual(payload["frames"][0].get("highlight_label"), "O(1)")

    def test_explain_reserve_changes_frame(self):
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "1"}):
            content, codes = presentation.authored_reserve(self.lesson, self.state, ())
        self.assertEqual(codes, ())
        self.assertIsNotNone(content)
        assert content is not None
        self.assertEqual(content["teach_frames"][0]["type"], "curated_diagram")
        self.assertEqual(
            content["teach_frames"][0]["asset_id"],
            "big-o.comparison-computational-complexity",
        )

    def test_render_text_multi_class_and_curated(self):
        curve = frame_to_text(self.teach["frames"][0])
        curated = frame_to_text(self.teach["frames"][1])
        self.assertIn("O(1)", curve)
        self.assertIn("O(n²)", curve)
        self.assertIn("growth chart (log)", curve)
        self.assertIn("curated diagram", curated)
        self.assertIn("big-o.comparison-computational-complexity", curated)


class AdaptReexplainFrameTypeSwapTests(unittest.TestCase):
    """Explain again must change the visible frame *type*, not only prose."""

    def test_big_o_reexplain_swaps_curve_to_curated_reference(self):
        lesson = load_lesson("big-o-growth-families")
        state = engine._new_state(lesson)
        before = teach_visual.resolve_teach(lesson["steps"][0]["teach"])[1]
        self.assertEqual(before[0]["type"], "growth_curve")
        state, info = engine.adapt(lesson, state, "reexplain")
        self.assertTrue(info.get("frames_changed"))
        after = presentation.effective(lesson, state)[1]
        self.assertEqual(after[0]["type"], "curated_diagram")


class ProvenancePackTests(unittest.TestCase):
    def test_provenance_and_step_map_exist(self):
        root = Path(__file__).resolve().parents[1]
        prov = json.loads((root / "content/teach-visuals/provenance.v1.json").read_text())
        self.assertEqual(prov["schema_version"], "study-os.teach-visual-provenance.v1")
        self.assertGreaterEqual(len(prov["assets"]), 5)
        for asset in prov["assets"]:
            path = root / "content/teach-visuals" / asset["path"]
            self.assertTrue(path.is_file(), asset["path"])
            pub = root / "web/public/teach-visuals" / asset["path"]
            self.assertTrue(pub.is_file(), asset["public_src"])
        step_map = json.loads((root / "content/teach-visuals/step-visual-map.v1.json").read_text())
        self.assertEqual(len(step_map["entries"]), 19)
        statuses = {e["lesson_id"]: e["status"] for e in step_map["entries"]}
        self.assertEqual(statuses["big-o-growth-families"], "landed")
        self.assertEqual(statuses["fractions-compare"], "landed")
        self.assertEqual(statuses["sliding-window-box"], "queued")


if __name__ == "__main__":
    unittest.main()
