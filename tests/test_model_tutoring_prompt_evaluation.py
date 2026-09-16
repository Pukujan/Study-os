from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from evaluate_model_tutoring_prompts import evaluate  # noqa: E402
from study_os.prompt_registry import DEFAULT_PROMPT_REGISTRY, DECOMPOSITION_PROMPT_VERSION  # noqa: E402


class PromptEvaluationTests(unittest.TestCase):
    def test_registry_hash_and_metamorphic_binding_receipt(self) -> None:
        definition = DEFAULT_PROMPT_REGISTRY.get(DECOMPOSITION_PROMPT_VERSION)
        corpus = {"scenarios": [{"id": "toy", "title": "Toy", "problem": "Find a value.", "variables": ["nums"], "turns": []}]}
        plan = {"scenario_id": "toy", "plan_payload": {"provenance": {"prompt_version": definition.version, "prompt_hash": definition.prompt_hash}}}
        report = evaluate(corpus, acceptance_report={"status": "passed", "scenario_count": 1, "exchange_count": 0, "visible_message_count": 0, "calibration": {"agreement": 1.0}}, plans=[plan])
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["metamorphic"]["all_source_variables_preserved"])
        self.assertTrue(report["metamorphic"]["all_hidden_annotations_absent"])

    def test_wrong_prompt_hash_is_not_promotable(self) -> None:
        corpus = {"scenarios": [{"id": "toy", "title": "Toy", "problem": "Find a value.", "variables": ["nums"], "turns": []}]}
        plan = {"scenario_id": "toy", "plan_payload": {"provenance": {"prompt_version": DECOMPOSITION_PROMPT_VERSION, "prompt_hash": "0" * 64}}}
        report = evaluate(corpus, acceptance_report={"status": "passed"}, plans=[plan])
        self.assertEqual(report["status"], "failed")


if __name__ == "__main__":
    unittest.main()
