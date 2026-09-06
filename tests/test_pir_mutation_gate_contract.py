from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tools" / "check_pir_mutation_results.py"


class PIRMutationGateContractTests(unittest.TestCase):
    def test_mutation_gate_targets_callable_pir_trust_kernel(self) -> None:
        config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["mutmut"]
        self.assertEqual(config["source_paths"], ["src/"])
        self.assertEqual(
            set(config["only_mutate"]),
            {
                "src/study_os/pir/contracts.py",
                "src/study_os/pir/controller.py",
                "src/study_os/services/pir_runtime.py",
            },
        )
        self.assertNotIn("src/study_os/pir/registry.py", config["only_mutate"])
        self.assertEqual(
            set(config["pytest_add_cli_args_test_selection"]),
            {
                "tests/test_pir_teaching_controller.py",
                "tests/test_p4_pir_runtime_integration.py",
            },
        )

    def test_mutation_workflow_is_pull_request_gated_pinned_and_fail_closed(self) -> None:
        workflow = (ROOT / ".github/workflows/pir-mutation.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request:", workflow)
        self.assertIn("mutmut==3.7.0", workflow)
        self.assertIn("mutmut run", workflow)
        self.assertIn("mutmut results --all", workflow)
        self.assertIn("mutmut export-cicd-stats", workflow)
        self.assertIn("python tools/check_pir_mutation_results.py", workflow)
        self.assertIn("timeout-minutes: 20", workflow)
        self.assertNotIn("junitxml", workflow)
        self.assertNotIn("continue-on-error", workflow)

    def run_checker(self, stats: dict[str, int] | None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "stats.json"
            if stats is not None:
                path.write_text(json.dumps(stats), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(CHECKER), str(path)],
                check=False,
                capture_output=True,
                text=True,
            )

    @staticmethod
    def stats(**overrides: int) -> dict[str, int]:
        values = {
            "total": 4,
            "killed": 4,
            "survived": 0,
            "no_tests": 0,
            "skipped": 0,
            "suspicious": 0,
            "timeout": 0,
            "check_was_interrupted_by_user": 0,
            "segfault": 0,
        }
        values.update(overrides)
        return values

    def test_checker_accepts_only_fully_killed_mutants(self) -> None:
        result = self.run_checker(self.stats())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("every measured mutant was killed", result.stdout)

    def test_checker_rejects_survivor_and_no_test_mutants(self) -> None:
        for stats in (
            self.stats(total=4, killed=3, survived=1),
            self.stats(total=4, killed=3, no_tests=1),
        ):
            with self.subTest(stats=stats):
                result = self.run_checker(stats)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("blocking mutation status", result.stdout)

    def test_checker_rejects_suspicious_timeout_and_runtime_failures(self) -> None:
        for key in (
            "suspicious",
            "timeout",
            "check_was_interrupted_by_user",
            "segfault",
            "skipped",
        ):
            with self.subTest(key=key):
                stats = self.stats(total=4, killed=3, **{key: 1})
                result = self.run_checker(stats)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"blocking mutation status {key}=1", result.stdout)

    def test_checker_rejects_zero_mutants_missing_stats_and_accounting_mismatch(self) -> None:
        zero = self.run_checker(self.stats(total=0, killed=0))
        self.assertNotEqual(zero.returncode, 0)
        self.assertIn("produced no mutants", zero.stdout)

        missing_file = self.run_checker(None)
        self.assertNotEqual(missing_file.returncode, 0)
        self.assertIn("stats file is missing", missing_file.stdout)

        incomplete = self.stats()
        del incomplete["survived"]
        incomplete_result = self.run_checker(incomplete)
        self.assertNotEqual(incomplete_result.returncode, 0)
        self.assertIn("missing required keys", incomplete_result.stdout)

        mismatch = self.run_checker(self.stats(total=5, killed=4))
        self.assertNotEqual(mismatch.returncode, 0)
        self.assertIn("total=5, accounted=4", mismatch.stdout)


if __name__ == "__main__":
    unittest.main()
