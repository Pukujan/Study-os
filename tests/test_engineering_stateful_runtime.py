import sys
import tempfile
import unittest
from pathlib import Path

from hypothesis import HealthCheck, given, settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.config import RuntimeConfig  # noqa: E402
from study_os.errors import StudyOSError  # noqa: E402
from study_os.services.runtime import StudyOSService  # noqa: E402


_SAFE_TEXT = st.text(
    alphabet=st.characters(min_codepoint=48, max_codepoint=122, blacklist_categories=("Cs",)),
    min_size=1,
    max_size=24,
)


class RuntimePropertyTests(unittest.TestCase):
    @settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(key=_SAFE_TEXT, value=st.integers(min_value=-10_000, max_value=10_000))
    def test_exact_event_retry_is_idempotent_and_conflicting_reuse_is_rejected(self, key: str, value: int) -> None:
        with tempfile.TemporaryDirectory() as root:
            service = StudyOSService(RuntimeConfig(root=Path(root)))
            try:
                session = service.start_session(
                    idempotency_key=f"session-{key}",
                    subject_id="subject-property",
                    project_id="project-property",
                    domain_id="dsa",
                )
                request = {
                    "idempotency_key": f"event-{key}",
                    "session_id": session["session_id"],
                    "subject_id": "subject-property",
                    "evidence_class": "observed",
                    "event_type": "property_observation",
                    "payload": {"value": value},
                }
                first = service.record_learning_event(**request)
                second = service.record_learning_event(**request)
                self.assertTrue(first["created"])
                self.assertFalse(second["created"])
                self.assertEqual(first["event_id"], second["event_id"])

                conflicting = dict(request)
                conflicting["payload"] = {"value": value + 1}
                with self.assertRaises(StudyOSError) as raised:
                    service.record_learning_event(**conflicting)
                self.assertEqual(raised.exception.category, "conflict")

                count = service.db.connection.execute(
                    "SELECT COUNT(*) FROM learning_events WHERE subject_id = ?",
                    ("subject-property",),
                ).fetchone()[0]
                self.assertEqual(count, 1)
                self.assertTrue(service.doctor()["healthy"])
            finally:
                service.close()


class RuntimeDurabilityStateMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.tmp = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig(root=Path(self.tmp.name))
        self.service = StudyOSService(self.config)
        started = self.service.start_session(
            idempotency_key="stateful-session",
            subject_id="subject-stateful",
            project_id="project-stateful",
            domain_id="dsa",
        )
        self.session_id = started["session_id"]
        self.next_index = 0
        self.requests: dict[str, dict[str, object]] = {}
        self.event_ids: dict[str, str] = {}

    @rule(value=st.integers(min_value=-1_000_000, max_value=1_000_000))
    def record_new_event(self, value: int) -> None:
        key = f"stateful-event-{self.next_index}"
        self.next_index += 1
        request: dict[str, object] = {
            "idempotency_key": key,
            "session_id": self.session_id,
            "subject_id": "subject-stateful",
            "evidence_class": "observed",
            "event_type": "stateful_observation",
            "payload": {"value": value},
        }
        result = self.service.record_learning_event(**request)
        assert result["created"] is True
        self.requests[key] = request
        self.event_ids[key] = str(result["event_id"])

    @precondition(lambda self: bool(self.requests))
    @rule()
    def retry_existing_event(self) -> None:
        key = next(reversed(self.requests))
        result = self.service.record_learning_event(**self.requests[key])
        assert result["created"] is False
        assert str(result["event_id"]) == self.event_ids[key]

    @precondition(lambda self: bool(self.requests))
    @rule()
    def conflicting_reuse_is_rejected(self) -> None:
        key = next(reversed(self.requests))
        request = dict(self.requests[key])
        request["event_type"] = "stateful_conflict"
        try:
            self.service.record_learning_event(**request)
        except StudyOSError as exc:
            assert exc.category == "conflict"
        else:
            raise AssertionError("conflicting idempotency-key reuse was accepted")

    @rule()
    def restart_service(self) -> None:
        self.service.close()
        self.service = StudyOSService(self.config)
        resumed_session = self.service.db.connection.execute(
            "SELECT session_id FROM sessions WHERE session_id = ?",
            (self.session_id,),
        ).fetchone()
        assert resumed_session is not None

    @invariant()
    def durable_event_count_matches_successful_unique_writes(self) -> None:
        count = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM learning_events WHERE subject_id = ?",
            ("subject-stateful",),
        ).fetchone()[0]
        assert count == len(self.requests)

    @invariant()
    def runtime_remains_healthy(self) -> None:
        assert self.service.doctor()["healthy"] is True

    def teardown(self) -> None:
        self.service.close()
        self.tmp.cleanup()


