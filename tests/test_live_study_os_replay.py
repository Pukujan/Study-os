from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tools" / "replay_stateful_study_os.py"
PLAN_PATH = ROOT / "datasets" / "dsa-live-stateful.v0.1.json"

spec = importlib.util.spec_from_file_location("study_os_stateful_replay", RUNNER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("unable to load stateful Study OS replay runner")
stateful_replay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = stateful_replay
spec.loader.exec_module(stateful_replay)


@unittest.skipUnless(
    os.environ.get("STUDY_OS_REPLAY_ACTOR_CMD"),
    "set STUDY_OS_REPLAY_ACTOR_CMD to run the connected Study OS actor",
)
class ConnectedStudyOSReplayTests(unittest.TestCase):
    """Opt-in truthful learner-visible regression against Study OS + Luna."""

    def test_two_sum_stateful_scenario_has_no_truthful_replay_failures(self) -> None:
        plan = stateful_replay.load_plan(PLAN_PATH)
        scenario = next(
            item for item in plan["scenarios"] if item["id"] == "two-sum-dictionary"
        )
        report = stateful_replay.run_scenario(
            scenario,
            os.environ["STUDY_OS_REPLAY_ACTOR_CMD"],
        )
        self.assertEqual(report["executed_turns"], 15)
        self.assertEqual(report["used_moves"], 15)
        self.assertEqual(
            report["failed_records"],
            0,
            msg=f"first divergence: {report['first_divergence']}",
        )


if __name__ == "__main__":
    unittest.main()
