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
    CreateFossilExportRequest,
    CreateFossilExportResult,
    application_contract_core_schema_bundle,
)

INVENTORY_PATH = ROOT / "contracts" / "application-operation-inventory.v0.1.json"


class FossilExportContractTests(unittest.TestCase):
    def setUp(self) -> None:
        inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        self.operation = next(
            item for item in inventory["operations"] if item["mcp_tool"] == "export_fossil"
        )

    def test_request_and_result_fields_match_inventory(self) -> None:
        request_fields = set(CreateFossilExportRequest.model_fields) - {
            "application_contract_version"
        }
        result_fields = set(CreateFossilExportResult.model_fields) - {
            "application_contract_version"
        }
        self.assertEqual(request_fields, set(self.operation["required_request_fields"]))
        self.assertEqual(result_fields, set(self.operation["required_result_fields"]))

    def test_request_is_strict_and_requires_curated_sources(self) -> None:
        base = {
            "idempotency_key": "fossil-key",
            "subject_id": "subject-001",
            "artifact_type": "study_fossil",
            "source_ids": ["attempt-001"],
        }
        request = CreateFossilExportRequest(**base)
        self.assertEqual(request.source_ids, ["attempt-001"])

        with self.assertRaises(ValidationError):
            CreateFossilExportRequest(**{**base, "source_ids": []})
        with self.assertRaises(ValidationError):
            CreateFossilExportRequest(**{**base, "artifact_type": " "})
        with self.assertRaises(ValidationError):
            CreateFossilExportRequest(**{**base, "source_ids": [1]})
        with self.assertRaises(ValidationError):
            CreateFossilExportRequest(**{**base, "invented": True})
        with self.assertRaises(ValidationError):
            CreateFossilExportRequest(
                **base,
                application_contract_version="0.2.0",
            )

    def test_result_requires_nonempty_resolved_source_ids(self) -> None:
        result = CreateFossilExportResult(
            export_id="export-001",
            created=True,
            artifact_type="study_fossil",
            source_ids=["attempt-001"],
        )
        self.assertEqual(result.source_ids, ["attempt-001"])
        with self.assertRaises(ValidationError):
            CreateFossilExportResult(
                export_id="export-001",
                created=True,
                artifact_type="study_fossil",
                source_ids=[],
            )

    def test_generated_schema_registers_and_validates_fossil_models(self) -> None:
        bundle = application_contract_core_schema_bundle()
        self.assertIn("create_fossil_export_request", bundle["models"])
        self.assertIn("create_fossil_export_result", bundle["models"])

        request = CreateFossilExportRequest(
            idempotency_key="fossil-key",
            subject_id="subject-001",
            artifact_type="study_fossil",
            source_ids=["attempt-001"],
        )
        result = CreateFossilExportResult(
            export_id="export-001",
            created=True,
            artifact_type="study_fossil",
            source_ids=["attempt-001"],
        )
        Draft202012Validator(bundle["models"]["create_fossil_export_request"]).validate(
            request.model_dump(mode="json")
        )
        Draft202012Validator(bundle["models"]["create_fossil_export_result"]).validate(
            result.model_dump(mode="json")
        )


if __name__ == "__main__":
    unittest.main()
