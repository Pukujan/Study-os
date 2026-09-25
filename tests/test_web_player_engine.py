"""Pure unit tests for the Study OS lesson player v2 engine."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import web_testkit  # noqa: E402, F401


class PlayerEngineTests(unittest.TestCase):
    def _load_lessons(self):
        from study_os.web.player.content import list_lessons, load_lesson

        return [(lid, load_lesson(lid)) for lid in list_lessons()]

    def _new_state(self, lesson):
        from study_os.web.player.engine import start

        return start(lesson)

    def _first_probe_accept(self, lesson, state):
        step = lesson["steps"][state["step_index"]]
        variant_index = state["variant_index"]
        if variant_index == -1:
            probe = step["probe"]
        else:
            probe = step["variants"][variant_index]["probe"]
        if probe is None:
            return "yes"
        return probe["accept"][0]

    def _first_probe_step(self, lesson):
        for idx, step in enumerate(lesson["steps"]):
            if step.get("probe") is not None:
                return idx
        return None

    def test_every_lesson_passes_check_lesson(self):
        from study_os.web.player.engine import check_lesson

        for lid, lesson in self._load_lessons():
            errors = check_lesson(lesson)
            self.assertEqual(errors, [], f"{lid} failed validation: {errors}")

    def test_view_never_leaks_server_only_fields(self):
        from study_os.web.player import engine

        for _lid, lesson in self._load_lessons():
            state = engine.start(lesson)
            for _ in range(200):
                if state["phase"] == "done":
                    break
                view = engine.view(lesson, state)
                dumped = json.dumps(view)
                for forbidden in ("accept", "solution_md", "hint_md"):
                    self.assertNotIn(f'"{forbidden}"', dumped, f"view leaks {forbidden}")
                # partial and misconceptions should not contain match lists in view.
                probe = view.get("step", {}).get("probe") or {}
                self.assertNotIn("partial", probe)
                self.assertNotIn("misconceptions", probe)
                # advance artificially
                state = engine.attempt(lesson, state, self._first_probe_accept(lesson, state), "text")[0]
                state = engine.next(lesson, state)
            else:
                self.fail("view loop did not reach done within 200 iterations")

    def test_correct_first_try_advances_after_why(self):
        from study_os.web.player import engine

        for _lid, lesson in self._load_lessons():
            state = engine.start(lesson)
            # Skip intro/problem steps that have no probe.
            first_idx = self._first_probe_step(lesson)
            self.assertIsNotNone(first_idx)
            state["step_index"] = first_idx
            state["status_by_step"][lesson["steps"][first_idx]["step_id"]] = "in_progress"
            answer = self._first_probe_accept(lesson, state)
            state, feedback = engine.attempt(lesson, state, answer, "text")
            self.assertEqual(feedback["outcome"], "correct")
            self.assertIn("**", feedback["message_md"])
            self.assertEqual(feedback["sticker"], "correct")
            self.assertEqual(feedback["next_action"], "continue")
            self.assertTrue(feedback["message_md"])  # why / explanation present
            state = engine.next(lesson, state)
            self.assertIn(state["phase"], {"probe", "done"})

    def test_incorrect_flow_answer_reassure_retry_check_advance(self):
        from study_os.web.player import engine

        for _lid, lesson in self._load_lessons():
            state = engine.start(lesson)
            first_idx = self._first_probe_step(lesson)
            self.assertIsNotNone(first_idx)
            state["step_index"] = first_idx
            state["status_by_step"][lesson["steps"][first_idx]["step_id"]] = "in_progress"
            wrong_answer = "this-is-wrong"
            state, feedback = engine.attempt(lesson, state, wrong_answer, "text")
            self.assertEqual(feedback["outcome"], "incorrect")
            self.assertEqual(feedback["sticker"], "reassure")
            self.assertTrue(feedback["reassure"])
            self.assertIn("right answer is", feedback["message_md"].lower())
            self.assertIn("that's okay", feedback["message_md"].lower())
            self.assertEqual(feedback["next_action"], "retry")

            state = engine.next(lesson, state)
            self.assertEqual(state["phase"], "probe")
            self.assertNotEqual(state["variant_index"], -1)

            # Retry correctly.
            state, feedback = engine.attempt(lesson, state, self._first_probe_accept(lesson, state), "text")
            self.assertEqual(feedback["outcome"], "correct")
            self.assertEqual(feedback["next_action"], "continue")
            state = engine.next(lesson, state)

            # One more check before advancing.
            self.assertEqual(state["phase"], "probe")
            state, feedback = engine.attempt(lesson, state, self._first_probe_accept(lesson, state), "text")
            self.assertEqual(feedback["outcome"], "correct")
            state = engine.next(lesson, state)
            self.assertIn(state["phase"], {"probe", "done"})
            break

    def test_partial_acknowledges_and_same_probe(self):
        from study_os.web.player import engine

        lesson = {
            "schema_version": "study-os.player-lesson.v1",
            "lesson_id": "partial-test",
            "revision": "partial-test.v1",
            "lane": "dsa",
            "title": "Partial test",
            "summary": "x",
            "representation": "box_index",
            "golden_ref": "derived",
            "steps": [
                {
                    "step_id": "p1",
                    "kc": "test.partial",
                    "skippable": False,
                    "confirm": False,
                    "teach": {"md": "Test.", "frames": []},
                    "probe": {
                        "prompt_md": "Say 5.",
                        "frames": [],
                        "answer_kind": "integer",
                        "accept": ["5"],
                        "partial": [{"match": ["3"], "note_md": "Three is close."}],
                        "misconceptions": [],
                        "correct_md": "Correct.",
                        "explain_md": "Because.",
                        "explain_frames": [],
                        "solution_md": "s",
                        "hint_md": "h",
                    },
                    "variants": [
                        {
                            "teach_frames": [],
                            "probe": {
                                "prompt_md": "Say 6.",
                                "frames": [],
                                "answer_kind": "integer",
                                "accept": ["6"],
                                "partial": [{"match": ["4"], "note_md": "Four is close."}],
                                "misconceptions": [],
                                "correct_md": "Correct.",
                                "explain_md": "Because.",
                                "explain_frames": [],
                                "solution_md": "s",
                                "hint_md": "h",
                            },
                        },
                        {
                            "teach_frames": [],
                            "probe": {
                                "prompt_md": "Say 7.",
                                "frames": [],
                                "answer_kind": "integer",
                                "accept": ["7"],
                                "partial": [{"match": ["5"], "note_md": "Five is close."}],
                                "misconceptions": [],
                                "correct_md": "Correct.",
                                "explain_md": "Because.",
                                "explain_frames": [],
                                "solution_md": "s",
                                "hint_md": "h",
                            },
                        },
                    ],
                }
            ],
        }

        state = engine.start(lesson)
        state, feedback = engine.attempt(lesson, state, "3", "text")
        self.assertEqual(feedback["outcome"], "partial")
        self.assertIsNone(feedback["sticker"])
        self.assertEqual(feedback["next_action"], "retry_same")
        self.assertIn("close", feedback["message_md"].lower())
        self.assertEqual(state["pending"], "retry_same")
        state = engine.next(lesson, state)
        self.assertEqual(state["phase"], "probe")
        self.assertEqual(state["variant_index"], -1)

    def test_three_misses_advance_needs_review(self):
        from study_os.web.player import engine

        for _lid, lesson in self._load_lessons():
            state = engine.start(lesson)
            first_idx = self._first_probe_step(lesson)
            self.assertIsNotNone(first_idx)
            state["step_index"] = first_idx
            state["status_by_step"][lesson["steps"][first_idx]["step_id"]] = "in_progress"
            target_step_id = lesson["steps"][first_idx]["step_id"]
            for _ in range(3):
                state, feedback = engine.attempt(lesson, state, "wrong", "text")
                if feedback["outcome"] == "partial":
                    # partial resets; count as miss for test purposes
                    state = engine.next(lesson, state)
                    continue
                self.assertEqual(feedback["outcome"], "incorrect")
                state = engine.next(lesson, state)

            self.assertEqual(state["status_by_step"][target_step_id], "needs_review")
            self.assertIn(state["phase"], {"probe", "done"})
            break

    def test_scaffold_rises_and_falls(self):
        from study_os.web.player import engine

        lesson = {
            "schema_version": "study-os.player-lesson.v1",
            "lesson_id": "scaffold-test",
            "revision": "scaffold-test.v1",
            "lane": "dsa",
            "title": "Scaffold test",
            "summary": "x",
            "representation": "box_index",
            "golden_ref": "derived",
            "steps": [
                {
                    "step_id": "s1",
                    "kc": "test.scaffold",
                    "skippable": False,
                    "confirm": False,
                    "teach": {"md": "Teach text.", "frames": []},
                    "probe": {
                        "prompt_md": "Say 1.",
                        "frames": [],
                        "answer_kind": "integer",
                        "accept": ["1"],
                        "partial": [],
                        "misconceptions": [],
                        "correct_md": "Correct.",
                        "explain_md": "Because.",
                        "explain_frames": [],
                        "solution_md": "s",
                        "hint_md": "h",
                    },
                    "variants": [
                        {
                            "teach_frames": [],
                            "probe": {
                                "prompt_md": "Say 2.",
                                "frames": [],
                                "answer_kind": "integer",
                                "accept": ["2"],
                                "partial": [],
                                "misconceptions": [],
                                "correct_md": "Correct.",
                                "explain_md": "Because.",
                                "explain_frames": [],
                                "solution_md": "s",
                                "hint_md": "h",
                            },
                        },
                        {
                            "teach_frames": [],
                            "probe": {
                                "prompt_md": "Say 3.",
                                "frames": [],
                                "answer_kind": "integer",
                                "accept": ["3"],
                                "partial": [],
                                "misconceptions": [],
                                "correct_md": "Correct.",
                                "explain_md": "Because.",
                                "explain_frames": [],
                                "solution_md": "s",
                                "hint_md": "h",
                            },
                        },
                    ],
                },
                {
                    "step_id": "s2",
                    "kc": "test.scaffold2",
                    "skippable": False,
                    "confirm": False,
                    "teach": {"md": "Teach two.", "frames": []},
                    "probe": {
                        "prompt_md": "Say a.",
                        "frames": [],
                        "answer_kind": "text",
                        "accept": ["a"],
                        "partial": [],
                        "misconceptions": [],
                        "correct_md": "Correct.",
                        "explain_md": "Because.",
                        "explain_frames": [],
                        "solution_md": "s",
                        "hint_md": "h",
                    },
                    "variants": [
                        {
                            "teach_frames": [],
                            "probe": {
                                "prompt_md": "Say b.",
                                "frames": [],
                                "answer_kind": "text",
                                "accept": ["b"],
                                "partial": [],
                                "misconceptions": [],
                                "correct_md": "Correct.",
                                "explain_md": "Because.",
                                "explain_frames": [],
                                "solution_md": "s",
                                "hint_md": "h",
                            },
                        },
                        {
                            "teach_frames": [],
                            "probe": {
                                "prompt_md": "Say c.",
                                "frames": [],
                                "answer_kind": "text",
                                "accept": ["c"],
                                "partial": [],
                                "misconceptions": [],
                                "correct_md": "Correct.",
                                "explain_md": "Because.",
                                "explain_frames": [],
                                "solution_md": "s",
                                "hint_md": "h",
                            },
                        },
                    ],
                },
            ],
        }

        state = engine.start(lesson)
        self.assertEqual(state["scaffold"], 0)
        # First correct first try.
        state, _f = engine.attempt(lesson, state, "1", "text")
        state = engine.next(lesson, state)
        self.assertEqual(state["scaffold"], 0)
        # Second correct first try raises scaffold.
        state, _f = engine.attempt(lesson, state, "a", "text")
        state = engine.next(lesson, state)
        self.assertEqual(state["scaffold"], 1)
        # An incorrect lowers scaffold.
        state, _f = engine.attempt(lesson, state, "wrong", "text")
        self.assertEqual(state["scaffold"], 0)

    def test_confused_switches_to_next_variant_same_representation(self):
        from study_os.web.player import engine

        for _lid, lesson in self._load_lessons():
            state = engine.start(lesson)
            first_idx = self._first_probe_step(lesson)
            self.assertIsNotNone(first_idx)
            state["step_index"] = first_idx
            state["status_by_step"][lesson["steps"][first_idx]["step_id"]] = "in_progress"
            prev_variant = state["variant_index"]
            state, feedback = engine.confused(lesson, state)
            self.assertEqual(feedback["next_action"], "retry")
            self.assertTrue(feedback["reassure"])
            state = engine.next(lesson, state)
            self.assertEqual(state["phase"], "probe")
            self.assertNotEqual(state["variant_index"], prev_variant)
            break


class GradingTests(unittest.TestCase):
    def _probe(self, accept, answer_kind="text", partial=None, misconceptions=None):
        return {
            "prompt_md": "x",
            "frames": [],
            "answer_kind": answer_kind,
            "accept": accept,
            "partial": partial or [],
            "misconceptions": misconceptions or [],
            "correct_md": "Correct.",
            "explain_md": "Because.",
            "explain_frames": [],
            "solution_md": "s",
            "hint_md": "h",
        }

    def test_unicode_fractions(self):
        from study_os.web.player.grading import grade

        probe = self._probe(["1/2"], answer_kind="fraction")
        self.assertEqual(grade(probe, "½", "text")[0], "correct")
        self.assertEqual(grade(probe, " ¾ ", "text")[0], "incorrect")

    def test_number_words(self):
        from study_os.web.player.grading import grade

        probe = self._probe(["5"], answer_kind="integer")
        self.assertEqual(grade(probe, "five", "text")[0], "correct")
        self.assertEqual(grade(probe, "twenty", "text")[0], "incorrect")

    def test_voice_phrases(self):
        from study_os.web.player.grading import grade

        probe = self._probe(["3/4"], answer_kind="fraction")
        self.assertEqual(grade(probe, "three quarters", "voice")[0], "correct")
        self.assertEqual(grade(probe, "three fourths", "voice")[0], "correct")

        probe = self._probe(["2/3"], answer_kind="fraction")
        self.assertEqual(grade(probe, "two thirds", "voice")[0], "correct")

        probe = self._probe(["1/2"], answer_kind="fraction")
        self.assertEqual(grade(probe, "one half", "voice")[0], "correct")

        probe = self._probe(["5/7"], answer_kind="fraction")
        self.assertEqual(grade(probe, "five over seven", "voice")[0], "correct")
        self.assertEqual(grade(probe, "five out of seven", "voice")[0], "correct")

    def test_value_equivalent_fractions(self):
        from study_os.web.player.grading import grade

        probe = self._probe(["3/4"], answer_kind="fraction")
        outcome, note, _ = grade(probe, "6/8", "text")
        self.assertEqual(outcome, "correct")
        self.assertIsNotNone(note)
        self.assertIn("same amount", note.lower())

    def test_trailing_punctuation_ignored(self):
        from study_os.web.player.grading import grade

        probe = self._probe(["4"], answer_kind="integer")
        self.assertEqual(grade(probe, "4.", "text")[0], "correct")
        self.assertEqual(grade(probe, "4!", "text")[0], "correct")


class LanesTests(unittest.TestCase):
    def test_lanes_payload_lists_all_four_lanes_and_one_continue_target(self):
        from study_os.web.player import lanes as lanes_module

        progress = {"sliding-window-box": "in_progress"}
        sessions = {"sliding-window-box": "sess-123"}
        payload = lanes_module.lanes_payload(progress, sessions)
        self.assertIn("continue", payload)
        self.assertIn("lanes", payload)
        lane_ids = [lane["lane_id"] for lane in payload["lanes"]]
        self.assertEqual(lane_ids, ["dsa", "hesi", "ai-from-scratch", "study-os"])
        self.assertIsNotNone(payload["continue"])
        self.assertEqual(payload["continue"]["lesson_id"], "sliding-window-box")
        self.assertEqual(payload["continue"]["session_id"], "sess-123")

    def test_continue_falls_back_to_first_not_started(self):
        from study_os.web.player import lanes as lanes_module

        payload = lanes_module.lanes_payload({}, {})
        self.assertIsNotNone(payload["continue"])
        # DSA lane has a lesson, so it should be first not-started target.
        self.assertEqual(payload["continue"]["lane"], "dsa")
        self.assertEqual(payload["continue"]["label"], "Start")


class RenderTextTests(unittest.TestCase):
    def test_box_index_frame_text(self):
        from study_os.web.player.render_text import frame_to_text

        frame = {
            "type": "box_index",
            "array": [4, 7, 2],
            "show_positions": True,
            "show_indices": True,
            "box": {"start": 1, "k": 2},
        }
        text = frame_to_text(frame)
        self.assertIn("positions(p)", text)
        self.assertIn("index(i)", text)
        self.assertIn("4", text)

    def test_fraction_bar_frame_text(self):
        from study_os.web.player.render_text import frame_to_text

        frame = {
            "type": "fraction_bar",
            "bars": [{"parts": 4, "shaded": 3, "label": "3/4"}],
        }
        text = frame_to_text(frame)
        self.assertIn("###.", text)
        self.assertIn("3/4", text)


if __name__ == "__main__":
    unittest.main()
