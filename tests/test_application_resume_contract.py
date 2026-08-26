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
    RecentRepresentationSummary,
    ResumeRetentionProbeSummary,
    ResumeSubjectRequest,
    ResumeSubjectResult,
    application_contract_core_schema_bundle,
    canonical_model_json,
)

INVENTORY_PATH = ROOT / "contracts" / "application-operation-inventory.v0.1.json"


class ResumeApplicationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))

    def test_resume_request_and_minimum_result_cover_inventory(self) -> None:
        operation = next(
            item for item in self.inventory["operations"] if item["mcp_tool"] == "resume"
        )
        request_fields = set(ResumeSubjectRequest.model_fields) - {"application_contract_version"}
        result_fields = set(ResumeSubjectResult.model_fields) - {"application_contract_version"}
        self.assertEqual(request_fields, set(operation["required_request_fields"]))
        self.assertTrue(set(operation["required_result_fields"]) <= result_fields)

    def test_resume_full_continuity_serializes_deterministically(self) -> None:
        result = ResumeSubjectResult(
            subject_id="subject-001",
            checkpoint_id="checkpoint-001",
            capability_state={"state_prediction": "pass_unaided"},
            assistance_state={"level": "none"},
            current_focus="state transition",
            do_not_reteach=["basic indexing"],
            next_action="solve transfer trace",
            retention_due_at="2026-09-01T00:00:00Z",
            next_retention_probe=ResumeRetentionProbeSummary(
                retention_probe_id="probe-001",
                concept_id="state-transition",
                due_at="2026-09-01T00:00:00Z",
                status="scheduled",
                source_checkpoint_id="checkpoint-001",
            ),
            recent_representation_history=[
                RecentRepresentationSummary(
                    representation_family="deterministic_state_trace",
                    operation="predict",
                    representation_version="0.1.0",
                    target_bottleneck="state_transition",
                    created_at="2026-08-25T23:00:00Z",
                )
            ],
        )
        first = canonical_model_json(result)
        second = canonical_model_json(result)
        self.assertEqual(first, second)
        payload = json.loads(first)
        self.assertEqual(payload["do_not_reteach"], ["basic indexing"])
        self.assertEqual(
            payload["next_retention_probe"]["source_checkpoint_id"],
            "checkpoint-001",
        )
        self.assertEqual(
            payload["recent_representation_history"][0]["representation_version"],
            "0.1.0",
        )

    def test_resume_state_reuses_public_privacy_boundary(self) -> None:
        with self.assertRaises(ValidationError):
            ResumeSubjectResult(
                subject_id="subject-001",
                checkpoint_id="checkpoint-001",
                capability_state={"nested": {"secret": "do-not-expose"}},
                assistance_state={},
                current_focus="focus",
                do_not_reteach=[],
                next_action="next",
                retention_due_at=None,
                next_retention_probe=None,
                recent_representation_history=[],
            )

    def test_resume_rejects_empty_required_continuity_fields(self) -> None:
        with self.assertRaises(ValidationError):
            ResumeSubjectResult(
                subject_id="subject-001",
                checkpoint_id="checkpoint-001",
                capability_state={},
                assistance_state={},
                current_focus="focus",
                do_not_reteach=[],
                next_action="next",
                retention_due_at=None,
                next_retention_probe=None,
                recent_representation_history=[],
            )

    def test_generated_resume_schemas_are_valid(self) -> None:
        bundle = application_contract_core_schema_bundle()
        for name in ("resume_subject_request", "resume_subject_result"):
            Draft202012Validator.check_schema(bundle["models"][name])


if __name__ == "__main__":
    unittest.main()
