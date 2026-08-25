import sys
import tempfile
import unittest
from pathlib import Path

from hypothesis import HealthCheck, given, settings, strategies as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.config import RuntimeConfig  # noqa: E402
from study_os.errors import StudyOSError  # noqa: E402
from study_os.services.runtime import StudyOSService  # noqa: E402


class EventReferenceModel:
    """Independent in-memory oracle for the narrow durable-event semantics under test.

    The model intentionally has no SQLite, filesystem, service, MCP, or production-helper
    dependencies. It predicts only externally meaningful outcomes for one operation family:
    first write, exact retry, and conflicting idempotency-key reuse.
    """

    def __init__(self) -> None:
        self.requests: dict[str, tuple[str, int]] = {}

    @property
    def event_count(self) -> int:
        return len(self.requests)

    def record_event(self, *, key: str, event_type: str, value: int) -> str:
        request = (event_type, value)
        previous = self.requests.get(key)
        if previous is None:
            self.requests[key] = request
            return "created"
        if previous == request:
            return "retry"
        return "conflict"


_OPERATION_STREAM = st.lists(
    st.tuples(
        st.sampled_from(("event", "restart")),
        st.integers(min_value=0, max_value=5),
        st.integers(min_value=-100, max_value=100),
    ),
    min_size=1,
    max_size=50,
)


class EventReferenceDifferentialTests(unittest.TestCase):
    @settings(
        max_examples=40,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(operations=_OPERATION_STREAM)
    def test_generated_event_stream_matches_independent_reference_model(
        self,
        operations: list[tuple[str, int, int]],
    ) -> None:
        with tempfile.TemporaryDirectory() as root:
            config = RuntimeConfig(root=Path(root))
            service = StudyOSService(config)
            model = EventReferenceModel()
            actual_event_ids: dict[str, str] = {}
            try:
                session = service.start_session(
                    idempotency_key="reference-session",
                    subject_id="subject-reference",
                    project_id="project-reference",
                    domain_id="dsa",
                )
                session_id = str(session["session_id"])

                for operation, key_index, value in operations:
                    if operation == "restart":
                        service.close()
                        service = StudyOSService(config)
                    else:
                        key = f"reference-event-{key_index}"
                        event_type = "reference_observation"
                        expected = model.record_event(
                            key=key,
                            event_type=event_type,
                            value=value,
                        )
                        try:
                            result = service.record_learning_event(
                                idempotency_key=key,
                                session_id=session_id,
                                subject_id="subject-reference",
                                evidence_class="observed",
                                event_type=event_type,
                                payload={"value": value},
                            )
                        except StudyOSError as exc:
                            actual = exc.category
                            self.assertEqual(expected, "conflict")
                            self.assertEqual(actual, "conflict")
                        else:
                            actual = "created" if result["created"] else "retry"
                            self.assertEqual(actual, expected)
                            event_id = str(result["event_id"])
                            if expected == "created":
                                actual_event_ids[key] = event_id
                            elif expected == "retry":
                                self.assertEqual(event_id, actual_event_ids[key])

                    count = service.db.connection.execute(
                        "SELECT COUNT(*) FROM learning_events WHERE subject_id = ?",
                        ("subject-reference",),
                    ).fetchone()[0]
                    self.assertEqual(count, model.event_count)
                    self.assertTrue(service.doctor()["healthy"])
            finally:
                service.close()


if __name__ == "__main__":
    unittest.main()
