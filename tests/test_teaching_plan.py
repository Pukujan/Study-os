from __future__ import annotations

import copy
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.prompt_registry import PromptDefinition  # noqa: E402
from study_os.teaching_plan import (  # noqa: E402
    TEACHING_PLAN_SCHEMA_VERSION,
    CompletionEvidence,
    ConceptSpec,
    ProblemSpec,
    RepresentationRequirement,
    SemanticInvariant,
    TeachingPlan,
    TeachingPlanProvenance,
    TeachingPlanValidationError,
    VariableSpec,
    load_teaching_plan_schema,
    validate_teaching_plan_schema,
)


def valid_payload() -> dict:
    return {
        "schema_version": TEACHING_PLAN_SCHEMA_VERSION,
        "problem": {
            "id": "contains-duplicate-set",
            "statement": "Determine whether a collection contains a repeated value.",
        },
        "concepts": [
            {
                "id": "recognize-duplicate",
                "prerequisites": [],
                "allowed_variables": ["nums"],
                "representation_requirement_ids": ["array-trace"],
                "semantic_invariant_ids": ["duplicate-definition"],
                "completion_evidence_ids": [],
            },
            {
                "id": "track-earlier-values",
                "prerequisites": ["recognize-duplicate"],
                "allowed_variables": ["nums", "box", "num"],
                "representation_requirement_ids": ["state-trace"],
                "semantic_invariant_ids": ["box-meaning"],
                "completion_evidence_ids": ["unaided-explanation"],
            },
        ],
        "variables": {
            "nums": {"role": "collection", "meaning": "the input values"},
            "box": {"role": "collection", "meaning": "values already passed"},
            "num": {"role": "value", "meaning": "the current value under inspection"},
        },
        "representation_requirements": [
            {
                "id": "array-trace",
                "kind": "stateful",
                "operation": "trace",
                "description": "Show positions and repeated values in the input.",
                "required": True,
            },
            {
                "id": "state-trace",
                "kind": "stateful",
                "operation": "predict",
                "description": "Show the current value and earlier-value collection.",
                "required": True,
            },
        ],
        "semantic_invariants": [
            {
                "id": "duplicate-definition",
                "concept_id": "recognize-duplicate",
                "statement": "A duplicate is a value occurring at least twice in nums.",
            },
            {
                "id": "box-meaning",
                "concept_id": "track-earlier-values",
                "statement": "box contains earlier nums values, not the boolean answer.",
            },
        ],
        "completion_evidence": [
            {
                "id": "unaided-explanation",
                "concept_id": "track-earlier-values",
                "evidence_type": "explanation",
                "description": "Learner explains box and num without a supplied definition.",
            }
        ],
        "terminal_behavior": [
            "After all values are checked without a match, return the no-duplicate result."
        ],
        "assistance_ceiling": "A2",
        "provenance": {
            "prompt_version": "study-os.model-tutoring-decompose.v1",
            "prompt_hash": "a" * 64,
            "model_identifier": "test-model",
            "teaching_plan_schema_version": TEACHING_PLAN_SCHEMA_VERSION,
            "turn_trace_schema_version": "study-os.model-tutoring-trace.v0.2",
            "run_id": "run-001",
            "source_problem_id": "contains-duplicate-set",
        },
    }


