from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.model_tutoring import (  # noqa: E402
    ModelDiagnosis,
    ModelTutoringController,
    ModelTutoringError,
    ModelTutoringState,
    validate_generated_response,
)


def _checker():
    path = ROOT / "tools/check_model_tutoring_acceptance.py"
    spec = importlib.util.spec_from_file_location("pilot_acceptance_mutation", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load acceptance checker")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ModelTutoringMutationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = ModelTutoringController()
        self.diagnosis = ModelDiagnosis("uncertain_mixed", "probe", "A1")
        self.contract = self.controller.authorize(
            self.diagnosis,
            turn_index=0,
            learner_signal="clarification",
        ).contract

    def test_two_stage_advance_mutant_is_killed(self) -> None:
        for index in range(2):
            authorization = self.controller.authorize(
                self.diagnosis,
                turn_index=index,
                learner_signal="recovery_or_check",
            )
            self.assertLessEqual(authorization.next_state.stage_index - self.controller.state.stage_index, 1)
            self.controller.commit(authorization)
        self.assertEqual(self.controller.state.stage, "membership")

    def test_assistance_ceiling_mutant_is_killed(self) -> None:
        with self.assertRaises(ModelTutoringError):
            ModelDiagnosis.from_payload(
                {
                    "diagnosis_family": "uncertain_mixed",
                    "operation": "probe",
                    "assistance_level": "A3",
                }
            )

    def test_mastery_from_model_mutant_is_killed(self) -> None:
        with self.assertRaises(ModelTutoringError):
            ModelTutoringState(mastery_proven=True)

    def test_forbidden_variable_mutant_is_killed(self) -> None:
        with self.assertRaises(ModelTutoringError):
            validate_generated_response(
                "```text\nnums = [4,7,4]\n```\n"
                "Relation: nums and duplicate\nTiny check: should seen contain 4?",
                self.contract,
            )

    def test_required_visual_mutant_is_killed(self) -> None:
        with self.assertRaises(ModelTutoringError):
            validate_generated_response(
                "Relation: nums and duplicate\nTiny check: which value repeats?",
                self.contract,
            )

    def test_trace_path_and_provenance_mutants_are_killed(self) -> None:
        checker = _checker()
        corpus = checker.load_json(ROOT / "datasets/dsa-conversation-replay.v0.1.json")
        scenario = checker.find_scenario(corpus, "contains-duplicate-set")
        trace = self.controller.authorize(
            self.diagnosis,
            turn_index=0,
            learner_signal="clarification",
        ).trace
        trace["path_kind"] = "canonical_asset"
        failure_codes = {
            item["code"]
            for item in checker.evaluate_trace([trace], scenario)
        }
        self.assertIn("NOT_MODEL_GENERATED", failure_codes)
        trace["path_kind"] = "model_generated"
        trace["prompt_version"] = ""
        failure_codes = {
            item["code"]
            for item in checker.evaluate_trace([trace], scenario)
        }
        self.assertIn("TRACE_PROVENANCE", failure_codes)

    def test_clarification_cannot_advance_mutant(self) -> None:
        authorization = self.controller.authorize(
            self.diagnosis,
            turn_index=0,
            learner_signal="clarification",
        )
        self.assertFalse(authorization.trace["advance"])


if __name__ == "__main__":
    unittest.main()
