"""Focused tests for the synthetic live-player A2A harness."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_player_agent_evals as harness  # noqa: E402


class PlayerAgentEvalTests(unittest.TestCase):
    def test_oracle_prefix_is_pinned_to_player_slice(self) -> None:
        prefix, digest, conforms = harness.golden_prefix()
        self.assertEqual(prefix, ["problem", "position", "index", "box_size_k", "box_start_i", "window_sum"])
        self.assertEqual(len(digest), 64)
        self.assertIsInstance(conforms, bool)

    def test_scripted_personas_are_deterministic(self) -> None:
        self.assertEqual(harness.learner_response("golden", "window-sum", 0), "9")
        self.assertEqual(harness.learner_response("wrong_then_right", "window-sum", 0), "not this")
        self.assertEqual(harness.learner_response("wrong_then_right", "window-sum", 1), "9")
        self.assertEqual(harness.learner_response("partial_then_right", "window-sum", 0), "2 6 1")

    def test_roleplays_get_distinct_stable_client_ips(self) -> None:
        personas = ["golden", "wrong_then_right", "partial_then_right", "confused_then_right"]
        first = {persona: harness.roleplay_ip(persona, 0) for persona in personas}
        second = {persona: harness.roleplay_ip(persona, 1) for persona in personas}
        self.assertEqual(len(set(first.values())), len(personas))
        self.assertEqual(len(set(first.values()) | set(second.values())), 2 * len(personas))
        for persona in personas:
            self.assertEqual(harness.roleplay_ip(persona, 0), first[persona])
            self.assertRegex(first[persona], r"^10\.0\.0\.\d+$")

    def test_missing_render_capability_is_a_failure(self) -> None:
        violations = harness.capability_detector(
            {"reply_md": "Try an example", "suggested_action": "example"},
            {"step": {"step_id": "position"}},
            {"step": {"step_id": "position"}},
        )
        self.assertEqual(violations[0]["code"], "MISSING_REGENERATE_PRESENTATION")

    @staticmethod
    def _render(**overrides: object) -> dict:
        render = {
            "operation": "regenerate_presentation",
            "step_id": "position",
            "concept_id": "kc",
            "version": 1,
            "previous_version": 0,
            "teach_md": "Same box, seen from the left edge.",
        }
        render.update(overrides)
        return render

    def _view(self, **overrides: object) -> dict:
        view = {"step": {"step_id": "position", "concept_id": "kc", "variant": -1, "teach_md": "Same box, seen from the left edge."}, "phase": "probe", "presentation_version": 1}
        view.update(overrides)
        return view

    def test_valid_render_preserves_identity_and_is_applied(self) -> None:
        tutor = {"regenerate_presentation": self._render()}
        self.assertEqual(harness.capability_detector(tutor, self._view(presentation_version=0), self._view()), [])

    def test_render_that_moves_the_step_is_a_failure(self) -> None:
        tutor = {"regenerate_presentation": self._render(step_id="index")}
        codes = [v["code"] for v in harness.capability_detector(tutor, self._view(presentation_version=0), self._view())]
        self.assertEqual(codes, ["INVALID_REGENERATE_PRESENTATION"])

    def test_render_that_skips_a_version_is_a_failure(self) -> None:
        tutor = {"regenerate_presentation": self._render(version=3, previous_version=0)}
        codes = [v["code"] for v in harness.capability_detector(tutor, self._view(presentation_version=0), self._view())]
        self.assertEqual(codes, ["INVALID_REGENERATE_PRESENTATION"])

    def test_text_only_reply_is_still_a_capability_failure(self) -> None:
        tutor = {"reply_md": "Try the left edge.", "regenerate_presentation": None}
        codes = [v["code"] for v in harness.capability_detector(tutor, self._view(presentation_version=0), self._view())]
        self.assertEqual(codes, ["MISSING_REGENERATE_PRESENTATION"])

    def test_unapplied_render_is_a_failure(self) -> None:
        tutor = {"regenerate_presentation": self._render()}
        stale = self._view(presentation_version=0, step={"step_id": "position", "concept_id": "kc", "variant": -1, "teach_md": "authored"})
        codes = [v["code"] for v in harness.capability_detector(tutor, self._view(presentation_version=0), stale)]
        self.assertEqual(codes, ["RENDER_NOT_APPLIED"])

    def test_render_that_advances_the_step_is_a_failure(self) -> None:
        tutor = {"regenerate_presentation": self._render()}
        moved = self._view(phase="feedback")
        codes = [v["code"] for v in harness.capability_detector(tutor, self._view(presentation_version=0), moved)]
        self.assertEqual(codes, ["RENDER_MOVED_STEP"])

    def test_scorecard_is_synthetic_and_machine_readable(self) -> None:
        card = harness.build_scorecard(
            [{"persona": "golden", "seed": 0, "observed_path": [], "events": [], "violations": [], "end_phase": "done"}],
            live=False,
        )
        self.assertEqual(card["schema_version"], harness.SCORECARD_VERSION)
        self.assertTrue(card["synthetic_only"])
        self.assertIn("transcripts", card)
        json.dumps(card)

    def test_review_event_is_golden_adjacent_and_synthetic_only(self) -> None:
        events = [
            {"kind": "view", "step_id": "position"},
            {"kind": "tutor", "step_id": "position", "presentation_version_after": 1},
            {"kind": "review", "step_id": "position", "golden_concept": "position", "presentation_version": 1,
             "rating": 3, "why": "The box helped; the index label was unclear.", "http_status": 200},
            {"kind": "attempt", "step_id": "position", "outcome": "correct"},
        ]
        self.assertEqual(events[2]["golden_concept"], harness.PLAYER_TO_GOLDEN[events[1]["step_id"]])
        self.assertEqual(events[2]["presentation_version"], events[1]["presentation_version_after"])
        card = harness.build_scorecard(
            [{"persona": "golden", "seed": 0, "observed_path": ["position"], "events": events,
              "violations": [], "end_phase": "probe"}], live=False,
        )
        self.assertTrue(card["synthetic_only"])
        self.assertEqual(card["transcripts"][0]["events"][2]["kind"], "review")
        self.assertEqual(harness.review_event_detector(events), [])
        self.assertEqual(harness.review_event_detector(events[:2] + events[3:])[0]["code"], "MISSING_STEP_REVIEW")
        stale = [dict(event) for event in events]
        stale[2]["step_id"] = "index"
        self.assertEqual(harness.review_event_detector(stale)[0]["code"], "INVALID_STEP_REVIEW_EVENT")
        boolean_rating = [dict(event) for event in events]
        boolean_rating[2]["rating"] = True
        self.assertEqual(harness.review_event_detector(boolean_rating)[0]["code"], "INVALID_STEP_REVIEW_EVENT")


if __name__ == "__main__":
    unittest.main()
