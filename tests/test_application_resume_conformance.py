from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT / "src"))

from study_os import RuntimeConfig, StudyOSService  # noqa: E402
from study_os.application.contracts import ResumeSubjectRequest  # noqa: E402
from study_os.application.service import (  # noqa: E402
    ApplicationService,
    project_resume_subject_to_mcp,
)
from study_os.mcp.server import MCPServer  # noqa: E402


class MalformedResumeService:
    def resume(self, *, subject_id: str) -> dict[str, Any]:
        return {
            "subject_id": subject_id,
            "checkpoint_id": "checkpoint-broken",
            "capability_state": {"skill": "pass"},
            "assistance_state": {},
            "current_focus": "focus",
            "do_not_reteach": [],
            "next_action": "next",
            "retention_due_at": None,
            "next_retention_probe": None,
            "recent_representation_history": "not-an-array",
        }


class ResumeApplicationConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)

    def tearDown(self) -> None:
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def seed_resume_state(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        session = self.service.start_session(
            idempotency_key="resume-session-1",
            subject_id="subject-resume",
            project_id="project-resume",
            domain_id="dsa",
        )
        artifact = self.service.capture_evidence(
            session_id=session["session_id"],
            subject_id="subject-resume",
            content=b"resume evidence",
            media_type="text/plain",
        )
        event = self.service.record_learning_event(
            idempotency_key="resume-event-1",
            session_id=session["session_id"],
            subject_id="subject-resume",
            evidence_class="observed",
            event_type="attempt_observed",
            payload={"summary": "resume continuity evidence"},
        )
        intervention = self.service.record_representation_intervention(
            idempotency_key="resume-intervention-1",
            session_id=session["session_id"],
            subject_id="subject-resume",
            representation_family="deterministic_state_trace",
            operation="predict",
            representation_version="0.1.0",
            target_bottleneck="state_transition",
        )
        checkpoint = self.service.checkpoint(
            idempotency_key="resume-checkpoint-1",
            subject_id="subject-resume",
            source_session_ids=[session["session_id"]],
            evidence_ids=[artifact["artifact_id"], event["event_id"]],
            capability_state={"state_prediction": "pass_unaided"},
            assistance_state={"level": "none"},
            resume={
                "current_focus": "state transition",
                "do_not_reteach": ["basic indexing"],
                "next_action": "solve transfer trace",
            },
            retention_due_at="2026-09-01T00:00:00Z",
        )
        probe = self.service.schedule_retention_probe(
            idempotency_key="resume-probe-1",
            subject_id="subject-resume",
            concept_id="state-transition",
            due_at="2026-09-01T00:00:00Z",
            source_checkpoint_id=checkpoint["checkpoint_id"],
        )
        return checkpoint, probe, intervention

    def test_resume_direct_application_and_mcp_preserve_full_continuity(self) -> None:
        checkpoint, probe, intervention = self.seed_resume_state()

        direct = self.service.resume(subject_id="subject-resume")
        application = project_resume_subject_to_mcp(
            ApplicationService(self.service).resume_subject(
                ResumeSubjectRequest(subject_id="subject-resume")
            )
        )
        mcp = MCPServer(self.service).call_tool("resume", {"subject_id": "subject-resume"})

        self.assertEqual(application, direct)
        self.assertEqual(mcp, direct)
        self.assertEqual(direct["checkpoint_id"], checkpoint["checkpoint_id"])
        self.assertEqual(direct["do_not_reteach"], ["basic indexing"])
        self.assertEqual(direct["retention_due_at"], "2026-09-01T00:00:00Z")
        self.assertEqual(
            direct["next_retention_probe"]["retention_probe_id"],
            probe["retention_probe_id"],
        )
        self.assertEqual(
            direct["recent_representation_history"][0]["representation_family"],
            "deterministic_state_trace",
        )
        self.assertEqual(
            direct["recent_representation_history"][0]["operation"],
            "predict",
        )
        self.assertEqual(intervention["intervention_id"], intervention["intervention_id"])

    def test_resume_preserves_no_checkpoint_not_found_semantics(self) -> None:
        self.service.start_session(
            idempotency_key="resume-no-checkpoint-session",
            subject_id="subject-no-checkpoint",
            project_id="project-resume",
            domain_id="dsa",
        )
        result = MCPServer(self.service).call_tool(
            "resume",
            {"subject_id": "subject-no-checkpoint"},
        )
        self.assertEqual(result["error"]["category"], "not_found")
        self.assertFalse(result["error"]["retryable"])

    def test_resume_malformed_runtime_result_fails_closed(self) -> None:
        result = MCPServer(MalformedResumeService()).call_tool(  # type: ignore[arg-type]
            "resume",
            {"subject_id": "subject-broken"},
        )
        self.assertEqual(result["error"]["category"], "internal_error")
        self.assertEqual(result["error"]["details"]["exception"], "ApplicationBoundaryError")

    def test_resume_rejects_application_only_transport_fields(self) -> None:
        result = MCPServer(self.service).call_tool(
            "resume",
            {
                "subject_id": "subject-resume",
                "application_contract_version": "0.1.0",
            },
        )
        self.assertEqual(result["error"]["category"], "validation_error")


if __name__ == "__main__":
    unittest.main()
