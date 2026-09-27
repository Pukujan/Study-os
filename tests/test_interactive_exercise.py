"""Catalog-wide interactive exercise generator (Refs #161 / #126)."""
from __future__ import annotations
import unittest
from study_os.web.player import interactive_exercise as ix
from study_os.web.player.content import load_lesson

class CatalogGeneratorTests(unittest.TestCase):
    def test_templates_cover_mapped_visual_types(self):
        types = {t["visual_type"] for t in ix.load_templates()["templates"]}
        self.assertIn("multi_class_growth_curve", types)
        self.assertIn("fraction_number_line", types)
        self.assertIn("box_index_array", types)

    def test_generate_all_emits_one_per_mapped_step(self):
        frames = ix.generate_all()
        self.assertGreaterEqual(len(frames), 19)
        kinds = {f.get("exercise_kind") or f.get("type") for f in frames}
        self.assertIn("match_curves", kinds)
        self.assertIn("place_number_line", kinds)

    def test_big_o_match_is_template_not_one_off(self):
        f = ix.generate("big-o-growth-families", "why_care", kind="match_curves")
        self.assertEqual(f["type"], "interactive_visual")
        self.assertEqual(f["exercise_kind"], "match_curves")
        self.assertEqual(len(f["panels"]), 3)
        f2 = ix.generate("big-o-growth-families", "o1_constant", kind="match_curves")
        self.assertEqual(f2["exercise_kind"], "match_curves")

    def test_fractions_place_number_line(self):
        lesson = load_lesson("fractions-compare")
        sid = lesson["steps"][0]["step_id"]
        f = ix.generate("fractions-compare", sid, kind="place_number_line", ctx={"fraction": "1/2"})
        self.assertEqual(f["exercise_kind"], "place_number_line")

    def test_lesson_o1_uses_graph_not_table_default(self):
        lesson = load_lesson("big-o-growth-families")
        o1 = next(s for s in lesson["steps"] if s["step_id"] == "o1_constant")
        self.assertEqual(o1["teach"]["frames"][0]["type"], "growth_curve")
        self.assertNotIn("table stays flat", o1["teach"]["md"].lower())
        self.assertNotRegex(o1["teach"]["md"], r"(?m)^\s*\d+[.)]\s")

if __name__ == "__main__":
    unittest.main()
