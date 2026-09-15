from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.model_tutoring import (  # noqa: E402
    LearnerAssessment,
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
        self.message = "not sure yet"
        self.assessment = LearnerAssessment("not_yet")
        self.contract = self.controller.authorize(
            self.diagnosis,
            self.assessment,
            turn_index=0,
            learner_message=self.message,
            learner_signal="recovery_or_check",
        ).contract

    def _demonstrated(self, message: str) -> LearnerAssessment:
        return LearnerAssessment("demonstrated", message, "test evidence")

    def test_scripted_signal_cannot_advance_mutant_is_killed(self) -> None:
        authorization = self.controller.authorize(
            self.diagnosis,
            LearnerAssessment("not_yet"),
            turn_index=0,
            learner_message="I do not know",
            learner_signal="recovery_or_check",
        )
        self.assertFalse(authorization.trace["advance"])
        self.assertEqual(authorization.next_state.stage, "anchor")

    def test_two_stage_advance_mutant_is_killed(self) -> None:
        for index in range(2):
            message = f"demonstration {index}"
            authorization = self.controller.authorize(
                self.diagnosis,
                self._demonstrated(message),
                turn_index=index,
                learner_message=message,
                learner_signal="clarification",
            )
            self.assertLessEqual(
                authorization.next_state.stage_index - self.controller.state.stage_index,
                1,
            )
            self.controller.commit(authorization)
        self.assertEqual(self.controller.state.stage, "membership")

    def test_fabricated_evidence_mutant_is_killed(self) -> None:
        with self.assertRaises(ModelTutoringError):
            LearnerAssessment.from_payload(
                {"learner_outcome": "demonstrated", "evidence_quote": "correct answer"},
                learner_message="banana",
            )

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

    def test_forbidden_variable_and_required_visual_mutants_are_killed(self) -> None:
        with self.assertRaises(ModelTutoringError):
            validate_generated_response(
                "```text\nnums = [4,7,4]\n```\nRelation: nums and duplicate\nTiny check: should seen contain 4?",
                self.contract,
            )
        with self.assertRaises(ModelTutoringError):
            validate_generated_response(
                "Relation: nums and duplicate\nTiny check: which value repeats?",
                self.contract,
            )

    def test_trace_path_provenance_and_outcome_mutants_are_killed(self) -> None:
        checker = _checker()
        corpus = checker.load_json(ROOT / "datasets/dsa-conversation-replay.v0.1.json")
        scenario = checker.find_scenario(corpus, "contains-duplicate-set")
        trace = self.controller.authorize(
            self.diagnosis,
            self.assessment,
            turn_index=0,
            learner_message=self.message,
        ).trace
        trace["path_kind"] = "canonical_asset"
        codes = {item["code"] for item in checker.evaluate_trace([trace], scenario)}
        self.assertIn("NOT_MODEL_GENERATED", codes)
        trace["path_kind"] = "model_generated"
        trace["prompt_version"] = ""
        codes = {item["code"] for item in checker.evaluate_trace([trace], scenario)}
        self.assertIn("TRACE_PROVENANCE", codes)
        trace["prompt_version"] = "v2"
        trace["advance"] = True
        trace["learner_outcome"] = "not_yet"
        codes = {item["code"] for item in checker.evaluate_trace([trace], scenario)}
        self.assertIn("UNSUPPORTED_ADVANCE", codes)


if __name__ == "__main__":
    unittest.main()
