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
    ScheduleRetentionProbeRequest,
    ScheduleRetentionProbeResult,
    application_contract_core_schema_bundle,
    canonical_model_json,
)

INVENTORY_PATH = ROOT / "contracts" / "application-operation-inventory.v0.1.json"


class RetentionScheduleContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))

    def test_request_and_result_fields_match_operation_inventory(self) -> None:
        operation = next(
            item
            for item in self.inventory["operations"]
            if item["mcp_tool"] == "schedule_retention_probe"
        )
        request_fields = set(ScheduleRetentionProbeRequest.model_fields) - {
            "application_contract_version"
        }
        result_fields = set(ScheduleRetentionProbeResult.model_fields) - {
            "application_contract_version"
        }
        self.assertEqual(request_fields, set(operation["required_request_fields"]))
        self.assertEqual(result_fields, set(operation["required_result_fields"]))

    def test_request_is_strict_and_due_at_remains_an_opaque_string(self) -> None:
        request = ScheduleRetentionProbeRequest(
            idempotency_key="retention-key",
            subject_id="subject-001",
            concept_id="sliding-window",
            due_at="retention-window-02",
            source_checkpoint_id="checkpoint-001",
        )
        self.assertEqual(request.due_at, "retention-window-02")
        self.assertIn('"due_at":"retention-window-02"', canonical_model_json(request))

        with self.assertRaises(ValidationError):
            ScheduleRetentionProbeRequest(
                idempotency_key="retention-key",
                subject_id="subject-001",
                concept_id="sliding-window",
                due_at=2,
                source_checkpoint_id="checkpoint-001",
            )
        with self.assertRaises(ValidationError):
            ScheduleRetentionProbeRequest(
                idempotency_key="retention-key",
                subject_id="subject-001",
                concept_id="sliding-window",
                due_at="retention-window-02",
                source_checkpoint_id="checkpoint-001",
                invented=True,
            )
        with self.assertRaises(ValidationError):
            ScheduleRetentionProbeRequest(
                application_contract_version="0.2.0",
                idempotency_key="retention-key",
                subject_id="subject-001",
                concept_id="sliding-window",
                due_at="retention-window-02",
                source_checkpoint_id="checkpoint-001",
            )

    def test_generated_schema_registers_and_validates_schedule_models(self) -> None:
        bundle = application_contract_core_schema_bundle()
        self.assertIn("schedule_retention_probe_request", bundle["models"])
        self.assertIn("schedule_retention_probe_result", bundle["models"])

        request = ScheduleRetentionProbeRequest(
            idempotency_key="retention-key",
            subject_id="subject-001",
            concept_id="sliding-window",
            due_at="retention-window-02",
            source_checkpoint_id="checkpoint-001",
        )
        result = ScheduleRetentionProbeResult(
            retention_probe_id="probe-001",
            created=True,
            due_at="retention-window-02",
        )
        Draft202012Validator(bundle["models"]["schedule_retention_probe_request"]).validate(
            request.model_dump(mode="json")
        )
        Draft202012Validator(bundle["models"]["schedule_retention_probe_result"]).validate(
            result.model_dump(mode="json")
        )


if __name__ == "__main__":
    unittest.main()
