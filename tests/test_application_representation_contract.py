from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.application.contracts import (  # noqa: E402
    RecordRepresentationInterventionRequest,
    RecordRepresentationInterventionResult,
    RecordRepresentationOutcomeRequest,
    RecordRepresentationOutcomeResult,
    application_contract_core_schema_bundle,
    canonical_model_json,
)

INVENTORY_PATH = ROOT / "contracts" / "application-operation-inventory.v0.1.json"


class RepresentationApplicationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        self.operations = {item["mcp_tool"]: item for item in inventory["operations"]}

    def test_intervention_request_and_result_cover_inventory(self) -> None:
        operation = self.operations["record_representation_intervention"]
        request_fields = set(RecordRepresentationInterventionRequest.model_fields) - {
            "application_contract_version"
        }
        result_fields = set(RecordRepresentationInterventionResult.model_fields) - {
            "application_contract_version"
        }
        self.assertEqual(request_fields, set(operation["required_request_fields"]))
        self.assertEqual(result_fields, set(operation["required_result_fields"]))

    def test_outcome_request_and_result_cover_inventory(self) -> None:
        operation = self.operations["record_representation_outcome"]
        request_fields = set(RecordRepresentationOutcomeRequest.model_fields) - {
            "application_contract_version"
        }
        result_fields = set(RecordRepresentationOutcomeResult.model_fields) - {
            "application_contract_version"
        }
        self.assertEqual(request_fields, set(operation["required_request_fields"]))
        self.assertEqual(result_fields, set(operation["required_result_fields"]))

    def test_intervention_requires_runtime_semver_shape(self) -> None:
        base = {
            "idempotency_key": "intervention-key",
            "session_id": "session-001",
            "subject_id": "subject-001",
            "representation_family": "deterministic_state_trace",
            "operation": "predict",
            "target_bottleneck": "state_transition",
        }
        valid = RecordRepresentationInterventionRequest(
            **base,
            representation_version="0.1.0",
        )
        self.assertEqual(valid.representation_version, "0.1.0")
        for invalid in ("version-one", "0.1", " 0.1.0 "):
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                RecordRepresentationInterventionRequest(
                    **base,
                    representation_version=invalid,
                )

    def test_outcome_score_and_evidence_bounds_are_strict(self) -> None:
        base = {
            "idempotency_key": "outcome-key",
            "intervention_id": "intervention-001",
            "subject_id": "subject-001",
            "evidence_ids": ["assessment-001"],
        }
        for score in range(6):
            result = RecordRepresentationOutcomeRequest(**base, evidence_score=score)
            self.assertEqual(result.evidence_score, score)
        for invalid in (-1, 6, True):
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                RecordRepresentationOutcomeRequest(**base, evidence_score=invalid)
        with self.assertRaises(ValidationError):
            RecordRepresentationOutcomeRequest(
                idempotency_key="outcome-key",
                intervention_id="intervention-001",
                subject_id="subject-001",
                evidence_score=3,
                evidence_ids=[],
            )

    def test_contracts_reject_unknown_fields_and_serialize_deterministically(self) -> None:
        intervention = RecordRepresentationInterventionRequest(
            idempotency_key="intervention-key",
            session_id="session-001",
            subject_id="subject-001",
            representation_family="deterministic_state_trace",
            operation="predict",
            representation_version="0.1.0",
            target_bottleneck="state_transition",
        )
        first = canonical_model_json(intervention)
        second = canonical_model_json(intervention)
        self.assertEqual(first, second)
        with self.assertRaises(ValidationError):
            RecordRepresentationInterventionRequest(
                idempotency_key="intervention-key",
                session_id="session-001",
                subject_id="subject-001",
                representation_family="deterministic_state_trace",
                operation="predict",
                representation_version="0.1.0",
                target_bottleneck="state_transition",
                invented=True,
            )

    def test_generated_representation_schemas_are_valid(self) -> None:
        bundle = application_contract_core_schema_bundle()
        for name in (
            "record_representation_intervention_request",
            "record_representation_intervention_result",
            "record_representation_outcome_request",
            "record_representation_outcome_result",
        ):
            Draft202012Validator.check_schema(bundle["models"][name])


if __name__ == "__main__":
    unittest.main()
