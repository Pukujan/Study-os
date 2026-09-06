from __future__ import annotations

import json
import tempfile
import unittest

from study_os import RuntimeConfig, StudyOSService
from study_os.errors import StudyOSError
from study_os.pir.contracts import ExpansionKind, RunStatus, StepKind, TransitionSpec
from study_os.pir.controller import build_expansion_bundle, start_run, submit_response
from study_os.pir.registry import CANONICAL_PROBLEM_ID, get_asset
from study_os.services.runtime_base import request_fingerprint


class PIRControllerAuthorityMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.asset = get_asset(CANONICAL_PROBLEM_ID)
        if self.asset is None:
            self.fail("reviewed sliding-window asset is unavailable")
        self.state, self.bundle = start_run(
            self.asset,
            problem_run_id="authority-run",
            subject_id="subject-001",
            session_id="session-001",
        )
        self.turn_id = self.bundle.response_turn_id
        self.assertIsNotNone(self.turn_id)
        assert self.turn_id is not None

    def _known_non_probe_step_id(self) -> str:
        for step in self.asset.steps:
            if step.kind != StepKind.PROBE:
                return step.step_id
        self.fail("asset must contain a non-probe step")

    def test_submit_rejects_each_invalid_controller_state_shape(self) -> None:
        states = {
            "inactive_with_step": self.state.model_copy(
                update={"status": RunStatus.ASSEMBLED_MASTERY_UNPROVEN}
            ),
            "active_without_step": self.state.model_copy(update={"current_step_id": None}),
            "active_non_probe": self.state.model_copy(
                update={"current_step_id": self._known_non_probe_step_id()}
            ),
            "active_unknown_step": self.state.model_copy(update={"current_step_id": "missing-step"}),
        }
        for label, state in states.items():
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    submit_response(self.asset, state, turn_id=self.turn_id, response="8")

    def test_expansion_rejects_each_invalid_controller_state_shape(self) -> None:
        states = {
            "inactive_with_step": self.state.model_copy(
                update={"status": RunStatus.ASSEMBLED_MASTERY_UNPROVEN}
            ),
            "active_without_step": self.state.model_copy(update={"current_step_id": None}),
            "active_non_probe": self.state.model_copy(
                update={"current_step_id": self._known_non_probe_step_id()}
            ),
            "active_unknown_step": self.state.model_copy(update={"current_step_id": "missing-step"}),
        }
        for label, state in states.items():
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    build_expansion_bundle(
                        self.asset,
                        state,
                        turn_id=self.turn_id,
                        kind=ExpansionKind.WHY,
                    )

    def test_direct_terminal_transition_returns_exact_no_mastery_status_turn(self) -> None:
        current_step_id = self.state.current_step_id
        self.assertIsNotNone(current_step_id)
        assert current_step_id is not None
        changed_steps = []
        for step in self.asset.steps:
            if step.step_id != current_step_id:
                changed_steps.append(step)
                continue
            changed_routes = tuple(
                TransitionSpec(
                    outcome=route.outcome,
                    exit_status=RunStatus.ASSEMBLED_MASTERY_UNPROVEN,
                )
                if route.outcome is not None and route.outcome.value == "correct"
                else route
                for route in step.outcome_transitions
            )
            changed_steps.append(step.model_copy(update={"outcome_transitions": changed_routes}))
        direct_terminal_asset = self.asset.model_copy(update={"steps": tuple(changed_steps)})

        result = submit_response(
            direct_terminal_asset,
            self.state,
            turn_id=self.turn_id,
            response="8",
        )
        self.assertEqual(result.outcome.value, "correct")
        self.assertEqual(result.state.status, RunStatus.ASSEMBLED_MASTERY_UNPROVEN)
        self.assertIsNone(result.state.current_step_id)
        self.assertEqual(result.bundle.run_status, RunStatus.ASSEMBLED_MASTERY_UNPROVEN)
        self.assertIsNone(result.bundle.response_turn_id)
        self.assertEqual(len(result.bundle.turns), 1)
        terminal = result.bundle.turns[0]
        self.assertEqual(terminal.run_status, RunStatus.ASSEMBLED_MASTERY_UNPROVEN)
        self.assertEqual(terminal.turn_kind, StepKind.STATUS)
        self.assertEqual(terminal.response_kind.value, "none")
        self.assertEqual(terminal.allowed_actions, ())
        self.assertEqual(
            terminal.learner_visible_markdown,
            "The reviewed lesson frontier is assembled. Independent mastery remains unproven.",
        )


class PIRRuntimeAuthorityMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)
        self.session = self.service.start_session(
            idempotency_key="authority-session",
            subject_id="subject-001",
            project_id="dsa-python",
            domain_id="dsa",
        )

    def tearDown(self) -> None:
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    @staticmethod
    def response_turn_id(result: dict[str, object]) -> str:
        bundle = result["turn"]
        if not isinstance(bundle, dict):
            raise AssertionError("expected teaching bundle")
        turn_id = bundle.get("response_turn_id")
        if not isinstance(turn_id, str):
            raise AssertionError("expected response turn id")
        return turn_id

    def start_problem(self, key: str = "authority-start") -> dict[str, object]:
        return self.service.start_problem(
            idempotency_key=key,
            session_id=str(self.session["session_id"]),
            subject_id="subject-001",
            canonical_problem_id=CANONICAL_PROBLEM_ID,
        )

    def _operation_row(self, operation_kind: str, key: str):
        row = self.service.db.connection.execute(
            "SELECT * FROM problem_run_operations WHERE operation_kind = ? AND idempotency_key = ?",
            (operation_kind, key),
        ).fetchone()
        self.assertIsNotNone(row)
        return row

    def test_start_result_replay_and_fingerprint_are_exact(self) -> None:
        key = "start-exact"
        result = self.start_problem(key)
        self.assertEqual(
            set(result),
            {
                "problem_run_id",
                "canonical_problem_id",
                "canonical_pir_revision",
                "run_status",
                "turn",
                "created",
            },
        )
        self.assertIs(result["created"], True)
        expected_request = {
            "session_id": str(self.session["session_id"]),
            "subject_id": "subject-001",
            "canonical_problem_id": CANONICAL_PROBLEM_ID,
        }
        row = self._operation_row("start_problem", key)
        self.assertEqual(row["request_fingerprint"], request_fingerprint(expected_request))
        stored = json.loads(row["result_json"])
        self.assertEqual(stored, result)

        replay = self.start_problem(key)
        self.assertEqual(set(replay), set(result))
        self.assertIs(replay["created"], False)
        self.assertEqual(replay["problem_run_id"], result["problem_run_id"])
        self.assertEqual(replay["turn"], result["turn"])

    def test_submit_result_evidence_replay_and_fingerprint_are_exact(self) -> None:
        started = self.start_problem("submit-start")
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)
        key = "submit-exact"
        result = self.service.submit_problem_response(
            idempotency_key=key,
            problem_run_id=run_id,
            subject_id="subject-001",
            turn_id=turn_id,
            response="8",
        )
        self.assertEqual(set(result), {"problem_run_id", "outcome", "run_status", "turn", "created"})
        self.assertEqual(result["problem_run_id"], run_id)
        self.assertEqual(result["outcome"], "correct")
        self.assertIs(result["created"], True)

        expected_request = {
            "problem_run_id": run_id,
            "subject_id": "subject-001",
            "turn_id": turn_id,
            "response": "8",
        }
        op = self._operation_row("submit_problem_response", key)
        self.assertEqual(op["request_fingerprint"], request_fingerprint(expected_request))
        self.assertEqual(json.loads(op["result_json"]), result)

        attempt = self.service.db.connection.execute(
            "SELECT * FROM attempts WHERE idempotency_key = ?",
            (f"pir:{key}:attempt",),
        ).fetchone()
        self.assertIsNotNone(attempt)
        assert attempt is not None
        context = json.loads(attempt["context_json"])
        self.assertEqual(
            set(context),
            {
                "problem_run_id",
                "canonical_problem_id",
                "canonical_pir_revision",
                "canonical_step_id",
                "turn_id",
                "controller_revision",
                "renderer_revision",
                "assessment_revision",
            },
        )
        self.assertEqual(context["problem_run_id"], run_id)
        self.assertEqual(context["turn_id"], turn_id)
        self.assertEqual(json.loads(attempt["response_json"]), "8")
        self.assertEqual(attempt["task_id"], f"pir:{CANONICAL_PROBLEM_ID}:{context['canonical_step_id']}")

        event = self.service.db.connection.execute(
            "SELECT * FROM learning_events WHERE idempotency_key = ?",
            (f"pir:{key}:outcome",),
        ).fetchone()
        self.assertIsNotNone(event)
        assert event is not None
        payload = json.loads(event["payload_json"])
        self.assertEqual(event["evidence_class"], "observed")
        self.assertEqual(event["event_type"], "pir_response_outcome")
        self.assertEqual(payload["problem_run_id"], run_id)
        self.assertEqual(payload["turn_id"], turn_id)
        self.assertEqual(payload["outcome"], "correct")
        self.assertEqual(payload["attempt_id"], attempt["attempt_id"])
        self.assertEqual(json.loads(event["source_ids_json"]), [attempt["attempt_id"]])

        replay = self.service.submit_problem_response(
            idempotency_key=key,
            problem_run_id=run_id,
            subject_id="subject-001",
            turn_id=turn_id,
            response="8",
        )
        self.assertIs(replay["created"], False)
        self.assertEqual(
            {k: replay[k] for k in replay if k != "created"},
            {k: result[k] for k in result if k != "created"},
        )

    def test_expansion_result_event_replay_and_fingerprint_are_exact(self) -> None:
        started = self.start_problem("expand-start")
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)
        key = "expand-exact"
        result = self.service.request_problem_expansion(
            idempotency_key=key,
            problem_run_id=run_id,
            subject_id="subject-001",
            turn_id=turn_id,
            request_kind="why",
            learner_request="why does this step work?",
        )
        self.assertEqual(set(result), {"problem_run_id", "run_status", "turn", "created"})
        self.assertEqual(result["problem_run_id"], run_id)
        self.assertIs(result["created"], True)
        expected_request = {
            "problem_run_id": run_id,
            "subject_id": "subject-001",
            "turn_id": turn_id,
            "request_kind": "why",
            "learner_request": "why does this step work?",
        }
        op = self._operation_row("request_problem_expansion", key)
        self.assertEqual(op["request_fingerprint"], request_fingerprint(expected_request))
        self.assertEqual(json.loads(op["result_json"]), result)

        event = self.service.db.connection.execute(
            "SELECT * FROM learning_events WHERE idempotency_key = ?",
            (f"pir:{key}:expansion",),
        ).fetchone()
        self.assertIsNotNone(event)
        assert event is not None
        payload = json.loads(event["payload_json"])
        self.assertEqual(event["evidence_class"], "observed")
        self.assertEqual(event["event_type"], "pir_expansion_request")
        self.assertEqual(
            set(payload),
            {
                "problem_run_id",
                "canonical_problem_id",
                "canonical_pir_revision",
                "canonical_step_id",
                "turn_id",
                "request_kind",
                "learner_request",
                "transition_seq",
            },
        )
        self.assertEqual(payload["problem_run_id"], run_id)
        self.assertEqual(payload["turn_id"], turn_id)
        self.assertEqual(payload["request_kind"], "why")
        self.assertEqual(payload["learner_request"], "why does this step work?")

        replay = self.service.request_problem_expansion(
            idempotency_key=key,
            problem_run_id=run_id,
            subject_id="subject-001",
            turn_id=turn_id,
            request_kind="why",
            learner_request="why does this step work?",
        )
        self.assertIs(replay["created"], False)
        self.assertEqual(
            {k: replay[k] for k in replay if k != "created"},
            {k: result[k] for k in result if k != "created"},
        )

    def test_invalid_current_step_is_validation_not_conflict(self) -> None:
        started = self.start_problem("invalid-step-start")
        run_id = str(started["problem_run_id"])
        self.service.db.connection.execute(
            "UPDATE problem_runs SET current_step_id = ?, transition_seq = 0 WHERE problem_run_id = ?",
            ("missing-step", run_id),
        )
        self.service.db.connection.commit()
        with self.assertRaises(StudyOSError) as caught:
            self.service.submit_problem_response(
                idempotency_key="invalid-step-submit",
                problem_run_id=run_id,
                subject_id="subject-001",
                turn_id=f"{run_id}:0:missing-step",
                response="8",
            )
        self.assertEqual(caught.exception.category, "validation_error")


if __name__ == "__main__":
    unittest.main()
