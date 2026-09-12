from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "tools" / "replay_dsa_conversations.py"
CORPUS_PATH = ROOT / "datasets" / "dsa-conversation-replay.v0.1.json"

spec = importlib.util.spec_from_file_location("dsa_replay_live", HARNESS_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("unable to load DSA replay harness")
dsa_replay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dsa_replay
spec.loader.exec_module(dsa_replay)


@unittest.skipUnless(
    os.environ.get("STUDY_OS_REPLAY_ACTOR_CMD"),
    "set STUDY_OS_REPLAY_ACTOR_CMD to run the connected Study OS actor",
)
class ConnectedStudyOSReplayTests(unittest.TestCase):
    """Opt-in learner-visible regression against the real connected actor."""

    def test_two_sum_full_scenario_has_no_visible_failures(self) -> None:
        corpus = dsa_replay.load_corpus(CORPUS_PATH)
        report = dsa_replay.run_actor(
            corpus,
            os.environ["STUDY_OS_REPLAY_ACTOR_CMD"],
            scenario_ids={"two-sum-dictionary"},
            max_turns=None,
        )
        self.assertEqual(report["executed_turns"], 15)
        self.assertEqual(
            report["failed_turns"],
            0,
            msg=f"first divergence: {report['first_divergence']}",
        )
