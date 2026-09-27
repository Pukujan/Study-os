"""teach_visual_v1 flag + Big O step-1 metaphor selection."""

from __future__ import annotations

import os
import json
import re
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
        self.assertEqual(self.teach["frames"][1]["type"], "growth_curve")

    def test_worked_example_is_not_teach_duplicate(self):
        state, info = engine.adapt(self.lesson, self.state, "example")
        self.assertEqual(info["card_mode"], "worked_example")
        payload = state["worked_example"]
        teach_md = self.teach["md"]
        self.assertNotEqual(payload["solution_md"].strip(), teach_md.strip())
        self.assertNotRegex(payload["solution_md"], r"(?m)^\s*\d+[.)]\s")
        # Distinct diagram from the default teach multi-class curve (#161).
        self.assertEqual(payload["frames"][0]["type"], "growth_curve")
        self.assertEqual(payload["frames"][0].get("highlight_label"), "O(n)")

    def test_worked_example_alt_rotates_diagram(self):
        state, _ = engine.adapt(self.lesson, self.state, "example")
        first = state["worked_example"]["frames"][0]
        state, info = engine.adapt(self.lesson, state, "example")
        self.assertEqual(info["variant_tag"], "example_alt")
        payload = state["worked_example"]
        alt = payload["frames"][0]
        # Same curve component, different card: the highlighted class rotates.
        self.assertNotEqual(alt.get("highlight_label"), first.get("highlight_label"))
        self.assertEqual(payload["frames"][0]["type"], "growth_curve")
        self.assertEqual(payload["frames"][0].get("highlight_label"), "O(1)")

    def test_explain_reserve_changes_frame(self):
        with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "1"}):
            content, codes = presentation.authored_reserve(self.lesson, self.state, ())
        self.assertEqual(codes, ())
        self.assertIsNotNone(content)
        assert content is not None
        self.assertEqual(content["teach_frames"][0]["type"], "growth_curve")
        self.assertEqual(content["teach_frames"][0].get("highlight_label"), "O(n²)")

    def test_render_text_four_class_curve_and_single_class_curve(self):
        curve = frame_to_text(self.teach["frames"][0])
        single = frame_to_text(self.teach["frames"][1])
        self.assertIn("n:", curve)
        self.assertIn("O(1)", curve)
        self.assertIn("O(n²)", curve)
        self.assertIn("O(n²)", single)


if __name__ == "__main__":
    unittest.main()


class AdaptReexplainFrameTypeSwapTests(unittest.TestCase):
    """Explain again must change the visible frame *type*, not only prose."""

    def test_big_o_reexplain_swaps_to_the_alternate_curve(self):
        lesson = load_lesson("big-o-growth-families")
        state = engine._new_state(lesson)
        before = teach_visual.resolve_teach(lesson["steps"][0]["teach"])[1]
        self.assertEqual(before[0]["type"], "growth_curve")
        self.assertIsNone(before[0].get("highlight_label"))
        state, info = engine.adapt(lesson, state, "reexplain")
        self.assertTrue(info.get("frames_changed"))
        after = presentation.effective(lesson, state)[1]
        self.assertEqual(after[0]["type"], "growth_curve")
        self.assertEqual(after[0].get("highlight_label"), "O(n²)")

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
            seen.append(
                (
                    frames[0]["type"],
                    frames[0].get("highlight_label"),
                    tuple(s["label"] for s in (frames[0].get("series_multi") or [])),
                    frames[0].get("caption"),
                )
            )
        # Must actually rotate the diagram across clicks, not stick on one card.
        self.assertGreaterEqual(len(set(seen)), 2, seen)


class BigOFourClassCurveTests(unittest.TestCase):
    """Per-class teach steps ship one 4-class series_multi curve (#161)."""

    EXPECTED_LABELS = ["O(1)", "O(log n)", "O(n)", "O(n²)"]
    HIGHLIGHT_BY_STEP = {
        "o1_constant": "O(1)",
        "ologn": "O(log n)",
        "on_linear": "O(n)",
        "on2_quadratic": "O(n²)",
    }

    def setUp(self):
        self.lesson = load_lesson("big-o-growth-families")

    def test_per_class_teach_highlights_the_class_being_taught(self):
        for step in self.lesson["steps"]:
            step_id = step["step_id"]
            if step_id not in self.HIGHLIGHT_BY_STEP:
                continue
            with self.subTest(step=step_id):
                frames = step["teach"]["frames"]
                self.assertTrue(frames)
                curve = frames[0]
                self.assertEqual(curve["type"], "growth_curve")
                labels = [s["label"] for s in curve["series_multi"]]
                self.assertEqual(labels, self.EXPECTED_LABELS)
                self.assertEqual(curve.get("highlight_label"), self.HIGHLIGHT_BY_STEP[step_id])

    def test_no_default_path_frame_uses_the_workers_metaphor(self):
        for step in self.lesson["steps"]:
            with self.subTest(step=step["step_id"]):
                for frame in step["teach"].get("frames") or []:
                    self.assertNotEqual(frame["type"], "growth_workers")
                for key in ("worked_example", "worked_example_alt"):
                    for frame in ((step.get(key) or {}).get("frames") or []):
                        self.assertNotEqual(frame["type"], "growth_workers")


