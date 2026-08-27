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
    RecordAttemptRequest,
    RecordAttemptResult,
    application_contract_core_schema_bundle,
    canonical_model_json,
)

INVENTORY_PATH = ROOT / "contracts" / "application-operation-inventory.v0.1.json"


class RecordAttemptApplicationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        self.operation = next(
            item for item in self.inventory["operations"] if item["mcp_tool"] == "record_attempt"
        )

    def test_request_and_result_cover_inventory(self) -> None:
        request_fields = set(RecordAttemptRequest.model_fields) - {"application_contract_version"}
        expected_request_fields = set(self.operation["required_request_fields"]) | set(
            self.operation["optional_request_fields"]
        )
        result_fields = set(RecordAttemptResult.model_fields) - {"application_contract_version"}

        self.assertEqual(request_fields, expected_request_fields)
        self.assertEqual(result_fields, set(self.operation["required_result_fields"]))
        self.assertEqual(
            self.operation["request_normalization"],
            {
                "assistance_level": "absent_to_legacy_none_string_default",
                "context": (
                    "absent_or_null_to_empty_object_before_runtime_idempotency_fingerprint"
                ),
            },
        )

    def test_legacy_defaults_and_null_context_normalize_before_fingerprinting(self) -> None:
        base = {
            "idempotency_key": "attempt-key",
            "session_id": "session-001",
            "subject_id": "subject-001",
            "task_id": "task-001",
            "response": {"answer": "right"},
        }
        absent = RecordAttemptRequest(**base)
        explicit = RecordAttemptRequest(
            **base,
            assistance_level="none",
            context=None,
        )
        explicit_empty = RecordAttemptRequest(
            **base,
            assistance_level="none",
            context={},
        )

        self.assertEqual(absent.assistance_level, "none")
        self.assertEqual(absent.context, {})
        self.assertEqual(explicit.context, {})
        self.assertEqual(canonical_model_json(absent), canonical_model_json(explicit))
        self.assertEqual(canonical_model_json(absent), canonical_model_json(explicit_empty))

    def test_existing_assistance_vocabulary_and_telemetry_json_remain_accepted(self) -> None:
        request = RecordAttemptRequest(
            idempotency_key="attempt-key",
            session_id="session-001",
            subject_id="subject-001",
            task_id="task-001",
            response={"prediction": [1, 2, 3], "answer_state": {"largest": 3}},
            assistance_level="representation_visible",
            context={
                "context_version": "0.1.0",
                "interaction_mode": "state_prediction",
                "attempt_number": 1,
                "self_report": {"confidence": "low"},
            },
        )
        payload = json.loads(canonical_model_json(request))

        self.assertEqual(payload["assistance_level"], "representation_visible")
        self.assertEqual(payload["response"]["answer_state"]["largest"], 3)
        self.assertEqual(payload["context"]["interaction_mode"], "state_prediction")

    def test_request_is_strict_and_rejects_unknown_fields(self) -> None:
        with self.assertRaises(ValidationError):
            RecordAttemptRequest(
                idempotency_key="attempt-key",
                session_id="session-001",
                subject_id="subject-001",
                task_id="task-001",
                response={"answer": "right"},
                assistance_level=None,
            )
        with self.assertRaises(ValidationError):
            RecordAttemptRequest(
                idempotency_key="attempt-key",
                session_id="session-001",
                subject_id="subject-001",
                task_id="task-001",
                response={"answer": "right"},
                invented=True,
            )

    def test_non_finite_response_or_context_is_rejected(self) -> None:
        for field_name in ("response", "context"):
            for value in (math.nan, math.inf, -math.inf):
                with self.subTest(field=field_name, value=value), self.assertRaises(
                    ValidationError
                ):
                    kwargs = {
                        "idempotency_key": "attempt-key",
                        "session_id": "session-001",
                        "subject_id": "subject-001",
                        "task_id": "task-001",
                        "response": {"answer": "right"},
                        "context": {},
                    }
                    kwargs[field_name] = {"numeric": value}
                    RecordAttemptRequest(**kwargs)

    def test_generated_record_attempt_schemas_are_valid(self) -> None:
        bundle = application_contract_core_schema_bundle()
        for name in ("record_attempt_request", "record_attempt_result"):
            Draft202012Validator.check_schema(bundle["models"][name])


if __name__ == "__main__":
    unittest.main()
