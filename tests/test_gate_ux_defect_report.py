"""Unit tests for Ultrafast UX defect CI gate (any P0/P1 fails; confidence never soft-skips)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.gate_ux_defect_report import blocking_defects, gate, load_summary, main


def _write(tmp: Path, payload: dict) -> Path:
    path = tmp / "summary.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class GateUxDefectReportTests(unittest.TestCase):
    def test_blocking_collects_p0_and_p1_only(self) -> None:
        defects = [
            {"id": "D1", "severity": "P0", "title": "blank"},
            {"id": "D2", "severity": "P1", "title": "noop"},
            {"id": "D3", "severity": "P2", "title": "soft"},
            {"id": "D4", "severity": "p1", "title": "case"},
        ]
        blocked = blocking_defects(defects)
        self.assertEqual([d["id"] for d in blocked], ["D1", "D2", "D4"])

    def test_pass_when_only_p2(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = _write(
                Path(td),
                {
                    "schema_version": "ux-defect-report.v1",
                    "defects": [{"id": "D1", "severity": "P2", "title": "soft", "confidence": 0.9}],
                    "pass": True,
                },
            )
            self.assertEqual(gate(load_summary(path), path=path), 0)

    def test_fail_on_p0_even_with_low_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = _write(
                Path(td),
                {
                    "defects": [
                        {
                            "id": "D004",
                            "severity": "P0",
                            "title": "Dead/no-op control: Worked example",
                            "confidence": 0.12,
                            "url": "https://study.design-bakery.com/play/x",
                        }
                    ]
                },
            )
            self.assertEqual(gate(load_summary(path), path=path), 1)

    def test_fail_on_p1_with_high_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = _write(
                Path(td),
                {
                    "defects": [
                        {
                            "id": "D002",
                            "severity": "P1",
                            "title": "Missing Back/exit",
                            "confidence": 0.98,
                            "url": "https://study.design-bakery.com/play/x",
                        }
                    ]
                },
            )
            self.assertEqual(gate(load_summary(path), path=path), 1)

    def test_cli_against_committed_bench_summary_fails(self) -> None:
        bench = Path("docs/benchmarks/ux-defect-jev-ultrafast/2026-09-27/summary.json")
        if not bench.is_file():
            self.skipTest("bench summary missing")
        self.assertEqual(main([str(bench)]), 1)

    def test_missing_file_is_error(self) -> None:
        self.assertEqual(main(["/tmp/does-not-exist-ux-defect-summary.json"]), 2)


if __name__ == "__main__":
    unittest.main()
