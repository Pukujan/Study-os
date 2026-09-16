from __future__ import annotations

import importlib.util
import random
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_sol_calibration_transfer.py"

spec = importlib.util.spec_from_file_location("sol_transfer", RUNNER)
assert spec is not None and spec.loader is not None
sol_transfer = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sol_transfer
spec.loader.exec_module(sol_transfer)


class SolCalibrationTransferRunnerTests(unittest.TestCase):
    def test_seeded_learner_fuzzing_is_reproducible(self) -> None:
        a = random.Random(12345)
        b = random.Random(12345)
        self.assertEqual(
            [sol_transfer.choose_state(a) for _ in range(30)],
            [sol_transfer.choose_state(b) for _ in range(30)],
        )

    def test_teacher_response_parser_preserves_visible_spacing(self) -> None:
        raw = '{"status":"continue","active_bridge":"value vs index","message":"index:  0  1\\nnums:  [2, 7]"}'
        turn = sol_transfer.parse_teacher(raw)
        self.assertEqual(turn.status, "continue")
        self.assertEqual(turn.active_bridge, "value vs index")
        self.assertEqual(turn.message, "index:  0  1\nnums:  [2, 7]")

    def test_calibration_is_teacher_only(self) -> None:
        marker = "UNIQUE_CALIBRATION_MARKER"
        teacher = sol_transfer.teacher_bootstrap(marker, sol_transfer.PROBLEM)
        student = sol_transfer.student_bootstrap(sol_transfer.PROBLEM)
        self.assertIn(marker, teacher)
        self.assertNotIn(marker, student)
        self.assertIn("Do not inspect files, repositories, tools", teacher)
        self.assertIn("Do not inspect files, repositories, tools", student)

    def test_known_codex_tool_events_are_rejected(self) -> None:
        event = {
            "type": "item.completed",
            "item": {"type": "command_execution", "command": "pwd"},
        }
        with self.assertRaisesRegex(RuntimeError, "forbidden tool activity"):
            sol_transfer.CodexSession._parse(__import__("json").dumps(event))

    def test_html_escapes_text_but_preserves_preformatted_content(self) -> None:
        rows = [
            {
                "exchange_id": 1,
                "active_bridge": "index < value",
                "learner_state": "wrong",
                "teacher_message": "index:  0  1\nnums:  [2, 7] <check>",
                "learner_message": "I think 7 is index 7?",
            }
        ]
        meta = {
            "run_id": "run-001",
            "status": "completed",
            "problem": sol_transfer.PROBLEM,
        }
        rendered = sol_transfer.render_html(meta, rows, None)
        self.assertIn(
            "<pre>index:  0  1\nnums:  [2, 7] &lt;check&gt;</pre>", rendered
        )
        self.assertNotIn("<check>", rendered)
        self.assertIn("Export TSV", rendered)
        self.assertIn("localStorage", rendered)

    def test_run_directories_are_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = sol_transfer.next_run_dir(root)
            second = sol_transfer.next_run_dir(root)
            self.assertEqual(first.name, "run-001")
            self.assertEqual(second.name, "run-002")
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())


if __name__ == "__main__":
    unittest.main()
