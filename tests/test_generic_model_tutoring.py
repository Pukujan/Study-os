from __future__ import annotations

import json
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.generic_model_tutoring import (  # noqa: E402
    GenericModelTutoringController,
    LearnerAssessment,
    LearnerState,
    ModelDiagnosis,
    ModelTutoringError,
    build_generation_prompt,
    parse_model_decision,
    validate_generated_response,
)
from study_os.prompt_registry import (  # noqa: E402
    DEFAULT_PROMPT_REGISTRY,
    DECOMPOSITION_PROMPT_VERSION,
    GENERATION_PROMPT_VERSION,
)
from study_os.teaching_plan import (  # noqa: E402
    TEACHING_PLAN_SCHEMA_VERSION,
    TeachingPlan,
    TeachingPlanValidationError,
)


def synthetic_payload() -> dict:
    source_problem_id = "synthetic-problem"
    decomposition = DEFAULT_PROMPT_REGISTRY.get(DECOMPOSITION_PROMPT_VERSION)
    provenance = decomposition.provenance(
        model_identifier="synthetic-model",
        teaching_plan_schema_version=TEACHING_PLAN_SCHEMA_VERSION,
        turn_trace_schema_version="study-os.model-tutoring-trace.v0.2",
        run_id="synthetic-run",
        source_problem_id=source_problem_id,
    )
    return {
        "schema_version": TEACHING_PLAN_SCHEMA_VERSION,
        "problem": {
            "id": source_problem_id,
            "statement": "Determine whether the input has the required property.",
        },
        "concepts": [
            {
                "id": "recognize-pattern",
                "prerequisites": [],
                "allowed_variables": ["items", "cursor"],
                "representation_requirement_ids": ["trace-pattern"],
                "semantic_invariant_ids": ["pattern-stable"],
                "completion_evidence_ids": ["pattern-explanation"],
            },
            {
                "id": "track-state",
                "prerequisites": ["recognize-pattern"],
                "allowed_variables": ["items", "cursor", "bucket"],
                "representation_requirement_ids": ["trace-state"],
                "semantic_invariant_ids": ["state-stable"],
                "completion_evidence_ids": ["state-explanation"],
            },
            {
                "id": "decide-result",
                "prerequisites": ["track-state"],
                "allowed_variables": ["items", "cursor", "bucket", "answer"],
                "representation_requirement_ids": ["trace-result"],
                "semantic_invariant_ids": ["result-stable"],
                "completion_evidence_ids": ["result-explanation"],
            },
        ],
        "variables": {
            "items": {"role": "collection", "meaning": "the input values"},
            "cursor": {"role": "index", "meaning": "the current position"},
            "bucket": {"role": "collection", "meaning": "state accumulated so far"},
            "answer": {"role": "result", "meaning": "the final decision"},
        },
        "representation_requirements": [
            {
                "id": "trace-pattern",
                "kind": "stateful",
                "operation": "trace",
                "description": "Trace the input position while recognizing the pattern.",
                "required": True,
            },
            {
                "id": "trace-state",
                "kind": "stateful",
                "operation": "trace",
                "description": "Trace the current state and position.",
                "required": True,
            },
            {
                "id": "trace-result",
                "kind": "formal",
                "operation": "explain",
                "description": "Explain how the result follows from the state.",
                "required": True,
            },
        ],
        "semantic_invariants": [
            {
                "id": "pattern-stable",
                "concept_id": "recognize-pattern",
                "statement": "The recognized pattern remains tied to the input values.",
            },
            {
                "id": "state-stable",
                "concept_id": "track-state",
                "statement": "The state contains only information accumulated so far.",
            },
            {
                "id": "result-stable",
                "concept_id": "decide-result",
                "statement": "The result follows from the established state.",
            },
        ],
        "completion_evidence": [
            {
                "id": "pattern-explanation",
                "concept_id": "recognize-pattern",
                "evidence_type": "explanation",
                "description": "Learner explains the recognized pattern unaided.",
            },
            {
                "id": "state-explanation",
                "concept_id": "track-state",
                "evidence_type": "explanation",
                "description": "Learner explains the accumulated state unaided.",
            },
            {
                "id": "result-explanation",
                "concept_id": "decide-result",
                "evidence_type": "explanation",
                "description": "Learner explains the result unaided.",
            },
        ],
        "terminal_behavior": [
            "After the state is established, explain the final decision without hidden steps."
        ],
        "assistance_ceiling": "A1",
        "provenance": provenance.to_payload(),
    }


def make_controller(*, state: LearnerState | None = None) -> GenericModelTutoringController:
    return GenericModelTutoringController(
        TeachingPlan.from_payload(synthetic_payload()),
        state=state,
        prompt_registry=DEFAULT_PROMPT_REGISTRY,
    )


