from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.application.contracts import RecordAssessmentRequest  # noqa: E402
from study_os.application.service import (  # noqa: E402
    ApplicationService,
    project_record_assessment_to_mcp,
)
from study_os.mcp.server import MCPServer  # noqa: E402


class MalformedAssessmentService:
    def record_assessment(self, **_: Any) -> dict[str, Any]:
        return {
            "assessment_id": "assessment-broken",
            "created": True,
            "capability": "cap-1",
            "result": "pass_delayed",
            "retention_probe_id": "probe-broken",
        }


class AssessmentApplicationConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.service = StudyOSService(RuntimeConfig.from_env(self.temp_dir.name))
        self.session_id, self.attempt_id = self.seed_session(
            self.service,
            subject_id="subject-assessment",
            suffix="assessment-local",
        )

    def tearDown(self) -> None:
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    @staticmethod
    def seed_session(
        service: StudyOSService,
        *,
        subject_id: str,
        suffix: str,
    ) -> tuple[str, str]:
        session = service.start_session(
            idempotency_key=f"{suffix}-session",
            subject_id=subject_id,
            project_id=f"{suffix}-project",
            domain_id=f"{suffix}-domain",
        )
        attempt = service.record_attempt(
            idempotency_key=f"{suffix}-attempt",
            session_id=session["session_id"],
            subject_id=subject_id,
            task_id="assessment-source-task",
            response={"prediction": "right"},
            assistance_level="none",
        )
        return session["session_id"], attempt["attempt_id"]

    @staticmethod
    def seed_probe(
        service: StudyOSService,
        *,
        subject_id: str,
        session_id: str,
        evidence_id: str,
        capability: str,
        suffix: str,
        probe_id: str | None = None,
    ) -> dict[str, Any]:
        checkpoint = service.checkpoint(
            idempotency_key=f"{suffix}-checkpoint",
            subject_id=subject_id,
            source_session_ids=[session_id],
            evidence_ids=[evidence_id],
            capability_state={capability: "supported"},
            assistance_state={"current": "none"},
            resume={
                "current_focus": capability,
                "do_not_reteach": [],
                "next_action": "run retention assessment",
            },
        )
        request = {
            "idempotency_key": f"{suffix}-probe",
            "subject_id": subject_id,
            "concept_id": capability,
            "due_at": "retention-window-02",
            "source_checkpoint_id": checkpoint["checkpoint_id"],
        }
        if probe_id is None:
            return service.schedule_retention_probe(**request)
        with patch("study_os.services.runtime_base.new_id", return_value=probe_id):
            return service.schedule_retention_probe(**request)

    def test_unlinked_direct_application_and_mcp_are_differentially_equivalent(self) -> None:
        roots = [tempfile.TemporaryDirectory() for _ in range(3)]
        services = [StudyOSService(RuntimeConfig.from_env(root.name)) for root in roots]
        seeded = [
            self.seed_session(
                service,
                subject_id="subject-assessment-differential",
                suffix=f"assessment-differential-{index}",
            )
            for index, service in enumerate(services)
        ]
        common = {
            "idempotency_key": "assessment-differential",
            "subject_id": "subject-assessment-differential",
            "capability": "state-prediction",
            "result": "pass_unaided",
            "assistance_level": "none",
        }
        try:
            with patch("study_os.services.runtime.new_id", return_value="assessment-fixed"):
                direct = services[0].record_assessment(
                    **common,
                    session_id=seeded[0][0],
                    evidence_ids=[seeded[0][1]],
                )
                application = project_record_assessment_to_mcp(
                    ApplicationService(services[1]).record_assessment(
                        RecordAssessmentRequest(
                            **common,
                            session_id=seeded[1][0],
                            evidence_ids=[seeded[1][1]],
                        )
                    )
                )
                mcp = MCPServer(services[2]).call_tool(
                    "record_assessment",
                    {
                        **common,
                        "session_id": seeded[2][0],
                        "evidence_ids": [seeded[2][1]],
                    },
                )

            self.assertEqual(application, direct)
            self.assertEqual(mcp, direct)
            self.assertNotIn("retention_probe_id", direct)
            self.assertNotIn("retention_probe_status", direct)
            for service in services:
                row = service.db.connection.execute(
                    "SELECT assessment_id, subject_id, capability, result, assistance_level "
                    "FROM assessments WHERE assessment_id = ?",
                    ("assessment-fixed",),
                ).fetchone()
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["subject_id"], "subject-assessment-differential")
                self.assertEqual(row["capability"], "state-prediction")
                self.assertEqual(row["result"], "pass_unaided")
                self.assertEqual(row["assistance_level"], "none")
        finally:
            for service in services:
                service.close()
            for root in roots:
                root.cleanup()

    def test_linked_probe_completion_is_differential_and_atomic(self) -> None:
        roots = [tempfile.TemporaryDirectory() for _ in range(3)]
        services = [StudyOSService(RuntimeConfig.from_env(root.name)) for root in roots]
        seeded = [
            self.seed_session(
                service,
                subject_id="subject-assessment-retention",
                suffix=f"assessment-retention-{index}",
            )
            for index, service in enumerate(services)
        ]
        probes = [
            self.seed_probe(
                service,
                subject_id="subject-assessment-retention",
                session_id=seeded[index][0],
                evidence_id=seeded[index][1],
                capability="cap-1",
                suffix=f"assessment-retention-{index}",
                probe_id="probe-fixed",
            )
            for index, service in enumerate(services)
        ]
        common = {
            "idempotency_key": "assessment-retention-linked",
            "subject_id": "subject-assessment-retention",
            "capability": "cap-1",
            "result": "pass_delayed",
            "assistance_level": "none",
            "retention_probe_id": "probe-fixed",
        }
        try:
            self.assertTrue(all(probe["retention_probe_id"] == "probe-fixed" for probe in probes))
            with patch("study_os.services.runtime.new_id", return_value="assessment-fixed"):
                direct = services[0].record_assessment(
                    **common,
                    session_id=seeded[0][0],
                    evidence_ids=[seeded[0][1]],
                )
                application = project_record_assessment_to_mcp(
                    ApplicationService(services[1]).record_assessment(
                        RecordAssessmentRequest(
                            **common,
                            session_id=seeded[1][0],
                            evidence_ids=[seeded[1][1]],
                        )
                    )
                )
                mcp = MCPServer(services[2]).call_tool(
                    "record_assessment",
                    {
                        **common,
                        "session_id": seeded[2][0],
                        "evidence_ids": [seeded[2][1]],
                    },
                )

            self.assertEqual(application, direct)
            self.assertEqual(mcp, direct)
            self.assertEqual(direct["retention_probe_id"], "probe-fixed")
            self.assertEqual(direct["retention_probe_status"], "completed")
            for service in services:
                row = service.db.connection.execute(
                    "SELECT status, result_json FROM retention_probes WHERE retention_probe_id = ?",
                    ("probe-fixed",),
                ).fetchone()
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["status"], "completed")
                self.assertIn("assessment-fixed", row["result_json"])
                self.assertIsNone(
                    service.get_next_probe(subject_id="subject-assessment-retention")["probe"]
                )
        finally:
            for service in services:
                service.close()
            for root in roots:
                root.cleanup()

    def test_linked_retry_reuses_result_and_changed_request_conflicts(self) -> None:
        probe = self.seed_probe(
            self.service,
            subject_id="subject-assessment",
            session_id=self.session_id,
            evidence_id=self.attempt_id,
            capability="cap-1",
            suffix="assessment-retry",
        )
        server = MCPServer(self.service)
        base = {
            "idempotency_key": "assessment-retry-key",
            "session_id": self.session_id,
            "subject_id": "subject-assessment",
            "capability": "cap-1",
            "result": "pass_delayed",
            "assistance_level": "none",
            "evidence_ids": [self.attempt_id],
            "retention_probe_id": probe["retention_probe_id"],
        }
        first = server.call_tool("record_assessment", base)
        retry = server.call_tool("record_assessment", base)
        conflict = server.call_tool(
            "record_assessment",
            {**base, "result": "fail_delayed"},
        )

        self.assertTrue(first["created"])
        self.assertFalse(retry["created"])
        self.assertEqual(first["assessment_id"], retry["assessment_id"])
        self.assertEqual(retry["retention_probe_status"], "completed")
        self.assertEqual(conflict["error"]["category"], "conflict")
        self.assertEqual(
            self.service.db.connection.execute(
                "SELECT COUNT(*) FROM assessments WHERE idempotency_key = ?",
                ("assessment-retry-key",),
            ).fetchone()[0],
            1,
        )

    def test_probe_failures_roll_back_assessment_and_preserve_probe_state(self) -> None:
        probe = self.seed_probe(
            self.service,
            subject_id="subject-assessment",
            session_id=self.session_id,
            evidence_id=self.attempt_id,
            capability="cap-1",
            suffix="assessment-probe-failures",
        )
        server = MCPServer(self.service)
        base = {
            "session_id": self.session_id,
            "subject_id": "subject-assessment",
            "result": "pass_delayed",
            "assistance_level": "none",
            "evidence_ids": [self.attempt_id],
        }

        missing = server.call_tool(
            "record_assessment",
            {
                **base,
                "idempotency_key": "assessment-missing-probe",
                "capability": "cap-1",
                "retention_probe_id": "missing-probe",
            },
        )
        self.assertEqual(missing["error"]["category"], "not_found")

        mismatch = server.call_tool(
            "record_assessment",
            {
                **base,
                "idempotency_key": "assessment-probe-mismatch",
                "capability": "cap-other",
                "retention_probe_id": probe["retention_probe_id"],
            },
        )
        self.assertEqual(mismatch["error"]["category"], "integrity_error")
        self.assertEqual(
            self.service.db.connection.execute(
                "SELECT COUNT(*) FROM assessments WHERE idempotency_key IN (?, ?)",
                ("assessment-missing-probe", "assessment-probe-mismatch"),
            ).fetchone()[0],
            0,
        )
        status = self.service.db.connection.execute(
            "SELECT status FROM retention_probes WHERE retention_probe_id = ?",
            (probe["retention_probe_id"],),
        ).fetchone()["status"]
        self.assertEqual(status, "scheduled")

        other_session, other_attempt = self.seed_session(
            self.service,
            subject_id="subject-assessment-other",
            suffix="assessment-other",
        )
        other_probe = self.seed_probe(
            self.service,
            subject_id="subject-assessment-other",
            session_id=other_session,
            evidence_id=other_attempt,
            capability="cap-1",
            suffix="assessment-other",
        )
        wrong_subject = server.call_tool(
            "record_assessment",
            {
                **base,
                "idempotency_key": "assessment-wrong-subject-probe",
                "capability": "cap-1",
                "retention_probe_id": other_probe["retention_probe_id"],
            },
        )
        self.assertEqual(wrong_subject["error"]["category"], "integrity_error")

    def test_completed_probe_cannot_be_closed_by_a_second_assessment(self) -> None:
        probe = self.seed_probe(
            self.service,
            subject_id="subject-assessment",
            session_id=self.session_id,
            evidence_id=self.attempt_id,
            capability="cap-1",
            suffix="assessment-completed-probe",
        )
        server = MCPServer(self.service)
        base = {
            "session_id": self.session_id,
            "subject_id": "subject-assessment",
            "capability": "cap-1",
            "result": "pass_delayed",
            "assistance_level": "none",
            "evidence_ids": [self.attempt_id],
            "retention_probe_id": probe["retention_probe_id"],
        }
        first = server.call_tool(
            "record_assessment",
            {**base, "idempotency_key": "assessment-close-first"},
        )
        second = server.call_tool(
            "record_assessment",
            {**base, "idempotency_key": "assessment-close-second"},
        )
        self.assertEqual(first["retention_probe_status"], "completed")
        self.assertEqual(second["error"]["category"], "conflict")
        self.assertEqual(
            self.service.db.connection.execute(
                "SELECT COUNT(*) FROM assessments WHERE idempotency_key IN (?, ?)",
                ("assessment-close-first", "assessment-close-second"),
            ).fetchone()[0],
            1,
        )

    def test_malformed_runtime_result_and_extra_mcp_fields_fail_closed(self) -> None:
        malformed = MCPServer(MalformedAssessmentService()).call_tool(  # type: ignore[arg-type]
            "record_assessment",
            {
                "idempotency_key": "assessment-malformed",
                "session_id": "session-broken",
                "subject_id": "subject-broken",
                "capability": "cap-1",
                "result": "pass_delayed",
                "assistance_level": "none",
                "evidence_ids": ["attempt-broken"],
            },
        )
        self.assertEqual(malformed["error"]["category"], "internal_error")
        self.assertEqual(
            malformed["error"]["details"]["exception"],
            "ApplicationBoundaryError",
        )

        base = {
            "idempotency_key": "assessment-unexpected",
            "session_id": self.session_id,
            "subject_id": "subject-assessment",
            "capability": "cap-1",
            "result": "pass_unaided",
            "assistance_level": "none",
            "evidence_ids": [self.attempt_id],
        }
        for extra in (
            {"application_contract_version": "0.1.0"},
            {"invented": True},
        ):
            with self.subTest(extra=extra):
                result = MCPServer(self.service).call_tool(
                    "record_assessment",
                    {**base, **extra},
                )
                self.assertEqual(result["error"]["category"], "validation_error")


if __name__ == "__main__":
    unittest.main()
