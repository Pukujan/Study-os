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
    ModelDiagnosis,
    ModelTutoringController,
    ModelTutoringError,
    STAGE_ANCHORS,
    STAGE_ORDER,
    STAGE_REQUIRED_VARIABLES,
    build_generation_prompt,
    parse_model_turn,
    validate_generated_response,
)


def response_for(stage: str, values: str = "[4, 7, 4]") -> str:
    anchors = STAGE_ANCHORS[stage]
    return (
        f"```text\nnums = {values}\nbox = {{4}}\nnum = 4\n```\n"
        f"Relation: {anchors[0]} connects to {anchors[-1]}.\n"
        "Tiny check: what do you notice?"
    )


class ModelTutoringPilotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.diagnosis = ModelDiagnosis(
            diagnosis_family="uncertain_mixed",
            operation="probe",
            assistance_level="A1",
            decomposition="one observable relation",
        )

    def test_schema_trace_shape_is_valid(self) -> None:
        schema = json.loads(
            (ROOT / "contracts/model-tutoring-trace.v0.1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        Draft202012Validator.check_schema(schema)
        controller = ModelTutoringController()
        authorization = controller.authorize(
            self.diagnosis,
            turn_index=0,
            learner_signal="clarification",
        )
        errors = list(Draft202012Validator(schema).iter_errors(authorization.trace))
        self.assertEqual(errors, [])

    def test_controller_owns_stage_and_advance_boundary(self) -> None:
        controller = ModelTutoringController()
        first = controller.authorize(
            self.diagnosis,
            turn_index=0,
            learner_signal="clarification",
        )
        self.assertEqual(first.contract.target_concept, "duplicate_meaning")
        self.assertFalse(first.trace["advance"])
        controller.commit(first)
        wrong = controller.authorize(
            self.diagnosis,
            turn_index=1,
            learner_signal="wrong_or_uncertain",
        )
        self.assertEqual(wrong.contract.stage, "anchor")
        self.assertFalse(wrong.trace["advance"])
        recovery = controller.authorize(
            self.diagnosis,
            turn_index=2,
            learner_signal="recovery_or_check",
        )
        self.assertTrue(recovery.trace["advance"])
        self.assertEqual(recovery.next_state.stage, "box-meaning")
        controller.commit(recovery)
        self.assertEqual(controller.state.stage, "box-meaning")

    def test_model_cannot_override_current_target(self) -> None:
        controller = ModelTutoringController()
        diagnosis = ModelDiagnosis(
            diagnosis_family="concept_failure",
            operation="assemble",
            assistance_level="A2",
        )
        authorization = controller.authorize(
            diagnosis,
            turn_index=0,
            learner_signal="clarification",
        )
        self.assertEqual(authorization.trace["target_concept"], "duplicate_meaning")
        self.assertEqual(authorization.contract.allowed_variables, ("nums",))

    def test_assistance_above_a2_and_unknown_values_are_rejected(self) -> None:
        with self.assertRaises(ModelTutoringError):
            ModelDiagnosis.from_payload(
                {
                    "diagnosis_family": "uncertain_mixed",
                    "operation": "probe",
                    "assistance_level": "A3",
                }
            )

    def test_model_diagnosis_common_labels_are_normalized_inside_policy_enum(self) -> None:
        diagnosis = ModelDiagnosis.from_payload(
            {
                "diagnosis_family": "mental_model",
                "operation": "contrast",
                "assistance_level": "minimal",
            }
        )
        self.assertEqual(diagnosis.diagnosis_family, "concept_failure")
        self.assertEqual(diagnosis.operation, "change_representation")
        self.assertEqual(diagnosis.assistance_level, "A1")
        with self.assertRaises(ModelTutoringError):
            ModelDiagnosis.from_payload(
                {
                    "diagnosis_family": "not-a-diagnosis",
                    "operation": "probe",
                    "assistance_level": "A1",
                }
            )

    def test_validator_requires_visual_relation_question_and_variables(self) -> None:
        controller = ModelTutoringController()
        contract = controller.authorize(
            self.diagnosis,
            turn_index=0,
            learner_signal="clarification",
        ).contract
        validate_generated_response(response_for("anchor"), contract)
        for bad in (
            "nums and duplicate?",
            "```text\nnums = [4,7,4]\n```\nRelation: duplicate and nums",
            "```text\nnums = [4,7,4]\n```\nRelation: duplicate and nums\nTiny check: seen?",
        ):
            with self.assertRaises(ModelTutoringError):
                validate_generated_response(bad, contract)

    def test_validator_rejects_aliases_future_terms_and_full_code(self) -> None:
        controller = ModelTutoringController()
        contract = controller.authorize(
            self.diagnosis,
            turn_index=0,
            learner_signal="clarification",
        ).contract
        for text in (
            "```text\nnums = [4,7,4]\n```\nRelation: duplicate and nums\nTiny check: is it a set?",
            "```text\nnums = [4,7,4]\n```\nRelation: duplicate and nums\nTiny check: use seen?",
            "```python\ndef solve(nums):\n    return True\n```\nRelation: nums and duplicate\nTiny check?",
        ):
            with self.assertRaises(ModelTutoringError):
                validate_generated_response(text, contract)

    def test_parse_model_json_envelope(self) -> None:
        diagnosis, response = parse_model_turn(
            json.dumps(
                {
                    "diagnosis": {
                        "diagnosis_family": "concept_failure",
                        "operation": "smaller_step",
                        "assistance_level": "A2",
                        "decomposition": "name the repeated value",
                    },
                    "response": response_for("anchor"),
                }
            )
        )
        self.assertEqual(diagnosis.operation, "smaller_step")
        self.assertIn("Relation:", response)
        with self.assertRaises(ModelTutoringError):
            parse_model_turn("not json")

    def test_differential_stage_policy_matches_calibrated_corpus(self) -> None:
        corpus = json.loads(
            (ROOT / "datasets/dsa-conversation-replay.v0.1.json").read_text(
                encoding="utf-8"
            )
        )
        scenario = next(item for item in corpus["scenarios"] if item["id"] == "contains-duplicate-set")
        controller = ModelTutoringController()
        for index, turn in enumerate(scenario["turns"]):
            authorization = controller.authorize(
                self.diagnosis,
                turn_index=index,
                learner_signal=turn["learner_signal"],
            )
            self.assertEqual(authorization.contract.stage, turn["stage"])
            self.assertEqual(
                set(authorization.contract.required_anchors),
                set(turn["expected"]["must_include_any"]),
            )
            self.assertEqual(
                authorization.contract.max_nonempty_lines,
                turn["expected"]["max_nonempty_lines"],
            )
            if turn["learner_signal"] != "recovery_or_check":
                self.assertFalse(authorization.trace["advance"])
            controller.commit(authorization)

    def test_metamorphic_paraphrases_and_numeric_substitution_preserve_policy(self) -> None:
        controller = ModelTutoringController()
        contract = controller.authorize(
            self.diagnosis,
            turn_index=0,
            learner_signal="recovery_or_check",
        ).contract
        for learner_message in (
            "what does duplicate mean?",
            "same number twice?",
            "if 4 shows up two times?",
            "duplicate??",
        ):
            prompt = build_generation_prompt(contract, learner_message=learner_message)
            self.assertIn("duplicate_meaning", prompt)
            self.assertIn("nums", prompt)
            self.assertIn("never use ['seen']", prompt)
        validate_generated_response(response_for("anchor", "[8, 3, 8]"), contract)

    def test_stateful_random_signals_never_skip_or_claim_mastery(self) -> None:
        rng = random.Random(77)
        controller = ModelTutoringController()
        previous_index = 0
        for index in range(60):
            signal = rng.choice(("clarification", "wrong_or_uncertain", "recovery_or_check"))
            authorization = controller.authorize(
                self.diagnosis,
                turn_index=index,
                learner_signal=signal,
            )
            self.assertLessEqual(authorization.next_state.stage_index - previous_index, 1)
            self.assertFalse(authorization.next_state.mastery_proven)
            controller.commit(authorization)
            previous_index = controller.state.stage_index
        self.assertEqual(controller.state.stage, STAGE_ORDER[-1])

    def test_mutation_style_boundaries_are_killed(self) -> None:
        controller = ModelTutoringController()
        authorization = controller.authorize(
            self.diagnosis,
            turn_index=0,
            learner_signal="wrong_or_uncertain",
        )
        self.assertFalse(authorization.trace["advance"])
        self.assertEqual(authorization.contract.forbidden_variables, ("seen",))
        self.assertEqual(
            set(authorization.contract.allowed_variables),
            set(STAGE_REQUIRED_VARIABLES["anchor"]),
        )
        with self.assertRaises(ModelTutoringError):
            validate_generated_response(
                "```text\nnums = [4,7,4]\n```\nRelation: nums and duplicate\nTiny check: okay?\nextra\nextra\nextra\nextra\nextra\nextra\nextra\nextra\nextra\nextra\nextra\nextra\nextra",
                authorization.contract,
            )


if __name__ == "__main__":
    unittest.main()