def diagnosis(assistance_level: str = "A1") -> ModelDiagnosis:
    return ModelDiagnosis(
        diagnosis_family="concept_failure",
        operation="probe",
        assistance_level=assistance_level,
    )


class GenericModelTutoringTests(unittest.TestCase):
    def test_progression_is_immutable_and_advances_at_most_one_concept(self) -> None:
        controller = make_controller()
        first = controller.authorize(
            diagnosis(),
            LearnerAssessment("not_yet"),
            learner_message="I am not sure yet.",
        )
        self.assertFalse(first.contract.advance_allowed)
        self.assertEqual(first.next_state.concept_index, 0)
        self.assertEqual(controller.state.concept_index, 0)
        with self.assertRaises(FrozenInstanceError):
            first.next_state.concept_index = 2  # type: ignore[misc]

        controller.commit(first)
        learner_message = "The repeated pattern is tied to the input values."
        second = controller.authorize(
            diagnosis(),
            LearnerAssessment("demonstrated", learner_message),
            learner_message=learner_message,
        )
        self.assertTrue(second.contract.advance_allowed)
        self.assertEqual(second.contract.active_concept_id, "recognize-pattern")
        self.assertEqual(second.next_state.concept_index, 1)
        self.assertNotEqual(second.next_state.concept_index, 2)
        controller.commit(second)

        state_message = "The state contains only information accumulated so far."
        third = controller.authorize(
            diagnosis("A0"),
            LearnerAssessment("demonstrated", state_message),
            learner_message=state_message,
        )
        self.assertEqual(third.contract.active_concept_id, "track-state")
        self.assertEqual(third.next_state.concept_index, 2)
        controller.commit(third)
        final_message = "The final state transition completes the scan and handles the terminal case."
        fourth = controller.authorize(
            diagnosis("A0"),
            LearnerAssessment("demonstrated", final_message),
            learner_message=final_message,
        )
        self.assertTrue(fourth.completion_candidate)
        self.assertFalse(fourth.contract.advance_allowed)

    def test_fabricated_or_non_verbatim_evidence_is_rejected(self) -> None:
        learner_message = "I can explain the pattern from the input values."
        with self.assertRaisesRegex(ModelTutoringError, "verbatim"):
            LearnerAssessment.from_payload(
                {
                    "learner_outcome": "demonstrated",
                    "evidence_quote": "I can explain the pattern perfectly.",
                },
                learner_message=learner_message,
            )

        assessment = LearnerAssessment("demonstrated", "I can explain the pattern")
        with self.assertRaisesRegex(ModelTutoringError, "verbatim"):
            make_controller().authorize(
                diagnosis(), assessment, learner_message=learner_message.upper()
            )

    def test_nested_assessment_shape_is_parsed_without_relaxing_evidence_binding(self) -> None:
        learner_message = "I can explain the pattern from the input values."
        diagnosis_value, assessment_value = parse_model_decision(
            json.dumps({
                "diagnosis": {
                    "diagnosis_family": "concept_failure",
                    "operation": "probe",
                    "assistance_level": "A0",
                    "assessment": {
                        "learner_outcome": "demonstrated",
                        "evidence_quote": learner_message,
                        "rationale": "verbatim evidence",
                    },
                }
            }),
            learner_message=learner_message,
        )
        self.assertEqual(diagnosis_value.operation, "probe")
        self.assertEqual(assessment_value.evidence_quote, learner_message)

    def test_assistance_overflow_is_rejected_by_the_plan_ceiling(self) -> None:
        with self.assertRaisesRegex(ModelTutoringError, "assistance"):
            make_controller().authorize(
                diagnosis("A2"),
                LearnerAssessment("uncertain"),
                learner_message="I am unsure.",
            )
        with self.assertRaisesRegex(ModelTutoringError, "assistance"):
            ModelDiagnosis("concept_failure", "probe", "A3")

    def test_prerequisite_order_and_references_are_rejected(self) -> None:
        unknown_reference = synthetic_payload()
        unknown_reference["concepts"][1]["prerequisites"] = ["missing-concept"]
        with self.assertRaises(TeachingPlanValidationError):
            TeachingPlan.from_payload(unknown_reference)

        wrong_order = synthetic_payload()
        wrong_order["concepts"] = [
            wrong_order["concepts"][1],
            wrong_order["concepts"][0],
            wrong_order["concepts"][2],
        ]
        reordered_plan = TeachingPlan.from_payload(wrong_order)
        with self.assertRaisesRegex(ModelTutoringError, "prerequisites"):
            GenericModelTutoringController(reordered_plan)

    def test_contract_and_trace_preserve_prompt_provenance(self) -> None:
        controller = make_controller()
        learner_message = "I can explain the pattern from the input values."
        authorization = controller.authorize(
            diagnosis(),
            LearnerAssessment("demonstrated", learner_message),
            learner_message=learner_message,
            turn_index=7,
        )
        contract = authorization.contract
        generation_prompt = DEFAULT_PROMPT_REGISTRY.get(GENERATION_PROMPT_VERSION)
        self.assertEqual(contract.active_concept_id, "recognize-pattern")
        self.assertEqual(contract.allowed_variables, ("items", "cursor"))
        self.assertEqual(contract.representation_requirement_ids, ("trace-pattern",))
        self.assertEqual(contract.semantic_invariant_ids, ("pattern-stable",))
        self.assertEqual(contract.completion_evidence_ids, ("pattern-explanation",))
        self.assertEqual(
            contract.prompt_provenance.prompt_hash, generation_prompt.prompt_hash
        )
        self.assertEqual(
            authorization.trace["prompt_provenance"]["prompt_version"],
            GENERATION_PROMPT_VERSION,
        )
        self.assertEqual(authorization.trace["plan_provenance"]["run_id"], "synthetic-run")
        prompt = build_generation_prompt(
            contract,
            learner_message=learner_message,
            history=[{"role": "learner", "content": learner_message}],
        )
        self.assertIn("Active concept: recognize-pattern", prompt)
        self.assertIn("trace-pattern", prompt)
        self.assertIn(generation_prompt.content, prompt)

    def test_response_validation_enforces_generic_boundaries_without_authoring(self) -> None:
        controller = make_controller()
        authorization = controller.authorize(
            diagnosis(),
            LearnerAssessment("not_yet"),
            learner_message="I am still working it out.",
        )
        contract = authorization.contract
        valid = "```text\nitems at cursor\n```\nRepresentation: trace-pattern\nstateful trace: items at cursor\n?"
        self.assertIsNone(validate_generated_response(valid, contract))

        with self.assertRaisesRegex(ModelTutoringError, "representation"):
            validate_generated_response("items at cursor?", contract)
        with self.assertRaisesRegex(ModelTutoringError, "outside the active"):
            validate_generated_response(
                "```text\nitems at cursor\n```\nRepresentation: trace-pattern\nstateful trace: bucket is ready?", contract
            )
        with self.assertRaisesRegex(ModelTutoringError, "internal"):
            validate_generated_response(
                "```text\nitems at cursor\n```\nRepresentation: trace-pattern\nstateful trace: needs_compilation?",
                contract,
            )
        too_many_lines = "\n".join(
            ["```text", "items at cursor", "```", "Representation: trace-pattern", "stateful trace: items at cursor"]
            + ["more" for _ in range(19)]
        )
        with self.assertRaisesRegex(ModelTutoringError, "line"):
            validate_generated_response(too_many_lines, contract)

    def test_source_forbidden_terms_are_enforced_without_scenario_logic(self) -> None:
        plan = TeachingPlan.from_payload(synthetic_payload())
        controller = GenericModelTutoringController(
            plan,
            forbidden_terms=("seen", "lookup_map"),
        )
        authorization = controller.authorize(
            diagnosis(),
            LearnerAssessment("not_yet"),
            learner_message="I am still working it out.",
        )
        with self.assertRaisesRegex(ModelTutoringError, "forbidden source terms"):
            validate_generated_response(
                "```text\nitems at cursor\n```\nRepresentation: trace-pattern\nstateful trace: items at cursor\n"
                "The seen alias is not allowed?",
                authorization.contract,
            )

    def test_representation_can_use_generated_description_language(self) -> None:
        controller = make_controller()
        authorization = controller.authorize(
            diagnosis(),
            LearnerAssessment("not_yet"),
            learner_message="I am still working it out.",
        )
        # The learner-visible chart need not echo the internal requirement id
        # or the metadata operation.  Its generated description still names
        # the semantic anchors that make the representation recognizable.
        response = (
            "| items: [a, b] |\n"
            "cursor: 0  1\n"
            "current state: b at cursor; recognizing pattern\n"
            "?"
        )
        self.assertIsNone(validate_generated_response(response, authorization.contract))

    def test_visual_first_accepts_variable_assignment_and_table_headers(self) -> None:
        controller = make_controller()
        authorization = controller.authorize(
            diagnosis(), LearnerAssessment("not_yet"), learner_message="Still unsure."
        )
        response = "items = [a, b]\ncursor | current item\nstateful trace: recognizing pattern\n?"
        self.assertIsNone(validate_generated_response(response, authorization.contract))


if __name__ == "__main__":
    unittest.main()
