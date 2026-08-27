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
    RecordAssessmentRequest,
    RecordAssessmentResult,
    application_contract_core_schema_bundle,
)

INVENTORY_PATH = ROOT / "contracts" / "application-operation-inventory.v0.1.json"


class AssessmentContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        self.operation = next(
            item
            for item in self.inventory["operations"]
            if item["mcp_tool"] == "record_assessment"
        )

    def test_request_fields_match_required_and_optional_inventory(self) -> None:
        request_fields = set(RecordAssessmentRequest.model_fields) - {
            "application_contract_version"
        }
        expected = set(self.operation["required_request_fields"]) | set(
            self.operation["optional_request_fields"]
        )
        self.assertEqual(request_fields, expected)
        self.assertEqual(self.operation["optional_request_fields"], ["retention_probe_id"])

    def test_request_is_strict_and_requires_nonempty_evidence(self) -> None:
        base = {
            "idempotency_key": "assessment-key",
            "session_id": "session-001",
            "subject_id": "subject-001",
            "capability": "state-prediction",
            "result": "pass_delayed",
            "assistance_level": "none",
            "evidence_ids": ["attempt-001"],
        }
        request = RecordAssessmentRequest(**base)
        self.assertIsNone(request.retention_probe_id)
        linked = RecordAssessmentRequest(**base, retention_probe_id="probe-001")
        self.assertEqual(linked.retention_probe_id, "probe-001")

        with self.assertRaises(ValidationError):
            RecordAssessmentRequest(**{**base, "evidence_ids": []})
        with self.assertRaises(ValidationError):
            RecordAssessmentRequest(**{**base, "retention_probe_id": 1})
        with self.assertRaises(ValidationError):
            RecordAssessmentRequest(**{**base, "invented": True})
        with self.assertRaises(ValidationError):
            RecordAssessmentRequest(
                **base,
                application_contract_version="0.2.0",
            )

    def test_result_retention_completion_fields_are_all_or_nothing(self) -> None:
        plain = RecordAssessmentResult(
            assessment_id="assessment-001",
            created=True,
            capability="state-prediction",
            result="pass_delayed",
        )
        self.assertNotIn("retention_probe_id", plain.model_fields_set)
        self.assertNotIn("retention_probe_status", plain.model_fields_set)

        linked = RecordAssessmentResult(
            assessment_id="assessment-002",
            created=True,
            capability="state-prediction",
            result="pass_delayed",
            retention_probe_id="probe-001",
            retention_probe_status="completed",
        )
        self.assertEqual(linked.retention_probe_status, "completed")

        with self.assertRaises(ValidationError):
            RecordAssessmentResult(
                assessment_id="assessment-bad-1",
                created=True,
                capability="state-prediction",
                result="pass_delayed",
                retention_probe_id="probe-001",
            )
        with self.assertRaises(ValidationError):
            RecordAssessmentResult(
                assessment_id="assessment-bad-2",
                created=True,
                capability="state-prediction",
                result="pass_delayed",
                retention_probe_status="completed",
            )
        with self.assertRaises(ValidationError):
            RecordAssessmentResult(
                assessment_id="assessment-bad-3",
                created=True,
                capability="state-prediction",
                result="pass_delayed",
                retention_probe_id=None,
                retention_probe_status="completed",
            )

    def test_generated_schema_registers_and_validates_assessment_models(self) -> None:
        bundle = application_contract_core_schema_bundle()
        self.assertIn("record_assessment_request", bundle["models"])
        self.assertIn("record_assessment_result", bundle["models"])

        request = RecordAssessmentRequest(
            idempotency_key="assessment-key",
            session_id="session-001",
            subject_id="subject-001",
            capability="state-prediction",
            result="pass_delayed",
            assistance_level="none",
            evidence_ids=["attempt-001"],
            retention_probe_id="probe-001",
        )
        result = RecordAssessmentResult(
            assessment_id="assessment-001",
            created=True,
            capability="state-prediction",
            result="pass_delayed",
            retention_probe_id="probe-001",
            retention_probe_status="completed",
        )
        Draft202012Validator(bundle["models"]["record_assessment_request"]).validate(
            request.model_dump(mode="json")
        )
        Draft202012Validator(bundle["models"]["record_assessment_result"]).validate(
            result.model_dump(mode="json")
        )


if __name__ == "__main__":
    unittest.main()
