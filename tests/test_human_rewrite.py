"""Done-when tests for plain-human rewrite v2 (Refs #126)."""
from __future__ import annotations
import re
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from study_os.web import packs
from study_os.web.player import content, engine, human_rewrite, presentation

MACHINE_WALL = (
    "Health-care math runs on a small set of fixed conversion facts, and most "
    "errors come from memorizing them loosely rather than exactly, highlighting "
    "the need for a comprehensive approach. Furthermore, it is important to note "
    "that the metric relationships are powers of 1,000: 1 g = 1,000 mg. In order "
    "to leverage these facts, you will practice exact conversions today."
)
DSA_TEACH_WALL = (
    "In this lesson we delve into the sliding window, showcasing a pivotal technique "
    "that serves as a robust foundation. Moreover, you will learn to track the left "
    "edge of the box across the array while keeping k fixed."
)
_DIGIT_LIST = re.compile(r"(?m)^\s*\d+[.)]\s")

class HumanRewriteUnitTests(unittest.TestCase):
    def test_prose_not_digit_list_and_scrubs_ai_tells(self) -> None:
        out = human_rewrite.rewrite(MACHINE_WALL, kind="decomposition")
        self.assertFalse(_DIGIT_LIST.search(out))
        self.assertLessEqual(len(out.splitlines()), 4)
        low = out.lower()
        for banned in ("highlighting", "furthermore", "comprehensive", "leverage", "it is important to note"):
            self.assertNotIn(banned, low)
        self.assertLessEqual(human_rewrite._content_words(out), human_rewrite._content_words(MACHINE_WALL))

    def test_teach_step1_prefers_grounding_and_caps_sentences(self) -> None:
        out = human_rewrite.rewrite(DSA_TEACH_WALL, kind="teach")
        self.assertFalse(_DIGIT_LIST.search(out))
        self.assertLessEqual(len(out.splitlines()), 3)
        first = out.splitlines()[0].lower()
        self.assertRegex(first, r"you will|learn|track|practice|look")
        self.assertNotIn("delve", out.lower())
        self.assertNotIn("showcasing", out.lower())

    def test_preserves_trailing_counts_not_eaten_as_lists(self) -> None:
        raw = "1) Use n · log2 n. 2) 16 · 4 = 64. 3) More than 2x24, less than n2."
        out = human_rewrite.rewrite(raw, kind="explain")
        self.assertFalse(_DIGIT_LIST.search(out))
        self.assertIn("64", out)

    def test_idempotent(self) -> None:
        once = human_rewrite.rewrite(MACHINE_WALL, kind="explain")
        twice = human_rewrite.rewrite(once, kind="explain")
        self.assertEqual(once, twice)

    def test_empty_and_fenced_passthrough(self) -> None:
        self.assertEqual(human_rewrite.rewrite("", kind="teach"), "")
        fenced = "See:\n```\ncode\n```\n"
        self.assertEqual(human_rewrite.rewrite(fenced, kind="teach").strip(), fenced.strip())

    def test_explain_budget_trims_tail(self) -> None:
        long_explain = " ".join(f"Fact {i} is true about this probe." for i in range(20))
        out = human_rewrite.rewrite(long_explain, kind="explain")
        self.assertLessEqual(human_rewrite._content_words(out), 36)
        self.assertLessEqual(len(out.splitlines()), 3)

class HumanRewriteHookTests(unittest.TestCase):
    def test_presentation_validate_rewrites_teach_md(self) -> None:
        lesson = {"lesson_id": "lesson", "revision": "lesson.v1", "steps": [
            {"step_id": "step", "kc": "concept", "teach": {"md": "old", "frames": [{"type": "box_index", "cells": [1]}]}, "probe": {}}
        ]}
        state = {"step_index": 0, "variant_index": -1, "phase": "feedback", "scaffold": 0, "card_mode": "probe"}
        content_out, codes = presentation.validate_proposal({"teach_md": DSA_TEACH_WALL, "frame_indices": [0]}, lesson, state, ())
        self.assertEqual(codes, ())
        assert content_out is not None
        self.assertFalse(_DIGIT_LIST.search(content_out["teach_md"]))
        self.assertNotIn("delve", content_out["teach_md"].lower())

    def test_engine_view_teach_is_short_prose(self) -> None:
        lesson = content.load_lesson("fractions-compare")
        state = engine.start(lesson)
        teach = str(engine.view(lesson, state)["step"]["teach_md"])
        self.assertFalse(_DIGIT_LIST.search(teach))
        self.assertLessEqual(len(teach.splitlines()), 3)

    def test_confused_explain_is_rewritten(self) -> None:
        lesson = content.load_lesson("fractions-compare")
        state = engine.start(lesson)
        state, _ = engine.confused(lesson, state)
        feedback = state["feedback"]["message_md"]
        self.assertIn("Let's look at this again.", feedback)
        self.assertFalse(_DIGIT_LIST.search(feedback.split("again.", 1)[-1]))

    def test_worked_example_uses_common_denominator_diagram(self) -> None:
        lesson = content.load_lesson("fractions-compare")
        state = engine.start(lesson)
        teach_frames = engine.view(lesson, state)["step"]["teach_frames"]
        state, _ = engine.adapt(lesson, state, "example")
        view = engine.view(lesson, state)
        md = view["worked_example"]["md"]
        self.assertFalse(_DIGIT_LIST.search(md))
        frames = view["worked_example"]["frames"]
        self.assertTrue(frames)
        self.assertNotEqual(frames, teach_frames)
        self.assertEqual(frames[0]["bars"][0]["parts"], 12)

    def test_reexplain_swaps_teach_diagram(self) -> None:
        lesson = content.load_lesson("fractions-compare")
        state = engine.start(lesson)
        before = engine.view(lesson, state)["step"]["teach_frames"]
        state, info = engine.adapt(lesson, state, "reexplain")
        self.assertTrue(info.get("frames_changed"))
        after = engine.view(lesson, state)["step"]["teach_frames"]
        self.assertNotEqual(before, after)
        self.assertEqual(after[0]["bars"][0]["parts"], 12)

    def test_pack_intro_is_rewritten_without_digit_list(self) -> None:
        topic_id = None
        for section in packs.topic_graph():
            for topic in section["topics"]:
                if topic["available"]:
                    topic_id = topic["topic_id"]
                    break
            if topic_id:
                break
        self.assertIsNotNone(topic_id)
        md = packs.intro_markdown(topic_id)  # type: ignore[arg-type]
        body = md.split("\n\n", 1)[-1]
        self.assertFalse(_DIGIT_LIST.search(body.split("**Key points**")[0]))

if __name__ == "__main__":
    unittest.main()
