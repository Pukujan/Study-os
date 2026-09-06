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
        self.assertEqual(config["max_stack_depth"], -1)
        self.assertEqual(
            set(config["pytest_add_cli_args_test_selection"]),
            {
                "tests/test_pir_teaching_controller.py",
                "tests/test_p4_pir_runtime_integration.py",
                "tests/test_pir_critical_mutations.py",
                "tests/test_pir_mutation_authority.py",
                "tests/test_pir_mutation_semantics.py",
                "tests/test_pir_mutation_contract_edges.py",
            },
        )

    def test_mutation_workflow_is_pull_request_gated_pinned_and_fail_closed(self) -> None:
        workflow = (ROOT / ".github/workflows/pir-mutation.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request:", workflow)
        self.assertIn("mutmut==3.7.0", workflow)
        self.assertIn("mutmut run", workflow)
        self.assertIn("mutmut results > mutmut-results.txt", workflow)
        self.assertIn("mutmut export-cicd-stats", workflow)
        self.assertIn("python tools/export_pir_critical_mutants.py", workflow)
        self.assertIn("python tools/check_pir_mutation_results.py", workflow)
        self.assertIn("tests/test_pir_mutation_authority.py", workflow)
        self.assertIn("tests/test_pir_mutation_contract_edges.py", workflow)
        self.assertIn("timeout-minutes: 20", workflow)
        self.assertNotIn("junitxml", workflow)
        self.assertNotIn("continue-on-error", workflow)

    def run_checker(
        self,
        stats: dict[str, int] | None,
        *,
        survivors: tuple[str, ...] = (),
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_path = Path(temp_dir) / "stats.json"
            results_path = Path(temp_dir) / "results.txt"
            if stats is not None:
                stats_path.write_text(json.dumps(stats), encoding="utf-8")
                lines: list[str] = []
                survivor_names = list(survivors)
                while len(survivor_names) < stats.get("survived", 0):
                    survivor_names.append(f"synthetic.unclassified.{len(survivor_names)}")
                lines.extend(f"{name}: survived" for name in survivor_names)
                for status in (
                    "killed",
                    "no_tests",
                    "skipped",
                    "suspicious",
                    "timeout",
                    "check_was_interrupted_by_user",
                    "segfault",
                ):
                    lines.extend(
                        f"synthetic.{status}.{index}: {status}"
                        for index in range(stats.get(status, 0))
                    )
                results_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(CHECKER), str(stats_path), str(results_path)],
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

    def test_checker_accepts_fully_killed_mutants(self) -> None:
        result = self.run_checker(self.stats())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("no unresolved non-equivalent semantic survivors", result.stdout)

    def test_checker_accepts_audited_equivalent_survivor(self) -> None:
        result = self.run_checker(
            self.stats(total=4, killed=3, survived=1),
            survivors=(
                "study_os.pir.controller.x_build_interaction_bundle__mutmut_49",
            ),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("equivalent=1", result.stdout)
        self.assertIn("unclassified=0", result.stdout)

    def test_checker_rejects_unclassified_survivor(self) -> None:
        result = self.run_checker(
            self.stats(total=4, killed=3, survived=1),
            survivors=(
                "study_os.pir.controller.x_build_interaction_bundle__mutmut_16",
            ),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unresolved non-equivalent or unaudited survivors remain", result.stdout)

    def test_checker_rejects_no_test_mutants(self) -> None:
        result = self.run_checker(self.stats(total=4, killed=3, no_tests=1))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("blocking mutation status no_tests=1", result.stdout)

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
