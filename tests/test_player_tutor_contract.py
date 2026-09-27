"""Focused contract tests for the guarded step tutor (prompt, tool, retry, re-render)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web_testkit import requires_web  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


LESSON = {
    "lesson_id": "lesson",
    "revision": "lesson.v1",
    "steps": [
        {
            "step_id": "position",
            "kc": "sliding-window.position",
            "skippable": False,
            "teach": {"md": "old", "frames": [{"type": "box_index", "array": [4, 7, 2], "show_positions": True}]},
            "probe": {"prompt_md": "Which position holds 4?", "accept": ["1"], "frames": []},
        }
    ],
}
STATE = {"step_index": 0, "variant_index": -1, "phase": "probe", "scaffold": 0, "card_mode": "probe"}
RENDER_MD = "Count from the left edge."
EXPECTED_TEACH_MD = "1) Count from the left edge."


def settings() -> SimpleNamespace:
    return SimpleNamespace(
        llm_primary_route="cb/glm-5.3",
        llm_fallback_route="cb/deepseek-v4.1-flash",
        tutor_prompt_version="tutor.v3",
    )


class FakeLLM:
    """Records the tool each call used and replays scripted answers per tool."""

    def __init__(self, main: list[object], render: list[object] | None = None) -> None:
        self._script = {"tutor_reply": list(main), "regenerate_presentation": list(render or [])}
        self.calls: list[str] = []

    def complete(self, routes, messages, tool, max_tokens=700):
        from study_os.web.models import LLMResponse

        name = tool["function"]["name"]
        self.calls.append(name)
        answer = self._script[name].pop(0) if self._script[name] else {"reply_md": "Look at the left column."}
        if isinstance(answer, Exception):
            raise answer
        return LLMResponse(routes[0], answer, 10, 10, 0.0, 1)


def unusable() -> Exception:
    from study_os.web.models import ModelUnavailable

    return ModelUnavailable("all_routes_failed:no_tool_call,no_tool_call")


@requires_web
class TutorRegenerationContractTests(unittest.TestCase):
    def test_tool_schema_offers_a_concrete_render_object(self) -> None:
        from study_os.web.player import tutor

        render = tutor.TOOL["function"]["parameters"]["properties"]["regenerate_presentation"]
        # A nullable object type invites the model to answer with ``null`` instead of
        # proposing a re-render; the property is optional, so it can simply be omitted.
        self.assertEqual(render["type"], "object")
        self.assertNotIn("regenerate_presentation", tutor.TOOL["function"]["parameters"]["required"])
        # The focused re-render call has a tool of its own, so the refresh does not
        # depend on how much of a combined tool call survived.
        self.assertEqual(tutor.RENDER_TOOL["function"]["name"], "regenerate_presentation")

    def test_context_declares_whether_regeneration_is_allowed(self) -> None:
        from study_os.web.player import tutor

        context = json.loads(tutor.build_messages(LESSON, STATE, "show me another way", [], "tutor.v3")[1]["content"])
        self.assertIs(context["regeneration_allowed"], True)
        done = dict(STATE, phase="done")
        context = json.loads(tutor.build_messages(LESSON, done, "show me another way", [], "tutor.v3")[1]["content"])
        self.assertIs(context["regeneration_allowed"], False)

    def test_the_prompt_tells_the_model_what_the_flag_means(self) -> None:
        from study_os.web.player import tutor

        system = tutor.build_messages(LESSON, STATE, "hi", [], "tutor.v3")[0]["content"]
        self.assertIn("regeneration_allowed", system)
        self.assertIn("regenerate_presentation", system)

    def test_a_dropped_tool_call_is_retried_once(self) -> None:
        from study_os.web.player import tutor

        llm = FakeLLM(
            main=[unusable(), {"reply_md": "Look at the left column.", "suggested_action": None}],
            render=[{"teach_md": RENDER_MD, "frame_indices": [0]}],
        )
        result = tutor.reply(llm, settings(), LESSON, STATE, "show me another way")
        self.assertEqual(llm.calls, ["tutor_reply", "tutor_reply", "regenerate_presentation"])
        self.assertEqual(result.served, "generated")
        self.assertEqual(result.reply_md, "Look at the left column.")
        self.assertEqual(result.regenerate_presentation["teach_md"], EXPECTED_TEACH_MD)

    def test_both_attempts_failing_still_falls_back_cleanly(self) -> None:
        from study_os.web.player import tutor

        llm = FakeLLM(main=[unusable(), unusable()], render=[unusable(), unusable()])
        result = tutor.reply(llm, settings(), LESSON, STATE, "show me another way")
        self.assertEqual(result.served, "fallback")
        self.assertEqual(result.regenerate_presentation, None)
        codes = result.validation_codes
        self.assertTrue(any(code.startswith("model_unavailable:") for code in codes))
        self.assertIn("render_unavailable:all_routes_failed:no_tool_call,no_tool_call", codes)
        # The focused render call is retried too, and the authored card is never
        # re-published as a new version because it is identical to the served one.
        self.assertEqual(llm.calls, ["tutor_reply", "tutor_reply", "regenerate_presentation", "regenerate_presentation"])
        self.assertNotIn("RENDER_AUTHORED_RESERVE", codes)

    def test_a_missing_render_is_refreshed_by_the_focused_call(self) -> None:
        from study_os.web.player import tutor

        llm = FakeLLM(
            main=[{"reply_md": "Look at the left column.", "suggested_action": None}],
            render=[{"teach_md": RENDER_MD, "frame_indices": [0]}],
        )
        result = tutor.reply(llm, settings(), LESSON, STATE, "show me another way")
        self.assertEqual(llm.calls, ["tutor_reply", "regenerate_presentation"])
        self.assertEqual(result.served, "generated")
        self.assertEqual(result.regenerate_presentation["teach_md"], EXPECTED_TEACH_MD)
        self.assertEqual(result.regenerate_presentation["teach_frames"], LESSON["steps"][0]["teach"]["frames"])

    def test_no_render_is_requested_when_regeneration_is_not_allowed(self) -> None:
        from study_os.web.player import tutor

        llm = FakeLLM(main=[{"reply_md": "Look at the left column.", "suggested_action": None}])
        result = tutor.reply(llm, settings(), LESSON, dict(STATE, phase="done"), "show me another way")
        self.assertEqual(llm.calls, ["tutor_reply"])
        self.assertIsNone(result.regenerate_presentation)

    def test_a_literal_null_suggested_action_is_not_an_adapt_kind(self) -> None:
        from study_os.web.player import tutor

        llm = FakeLLM(
            main=[{"reply_md": "Look at the left column.", "suggested_action": "null"}],
            render=[{"teach_md": RENDER_MD, "frame_indices": [0]}],
        )
        result = tutor.reply(llm, settings(), LESSON, STATE, "show me another way")
        self.assertEqual(result.served, "generated")
        self.assertIsNone(result.suggested_action)

    def test_an_answer_bearing_render_is_refused_and_replaced(self) -> None:
        from study_os.web.player import tutor

        leaky = {"teach_md": "The position is 1.", "frame_indices": [0]}
        llm = FakeLLM(
            main=[{"reply_md": "Look at the left column.", "regenerate_presentation": leaky}],
            render=[{"teach_md": RENDER_MD, "frame_indices": [0]}],
        )
        result = tutor.reply(llm, settings(), LESSON, STATE, "show me another way")
        self.assertEqual(llm.calls, ["tutor_reply", "regenerate_presentation"])
        self.assertIn("ANSWER_REVEAL_FORBIDDEN", result.validation_codes)
        self.assertEqual(result.regenerate_presentation["teach_md"], EXPECTED_TEACH_MD)

    def test_an_identical_authored_card_is_not_re_published_as_a_new_version(self) -> None:
        from study_os.web.player import tutor

        llm = FakeLLM(main=[{"reply_md": "Look at the left column.", "suggested_action": None}], render=[unusable()])
        result = tutor.reply(llm, settings(), LESSON, STATE, "show me another way")
        self.assertIsNone(result.regenerate_presentation)
        self.assertIn("RENDER_UNAVAILABLE", result.validation_codes)
        self.assertNotIn("RENDER_AUTHORED_RESERVE", result.validation_codes)


if __name__ == "__main__":
    unittest.main()
