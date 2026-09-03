from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import study_os.application as application  # noqa: E402


class ApplicationPublicSurfaceTests(unittest.TestCase):
    def test_public_contract_exports_match_current_canonical_models(self) -> None:
        expected = {
            "APPLICATION_CONTRACT_VERSION",
            "AppendConversationTurnRequest",
            "AppendConversationTurnResult",
            "ApplicationError",
            "ApplicationErrorCategory",
            "ApplicationErrorEnvelope",
            "NextRetentionProbeRequest",
            "NextRetentionProbeResult",
            "RecentRepresentationSummary",
            "RecordAssessmentRequest",
            "RecordAssessmentResult",
            "RecordAttemptRequest",
            "RecordAttemptResult",
            "RecordLearningEventRequest",
            "RecordLearningEventResult",
            "RecordRepresentationInterventionRequest",
            "RecordRepresentationInterventionResult",
            "RecordRepresentationOutcomeRequest",
            "RecordRepresentationOutcomeResult",
            "ResumeRetentionProbeSummary",
            "ResumeSubjectRequest",
            "ResumeSubjectResult",
            "RetentionProbeSummary",
            "RuntimeHealthCheck",
            "RuntimeHealthRequest",
            "RuntimeHealthResult",
            "ScheduleRetentionProbeRequest",
            "ScheduleRetentionProbeResult",
            "StartStudySessionRequest",
            "StartStudySessionResult",
            "SubjectStatusRequest",
            "SubjectStatusResult",
            "application_contract_core_schema_bundle",
            "canonical_model_json",
            "render_application_contract_core_schema",
        }
        self.assertEqual(set(application.__all__), expected)
        for name in expected:
            self.assertTrue(hasattr(application, name), name)


if __name__ == "__main__":
    unittest.main()
