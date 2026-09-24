"""The T0 agent-vs-agent eval harness runs clean and its detectors fire on bad turns."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web_testkit import requires_db, requires_web  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _load() -> object:
    spec = importlib.util.spec_from_file_location("run_agent_evals", ROOT / "tools" / "run_agent_evals.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_agent_evals"] = mod
    spec.loader.exec_module(mod)
    return mod


@requires_web
class DetectorTests(unittest.TestCase):
    def test_detectors_flag_bad_turns(self) -> None:
        ev = _load()
        res = ev.RunResult("p", "dsa", 0, None)  # type: ignore[attr-defined]
        ev.check_turns(res, [  # type: ignore[attr-defined]
            {"markdown": "Great, you have mastered this!", "awaiting": False, "step_id": "x"},
            {"markdown": "What is it? And why?", "awaiting": True, "step_id": "y"},
            {"markdown": "Pick one", "awaiting": True, "step_id": "z", "correct_index": 2},
        ], "dsa")
        codes = {v["code"] for v in res.violations}
        self.assertEqual(codes, {"MASTERY_CLAIM", "MULTI_QUESTION", "MISSING_CHART", "ANSWER_KEY_IN_PAYLOAD"})
        clean = ev.RunResult("p", "dsa", 0, None)  # type: ignore[attr-defined]
        ev.check_turns(clean, [{"markdown": "Independent mastery remains unproven.", "awaiting": False}], "dsa")  # type: ignore[attr-defined]
        self.assertEqual(clean.violations, [])

    def test_reachable_probes_follow_automatic_transitions(self) -> None:
        from study_os.pir.registry import sliding_window_asset

        ev = _load()
        asset = sliding_window_asset()
        self.assertEqual(ev._reachable_probes(asset, "position.e0.n2", "correct"), {"position.e1.n1"})  # type: ignore[attr-defined]
        self.assertNotIn("position.e0.n2", ev._reachable_probes(asset, "position.e0.n2", "incorrect"))  # type: ignore[attr-defined]


@requires_db
class HarnessTests(unittest.TestCase):
    def test_small_run_passes(self) -> None:
        ev = _load()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "score.json"
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = ev.main(["--seeds", "1", "--personas", "diligent,oversharer,injector,hint_seeker", "--out", str(out)])  # type: ignore[attr-defined]
            card = json.loads(out.read_text())
        self.assertEqual(code, 0, card["violations_by_code"])
        self.assertTrue(card["passed"])
        self.assertEqual(card["runs"], 8)
        self.assertGreater(card["db_stats"]["rule_decisions"], 0)


if __name__ == "__main__":
    unittest.main()
