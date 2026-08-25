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


if __name__ == "__main__":
    unittest.main()
