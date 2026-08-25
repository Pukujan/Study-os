import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.errors import StudyOSError  # noqa: E402
from study_os.services.retention import (  # noqa: E402
    retention_result_payload,
    validate_retention_probe_id,
    validate_scheduled_probe,
)


class RetentionClosureHelperTests(unittest.TestCase):
    def test_optional_probe_id_validation(self):
        self.assertIsNone(validate_retention_probe_id(None))
        self.assertEqual(validate_retention_probe_id("probe-1"), "probe-1")
        with self.assertRaises(StudyOSError) as raised:
            validate_retention_probe_id("  ")
        self.assertEqual(raised.exception.category, "validation_error")

    def test_probe_must_exist_belong_to_subject_and_be_scheduled(self):
        with self.assertRaises(StudyOSError) as missing:
            validate_scheduled_probe(None, retention_probe_id="p1", subject_id="s1")
        self.assertEqual(missing.exception.category, "not_found")

        with self.assertRaises(StudyOSError) as mismatched:
            validate_scheduled_probe(
                {"subject_id": "s2", "status": "scheduled"},
                retention_probe_id="p1",
                subject_id="s1",
            )
        self.assertEqual(mismatched.exception.category, "integrity_error")

        with self.assertRaises(StudyOSError) as completed:
            validate_scheduled_probe(
                {"subject_id": "s1", "status": "completed"},
                retention_probe_id="p1",
                subject_id="s1",
            )
        self.assertEqual(completed.exception.category, "conflict")

    def test_result_payload_links_behavioral_assessment(self):
        payload = retention_result_payload(
            assessment_id="assessment-1",
            capability="retention",
            result="pass_unaided",
            assistance_level="A0",
            evidence_ids=["attempt-1"],
            completed_at="2026-08-25T06:00:00Z",
        )
        self.assertEqual(payload["assessment_id"], "assessment-1")
        self.assertEqual(payload["evidence_ids"], ["attempt-1"])
        self.assertEqual(payload["completed_at"], "2026-08-25T06:00:00Z")


if __name__ == "__main__":
    unittest.main()
