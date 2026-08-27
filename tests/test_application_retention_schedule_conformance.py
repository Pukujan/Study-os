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
from study_os.application.contracts import ScheduleRetentionProbeRequest  # noqa: E402
from study_os.application.service import (  # noqa: E402
    ApplicationService,
    project_schedule_retention_probe_to_mcp,
)
from study_os.mcp.server import MCPServer  # noqa: E402


class MalformedRetentionScheduleService:
    def schedule_retention_probe(self, **_: Any) -> dict[str, Any]:
        return {
            "retention_probe_id": 123,
            "created": True,
            "due_at": "retention-window-broken",
        }


class RetentionScheduleApplicationConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)
        self.checkpoint = self.seed_checkpoint(
            self.service,
            subject_id="subject-retention",
            suffix="retention-local",
        )

    def tearDown(self) -> None:
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    @staticmethod
    def seed_checkpoint(
        service: StudyOSService,
        *,
        subject_id: str,
        suffix: str,
    ) -> dict[str, Any]:
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
            task_id="retention-source-task",
            response={"prediction": "right"},
            assistance_level="none",
        )
        return service.checkpoint(
            idempotency_key=f"{suffix}-checkpoint",
            subject_id=subject_id,
            source_session_ids=[session["session_id"]],
            evidence_ids=[attempt["attempt_id"]],
            capability_state={"state_prediction": "supported"},
            assistance_state={"current": "none"},
            resume={
                "current_focus": "retention scheduling",
                "do_not_reteach": [],
                "next_action": "run retention probe",
            },
        )

    def test_direct_application_and_mcp_are_differentially_equivalent(self) -> None:
        roots = [tempfile.TemporaryDirectory() for _ in range(3)]
        services = [StudyOSService(RuntimeConfig.from_env(root.name)) for root in roots]
        checkpoints = [
            self.seed_checkpoint(
                service,
                subject_id="subject-retention-differential",
                suffix=f"retention-differential-{index}",
            )
            for index, service in enumerate(services)
        ]
        common = {
            "idempotency_key": "retention-differential",
            "subject_id": "subject-retention-differential",
            "concept_id": "sliding-window",
            "due_at": "retention-window-02",
        }
        try:
            with patch(
                "study_os.services.runtime_base.new_id",
                return_value="retention-probe-fixed",
            ):
                direct = services[0].schedule_retention_probe(
                    **common,
                    source_checkpoint_id=checkpoints[0]["checkpoint_id"],
                )
                application = project_schedule_retention_probe_to_mcp(
                    ApplicationService(services[1]).schedule_retention_probe(
                        ScheduleRetentionProbeRequest(
                            **common,
                            source_checkpoint_id=checkpoints[1]["checkpoint_id"],
                        )
                    )
                )
                mcp = MCPServer(services[2]).call_tool(
                    "schedule_retention_probe",
                    {
                        **common,
                        "source_checkpoint_id": checkpoints[2]["checkpoint_id"],
                    },
                )

            self.assertEqual(application, direct)
            self.assertEqual(mcp, direct)
            for index, service in enumerate(services):
                row = service.db.connection.execute(
                    "SELECT retention_probe_id, subject_id, concept_id, due_at, "
                    "source_checkpoint_id, status FROM retention_probes WHERE subject_id = ?",
                    ("subject-retention-differential",),
                ).fetchone()
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["retention_probe_id"], "retention-probe-fixed")
                self.assertEqual(row["subject_id"], "subject-retention-differential")
                self.assertEqual(row["concept_id"], "sliding-window")
                self.assertEqual(row["due_at"], "retention-window-02")
                self.assertEqual(
                    row["source_checkpoint_id"],
                    checkpoints[index]["checkpoint_id"],
                )
                self.assertEqual(row["status"], "scheduled")
                concept = service.db.connection.execute(
                    "SELECT concept_id FROM concepts WHERE concept_id = ?",
                    ("sliding-window",),
                ).fetchone()
                self.assertIsNotNone(concept)
        finally:
            for service in services:
                service.close()
            for root in roots:
                root.cleanup()

    def test_retry_conflict_and_get_next_probe_projection_remain_unchanged(self) -> None:
        server = MCPServer(self.service)
        base = {
            "idempotency_key": "retention-retry",
            "subject_id": "subject-retention",
            "concept_id": "sliding-window",
            "due_at": "retention-window-02",
            "source_checkpoint_id": self.checkpoint["checkpoint_id"],
        }
        first = server.call_tool("schedule_retention_probe", base)
        retry = server.call_tool("schedule_retention_probe", base)
        conflict = server.call_tool(
            "schedule_retention_probe",
            {**base, "due_at": "retention-window-03"},
        )

        self.assertTrue(first["created"])
        self.assertFalse(retry["created"])
        self.assertEqual(first["retention_probe_id"], retry["retention_probe_id"])
        self.assertEqual(conflict["error"]["category"], "conflict")
        self.assertEqual(
            self.service.db.connection.execute(
                "SELECT COUNT(*) FROM retention_probes WHERE subject_id = ?",
                ("subject-retention",),
            ).fetchone()[0],
            1,
        )

        direct_next = self.service.get_next_probe(subject_id="subject-retention")
        mcp_next = server.call_tool("get_next_probe", {"subject_id": "subject-retention"})
        self.assertEqual(mcp_next, direct_next)
        self.assertEqual(mcp_next["probe"]["due_at"], "retention-window-02")
        self.assertEqual(
            mcp_next["source_checkpoint_id"],
            self.checkpoint["checkpoint_id"],
        )

    def test_missing_and_wrong_subject_source_checkpoints_fail_closed(self) -> None:
        server = MCPServer(self.service)
        missing = server.call_tool(
            "schedule_retention_probe",
            {
                "idempotency_key": "retention-missing-checkpoint",
                "subject_id": "subject-retention",
                "concept_id": "sliding-window",
                "due_at": "retention-window-02",
                "source_checkpoint_id": "missing-checkpoint",
            },
        )
        self.assertEqual(missing["error"]["category"], "not_found")

        other_checkpoint = self.seed_checkpoint(
            self.service,
            subject_id="subject-retention-other",
            suffix="retention-other",
        )
        mismatch = server.call_tool(
            "schedule_retention_probe",
            {
                "idempotency_key": "retention-wrong-subject-checkpoint",
                "subject_id": "subject-retention",
                "concept_id": "sliding-window",
                "due_at": "retention-window-02",
                "source_checkpoint_id": other_checkpoint["checkpoint_id"],
            },
        )
        self.assertEqual(mismatch["error"]["category"], "integrity_error")
        self.assertEqual(
            self.service.db.connection.execute(
                "SELECT COUNT(*) FROM retention_probes WHERE subject_id = ?",
                ("subject-retention",),
            ).fetchone()[0],
            0,
        )

    def test_malformed_runtime_result_and_extra_mcp_fields_fail_closed(self) -> None:
        malformed = MCPServer(MalformedRetentionScheduleService()).call_tool(  # type: ignore[arg-type]
            "schedule_retention_probe",
            {
                "idempotency_key": "retention-malformed",
                "subject_id": "subject-retention",
                "concept_id": "sliding-window",
                "due_at": "retention-window-02",
                "source_checkpoint_id": "checkpoint-broken",
            },
        )
        self.assertEqual(malformed["error"]["category"], "internal_error")
        self.assertEqual(
            malformed["error"]["details"]["exception"],
            "ApplicationBoundaryError",
        )

        base = {
            "idempotency_key": "retention-unexpected",
            "subject_id": "subject-retention",
            "concept_id": "sliding-window",
            "due_at": "retention-window-02",
            "source_checkpoint_id": self.checkpoint["checkpoint_id"],
        }
        for extra in (
            {"application_contract_version": "0.1.0"},
            {"invented": True},
        ):
            with self.subTest(extra=extra):
                result = MCPServer(self.service).call_tool(
                    "schedule_retention_probe",
                    {**base, **extra},
                )
                self.assertEqual(result["error"]["category"], "validation_error")


if __name__ == "__main__":
    unittest.main()
