import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.adaptive.contracts import LearnerSnapshot  # noqa: E402
from study_os.adaptive.fsrs_adapter import (  # noqa: E402
    FSRS_PACKAGE_VERSION,
    FsrsMaintenanceCandidate,
    propose_fsrs_maintenance,
    propose_fsrs_review_update,
)


class FsrsAdapterTests(unittest.TestCase):
    def snapshot(self, evidence_id="assessment-retention-1"):
        return LearnerSnapshot.from_mapping(
            {
                "subject_id": "subject-fsrs",
                "checkpoint_id": "checkpoint-fsrs",
                "phase": "maintenance",
                "current_focus": "delayed retention",
                "capabilities": {
                    "algo.two_candidate_update_order": {
                        "status": "pass_unaided",
                        "assistance_level": "A0",
                        "evidence_ids": [evidence_id],
                    }
                },
            }
        )

    @staticmethod
    def parse_utc(value):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def test_adapter_reproduces_upstream_no_fuzz_good_interval_sequence(self):
        # Upstream py-fsrs test_basic.py documents this prefix for repeated
        # Rating.Good reviews with enable_fuzzing=False.
        expected_day_intervals = [0, 2, 11, 46, 163]
        snapshot = self.snapshot()
        review_datetime = datetime(2022, 11, 29, 12, 30, tzinfo=timezone.utc)
        card_state = None
        actual = []

        for index in range(len(expected_day_intervals)):
            proposal = propose_fsrs_review_update(
                snapshot,
                concept_id="algo.two_candidate_update_order",
                source_assessment_id="assessment-retention-1",
                rating="good",
                review_datetime=review_datetime,
                card_state=card_state,
            )
            fsrs_state = proposal.expected_evidence["fsrs"]
            due = self.parse_utc(fsrs_state["due_at"])
            actual.append((due - review_datetime).days)
            card_state = fsrs_state["card"]
            review_datetime = due

        self.assertEqual(actual, expected_day_intervals)

    def test_review_update_requires_canonical_assessment_evidence(self):
        with self.assertRaisesRegex(ValueError, "canonical evidence"):
            propose_fsrs_review_update(
                self.snapshot(),
                concept_id="algo.two_candidate_update_order",
                source_assessment_id="assessment-not-in-snapshot",
                rating="good",
                review_datetime=datetime(2026, 8, 24, 20, 0, tzinfo=timezone.utc),
            )

    def test_review_update_does_not_guess_rating_from_generic_pass(self):
        with self.assertRaisesRegex(ValueError, "again, hard, good, easy"):
            propose_fsrs_review_update(
                self.snapshot(),
                concept_id="algo.two_candidate_update_order",
                source_assessment_id="assessment-retention-1",
                rating="pass",
                review_datetime=datetime(2026, 8, 24, 20, 0, tzinfo=timezone.utc),
            )

    def test_review_update_is_shadow_and_serializes_donor_state(self):
        proposal = propose_fsrs_review_update(
            self.snapshot(),
            concept_id="algo.two_candidate_update_order",
            source_assessment_id="assessment-retention-1",
            rating="easy",
            review_datetime=datetime(2026, 8, 24, 20, 0, tzinfo=timezone.utc),
            review_duration_ms=3200,
        )
        fsrs_state = proposal.expected_evidence["fsrs"]
        self.assertEqual(proposal.mode, "shadow")
        self.assertEqual(proposal.selected.action_type, "schedule_retention_probe")
        self.assertEqual(fsrs_state["package_version"], FSRS_PACKAGE_VERSION)
        self.assertFalse(fsrs_state["enable_fuzzing"])
        self.assertEqual(fsrs_state["rating"], "easy")
        self.assertEqual(fsrs_state["review_duration_ms"], 3200)
        self.assertIn("stability", fsrs_state["card"])
        self.assertIn("review_datetime", fsrs_state["review_log"])

    def test_maintenance_selector_only_ranks_due_reviewed_cards(self):
        snapshot = self.snapshot()
        initial_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        reviewed = propose_fsrs_review_update(
            snapshot,
            concept_id="algo.two_candidate_update_order",
            source_assessment_id="assessment-retention-1",
            rating="easy",
            review_datetime=initial_time,
        ).expected_evidence["fsrs"]["card"]

        due_time = self.parse_utc(reviewed["due"])
        overdue_state = dict(reviewed)
        overdue_state["due"] = (initial_time - timedelta(minutes=1)).isoformat()
        future_state = dict(reviewed)
        future_state["due"] = (due_time + timedelta(days=30)).isoformat()

        proposal = propose_fsrs_maintenance(
            snapshot,
            (
                FsrsMaintenanceCandidate(
                    "algo.two_candidate_update_order",
                    overdue_state,
                    goal_relevance=1.0,
                ),
                FsrsMaintenanceCandidate(
                    "algo.running_max",
                    future_state,
                    goal_relevance=1.0,
                ),
            ),
            current_datetime=initial_time,
        )
        self.assertEqual(proposal.selected.candidate_id, "algo.two_candidate_update_order")
        reasons = {item.candidate_id: item.reason_code for item in proposal.exclusions}
        self.assertEqual(reasons["algo.running_max"], "retention_not_due")

    def test_non_utc_review_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "UTC"):
            propose_fsrs_review_update(
                self.snapshot(),
                concept_id="algo.two_candidate_update_order",
                source_assessment_id="assessment-retention-1",
                rating="good",
                review_datetime=datetime(2026, 8, 24, 20, 0),
            )


if __name__ == "__main__":
    unittest.main()
