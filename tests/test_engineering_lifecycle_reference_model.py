import sys
import tempfile
import unittest
from pathlib import Path

from hypothesis import settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.config import RuntimeConfig  # noqa: E402
from study_os.errors import StudyOSError  # noqa: E402
from study_os.services.runtime import StudyOSService  # noqa: E402


class LifecycleReferenceModel:
    """Independent in-memory oracle for a narrow semantic lifecycle.

    The model intentionally knows nothing about SQLite, files, MCP, runtime helpers,
    UUID generation, or production implementation details. It tracks only the
    externally meaningful state transitions this differential slice is meant to
    protect before application-boundary extraction begins.
    """

    def __init__(self) -> None:
        self.attempt_count = 0
        self.assessment_count = 0
        self.checkpoint_count = 0
        self.probe_status: str | None = None

    def record_attempt(self) -> None:
        self.attempt_count += 1

    def record_assessment(self) -> None:
        if self.attempt_count == 0:
            raise AssertionError("reference assessment requires an attempt")
        self.assessment_count += 1

    def accept_checkpoint(self) -> None:
        if self.assessment_count == 0:
            raise AssertionError("reference checkpoint requires an assessment")
        self.checkpoint_count += 1

    def stale_checkpoint_result(self) -> str:
        if self.checkpoint_count == 0:
            raise AssertionError("reference stale-pointer check requires a checkpoint")
        return "conflict"

    def schedule_probe(self) -> None:
        if self.checkpoint_count == 0 or self.probe_status is not None:
            raise AssertionError("reference probe scheduling preconditions were not met")
        self.probe_status = "scheduled"

    def mismatched_probe_result(self) -> str:
        if self.probe_status != "scheduled":
            raise AssertionError("reference mismatched completion requires a scheduled probe")
        return "integrity_error"

    def complete_probe(self) -> None:
        if self.probe_status != "scheduled" or self.attempt_count == 0:
            raise AssertionError("reference probe completion preconditions were not met")
        self.assessment_count += 1
        self.probe_status = "completed"

    def repeat_completed_probe_result(self) -> str:
        if self.probe_status != "completed":
            raise AssertionError("reference repeated completion requires a completed probe")
        return "conflict"


