from __future__ import annotations

import json
import random
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.model_tutoring import (  # noqa: E402
    LearnerAssessment,
    ModelDiagnosis,
    ModelTutoringController,
    ModelTutoringError,
    STAGE_ANCHORS,
    STAGE_ORDER,
    build_generation_prompt,
    parse_model_decision,
    validate_generated_response,
)


def response_for(stage: str, values: str = "[4, 7, 4]", *, final: bool = False) -> str:
    anchors = STAGE_ANCHORS[stage]
    tail = "\nIf the scan finishes with no match: `return False`." if final else ""
    return (
        f"```text\nnums = {values}\nbox = {{4}}\nnum = 4\n```\n"
        f"Relation: {anchors[0]} connects to {anchors[-1]}."
        f"{tail}\nTiny check: what do you notice?"
    )


class ModelTutoringPilotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.diagnosis = ModelDiagnosis("uncertain_mixed", "probe", "A1", "one relation")

    def assessment(self, outcome: str, message: str) -> LearnerAssessment:
        quote = message if outcome == "demonstrated" else ""
        return LearnerAssessment.from_payload(
            {"learner_outcome": outcome, "evidence_quote": quote, "rationale": "test"},
            learner_message=message,
        )

    def test_trace_schema_is_valid(self) -> None:
        schema = json.loads(
            (ROOT / "contracts/model-tutoring-trace.v0.2.schema.json").read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(schema)

    def test_progression_uses_actual_assessment_not_corpus_signal(self) -> None:
        controller = ModelTutoringController()
        message = "4 appears twice"
        authorization = controller.authorize(
            self.diagnosis,
            self.assessment("demonstrated", message),
            turn_index=0,
            learner_message=message,
            learner_signal="clarification",
        )
        self.assertTrue(authorization.trace["advance"])
        self.assertEqual(authorization.next_state.stage, "box-meaning")

        controller = ModelTutoringController()
        message = "I have no idea"
        authorization = controller.authorize(
            self.diagnosis,
            self.assessment("not_yet", message),
            turn_index=0,
            learner_message=message,
            learner_signal="recovery_or_check",
        )
        self.assertFalse(authorization.trace["advance"])
        self.assertEqual(authorization.next_state.stage, "anchor")

    def test_demonstrated_requires_verbatim_learner_evidence(self) -> None:
        with self.assertRaises(ModelTutoringError):
            LearnerAssessment.from_payload(
                {
                    "learner_outcome": "demonstrated",
                    "evidence_quote": "4 appears twice",
                    "rationale": "claimed",
                },
                learner_message="banana",
            )
        with self.assertRaises(ModelTutoringError):
            LearnerAssessment.from_payload(
                {"learner_outcome": "demonstrated", "evidence_quote": ""},
                learner_message="4 appears twice",
            )

    def test_parse_model_decision_binds_evidence_to_message(self) -> None:
        message = "The duplicate is 4 because 4 appears twice."
        diagnosis, assessment = parse_model_decision(
            json.dumps(
                {
                    "diagnosis": {
                        "diagnosis_family": "none",
                        "operation": "probe",
                        "assistance_level": "A0",
                        "decomposition": "verify duplicate meaning",
                    },
                    "assessment": {
                        "learner_outcome": "demonstrated",
                        "evidence_quote": "4 appears twice",
                        "rationale": "states the rule",
                    },
                }
            ),
            learner_message=message,
        )
        self.assertEqual(diagnosis.diagnosis_family, "none")
        self.assertEqual(assessment.learner_outcome, "demonstrated")

    def test_assistance_above_a2_is_rejected(self) -> None:
        with self.assertRaises(ModelTutoringError):
            ModelDiagnosis.from_payload(
                {
                    "diagnosis_family": "uncertain_mixed",
                    "operation": "probe",
                    "assistance_level": "A3",
                }
            )

    def test_validator_requires_visual_relation_question_and_forbidden_alias(self) -> None:
        controller = ModelTutoringController()
        message = "not sure"
        contract = controller.authorize(
            self.diagnosis,
            self.assessment("not_yet", message),
            turn_index=0,
            learner_message=message,
        ).contract
        validate_generated_response(response_for("anchor"), contract)
        with self.assertRaises(ModelTutoringError):
            validate_generated_response("Relation: nums and duplicate\nQuestion?", contract)
        with self.assertRaises(ModelTutoringError):
            validate_generated_response(
                "```text\nnums=[4,7,4]\n```\nRelation: nums and duplicate\nShould seen hold 4?",
                contract,
            )

    def test_final_loop_contract_requires_explicit_return_false(self) -> None:
        controller = ModelTutoringController()
        for index in range(4):
            message = f"demonstrated stage {index}"
            auth = controller.authorize(
                self.diagnosis,
                self.assessment("demonstrated", message),
                turn_index=index,
                learner_message=message,
                learner_signal="wrong_or_uncertain",
            )
            controller.commit(auth)
        self.assertEqual(controller.state.stage, "loop")
        message = "I check the next num"
        final = controller.authorize(
            self.diagnosis,
            self.assessment("not_yet", message),
            turn_index=14,
            learner_message=message,
        ).contract
        with self.assertRaises(ModelTutoringError):
            validate_generated_response(response_for("loop"), final)
        validate_generated_response(response_for("loop", final=True), final)

    def test_metamorphic_paraphrases_preserve_policy_not_progression(self) -> None:
        controller = ModelTutoringController()
        for learner_message in (
            "what does duplicate mean?",
            "same number twice?",
            "if 4 shows up two times?",
            "duplicate??",
        ):
            contract = controller.authorize(
                self.diagnosis,
                self.assessment("uncertain", learner_message),
                turn_index=0,
                learner_message=learner_message,
            ).contract
            prompt = build_generation_prompt(contract, learner_message=learner_message)
            self.assertIn("duplicate_meaning", prompt)
            self.assertIn("nums", prompt)
            self.assertFalse(contract.advance_allowed)

    def test_stateful_random_outcomes_never_skip_or_claim_mastery(self) -> None:
        rng = random.Random(77)
        controller = ModelTutoringController()
        previous = 0
        for index in range(60):
            outcome = rng.choice(("demonstrated", "not_yet", "uncertain"))
            message = f"learner evidence {index}"
            auth = controller.authorize(
                self.diagnosis,
                self.assessment(outcome, message),
                turn_index=index,
                learner_message=message,
                learner_signal=rng.choice(("clarification", "wrong_or_uncertain", "recovery_or_check")),
            )
            self.assertLessEqual(auth.next_state.stage_index - previous, 1)
            self.assertFalse(auth.next_state.mastery_proven)
            controller.commit(auth)
            previous = controller.state.stage_index
        self.assertEqual(controller.state.stage, STAGE_ORDER[-1])


if __name__ == "__main__":
    unittest.main()
