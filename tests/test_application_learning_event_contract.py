from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.application.contracts import (  # noqa: E402
    RecordLearningEventRequest,
    RecordLearningEventResult,
    application_contract_core_schema_bundle,
    canonical_model_json,
)

INVENTORY_PATH = ROOT / "contracts" / "application-operation-inventory.v0.1.json"


class RecordLearningEventApplicationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        self.operation = next(
            item for item in inventory["operations"]
            if item["mcp_tool"] == "record_learning_event"
        )

    def test_request_and_result_cover_inventory(self) -> None:
        request_fields = set(RecordLearningEventRequest.model_fields) - {
            "application_contract_version"
        }
        expected_request_fields = set(self.operation["required_request_fields"]) | set(
            self.operation["optional_request_fields"]
        )
        result_fields = set(RecordLearningEventResult.model_fields) - {
            "application_contract_version"
        }

        self.assertEqual(request_fields, expected_request_fields)
        self.assertEqual(result_fields, set(self.operation["required_result_fields"]))
        self.assertEqual(
            self.operation["request_normalization"],
            {
                "source_ids": (
                    "absent_or_null_derives_from_payload_evidence_ids_before_runtime_"
                    "idempotency_fingerprint"
                ),
                "payload_version": "absent_to_legacy_0.1.0_default",
            },
        )

    def test_legacy_defaults_remain_explicit(self) -> None:
        base = {
            "idempotency_key": "event-key",
            "session_id": "session-001",
            "subject_id": "subject-001",
            "evidence_class": "observed",
            "event_type": "prediction_submitted",
            "payload": {"prediction": "right"},
        }
        absent = RecordLearningEventRequest(**base)
        explicit = RecordLearningEventRequest(
            **base,
            source_ids=None,
            payload_version="0.1.0",
        )

        self.assertIsNone(absent.source_ids)
        self.assertEqual(absent.payload_version, "0.1.0")
        self.assertEqual(canonical_model_json(absent), canonical_model_json(explicit))

    def test_evidence_class_is_canonical_but_payload_remains_semantic_json(self) -> None:
        request = RecordLearningEventRequest(
            idempotency_key="event-key",
            session_id="session-001",
            subject_id="subject-001",
            evidence_class="derived",
            event_type="diagnosis",
            payload={
                "evidence_ids": ["attempt-1"],
                "claim": {"possible_bottleneck": "update_order"},
            },
        )
        payload = json.loads(canonical_model_json(request))
        self.assertEqual(payload["evidence_class"], "derived")
        self.assertEqual(payload["payload"]["evidence_ids"], ["attempt-1"])

        with self.assertRaises(ValidationError):
            RecordLearningEventRequest(
                idempotency_key="event-key",
                session_id="session-001",
                subject_id="subject-001",
                evidence_class="invented",
                event_type="diagnosis",
                payload={},
            )

    def test_request_rejects_unknown_fields_and_invalid_source_ids(self) -> None:
        base = {
            "idempotency_key": "event-key",
            "session_id": "session-001",
            "subject_id": "subject-001",
            "evidence_class": "observed",
            "event_type": "prediction_submitted",
            "payload": {},
        }
        with self.assertRaises(ValidationError):
            RecordLearningEventRequest(**base, invented=True)
        with self.assertRaises(ValidationError):
            RecordLearningEventRequest(**base, source_ids=[""])

    def test_non_finite_payload_is_rejected(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                RecordLearningEventRequest(
                    idempotency_key="event-key",
                    session_id="session-001",
                    subject_id="subject-001",
                    evidence_class="observed",
                    event_type="numeric_observation",
                    payload={"numeric": value},
                )

    def test_generated_learning_event_schemas_are_valid(self) -> None:
        bundle = application_contract_core_schema_bundle()
        for name in ("record_learning_event_request", "record_learning_event_result"):
            Draft202012Validator.check_schema(bundle["models"][name])


if __name__ == "__main__":
    unittest.main()