class SlidingWindowMultiRepresentationTests(unittest.TestCase):
    """sliding-window-box.v1 ships real multi-representation frames (#126).

    The first DSA lesson must change the *picture* on Explain again, not only the
    prose: each step keeps its geometry frames as the default card and offers
    authored code/flow frames as the alternate card.
    """

    LESSON_ID = "sliding-window-box"
    STEP_ORDER = ["problem", "position", "index", "box-size", "box-start", "window-sum"]
    GEOMETRY = "box_index"
    NON_GEOMETRY = ("code_block", "mermaid_flow")

    def setUp(self):
        self.lesson = load_lesson(self.LESSON_ID)

    def test_step_order_and_revision_unchanged(self):
        self.assertEqual(self.lesson["revision"], "sliding-window-box.v1")
        self.assertEqual([s["step_id"] for s in self.lesson["steps"]], self.STEP_ORDER)

    def test_every_step_declares_a_disjoint_in_range_alt_card(self):
        for step in self.lesson["steps"]:
            with self.subTest(step=step["step_id"]):
                teach = step["teach"]
                frames = teach["frames"]
                cfg = teach.get("teach_visual_v1")
                self.assertIsInstance(cfg, dict, "every step needs a teach_visual_v1 block")
                default = cfg["default_frame_indices"]
                explain = cfg["explain_frame_indices"]
                self.assertTrue(default)
                self.assertTrue(explain)
                self.assertEqual(len(set(default)), len(default))
                self.assertEqual(len(set(explain)), len(explain))
                self.assertFalse(set(default) & set(explain))
                for idx in default + explain:
                    self.assertGreaterEqual(idx, 0)
                    self.assertLess(idx, len(frames))
                # The engine must agree with the literal JSON, not merely parse it.
                self.assertEqual(teach_visual.default_frame_indices(teach), default)
                self.assertEqual(teach_visual.explain_frame_indices(teach), explain)

    def test_default_card_is_still_the_geometry_frame(self):
        for step in self.lesson["steps"]:
            with self.subTest(step=step["step_id"]):
                teach = step["teach"]
                frames = teach["frames"]
                default = teach_visual.default_frame_indices(teach)
                selected = teach_visual.select_frames(teach, default)
                self.assertTrue(selected)
                for frame in selected:
                    self.assertEqual(frame["type"], self.GEOMETRY)
                # The authored pool keeps the original geometry frames first, in order.
                self.assertEqual(selected, frames[: len(default)])

    def test_explain_again_returns_a_different_picture(self):
        for step in self.lesson["steps"]:
            with self.subTest(step=step["step_id"]):
                teach = step["teach"]
                on_screen = teach_visual.select_frames(
                    teach, teach_visual.default_frame_indices(teach)
                )
                alt = teach_visual.alternate_indices(teach, list(on_screen))
                self.assertTrue(alt, "Explain again must have an authored alternate card")
                alt_frames = teach_visual.select_frames(teach, alt)
                self.assertTrue(alt_frames)
                self.assertNotEqual(alt_frames, on_screen)
                for frame in alt_frames:
                    self.assertIn(frame["type"], self.NON_GEOMETRY)

    def test_required_frame_type_coverage(self):
        types_by_step = {}
        seen = set()
        for step in self.lesson["steps"]:
            types = [f["type"] for f in step["teach"]["frames"]]
            types_by_step[step["step_id"]] = types
            seen.update(types)
            self.assertEqual(types[0], self.GEOMETRY)
        self.assertEqual(seen, {self.GEOMETRY, "code_block", "mermaid_flow"})
        for step_id in ("problem", "index", "window-sum"):
            self.assertIn("code_block", types_by_step[step_id])
            self.assertIn("mermaid_flow", types_by_step[step_id])
        for step_id in ("position", "box-size", "box-start"):
            self.assertTrue(set(types_by_step[step_id]) & set(self.NON_GEOMETRY))

    def test_flows_stay_small_and_short_labelled(self):
        for step in self.lesson["steps"]:
            for frame in step["teach"]["frames"]:
                if frame["type"] != "mermaid_flow":
                    continue
                with self.subTest(step=step["step_id"], caption=frame.get("caption")):
                    self.assertTrue(frame["source"].startswith("graph "))
                    nodes = re.findall(r'\["([^"]*)"\]', frame["source"])
                    self.assertTrue(nodes)
                    self.assertLessEqual(len(nodes), 8)
                    for label in nodes:
                        self.assertLessEqual(len(label.split()), 6, label)
                    if frame.get("direction") == "LR":
                        self.assertLessEqual(len(nodes), 4)

    def test_legacy_flag_keeps_the_original_geometry_card(self):
        for step in self.lesson["steps"]:
            with self.subTest(step=step["step_id"]):
                teach = step["teach"]
                authored_md = teach["md"]
                with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "0"}):
                    md, frames = teach_visual.resolve_teach(teach)
                self.assertEqual(md, authored_md)
                base = len(teach_visual.default_frame_indices(teach))
                self.assertEqual(frames[:base], teach["frames"][:base])
                for frame in frames[:base]:
                    self.assertEqual(frame["type"], self.GEOMETRY)

    def test_alternate_cards_never_state_the_open_probe_answer(self):
        """An alternate card is served while the step's probe is still open.

        The geometry default already shows the array, so plain values are fine;
        what is banned is the answer *claim* for that step (for example
        ``p = 4`` for number 6, ``a[1:4] = [7, 2, 6]``, or ``sum[i=2] = 9``).
        """

        banned_claims = {
            "position": ["p = 4", "p=4", "position 4"],
            "index": ["i = 3", "i=3", "index 3"],
            "box-size": ["4, 7, 2", "4 7 2", "[4, 7, 2]"],
            "box-start": ["7, 2, 6", "7 2 6", "[7, 2, 6]", "a[1:4]"],
            "window-sum": ["sum[2]", "sum[i=2]", "= 9", "2 + 6 + 1", "2+6+1"],
        }
        # The array itself is public: the geometry default frame already shows it.
        array_literal = "4, 7, 2, 6, 1, 9"
        for step in self.lesson["steps"]:
            claims = banned_claims.get(step["step_id"])
            if not claims:
                continue
            teach = step["teach"]
            default = set(teach_visual.default_frame_indices(teach))
            for index, frame in enumerate(teach["frames"]):
                if index in default:
                    continue
                blob = json.dumps(frame, ensure_ascii=False).replace(array_literal, " the array ")
                with self.subTest(step=step["step_id"], index=index):
                    for claim in claims:
                        self.assertNotIn(claim, blob)

    def test_flag_on_serves_only_the_default_card(self):
        for step in self.lesson["steps"]:
            with self.subTest(step=step["step_id"]):
                teach = step["teach"]
                with mock.patch.dict(os.environ, {teach_visual.FLAG_ENV: "1"}):
                    md, frames = teach_visual.resolve_teach(teach)
                self.assertEqual(md, teach["md"])
                self.assertEqual(
                    frames,
                    teach_visual.select_frames(teach, teach_visual.default_frame_indices(teach)),
                )
                for frame in frames:
                    self.assertEqual(frame["type"], self.GEOMETRY)