class TeachingPlanTests(unittest.TestCase):
    def test_schema_is_valid_and_round_trip_is_structurally_valid(self) -> None:
        schema = load_teaching_plan_schema()
        Draft202012Validator.check_schema(schema)
        plan = TeachingPlan.from_payload(valid_payload())

        payload = plan.to_payload()
        validate_teaching_plan_schema(payload)
        Draft202012Validator(schema).validate(payload)
        self.assertEqual(payload, valid_payload())
        self.assertEqual(plan.concepts[1].prerequisites, ("recognize-duplicate",))
        self.assertEqual(plan.variables["box"].role, "collection")

    def test_nested_values_and_provenance_are_immutable(self) -> None:
        source = valid_payload()
        plan = TeachingPlan.from_payload(source)
        source["variables"]["box"]["meaning"] = "mutated input"
        source["concepts"][0]["prerequisites"].append("track-earlier-values")

        self.assertEqual(plan.variables["box"].meaning, "values already passed")
        self.assertEqual(plan.concepts[0].prerequisites, ())
        with self.assertRaises(FrozenInstanceError):
            plan.assistance_ceiling = "A0"  # type: ignore[misc]
        with self.assertRaises(TypeError):
            plan.variables["box"] = VariableSpec("value", "changed")  # type: ignore[index]
        with self.assertRaises(FrozenInstanceError):
            plan.provenance.run_id = "other"  # type: ignore[misc]

    def test_prompt_registry_provenance_can_be_copied_without_mutation(self) -> None:
        definition = PromptDefinition("test-prompt-v1", "decomposition", "stable prompt")
        prompt_provenance = definition.provenance(
            model_identifier="test-model",
            teaching_plan_schema_version=TEACHING_PLAN_SCHEMA_VERSION,
            turn_trace_schema_version="study-os.model-tutoring-trace.v0.2",
            run_id="run-002",
            source_problem_id="contains-duplicate-set",
        )

        provenance = TeachingPlanProvenance.from_prompt_provenance(prompt_provenance)
        self.assertEqual(provenance.prompt_hash, definition.prompt_hash)
        self.assertEqual(provenance.source_problem_id, "contains-duplicate-set")

    def test_unknown_references_and_prerequisite_cycles_are_rejected(self) -> None:
        unknown = valid_payload()
        unknown["concepts"][1]["prerequisites"] = ["missing-concept"]
        with self.assertRaisesRegex(TeachingPlanValidationError, "unknown identifiers"):
            TeachingPlan.from_payload(unknown)

        cycle = valid_payload()
        cycle["concepts"][0]["prerequisites"] = ["track-earlier-values"]
        with self.assertRaisesRegex(TeachingPlanValidationError, "cycle"):
            TeachingPlan.from_payload(cycle)

    def test_cross_record_semantics_require_bindings_and_terminal_evidence(self) -> None:
        missing_variable = valid_payload()
        missing_variable["concepts"][1]["allowed_variables"] = ["nums", "unknown"]
        with self.assertRaisesRegex(TeachingPlanValidationError, "allowed_variables"):
            TeachingPlan.from_payload(missing_variable)

        missing_evidence = valid_payload()
        missing_evidence["concepts"][1]["completion_evidence_ids"] = []
        with self.assertRaisesRegex(TeachingPlanValidationError, "completion evidence"):
            TeachingPlan.from_payload(missing_evidence)

        wrong_source = valid_payload()
        wrong_source["provenance"]["source_problem_id"] = "different-problem"
        with self.assertRaisesRegex(TeachingPlanValidationError, "source_problem_id"):
            TeachingPlan.from_payload(wrong_source)

    def test_schema_rejects_assistance_overflow_and_unknown_fields(self) -> None:
        overflow = valid_payload()
        overflow["assistance_ceiling"] = "A3"
        with self.assertRaises(TeachingPlanValidationError):
            TeachingPlan.from_payload(overflow)

        extra = copy.deepcopy(valid_payload())
        extra["unexpected"] = True
        with self.assertRaises(TeachingPlanValidationError):
            validate_teaching_plan_schema(extra)

    def test_component_models_validate_their_own_contracts(self) -> None:
        with self.assertRaises(TeachingPlanValidationError):
            ProblemSpec("bad id!", "statement")
        with self.assertRaises(TeachingPlanValidationError):
            VariableSpec("", "meaning")
        with self.assertRaises(TeachingPlanValidationError):
            RepresentationRequirement("r", "stateful", "trace", "", True)
        with self.assertRaises(TeachingPlanValidationError):
            SemanticInvariant("i", "concept", "")
        with self.assertRaises(TeachingPlanValidationError):
            CompletionEvidence("e", "concept", "explanation", "")
        with self.assertRaises(TeachingPlanValidationError):
            ConceptSpec("concept", (), (), ("r",), ("i",))


if __name__ == "__main__":
    unittest.main()
