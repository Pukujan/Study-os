from __future__ import annotations

import json
import math
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jsonschema import Draft202012Validator
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.application.contracts import (  # noqa: E402
    APPLICATION_CONTRACT_VERSION,
    ApplicationError,
    ApplicationErrorCategory,
    ApplicationErrorEnvelope,
    RuntimeHealthCheck,
    RuntimeHealthRequest,
    RuntimeHealthResult,
    StartStudySessionRequest,
    StartStudySessionResult,
    application_contract_core_schema_bundle,
    canonical_model_json,
    render_application_contract_core_schema,
)

MCP_CONTRACT_PATH = ROOT / "contracts" / "study-os-mcp-tools.v0.1.json"
INVENTORY_PATH = ROOT / "contracts" / "application-operation-inventory.v0.1.json"


class ApplicationContractCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mcp_contract = json.loads(MCP_CONTRACT_PATH.read_text(encoding="utf-8"))
        self.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))

    def test_error_categories_match_durable_runtime_vocabulary(self) -> None:
        self.assertEqual(
            [category.value for category in ApplicationErrorCategory],
            self.mcp_contract["error_categories"],
        )

    def test_contract_version_and_extra_fields_fail_closed(self) -> None:
        with self.assertRaises(ValidationError):
            RuntimeHealthRequest(application_contract_version="0.2.0")
        with self.assertRaises(ValidationError):
            StartStudySessionRequest(
                idempotency_key="key-1",
                subject_id="subject-001",
                project_id="dsa-python",
                domain_id="dsa",
                invented=True,
            )

    def test_strict_request_types_do_not_coerce(self) -> None:
        with self.assertRaises(ValidationError):
            StartStudySessionRequest(
                idempotency_key="key-1",
                subject_id=1,
                project_id="dsa-python",
                domain_id="dsa",
            )

    def test_representative_request_result_fields_cover_inventory(self) -> None:
        start_operation = next(
            item for item in self.inventory["operations"] if item["mcp_tool"] == "start_session"
        )
        request_fields = set(StartStudySessionRequest.model_fields) - {"application_contract_version"}
        expected_request_fields = set(start_operation["required_request_fields"]) | set(
            start_operation["optional_request_fields"]
        )
        result_fields = set(StartStudySessionResult.model_fields) - {"application_contract_version"}
        self.assertEqual(request_fields, expected_request_fields)
        self.assertTrue(set(start_operation["required_result_fields"]) <= result_fields)

        doctor_operation = next(
            item for item in self.inventory["operations"] if item["mcp_tool"] == "doctor"
        )
        health_request_fields = set(RuntimeHealthRequest.model_fields) - {"application_contract_version"}
        health_result_fields = set(RuntimeHealthResult.model_fields) - {"application_contract_version"}
        self.assertEqual(health_request_fields, set(doctor_operation["required_request_fields"]))
        self.assertTrue(set(doctor_operation["required_result_fields"]) <= health_result_fields)

    def test_start_session_optional_compatibility_normalization(self) -> None:
        absent = StartStudySessionRequest(
            idempotency_key="key-1",
            subject_id="subject-001",
            project_id="dsa-python",
            domain_id="dsa",
        )
        explicit_null = StartStudySessionRequest(
            idempotency_key="key-1",
            subject_id="subject-001",
            project_id="dsa-python",
            domain_id="dsa",
            source_client=None,
            metadata=None,
        )
        explicit_empty = StartStudySessionRequest(
            idempotency_key="key-1",
            subject_id="subject-001",
            project_id="dsa-python",
            domain_id="dsa",
            metadata={},
        )
        self.assertIsNone(absent.source_client)
        self.assertEqual(absent.metadata, {})
        self.assertEqual(explicit_null.metadata, {})
        self.assertEqual(explicit_empty.metadata, {})
        self.assertEqual(canonical_model_json(absent), canonical_model_json(explicit_null))
        self.assertEqual(canonical_model_json(absent), canonical_model_json(explicit_empty))

    def test_start_session_metadata_uses_public_privacy_boundary(self) -> None:
        with self.assertRaises(ValidationError):
            StartStudySessionRequest(
                idempotency_key="key-1",
                subject_id="subject-001",
                project_id="dsa-python",
                domain_id="dsa",
                metadata={"nested": {"secret": "do not expose"}},
            )
        with self.assertRaises(ValidationError):
            StartStudySessionRequest(
                idempotency_key="key-1",
                subject_id="subject-001",
                project_id="dsa-python",
                domain_id="dsa",
                metadata=["not", "an", "object"],
            )

    def test_start_session_json_is_deterministic_and_utc_z(self) -> None:
        result = StartStudySessionResult(
            session_id="session-1",
            subject_id="subject-001",
            started_at=datetime(2026, 8, 25, 17, 30, tzinfo=timezone.utc),
            created=True,
        )
        first = canonical_model_json(result)
        second = canonical_model_json(result)
        self.assertEqual(first, second)
        payload = json.loads(first)
        self.assertEqual(payload["application_contract_version"], APPLICATION_CONTRACT_VERSION)
        self.assertEqual(payload["started_at"], "2026-08-25T17:30:00.000000Z")
        self.assertEqual(first, json.dumps(payload, sort_keys=True, separators=(",", ":")))

    def test_non_utc_or_naive_timestamp_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            StartStudySessionResult(
                session_id="session-1",
                subject_id="subject-001",
                started_at=datetime(2026, 8, 25, 17, 30),
                created=True,
            )
        with self.assertRaises(ValidationError):
            StartStudySessionResult(
                session_id="session-1",
                subject_id="subject-001",
                started_at=datetime(
                    2026,
                    8,
                    25,
                    17,
                    30,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                created=True,
            )

    def test_private_detail_keys_are_rejected_recursively(self) -> None:
        with self.assertRaises(ValidationError):
            ApplicationError(
                category=ApplicationErrorCategory.INTEGRITY_ERROR,
                code="evidence.invalid",
                message="Evidence is invalid",
                details={"context": {"private_transcript_body": "do not expose"}},
            )
        with self.assertRaises(ValidationError):
            RuntimeHealthCheck(
                healthy=False,
                detail="failed",
                metadata={"nested": [{"secret": "do not expose"}]},
            )

    def test_non_finite_public_json_is_rejected(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                ApplicationError(
                    category=ApplicationErrorCategory.INTERNAL_ERROR,
                    code="runtime.failure",
                    message="Runtime failure",
                    details={"numeric": value},
                )

    def test_error_code_is_machine_readable(self) -> None:
        envelope = ApplicationErrorEnvelope(
            error=ApplicationError(
                category=ApplicationErrorCategory.CONFLICT,
                code="checkpoint.stale_pointer",
                message="Checkpoint pointer is stale",
                details={"expected": "checkpoint-1"},
            )
        )
        self.assertIn('"code":"checkpoint.stale_pointer"', canonical_model_json(envelope))
        for invalid in ("Has Spaces", "UPPERCASE"):
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                ApplicationError(
                    category=ApplicationErrorCategory.CONFLICT,
                    code=invalid,
                    message="Conflict",
                )

    def test_generated_schema_is_valid_deterministic_and_accepts_examples(self) -> None:
        first = render_application_contract_core_schema()
        second = render_application_contract_core_schema()
        self.assertEqual(first, second)
        bundle = application_contract_core_schema_bundle()
        self.assertEqual(bundle["application_contract_version"], APPLICATION_CONTRACT_VERSION)

        for schema in bundle["models"].values():
            Draft202012Validator.check_schema(schema)

        request = StartStudySessionRequest(
            idempotency_key="key-1",
            subject_id="subject-001",
            project_id="dsa-python",
            domain_id="dsa",
            source_client="mcp",
            metadata={"surface": "chat"},
        )
        result = RuntimeHealthResult(
            healthy=True,
            runtime_version="0.1.0",
            schema_version=1,
            checks={"schema_version": RuntimeHealthCheck(healthy=True, detail="ok")},
        )
        Draft202012Validator(bundle["models"]["start_study_session_request"]).validate(
            request.model_dump(mode="json")
        )
        Draft202012Validator(bundle["models"]["inspect_runtime_health_result"]).validate(
            result.model_dump(mode="json")
        )


if __name__ == "__main__":
    unittest.main()