class SlidingWindowReexplainRotationTests(unittest.TestCase):
    """Explain again must rotate the visible card for sliding-window-box (#126)."""

    def setUp(self):
        self.lesson = load_lesson("sliding-window-box")

    def test_reexplain_swaps_geometry_for_algebra_or_flow(self):
        state = engine._new_state(self.lesson)
        before = presentation.effective(self.lesson, state)[1]
        self.assertTrue(before)
        self.assertEqual({f["type"] for f in before}, {"box_index"})
        state, info = engine.adapt(self.lesson, state, "reexplain")
        self.assertTrue(info.get("frames_changed"), info)
        after = presentation.effective(self.lesson, state)[1]
        self.assertTrue(after)
        self.assertNotEqual(after, before)
        self.assertTrue({f["type"] for f in after} & {"code_block", "mermaid_flow"})

    def test_repeated_reexplain_never_returns_an_empty_or_typeless_card(self):
        state = engine._new_state(self.lesson)
        seen = []
        for _ in range(4):
            state, info = engine.adapt(self.lesson, state, "reexplain")
            self.assertFalse(info.get("refused"), info)
            frames = presentation.effective(self.lesson, state)[1]
            self.assertTrue(frames, "Explain again must keep at least one frame")
            for frame in frames:
                self.assertIsInstance(frame, dict)
                self.assertIsInstance(frame.get("type"), str)
                self.assertTrue(frame["type"])
            seen.append(tuple(f["type"] for f in frames))
        self.assertGreaterEqual(len(set(seen)), 2, seen)
