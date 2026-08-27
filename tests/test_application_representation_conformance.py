from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.application.contracts import (  # noqa: E402
    RecordRepresentationInterventionRequest,
    RecordRepresentationOutcomeRequest,
)
from study_os.application.service import (  # noqa: E402
    ApplicationService,
    project_record_representation_intervention_to_mcp,
    project_record_representation_outcome_to_mcp,
)
from study_os.mcp.server import MCPServer  # noqa: E402


class MalformedInterventionService:
    def record_representation_intervention(self, **_: Any) -> dict[str, Any]:
        return {"intervention_id": 123, "created": True}


class MalformedOutcomeService:
    def record_representation_outcome(self, **_: Any) -> dict[str, Any]:
        return {"outcome_id": "outcome-broken", "created": True, "evidence_score": 9}


class RepresentationApplicationConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)
        self.session = self.service.start_session(
            idempotency_key="representation-session",
            subject_id="subject-representation",
            project_id="project-representation",
            domain_id="dsa",
        )

    def tearDown(self) -> None:
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    @staticmethod
    def seed_behavioral_chain(
        service: StudyOSService,
        *,
        subject_id: str,
        suffix: str,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        session = service.start_session(
            idempotency_key=f"{suffix}-session",
            subject_id=subject_id,
            project_id=f"{suffix}-project",
            domain_id="dsa",
        )
        attempt = service.record_attempt(
            idempotency_key=f"{suffix}-attempt",
            session_id=session["session_id"],
            subject_id=subject_id,
            task_id="state-transition-trace",
            response={"prediction": "right"},
            assistance_level="none",
        )
        assessment = service.record_assessment(
            idempotency_key=f"{suffix}-assessment",
            session_id=session["session_id"],
            subject_id=subject_id,
            capability="state_prediction",
            result="pass",
            assistance_level="none",
            evidence_ids=[attempt["attempt_id"]],
        )
        intervention = service.record_representation_intervention(
            idempotency_key=f"{suffix}-intervention",
            session_id=session["session_id"],
            subject_id=subject_id,
            representation_family="deterministic_state_trace",
            operation="predict",
            representation_version="0.1.0",
            target_bottleneck="state_transition",
        )
        return session, assessment, intervention

    def test_intervention_direct_application_and_mcp_are_differentially_equivalent(self) -> None:
        roots = [tempfile.TemporaryDirectory() for _ in range(3)]
        services = [StudyOSService(RuntimeConfig.from_env(root.name)) for root in roots]
        sessions = [
            service.start_session(
                idempotency_key="representation-differential-session",
                subject_id="subject-representation-differential",
                project_id="project-representation-differential",
                domain_id="dsa",
            )
            for service in services
        ]
        common = {
            "idempotency_key": "representation-differential",
            "subject_id": "subject-representation-differential",
            "representation_family": "deterministic_state_trace",
            "operation": "predict",
            "representation_version": "0.1.0",
            "target_bottleneck": "state_transition",
        }
        try:
            with patch(
                "study_os.services.runtime_base.new_id",
                side_effect=[
                    "representation-fixed",
                    "intervention-fixed",
                    "representation-fixed",
                    "intervention-fixed",
                    "representation-fixed",
                    "intervention-fixed",
                ],
            ):
                direct = services[0].record_representation_intervention(
                    **common,
                    session_id=sessions[0]["session_id"],
                )
                application = project_record_representation_intervention_to_mcp(
                    ApplicationService(services[1]).record_representation_intervention(
                        RecordRepresentationInterventionRequest(
                            **common,
                            session_id=sessions[1]["session_id"],
                        )
                    )
                )
                mcp = MCPServer(services[2]).call_tool(
                    "record_representation_intervention",
                    {**common, "session_id": sessions[2]["session_id"]},
                )

            self.assertEqual(application, direct)
            self.assertEqual(mcp, direct)
            for service in services:
                row = service.db.connection.execute(
                    "SELECT intervention_id, representation_id, representation_family, "
                    "operation, representation_version, target_bottleneck FROM interventions "
                    "WHERE subject_id = ?",
                    ("subject-representation-differential",),
                ).fetchone()
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["intervention_id"], "intervention-fixed")
                self.assertEqual(row["representation_id"], "representation-fixed")
                self.assertEqual(row["representation_family"], "deterministic_state_trace")
                self.assertEqual(row["operation"], "predict")
                self.assertEqual(row["representation_version"], "0.1.0")
                self.assertEqual(row["target_bottleneck"], "state_transition")
        finally:
            for service in services:
                service.close()
            for root in roots:
                root.cleanup()

    def test_intervention_retry_reuses_one_representation_and_conflicting_request_fails(self) -> None:
        server = MCPServer(self.service)
        base = {
            "idempotency_key": "representation-retry",
            "session_id": self.session["session_id"],
            "subject_id": "subject-representation",
            "representation_family": "deterministic_state_trace",
            "operation": "predict",
            "representation_version": "0.1.0",
            "target_bottleneck": "state_transition",
        }
        first = server.call_tool("record_representation_intervention", base)
        retry = server.call_tool("record_representation_intervention", base)
        conflict = server.call_tool(
            "record_representation_intervention",
            {**base, "operation": "explain"},
        )

        self.assertTrue(first["created"])
        self.assertFalse(retry["created"])
        self.assertEqual(first["intervention_id"], retry["intervention_id"])
        self.assertEqual(conflict["error"]["category"], "conflict")
        representation_count = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM representations WHERE family = ? AND semantic_version = ?",
            ("deterministic_state_trace", "0.1.0"),
        ).fetchone()[0]
        intervention_count = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM interventions WHERE subject_id = ?",
            ("subject-representation",),
        ).fetchone()[0]
        self.assertEqual(representation_count, 1)
        self.assertEqual(intervention_count, 1)

    def test_intervention_validation_not_found_and_malformed_result_fail_closed(self) -> None:
        base = {
            "idempotency_key": "representation-invalid",
            "session_id": self.session["session_id"],
            "subject_id": "subject-representation",
            "representation_family": "deterministic_state_trace",
            "operation": "predict",
            "representation_version": "version-one",
            "target_bottleneck": "state_transition",
        }
        invalid = MCPServer(self.service).call_tool(
            "record_representation_intervention",
            base,
        )
        self.assertEqual(invalid["error"]["category"], "validation_error")

        missing = MCPServer(self.service).call_tool(
            "record_representation_intervention",
            {**base, "session_id": "missing-session", "representation_version": "0.1.0"},
        )
        self.assertEqual(missing["error"]["category"], "not_found")

        malformed = MCPServer(MalformedInterventionService()).call_tool(  # type: ignore[arg-type]
            "record_representation_intervention",
            {**base, "representation_version": "0.1.0"},
        )
        self.assertEqual(malformed["error"]["category"], "internal_error")
        self.assertEqual(
            malformed["error"]["details"]["exception"],
            "ApplicationBoundaryError",
        )

    def test_outcome_direct_application_and_mcp_are_differentially_equivalent(self) -> None:
        roots = [tempfile.TemporaryDirectory() for _ in range(3)]
        services = [StudyOSService(RuntimeConfig.from_env(root.name)) for root in roots]
        seeded = [
            self.seed_behavioral_chain(
                service,
                subject_id="subject-outcome-differential",
                suffix=f"outcome-{index}",
            )
            for index, service in enumerate(services)
        ]
        try:
            with patch(
                "study_os.services.runtime_base.new_id",
                return_value="outcome-fixed",
            ):
                direct = services[0].record_representation_outcome(
                    idempotency_key="outcome-differential",
                    intervention_id=seeded[0][2]["intervention_id"],
                    subject_id="subject-outcome-differential",
                    evidence_score=3,
                    evidence_ids=[seeded[0][1]["assessment_id"]],
                )
                application = project_record_representation_outcome_to_mcp(
                    ApplicationService(services[1]).record_representation_outcome(
                        RecordRepresentationOutcomeRequest(
                            idempotency_key="outcome-differential",
                            intervention_id=seeded[1][2]["intervention_id"],
                            subject_id="subject-outcome-differential",
                            evidence_score=3,
                            evidence_ids=[seeded[1][1]["assessment_id"]],
                        )
                    )
                )
                mcp = MCPServer(services[2]).call_tool(
                    "record_representation_outcome",
                    {
                        "idempotency_key": "outcome-differential",
                        "intervention_id": seeded[2][2]["intervention_id"],
                        "subject_id": "subject-outcome-differential",
                        "evidence_score": 3,
                        "evidence_ids": [seeded[2][1]["assessment_id"]],
                    },
                )

            self.assertEqual(application, direct)
            self.assertEqual(mcp, direct)
            for index, service in enumerate(services):
                row = service.db.connection.execute(
                    "SELECT outcome_id, evidence_score, evidence_ids_json "
                    "FROM representation_outcomes WHERE subject_id = ?",
                    ("subject-outcome-differential",),
                ).fetchone()
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["outcome_id"], "outcome-fixed")
                self.assertEqual(row["evidence_score"], 3)
                self.assertEqual(
                    json.loads(row["evidence_ids_json"]),
                    [seeded[index][1]["assessment_id"]],
                )
        finally:
            for service in services:
                service.close()
            for root in roots:
                root.cleanup()

    def test_outcome_retry_conflict_and_behavioral_evidence_invariant(self) -> None:
        _, assessment, intervention = self.seed_behavioral_chain(
            self.service,
            subject_id="subject-outcome",
            suffix="outcome-local",
        )
        server = MCPServer(self.service)
        base = {
            "idempotency_key": "outcome-retry",
            "intervention_id": intervention["intervention_id"],
            "subject_id": "subject-outcome",
            "evidence_score": 3,
            "evidence_ids": [assessment["assessment_id"]],
        }
        first = server.call_tool("record_representation_outcome", base)
        retry = server.call_tool("record_representation_outcome", base)
        conflict = server.call_tool(
            "record_representation_outcome",
            {**base, "evidence_score": 4},
        )
        self.assertTrue(first["created"])
        self.assertFalse(retry["created"])
        self.assertEqual(first["outcome_id"], retry["outcome_id"])
        self.assertEqual(conflict["error"]["category"], "conflict")

        event = self.service.record_learning_event(
            idempotency_key="outcome-non-assessment-event",
            session_id=self.session["session_id"],
            subject_id="subject-representation",
            evidence_class="observed",
            event_type="hint_presented",
            payload={"hint": "consider state transition"},
        )
        other_intervention = self.service.record_representation_intervention(
            idempotency_key="outcome-non-assessment-intervention",
            session_id=self.session["session_id"],
            subject_id="subject-representation",
            representation_family="state_table",
            operation="predict",
            representation_version="0.1.0",
            target_bottleneck="state_transition",
        )
        invalid = server.call_tool(
            "record_representation_outcome",
            {
                "idempotency_key": "outcome-non-assessment",
                "intervention_id": other_intervention["intervention_id"],
                "subject_id": "subject-representation",
                "evidence_score": 2,
                "evidence_ids": [event["event_id"]],
            },
        )
        self.assertEqual(invalid["error"]["category"], "integrity_error")

    def test_outcome_not_found_subject_mismatch_and_malformed_result_fail_closed(self) -> None:
        _, assessment, intervention = self.seed_behavioral_chain(
            self.service,
            subject_id="subject-outcome-negative",
            suffix="outcome-negative",
        )
        server = MCPServer(self.service)
        missing = server.call_tool(
            "record_representation_outcome",
            {
                "idempotency_key": "outcome-missing",
                "intervention_id": "missing-intervention",
                "subject_id": "subject-outcome-negative",
                "evidence_score": 3,
                "evidence_ids": [assessment["assessment_id"]],
            },
        )
        self.assertEqual(missing["error"]["category"], "not_found")

        mismatch = server.call_tool(
            "record_representation_outcome",
            {
                "idempotency_key": "outcome-mismatch",
                "intervention_id": intervention["intervention_id"],
                "subject_id": "other-subject",
                "evidence_score": 3,
                "evidence_ids": [assessment["assessment_id"]],
            },
        )
        self.assertEqual(mismatch["error"]["category"], "integrity_error")

        malformed = MCPServer(MalformedOutcomeService()).call_tool(  # type: ignore[arg-type]
            "record_representation_outcome",
            {
                "idempotency_key": "outcome-malformed",
                "intervention_id": "intervention-broken",
                "subject_id": "subject-broken",
                "evidence_score": 3,
                "evidence_ids": ["assessment-broken"],
            },
        )
        self.assertEqual(malformed["error"]["category"], "internal_error")
        self.assertEqual(
            malformed["error"]["details"]["exception"],
            "ApplicationBoundaryError",
        )

    def test_representation_mcp_rejects_application_only_or_unknown_fields(self) -> None:
        intervention_base = {
            "idempotency_key": "representation-unexpected",
            "session_id": self.session["session_id"],
            "subject_id": "subject-representation",
            "representation_family": "deterministic_state_trace",
            "operation": "predict",
            "representation_version": "0.1.0",
            "target_bottleneck": "state_transition",
        }
        for extra in (
            {"application_contract_version": "0.1.0"},
            {"invented": True},
        ):
            with self.subTest(operation="intervention", extra=extra):
                result = MCPServer(self.service).call_tool(
                    "record_representation_intervention",
                    {**intervention_base, **extra},
                )
                self.assertEqual(result["error"]["category"], "validation_error")

        outcome_base = {
            "idempotency_key": "outcome-unexpected",
            "intervention_id": "intervention-001",
            "subject_id": "subject-representation",
            "evidence_score": 3,
            "evidence_ids": ["assessment-001"],
        }
        for extra in (
            {"application_contract_version": "0.1.0"},
            {"invented": True},
        ):
            with self.subTest(operation="outcome", extra=extra):
                result = MCPServer(self.service).call_tool(
                    "record_representation_outcome",
                    {**outcome_base, **extra},
                )
                self.assertEqual(result["error"]["category"], "validation_error")


if __name__ == "__main__":
    unittest.main()