class LifecycleReferenceDifferentialStateMachine(RuleBasedStateMachine):
    SUBJECT = "subject-lifecycle-reference"
    CAPABILITY = "cap-lifecycle-reference"

    def __init__(self) -> None:
        super().__init__()
        self.tmp = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig(root=Path(self.tmp.name))
        self.service = StudyOSService(self.config)
        self.model = LifecycleReferenceModel()
        started = self.service.start_session(
            idempotency_key="lifecycle-reference-session",
            subject_id=self.SUBJECT,
            project_id="project-lifecycle-reference",
            domain_id="dsa",
        )
        self.session_id = str(started["session_id"])
        self.attempt_ids: list[str] = []
        self.assessment_ids: list[str] = []
        self.checkpoint_ids: list[str] = []
        self.probe_id: str | None = None
        self.next_attempt = 0
        self.next_assessment = 0
        self.next_checkpoint = 0
        self.next_negative = 0

    @rule(answer=st.integers(min_value=-100_000, max_value=100_000))
    def record_attempt(self, answer: int) -> None:
        key = f"lifecycle-reference-attempt-{self.next_attempt}"
        self.next_attempt += 1
        result = self.service.record_attempt(
            idempotency_key=key,
            session_id=self.session_id,
            subject_id=self.SUBJECT,
            task_id="task-lifecycle-reference",
            response={"answer": answer},
            assistance_level="none",
        )
        self.model.record_attempt()
        self.attempt_ids.append(str(result["attempt_id"]))
        assert result["created"] is True

    @precondition(lambda self: self.model.attempt_count > 0)
    @rule()
    def record_unaided_assessment(self) -> None:
        key = f"lifecycle-reference-assessment-{self.next_assessment}"
        self.next_assessment += 1
        result = self.service.record_assessment(
            idempotency_key=key,
            session_id=self.session_id,
            subject_id=self.SUBJECT,
            capability=self.CAPABILITY,
            result="pass_unaided",
            assistance_level="none",
            evidence_ids=[self.attempt_ids[-1]],
        )
        self.model.record_assessment()
        self.assessment_ids.append(str(result["assessment_id"]))
        assert result["created"] is True

    @precondition(lambda self: self.model.assessment_count > 0)
    @rule()
    def accept_checkpoint_with_current_pointer_expectation(self) -> None:
        key = f"lifecycle-reference-checkpoint-{self.next_checkpoint}"
        self.next_checkpoint += 1
        resume: dict[str, object] = {
            "current_focus": self.CAPABILITY,
            "next_action": "continue lifecycle reference",
            "do_not_reteach": [],
        }
        if self.checkpoint_ids:
            resume["expected_current_checkpoint_id"] = self.checkpoint_ids[-1]
        result = self.service.checkpoint(
            idempotency_key=key,
            subject_id=self.SUBJECT,
            source_session_ids=[self.session_id],
            evidence_ids=[self.assessment_ids[-1]],
            capability_state={self.CAPABILITY: "pass_unaided"},
            assistance_state={self.CAPABILITY: "A0"},
            resume=resume,
            retention_due_at="2026-08-26T06:00:00Z",
        )
        self.model.accept_checkpoint()
        self.checkpoint_ids.append(str(result["checkpoint_id"]))
        assert result["accepted"] is True

    @precondition(lambda self: self.model.checkpoint_count > 0 and self.model.assessment_count > 0)
    @rule()
    def stale_checkpoint_pointer_is_rejected_without_state_change(self) -> None:
        before_model_count = self.model.checkpoint_count
        expected = self.model.stale_checkpoint_result()
        key = f"lifecycle-reference-stale-checkpoint-{self.next_negative}"
        self.next_negative += 1
        try:
            self.service.checkpoint(
                idempotency_key=key,
                subject_id=self.SUBJECT,
                source_session_ids=[self.session_id],
                evidence_ids=[self.assessment_ids[-1]],
                capability_state={self.CAPABILITY: "pass_unaided"},
                assistance_state={self.CAPABILITY: "A0"},
                resume={
                    "current_focus": self.CAPABILITY,
                    "next_action": "must not replace current checkpoint",
                    "do_not_reteach": [],
                    "expected_current_checkpoint_id": "stale-reference-checkpoint",
                },
                retention_due_at="2026-08-26T06:00:00Z",
            )
        except StudyOSError as exc:
            assert exc.category == expected
        else:
            raise AssertionError("stale checkpoint pointer was accepted")
        assert self.model.checkpoint_count == before_model_count

    @precondition(lambda self: self.model.checkpoint_count > 0)
    @rule()
    def resume_matches_reference_current_state(self) -> None:
        resumed = self.service.resume(subject_id=self.SUBJECT)
        assert str(resumed["checkpoint_id"]) == self.checkpoint_ids[-1]
        assert resumed["current_focus"] == self.CAPABILITY
        if self.model.probe_status == "scheduled":
            assert self.probe_id is not None
            next_probe = resumed["next_retention_probe"]
            assert next_probe is not None
            assert str(next_probe["retention_probe_id"]) == self.probe_id
        else:
            assert resumed["next_retention_probe"] is None

    @precondition(
        lambda self: self.model.checkpoint_count > 0 and self.model.probe_status is None
    )
    @rule()
    def schedule_retention_probe(self) -> None:
        result = self.service.schedule_retention_probe(
            idempotency_key="lifecycle-reference-probe",
            subject_id=self.SUBJECT,
            concept_id=self.CAPABILITY,
            due_at="2026-08-26T06:00:00Z",
            source_checkpoint_id=self.checkpoint_ids[-1],
        )
        self.model.schedule_probe()
        self.probe_id = str(result["retention_probe_id"])
        assert result["created"] is True

    @precondition(
        lambda self: self.model.probe_status == "scheduled" and self.model.attempt_count > 0
    )
    @rule()
    def mismatched_probe_completion_rolls_back(self) -> None:
        assert self.probe_id is not None
        expected = self.model.mismatched_probe_result()
        key = f"lifecycle-reference-bad-probe-{self.next_negative}"
        self.next_negative += 1
        before_assessments = self.model.assessment_count
        try:
            self.service.record_assessment(
                idempotency_key=key,
                session_id=self.session_id,
                subject_id=self.SUBJECT,
                capability="wrong-capability",
                result="pass_delayed",
                assistance_level="none",
                evidence_ids=[self.attempt_ids[-1]],
                retention_probe_id=self.probe_id,
            )
        except StudyOSError as exc:
            assert exc.category == expected
        else:
            raise AssertionError("mismatched retention-probe completion was accepted")
        assert self.model.assessment_count == before_assessments
        assert self.model.probe_status == "scheduled"

    @precondition(
        lambda self: self.model.probe_status == "scheduled" and self.model.attempt_count > 0
    )
    @rule()
    def complete_matching_retention_probe(self) -> None:
        assert self.probe_id is not None
        key = f"lifecycle-reference-delayed-{self.next_assessment}"
        self.next_assessment += 1
        result = self.service.record_assessment(
            idempotency_key=key,
            session_id=self.session_id,
            subject_id=self.SUBJECT,
            capability=self.CAPABILITY,
            result="pass_delayed",
            assistance_level="none",
            evidence_ids=[self.attempt_ids[-1]],
            retention_probe_id=self.probe_id,
        )
        self.model.complete_probe()
        self.assessment_ids.append(str(result["assessment_id"]))
        assert result["retention_probe_status"] == "completed"

    @precondition(
        lambda self: self.model.probe_status == "completed" and self.model.attempt_count > 0
    )
    @rule()
    def completed_probe_cannot_be_completed_again(self) -> None:
        assert self.probe_id is not None
        expected = self.model.repeat_completed_probe_result()
        key = f"lifecycle-reference-repeat-probe-{self.next_negative}"
        self.next_negative += 1
        before_assessments = self.model.assessment_count
        try:
            self.service.record_assessment(
                idempotency_key=key,
                session_id=self.session_id,
                subject_id=self.SUBJECT,
                capability=self.CAPABILITY,
                result="pass_delayed",
                assistance_level="none",
                evidence_ids=[self.attempt_ids[-1]],
                retention_probe_id=self.probe_id,
            )
        except StudyOSError as exc:
            assert exc.category == expected
        else:
            raise AssertionError("completed retention probe was completed twice")
        assert self.model.assessment_count == before_assessments

    @rule()
    def restart_service(self) -> None:
        self.service.close()
        self.service = StudyOSService(self.config)

    @invariant()
    def durable_row_counts_match_reference_model(self) -> None:
        connection = self.service.db.connection
        attempt_count = connection.execute(
            "SELECT COUNT(*) FROM attempts WHERE subject_id = ?", (self.SUBJECT,)
        ).fetchone()[0]
        assessment_count = connection.execute(
            "SELECT COUNT(*) FROM assessments WHERE subject_id = ?", (self.SUBJECT,)
        ).fetchone()[0]
        checkpoint_count = connection.execute(
            "SELECT COUNT(*) FROM checkpoints WHERE subject_id = ?", (self.SUBJECT,)
        ).fetchone()[0]
        assert attempt_count == self.model.attempt_count
        assert assessment_count == self.model.assessment_count
        assert checkpoint_count == self.model.checkpoint_count

    @invariant()
    def checkpoint_pointer_matches_reference_model(self) -> None:
        row = self.service.db.connection.execute(
            "SELECT checkpoint_id FROM subject_current_checkpoint WHERE subject_id = ?",
            (self.SUBJECT,),
        ).fetchone()
        if self.model.checkpoint_count == 0:
            assert row is None
        else:
            assert row is not None
            assert str(row["checkpoint_id"]) == self.checkpoint_ids[-1]
            resumed = self.service.resume(subject_id=self.SUBJECT)
            assert str(resumed["checkpoint_id"]) == self.checkpoint_ids[-1]

    @invariant()
    def retention_state_matches_reference_model(self) -> None:
        next_probe = self.service.get_next_probe(subject_id=self.SUBJECT)["probe"]
        if self.model.probe_status is None:
            assert self.probe_id is None
            assert next_probe is None
            return

        assert self.probe_id is not None
        row = self.service.db.connection.execute(
            "SELECT status FROM retention_probes WHERE retention_probe_id = ?",
            (self.probe_id,),
        ).fetchone()
        assert row is not None
        assert row["status"] == self.model.probe_status
        if self.model.probe_status == "scheduled":
            assert next_probe is not None
            assert str(next_probe["retention_probe_id"]) == self.probe_id
        else:
            assert next_probe is None

    @invariant()
    def runtime_remains_healthy(self) -> None:
        assert self.service.doctor()["healthy"] is True

    def teardown(self) -> None:
        self.service.close()
        self.tmp.cleanup()


LifecycleReferenceDifferentialStateMachine.TestCase.settings = settings(
    max_examples=24,
    stateful_step_count=30,
    deadline=None,
)
TestLifecycleReferenceDifferentialStateMachine = LifecycleReferenceDifferentialStateMachine.TestCase


if __name__ == "__main__":
    unittest.main()
