from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tools" / "replay_stateful_study_os.py"
ADAPTER_PATH = ROOT / "tools" / "replay_opencode_adapter.py"
PLAN_PATH = ROOT / "datasets" / "dsa-live-stateful.v0.1.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


stateful = _load_module("stateful_replay_contract", RUNNER_PATH)
adapter = _load_module("opencode_replay_contract", ADAPTER_PATH)


class StatefulReplayContractTests(unittest.TestCase):
    def test_live_plan_has_fifteen_two_sum_moves_and_state_conditions(self) -> None:
        plan = stateful.load_plan(PLAN_PATH)
        scenario = next(
            item for item in plan["scenarios"] if item["id"] == "two-sum-dictionary"
        )
        self.assertEqual(len(scenario["moves"]), 15)
        self.assertEqual(scenario["terminal_steps"], ["two_sum_final"])
        for move in scenario["moves"]:
            self.assertTrue(move["when_steps"])
            self.assertTrue(move["learner_message"].strip())
            self.assertNotIn("expected", move)

    def test_move_selection_uses_actual_backend_step(self) -> None:
        moves = [
            {"id": "a", "when_steps": ["goal"]},
            {"id": "b", "when_steps": ["needed"]},
            {"id": "c", "when_steps": ["goal"]},
        ]
        first = stateful._select_move(moves, set(), "goal")
        self.assertEqual(first[1]["id"], "a")
        second = stateful._select_move(moves, {0}, "goal")
        self.assertEqual(second[1]["id"], "c")
        needed = stateful._select_move(moves, {0}, "needed")
        self.assertEqual(needed[1]["id"], "b")
        self.assertIsNone(stateful._select_move(moves, {0, 2}, "goal"))

    def test_pedagogy_and_authority_are_independent(self) -> None:
        expected = {
            "must_include_any": ["needed", "target"],
            "must_not_include": ["seen"],
            "visual_required": True,
            "max_nonempty_lines": 8,
            "must_ask_question": True,
        }
        backend = "```text\ntarget = 9\nneeded = 7\n```\nWhat is needed?"
        self.assertEqual(stateful.grade_pedagogy(expected, backend), [])
        luna = backend + "\nExtra explanation"
        self.assertNotEqual(luna, backend)

    def test_adapter_extracts_backend_tool_text_and_final_luna_text_separately(self) -> None:
        backend = "```text\nindex | 0 | 1\n```\nWhich indexes?"
        response = {
            "info": {"role": "assistant", "agent": "luna"},
            "parts": [
                {
                    "type": "tool",
                    "tool": "study-os-replay_get_problem_turn",
                    "state": {
                        "output": json.dumps(
                            {
                                "turn": {
                                    "turns": [
                                        {
                                            "canonical_step_id": "two_sum_goal_probe",
                                            "learner_visible_markdown": backend,
                                        }
                                    ]
                                }
                            }
                        )
                    },
                },
                {"type": "text", "text": backend + "\nI added this."},
            ],
        }
        snapshots = adapter.LunaActor._tool_snapshots(response)
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0]["backend_message"], backend)
        self.assertEqual(snapshots[0]["backend_step"], "two_sum_goal_probe")
        self.assertEqual(
            adapter.LunaActor._assistant_text(response), backend + "\nI added this."
        )
        self.assertNotEqual(
            adapter.LunaActor._assistant_text(response),
            snapshots[0]["backend_message"],
        )


if __name__ == "__main__":
    unittest.main()
