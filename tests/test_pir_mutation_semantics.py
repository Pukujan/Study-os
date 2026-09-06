from __future__ import annotations

import json
import tempfile
import unittest
from typing import Any, cast
from unittest.mock import patch

from study_os import RuntimeConfig, StudyOSService
from study_os.errors import StudyOSError
from study_os.pir.contracts import ProblemRunState, RunStatus, StepKind, TransitionSpec
from study_os.pir.controller import build_interaction_bundle, start_run, submit_response
from study_os.pir.registry import CANONICAL_PROBLEM_ID, get_asset


class PIRControllerSemanticMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.asset = get_asset(CANONICAL_PROBLEM_ID)
        if self.asset is None:
            self.fail("reviewed sliding-window asset is unavailable")

    def test_automatic_cycle_is_rejected_by_cycle_guard(self) -> None:
        cycling_step = next(
            step
            for step in self.asset.steps
            if step.kind != StepKind.PROBE and step.automatic_transition is not None
        )
        changed_steps = tuple(
            step.model_copy(
                update={
                    "automatic_transition": TransitionSpec(next_step_id=step.step_id),
                }
            )
            if step.step_id == cycling_step.step_id
            else step
            for step in self.asset.steps
        )
        cycling_asset = self.asset.model_copy(
            update={
                "entry_step_id": cycling_step.step_id,
                "steps": changed_steps,
            }
        )
        state = ProblemRunState(
            schema_version="study-os.problem-run-state.v0",
            problem_run_id="cycle-run",
            subject_id="subject-001",
            session_id="session-001",
            canonical_problem_id=cycling_asset.canonical_problem_id,
            canonical_pir_revision=cycling_asset.canonical_pir_revision,
            controller_revision=cycling_asset.controller_revision,
            renderer_revision=cycling_asset.renderer_revision,
            assessment_revision=cycling_asset.assessment_revision,
            current_step_id=cycling_step.step_id,
            status=RunStatus.ACTIVE,
            transition_seq=0,
        )
        with self.assertRaisesRegex(ValueError, "^automatic teaching-step cycle detected$"):
            build_interaction_bundle(cycling_asset, state)

    def test_direct_terminal_status_representation_is_exact(self) -> None:
        state, bundle = start_run(
            self.asset,
            problem_run_id="terminal-run",
            subject_id="subject-001",
            session_id="session-001",
        )
        step_id = state.current_step_id
        self.assertIsNotNone(step_id)
        assert step_id is not None
        changed_steps = []
        for step in self.asset.steps:
            if step.step_id != step_id:
                changed_steps.append(step)
                continue
            routes = tuple(
                TransitionSpec(
                    outcome=route.outcome,
                    exit_status=RunStatus.ASSEMBLED_MASTERY_UNPROVEN,
                )
                if route.outcome is not None and route.outcome.value == "correct"
                else route
                for route in step.outcome_transitions
            )
            changed_steps.append(step.model_copy(update={"outcome_transitions": routes}))
        direct_asset = self.asset.model_copy(update={"steps": tuple(changed_steps)})
        turn_id = bundle.response_turn_id
        self.assertIsNotNone(turn_id)
        assert turn_id is not None

        result = submit_response(direct_asset, state, turn_id=turn_id, response="8")
        self.assertEqual(result.state.status, RunStatus.ASSEMBLED_MASTERY_UNPROVEN)
        self.assertEqual(len(result.bundle.turns), 1)
        terminal = result.bundle.turns[0]
        self.assertEqual(terminal.representation_id, "status")
        self.assertEqual(terminal.turn_kind, StepKind.STATUS)
        self.assertEqual(terminal.allowed_actions, ())
        self.assertIsNone(result.bundle.response_turn_id)


class PIRRuntimeSemanticMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)
        self.session = self.service.start_session(
            idempotency_key="semantic-session",
            subject_id="subject-001",
            project_id="dsa-python",
            domain_id="dsa",
        )

    def tearDown(self) -> None:
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def start_problem(self, key: str) -> dict[str, object]:
        return self.service.start_problem(
            idempotency_key=key,
            session_id=str(self.session["session_id"]),
            subject_id="subject-001",
            canonical_problem_id=CANONICAL_PROBLEM_ID,
        )

    @staticmethod
    def response_turn_id(result: dict[str, object]) -> str:
        bundle = result["turn"]
        if not isinstance(bundle, dict):
            raise AssertionError("expected teaching bundle")
        turn_id = bundle.get("response_turn_id")
        if not isinstance(turn_id, str):
            raise AssertionError("expected response turn id")
        return turn_id

    @staticmethod
    def current_step_id(result: dict[str, object]) -> str:
        bundle = result["turn"]
        if not isinstance(bundle, dict):
            raise AssertionError("expected teaching bundle")
        turns = bundle.get("turns")
        if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
            raise AssertionError("expected learner-visible turns")
        step_id = turns[-1].get("canonical_step_id")
        if not isinstance(step_id, str) or not step_id:
            raise AssertionError("expected canonical step id")
        return step_id

    def test_blank_idempotency_key_fails_closed(self) -> None:
        before = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM problem_runs"
        ).fetchone()[0]
        with self.assertRaises(StudyOSError) as caught:
            self.start_problem("   ")
        self.assertEqual(caught.exception.category, "validation_error")
        after = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM problem_runs"
        ).fetchone()[0]
        self.assertEqual(after, before)

    def test_blank_response_is_atomic(self) -> None:
        started = self.start_problem("blank-response-start")
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)
        before_state = self.service.db.connection.execute(
            "SELECT current_step_id, status, transition_seq FROM problem_runs WHERE problem_run_id = ?",
            (run_id,),
        ).fetchone()
        before_attempts = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM attempts"
        ).fetchone()[0]
        before_events = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM learning_events"
        ).fetchone()[0]
        with self.assertRaises(StudyOSError) as caught:
            self.service.submit_problem_response(
                idempotency_key="blank-response",
                problem_run_id=run_id,
                subject_id="subject-001",
                turn_id=turn_id,
                response="   ",
            )
        self.assertEqual(caught.exception.category, "validation_error")
        after_state = self.service.db.connection.execute(
            "SELECT current_step_id, status, transition_seq FROM problem_runs WHERE problem_run_id = ?",
            (run_id,),
        ).fetchone()
        self.assertEqual(tuple(after_state), tuple(before_state))
        self.assertEqual(
            self.service.db.connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0],
            before_attempts,
        )
        self.assertEqual(
            self.service.db.connection.execute("SELECT COUNT(*) FROM learning_events").fetchone()[0],
            before_events,
        )

    def test_non_string_response_fails_at_runtime_boundary(self) -> None:
        started = self.start_problem("non-string-response-start")
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)
        with self.assertRaises(StudyOSError) as caught:
            self.service.submit_problem_response(
                idempotency_key="non-string-response",
                problem_run_id=run_id,
                subject_id="subject-001",
                turn_id=turn_id,
                response=cast(Any, 8),
            )
        self.assertEqual(caught.exception.category, "validation_error")

    def test_blank_expansion_request_is_atomic(self) -> None:
        started = self.start_problem("blank-expansion-start")
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)
        before_state = self.service.db.connection.execute(
            "SELECT current_step_id, status, transition_seq FROM problem_runs WHERE problem_run_id = ?",
            (run_id,),
        ).fetchone()
        before_events = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM learning_events"
        ).fetchone()[0]
        with self.assertRaises(StudyOSError) as caught:
            self.service.request_problem_expansion(
                idempotency_key="blank-expansion",
                problem_run_id=run_id,
                subject_id="subject-001",
                turn_id=turn_id,
                request_kind="why",
                learner_request="   ",
            )
        self.assertEqual(caught.exception.category, "validation_error")
        after_state = self.service.db.connection.execute(
            "SELECT current_step_id, status, transition_seq FROM problem_runs WHERE problem_run_id = ?",
            (run_id,),
        ).fetchone()
        self.assertEqual(tuple(after_state), tuple(before_state))
        self.assertEqual(
            self.service.db.connection.execute("SELECT COUNT(*) FROM learning_events").fetchone()[0],
            before_events,
        )

    def test_stale_expansion_is_conflict_and_writes_no_event(self) -> None:
        started = self.start_problem("stale-expansion-start")
        run_id = str(started["problem_run_id"])
        before_events = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM learning_events"
        ).fetchone()[0]
        with self.assertRaises(StudyOSError) as caught:
            self.service.request_problem_expansion(
                idempotency_key="stale-expansion",
                problem_run_id=run_id,
                subject_id="subject-001",
                turn_id=f"{run_id}:999:wrong-step",
                request_kind="why",
                learner_request="why?",
            )
        self.assertEqual(caught.exception.category, "conflict")
        self.assertEqual(
            self.service.db.connection.execute("SELECT COUNT(*) FROM learning_events").fetchone()[0],
            before_events,
        )

    def test_response_conflict_classifier_handles_each_supported_stale_signal(self) -> None:
        started = self.start_problem("response-conflict-classifier-start")
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)
        for index, message in enumerate(("stale", "current step")):
            with self.subTest(message=message):
                with patch(
                    "study_os.services.pir_runtime.submit_response",
                    side_effect=ValueError(message),
                ):
                    with self.assertRaises(StudyOSError) as caught:
                        self.service.submit_problem_response(
                            idempotency_key=f"response-conflict-classifier-{index}",
                            problem_run_id=run_id,
                            subject_id="subject-001",
                            turn_id=turn_id,
                            response="8",
                        )
                self.assertEqual(caught.exception.category, "conflict")

    def test_expansion_conflict_classifier_handles_each_supported_stale_signal(self) -> None:
        started = self.start_problem("expansion-conflict-classifier-start")
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)
        for index, message in enumerate(("stale", "current step")):
            with self.subTest(message=message):
                with patch(
                    "study_os.services.pir_runtime.build_expansion_bundle",
                    side_effect=ValueError(message),
                ):
                    with self.assertRaises(StudyOSError) as caught:
                        self.service.request_problem_expansion(
                            idempotency_key=f"expansion-conflict-classifier-{index}",
                            problem_run_id=run_id,
                            subject_id="subject-001",
                            turn_id=turn_id,
                            request_kind="why",
                            learner_request="why?",
                        )
                self.assertEqual(caught.exception.category, "conflict")

    def test_response_evidence_identity_and_version_are_exact(self) -> None:
        started = self.start_problem("evidence-start")
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)
        expected_step_id = self.current_step_id(started)
        self.service.submit_problem_response(
            idempotency_key="evidence-submit",
            problem_run_id=run_id,
            subject_id="subject-001",
            turn_id=turn_id,
            response="8",
        )
        attempt = self.service.db.connection.execute(
            "SELECT * FROM attempts WHERE idempotency_key = ?",
            ("pir:evidence-submit:attempt",),
        ).fetchone()
        self.assertIsNotNone(attempt)
        assert attempt is not None
        self.assertIsInstance(attempt["attempt_id"], str)
        self.assertTrue(attempt["attempt_id"])
        self.assertEqual(attempt["assistance_level"], "none")
        context = json.loads(attempt["context_json"])
        self.assertEqual(context["canonical_step_id"], expected_step_id)
        self.assertIsNotNone(context["canonical_step_id"])

        event = self.service.db.connection.execute(
            "SELECT * FROM learning_events WHERE idempotency_key = ?",
            ("pir:evidence-submit:outcome",),
        ).fetchone()
        self.assertIsNotNone(event)
        assert event is not None
        self.assertIsInstance(event["event_id"], str)
        self.assertTrue(event["event_id"])
        self.assertEqual(event["payload_version"], "0.1.0")
        payload = json.loads(event["payload_json"])
        self.assertEqual(payload["canonical_step_id"], expected_step_id)
        self.assertEqual(payload["attempt_id"], attempt["attempt_id"])
        self.assertEqual(json.loads(event["source_ids_json"]), [attempt["attempt_id"]])

    def test_expansion_event_identity_and_version_are_exact(self) -> None:
        started = self.start_problem("expansion-evidence-start")
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)
        self.service.request_problem_expansion(
            idempotency_key="expansion-evidence",
            problem_run_id=run_id,
            subject_id="subject-001",
            turn_id=turn_id,
            request_kind="why",
            learner_request="why?",
        )
        event = self.service.db.connection.execute(
            "SELECT * FROM learning_events WHERE idempotency_key = ?",
            ("pir:expansion-evidence:expansion",),
        ).fetchone()
        self.assertIsNotNone(event)
        assert event is not None
        self.assertIsInstance(event["event_id"], str)
        self.assertTrue(event["event_id"])
        self.assertEqual(event["payload_version"], "0.1.0")

    def test_get_problem_turn_public_shape_is_exact(self) -> None:
        started = self.start_problem("get-shape-start")
        run_id = str(started["problem_run_id"])
        with patch.object(
            self.service.repository,
            "transaction",
            wraps=self.service.repository.transaction,
        ) as transaction:
            result = self.service.get_problem_turn(
                problem_run_id=run_id,
                subject_id="subject-001",
            )
        transaction.assert_called_once_with(immediate=False)
        self.assertEqual(set(result), {"problem_run_id", "run_status", "turn"})
        self.assertEqual(result["problem_run_id"], run_id)
        self.assertEqual(result["run_status"], RunStatus.ACTIVE.value)


if __name__ == "__main__":
    unittest.main()