RuntimeDurabilityStateMachine.TestCase.settings = settings(
    max_examples=30,
    stateful_step_count=25,
    deadline=None,
)
TestRuntimeDurabilityStateMachine = RuntimeDurabilityStateMachine.TestCase


class SemanticLifecycleStateMachine(RuleBasedStateMachine):
    """Generated lifecycle sequences across the semantic persistence boundary.

    This intentionally exercises the real SQLite-backed service rather than a mock.
    The independent in-memory reference model is the next verification layer.
    """

    SUBJECT = "subject-lifecycle"
    CAPABILITY = "cap-lifecycle"

    def __init__(self) -> None:
        super().__init__()
        self.tmp = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig(root=Path(self.tmp.name))
        self.service = StudyOSService(self.config)
        started = self.service.start_session(
            idempotency_key="lifecycle-session",
            subject_id=self.SUBJECT,
            project_id="project-lifecycle",
            domain_id="dsa",
        )
        self.session_id = str(started["session_id"])
        self.next_attempt = 0
        self.next_assessment = 0
        self.attempt_ids: list[str] = []
        self.assessment_ids: list[str] = []
        self.checkpoint_id: str | None = None
        self.probe_id: str | None = None
        self.probe_completed = False

    @rule(answer=st.integers(min_value=-100_000, max_value=100_000))
    def record_attempt(self, answer: int) -> None:
        key = f"lifecycle-attempt-{self.next_attempt}"
        self.next_attempt += 1
        result = self.service.record_attempt(
            idempotency_key=key,
            session_id=self.session_id,
            subject_id=self.SUBJECT,
            task_id="task-lifecycle",
            response={"answer": answer},
            assistance_level="none",
        )
        self.attempt_ids.append(str(result["attempt_id"]))

    @precondition(lambda self: bool(self.attempt_ids))
    @rule()
    def record_unaided_assessment(self) -> None:
        key = f"lifecycle-assessment-{self.next_assessment}"
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
        self.assessment_ids.append(str(result["assessment_id"]))

    @precondition(lambda self: bool(self.assessment_ids) and self.checkpoint_id is None)
    @rule()
    def create_checkpoint(self) -> None:
        result = self.service.checkpoint(
            idempotency_key="lifecycle-checkpoint",
            subject_id=self.SUBJECT,
            source_session_ids=[self.session_id],
            evidence_ids=[self.assessment_ids[-1]],
            capability_state={self.CAPABILITY: "pass_unaided"},
            assistance_state={self.CAPABILITY: "A0"},
            resume={
                "current_focus": self.CAPABILITY,
                "next_action": "schedule delayed probe",
                "do_not_reteach": [],
            },
            retention_due_at="2026-08-26T06:00:00Z",
        )
        self.checkpoint_id = str(result["checkpoint_id"])

    @precondition(lambda self: self.checkpoint_id is not None)
    @rule()
    def resume_checkpoint(self) -> None:
        resumed = self.service.resume(subject_id=self.SUBJECT)
        assert str(resumed["checkpoint_id"]) == self.checkpoint_id
        assert resumed["current_focus"] == self.CAPABILITY

    @precondition(lambda self: self.checkpoint_id is not None and self.probe_id is None)
    @rule()
    def schedule_probe(self) -> None:
        result = self.service.schedule_retention_probe(
            idempotency_key="lifecycle-probe",
            subject_id=self.SUBJECT,
            concept_id=self.CAPABILITY,
            due_at="2026-08-26T06:00:00Z",
            source_checkpoint_id=self.checkpoint_id,
        )
        self.probe_id = str(result["retention_probe_id"])
        next_probe = self.service.get_next_probe(subject_id=self.SUBJECT)["probe"]
        assert next_probe is not None
        assert str(next_probe["retention_probe_id"]) == self.probe_id

    @precondition(lambda self: self.probe_id is not None and not self.probe_completed and bool(self.attempt_ids))
    @rule()
    def mismatched_probe_completion_rolls_back(self) -> None:
        before = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM assessments WHERE subject_id = ?",
            (self.SUBJECT,),
        ).fetchone()[0]
        try:
            self.service.record_assessment(
                idempotency_key=f"lifecycle-bad-probe-{self.next_assessment}",
                session_id=self.session_id,
                subject_id=self.SUBJECT,
                capability="wrong-capability",
                result="pass_delayed",
                assistance_level="none",
                evidence_ids=[self.attempt_ids[-1]],
                retention_probe_id=self.probe_id,
            )
        except StudyOSError:
            pass
        else:
            raise AssertionError("mismatched retention-probe completion was accepted")

        after = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM assessments WHERE subject_id = ?",
            (self.SUBJECT,),
        ).fetchone()[0]
        row = self.service.db.connection.execute(
            "SELECT status FROM retention_probes WHERE retention_probe_id = ?",
            (self.probe_id,),
        ).fetchone()
        assert after == before
        assert row is not None
        assert row["status"] == "scheduled"

    @precondition(lambda self: self.probe_id is not None and not self.probe_completed and bool(self.attempt_ids))
    @rule()
    def complete_probe_with_matching_assessment(self) -> None:
        key = f"lifecycle-delayed-assessment-{self.next_assessment}"
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
        self.assessment_ids.append(str(result["assessment_id"]))
        assert result["retention_probe_status"] == "completed"
        self.probe_completed = True
        assert self.service.get_next_probe(subject_id=self.SUBJECT)["probe"] is None

    @rule()
    def restart_service(self) -> None:
        self.service.close()
        self.service = StudyOSService(self.config)
        row = self.service.db.connection.execute(
            "SELECT session_id FROM sessions WHERE session_id = ?",
            (self.session_id,),
        ).fetchone()
        assert row is not None
        if self.checkpoint_id is not None:
            resumed = self.service.resume(subject_id=self.SUBJECT)
            assert str(resumed["checkpoint_id"]) == self.checkpoint_id

    @invariant()
    def successful_semantic_rows_remain_durable(self) -> None:
        attempt_count = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM attempts WHERE subject_id = ?",
            (self.SUBJECT,),
        ).fetchone()[0]
        assessment_count = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM assessments WHERE subject_id = ?",
            (self.SUBJECT,),
        ).fetchone()[0]
        assert attempt_count == len(self.attempt_ids)
        assert assessment_count == len(self.assessment_ids)

    @invariant()
    def checkpoint_pointer_and_probe_status_match_model(self) -> None:
        if self.checkpoint_id is not None:
            resumed = self.service.resume(subject_id=self.SUBJECT)
            assert str(resumed["checkpoint_id"]) == self.checkpoint_id
        if self.probe_id is not None:
            row = self.service.db.connection.execute(
                "SELECT status FROM retention_probes WHERE retention_probe_id = ?",
                (self.probe_id,),
            ).fetchone()
            assert row is not None
            expected = "completed" if self.probe_completed else "scheduled"
            assert row["status"] == expected

    @invariant()
    def runtime_remains_healthy(self) -> None:
        assert self.service.doctor()["healthy"] is True

    def teardown(self) -> None:
        self.service.close()
        self.tmp.cleanup()


SemanticLifecycleStateMachine.TestCase.settings = settings(
    max_examples=24,
    stateful_step_count=30,
    deadline=None,
)
TestSemanticLifecycleStateMachine = SemanticLifecycleStateMachine.TestCase


if __name__ == "__main__":
    unittest.main()
