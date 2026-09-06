from __future__ import annotations

import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PIRMutationGateContractTests(unittest.TestCase):
    def test_mutation_gate_targets_the_pir_trust_kernel(self) -> None:
        config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["mutmut"]
        self.assertEqual(config["source_paths"], ["src/"])
        self.assertEqual(
            set(config["only_mutate"]),
            {
                "src/study_os/pir/contracts.py",
                "src/study_os/pir/controller.py",
                "src/study_os/pir/registry.py",
                "src/study_os/services/pir_runtime.py",
            },
        )
        self.assertEqual(
            set(config["pytest_add_cli_args_test_selection"]),
            {
                "tests/test_pir_teaching_controller.py",
                "tests/test_p4_pir_runtime_integration.py",
            },
        )

    def test_mutation_workflow_is_pull_request_gated_and_pinned(self) -> None:
        workflow = (ROOT / ".github/workflows/pir-mutation.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request:", workflow)
        self.assertIn("mutmut==3.7.0", workflow)
        self.assertIn("mutmut run", workflow)
        self.assertIn("timeout-minutes: 20", workflow)
        self.assertNotIn("continue-on-error", workflow)


if __name__ == "__main__":
    unittest.main()
