from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "experiments" / "model-tutoring" / "manifest.json"
README = ROOT / "experiments" / "model-tutoring" / "README.md"
HISTORY = ROOT / "experiments" / "model-tutoring" / "HISTORY.md"


class ModelTutoringExperimentRegistryTests(unittest.TestCase):
    def _registry(self) -> dict[str, object]:
        return json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_registry_entrypoints_exist(self) -> None:
        for path in (ROOT / "experiments" / "README.md", README, HISTORY, REGISTRY):
            self.assertTrue(path.is_file(), f"missing experiment notebook file: {path}")

        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("experiments/model-tutoring/README.md", agents)
        self.assertIn("experiments/model-tutoring/manifest.json", agents)
        self.assertIn("experiments/model-tutoring/HISTORY.md", agents)

    def test_registry_ids_are_unique_and_active_experiment_resolves(self) -> None:
        registry = self._registry()
        self.assertEqual(
            registry.get("schema_version"),
            "study-os.model-tutoring-experiment-registry.v0.1",
        )
        experiments = registry.get("experiments")
        self.assertIsInstance(experiments, list)
        assert isinstance(experiments, list)

        ids = [item.get("id") for item in experiments if isinstance(item, dict)]
        self.assertTrue(ids)
        self.assertEqual(len(ids), len(set(ids)))

        active_id = registry.get("active_experiment_id")
        self.assertIsInstance(active_id, str)
        matching = [item for item in experiments if isinstance(item, dict) and item.get("id") == active_id]
        self.assertEqual(len(matching), 1)
        active = matching[0]
        self.assertEqual(active.get("status"), "implemented_unrun")

        for field in ("proposal", "runner", "calibration_input"):
            value = active.get(field)
            self.assertIsInstance(value, str)
            assert isinstance(value, str)
            self.assertTrue((ROOT / value).is_file(), f"active {field} does not resolve: {value}")

        self.assertEqual(active.get("default_command"), "python tools/run_sol_calibration_transfer.py")

    def test_history_statuses_avoid_false_deterministic_failure_claim(self) -> None:
        registry = self._registry()
        experiments = registry["experiments"]
        deterministic = next(
            item
            for item in experiments
            if isinstance(item, dict) and item.get("id") == "MT-H002"
        )
        self.assertEqual(deterministic.get("status"), "supported")
        self.assertIn("does not guarantee", str(deterministic.get("summary", "")))

        fixed_turn = next(
            item
            for item in experiments
            if isinstance(item, dict) and item.get("id") == "MT-H003"
        )
        self.assertEqual(fixed_turn.get("status"), "insufficient")


if __name__ == "__main__":
    unittest.main()
