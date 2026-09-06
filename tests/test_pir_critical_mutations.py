from __future__ import annotations

import tempfile
import unittest

from study_os import RuntimeConfig, StudyOSService
from study_os.errors import StudyOSError
from study_os.pir.contracts import ExpansionKind, RunStatus, TransitionSpec
from study_os.pir.controller import (
    _apply_transition,
    _require_matching_state,
    build_expansion_bundle,
    start_run,
    submit_response,
)
from study_os.pir.registry import CANONICAL_PROBLEM_ID, get_asset
from study_os.services.pir_runtime import PIRRuntimeMixin


class PIRControllerCriticalMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.asset = get_asset(CANONICAL_PROBLEM_ID)
        if self.asset is None:
            self.fail("reviewed sliding-window asset is unavailable")

    def test_revision_identity_tuple_is_exact_in_every_position(self) -> None:
        state, _ = start_run(
            self.asset,
            problem_run_id="run-revision",
            subject_id="subject-001",
            session_id="session-001",
        )
        _require_matching_state(self.asset, state)

        mismatches = {
            "canonical_problem_id": "different.problem",
            "canonical_pir_revision": "different-pir",
            "controller_revision": "different-controller",
            "renderer_revision": "different-renderer",
            "assessment_revision": "different-assessment",
        }
        for field, value in mismatches.items():
            with self.subTest(field=field):
                changed = state.model_copy(update={field: value})
                with self.assertRaisesRegex(ValueError, "revision tuple"):
                    _require_matching_state(self.asset, changed)

    def test_transition_updates_only_target_status_and_sequence(self) -> None:
        state, _ = start_run(
            self.asset,
            problem_run_id="run-transition",
            subject_id="subject-001",
            session_id="session-001",
        )
        identity = {
            "problem_run_id": state.problem_run_id,
            "subject_id": state.subject_id,
            "session_id": state.session_id,
            "canonical_problem_id": state.canonical_problem_id,
            "canonical_pir_revision": state.canonical_pir_revision,
            "controller_revision": state.controller_revision,
            "renderer_revision": state.renderer_revision,
            "assessment_revision": state.assessment_revision,
        }

        advanced = _apply_transition(
            state,
            TransitionSpec(next_step_id="recurrence_probe"),
        )
        self.assertEqual(advanced.current_step_id, "recurrence_probe")
        self.assertEqual(advanced.status, RunStatus.ACTIVE)
        self.assertEqual(advanced.transition_seq, state.transition_seq + 1)
        for field, value in identity.items():
            self.assertEqual(getattr(advanced, field), value)

        terminal = _apply_transition(
            state,
            TransitionSpec(exit_status=RunStatus.ASSEMBLED_MASTERY_UNPROVEN),
        )
        self.assertIsNone(terminal.current_step_id)
        self.assertEqual(terminal.status, RunStatus.ASSEMBLED_MASTERY_UNPROVEN)
        self.assertEqual(terminal.transition_seq, state.transition_seq + 1)
        for field, value in identity.items():
            self.assertEqual(getattr(terminal, field), value)

    def test_submit_response_rejects_each_stale_turn_dimension(self) -> None:
        state, bundle = start_run(
            self.asset,
            problem_run_id="run-stale",
            subject_id="subject-001",
            session_id="session-001",
        )
        good_turn = bundle.response_turn_id
        self.assertIsNotNone(good_turn)
        assert good_turn is not None
        run_id, sequence, step_id = good_turn.split(":", 2)

        stale_turns = (
            f"different-run:{sequence}:{step_id}",
            f"{run_id}:{int(sequence) + 1}:{step_id}",
            f"{run_id}:{sequence}:different-step",
        )
        for turn_id in stale_turns:
            with self.subTest(turn_id=turn_id):
                with self.assertRaisesRegex(ValueError, "stale"):
                    submit_response(self.asset, state, turn_id=turn_id, response="8")

    def test_expansion_is_renderer_only_and_preserves_exact_state(self) -> None:
        state, bundle = start_run(
            self.asset,
            problem_run_id="run-expand",
            subject_id="subject-001",
            session_id="session-001",
        )
        before = state.model_dump(mode="json")
        turn_id = bundle.response_turn_id
        self.assertIsNotNone(turn_id)
        assert turn_id is not None

        expanded = build_expansion_bundle(
            self.asset,
            state,
            turn_id=turn_id,
            kind=ExpansionKind.WHY,
        )

        self.assertEqual(state.model_dump(mode="json"), before)
        self.assertEqual(expanded.problem_run_id, state.problem_run_id)
        self.assertEqual(expanded.run_status, RunStatus.ACTIVE)
        self.assertEqual(expanded.response_turn_id, turn_id)
        self.assertEqual(len(expanded.turns), 2)
        self.assertEqual(expanded.turns[0].turn_id, f"{turn_id}:expansion:why")
        self.assertEqual(expanded.turns[0].canonical_step_id, state.current_step_id)
        self.assertEqual(expanded.turns[-1].turn_id, turn_id)
        self.assertEqual(expanded.turns[-1].canonical_step_id, state.current_step_id)
        self.assertEqual(
            expanded.turns[-1].allowed_actions,
            ("submit_response", "request_expansion"),
        )


class PIRRuntimeCriticalMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)
        self.session = self.service.start_session(
            idempotency_key="critical-session",
            subject_id="subject-001",
            project_id="dsa-python",
            domain_id="dsa",
        )

    def tearDown(self) -> None:
        try:
            self.service.close()
        finally:
            self.temp_dir.cleanup()

    def start_problem(self, key: str = "critical-start") -> dict[str, object]:
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

    def test_persisted_run_contains_exact_installed_revision_identity(self) -> None:
        started = self.start_problem()
        run_id = str(started["problem_run_id"])
        installed = get_asset(CANONICAL_PROBLEM_ID)
        self.assertIsNotNone(installed)
        assert installed is not None

        row = self.service.db.connection.execute(
            "SELECT * FROM problem_runs WHERE problem_run_id = ?",
            (run_id,),
        ).fetchone()
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["subject_id"], "subject-001")
        self.assertEqual(row["session_id"], self.session["session_id"])
        self.assertEqual(row["canonical_problem_id"], installed.canonical_problem_id)
        self.assertEqual(row["canonical_pir_revision"], installed.canonical_pir_revision)
        self.assertEqual(row["controller_revision"], installed.controller_revision)
        self.assertEqual(row["renderer_revision"], installed.renderer_revision)
        self.assertEqual(row["assessment_revision"], installed.assessment_revision)
        self.assertEqual(row["status"], RunStatus.ACTIVE.value)

        revision_columns = {
            "canonical_pir_revision": installed.canonical_pir_revision,
            "controller_revision": installed.controller_revision,
            "renderer_revision": installed.renderer_revision,
            "assessment_revision": installed.assessment_revision,
        }
        for column, original in revision_columns.items():
            with self.subTest(column=column):
                self.service.db.connection.execute(
                    f"UPDATE problem_runs SET {column} = ? WHERE problem_run_id = ?",
                    (f"wrong-{column}", run_id),
                )
                self.service.db.connection.commit()
                with self.assertRaises(StudyOSError) as mismatch:
                    self.service.get_problem_turn(
                        problem_run_id=run_id,
                        subject_id="subject-001",
                    )
                self.assertEqual(mismatch.exception.category, "integrity_error")
                self.service.db.connection.execute(
                    f"UPDATE problem_runs SET {column} = ? WHERE problem_run_id = ?",
                    (original, run_id),
                )
                self.service.db.connection.commit()

    def test_same_idempotency_key_is_scoped_by_operation_kind(self) -> None:
        started = self.start_problem(key="shared-key")
        expansion = self.service.request_problem_expansion(
            idempotency_key="shared-key",
            problem_run_id=str(started["problem_run_id"]),
            subject_id="subject-001",
            turn_id=self.response_turn_id(started),
            request_kind="why",
            learner_request="why does the box start here?",
        )
        self.assertTrue(expansion["created"])
        rows = self.service.db.connection.execute(
            "SELECT operation_kind, idempotency_key FROM problem_run_operations "
            "WHERE idempotency_key = ? ORDER BY operation_kind",
            ("shared-key",),
        ).fetchall()
        self.assertEqual(
            [(row["operation_kind"], row["idempotency_key"]) for row in rows],
            [("request_problem_expansion", "shared-key"), ("start_problem", "shared-key")],
        )

    def test_stale_response_is_atomic_and_writes_no_evidence(self) -> None:
        started = self.start_problem()
        run_id = str(started["problem_run_id"])
        before_state = self.service.db.connection.execute(
            "SELECT current_step_id, status, transition_seq FROM problem_runs "
            "WHERE problem_run_id = ?",
            (run_id,),
        ).fetchone()
        before_attempts = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM attempts"
        ).fetchone()[0]
        before_events = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM learning_events"
        ).fetchone()[0]

        with self.assertRaises(StudyOSError) as stale:
            self.service.submit_problem_response(
                idempotency_key="critical-stale",
                problem_run_id=run_id,
                subject_id="subject-001",
                turn_id=f"{run_id}:999:wrong-step",
                response="8",
            )
        self.assertEqual(stale.exception.category, "conflict")

        after_state = self.service.db.connection.execute(
            "SELECT current_step_id, status, transition_seq FROM problem_runs "
            "WHERE problem_run_id = ?",
            (run_id,),
        ).fetchone()
        after_attempts = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM attempts"
        ).fetchone()[0]
        after_events = self.service.db.connection.execute(
            "SELECT COUNT(*) FROM learning_events"
        ).fetchone()[0]
        self.assertEqual(tuple(after_state), tuple(before_state))
        self.assertEqual(after_attempts, before_attempts)
        self.assertEqual(after_events, before_events)

    def test_expansion_preserves_every_pedagogical_state_column(self) -> None:
        started = self.start_problem()
        run_id = str(started["problem_run_id"])
        columns = (
            "subject_id, session_id, canonical_problem_id, canonical_pir_revision, "
            "controller_revision, renderer_revision, assessment_revision, current_step_id, "
            "status, transition_seq"
        )
        before = self.service.db.connection.execute(
            f"SELECT {columns} FROM problem_runs WHERE problem_run_id = ?",
            (run_id,),
        ).fetchone()

        result = self.service.request_problem_expansion(
            idempotency_key="critical-expand",
            problem_run_id=run_id,
            subject_id="subject-001",
            turn_id=self.response_turn_id(started),
            request_kind="why",
            learner_request="why?",
        )
        self.assertTrue(result["created"])

        after = self.service.db.connection.execute(
            f"SELECT {columns} FROM problem_runs WHERE problem_run_id = ?",
            (run_id,),
        ).fetchone()
        self.assertEqual(tuple(after), tuple(before))

    def test_terminal_bundle_is_exact_and_never_claims_mastery(self) -> None:
        current = self.start_problem()
        run_id = str(current["problem_run_id"])
        answers = (
            "8",
            "S[i]=S[i-1]-a[i-1]+a[i+j]",
            "for i,num in enumerate(a):",
            "S.append(S[i-1]-a[i-1]+a[i+j])",
            "if S[i] > max_sum:\n    max_sum = S[i]",
        )
        for index, answer in enumerate(answers):
            current = self.service.submit_problem_response(
                idempotency_key=f"critical-complete-{index}",
                problem_run_id=run_id,
                subject_id="subject-001",
                turn_id=self.response_turn_id(current),
                response=answer,
            )

        self.assertEqual(current["run_status"], RunStatus.ASSEMBLED_MASTERY_UNPROVEN.value)
        terminal = self.service.get_problem_turn(
            problem_run_id=run_id,
            subject_id="subject-001",
        )
        self.assertEqual(terminal["run_status"], RunStatus.ASSEMBLED_MASTERY_UNPROVEN.value)
        bundle = terminal["turn"]
        self.assertEqual(bundle["response_turn_id"], None)
        self.assertEqual(bundle["run_status"], RunStatus.ASSEMBLED_MASTERY_UNPROVEN.value)
        self.assertEqual(len(bundle["turns"]), 1)
        turn = bundle["turns"][0]
        self.assertEqual(turn["canonical_step_id"], "status")
        self.assertEqual(turn["turn_kind"], "status")
        self.assertEqual(turn["representation_id"], "status")
        self.assertEqual(turn["response_kind"], "none")
        self.assertEqual(turn["allowed_actions"], [])
        self.assertEqual(turn["run_status"], RunStatus.ASSEMBLED_MASTERY_UNPROVEN.value)
        self.assertEqual(
            turn["learner_visible_markdown"],
            "The reviewed lesson frontier is assembled. Independent mastery remains unproven.",
        )

        self.service.close()
        self.service = StudyOSService(self.config)
        resumed = self.service.get_problem_turn(
            problem_run_id=run_id,
            subject_id="subject-001",
        )
        self.assertEqual(resumed, terminal)

    def test_optimistic_transition_write_conflicts_if_sequence_changed(self) -> None:
        started = self.start_problem()
        run_id = str(started["problem_run_id"])
        with self.service.repository.transaction() as connection:
            state = self.service._load_problem_run(connection, run_id, "subject-001")
            updated = state.model_copy(
                update={
                    "current_step_id": state.current_step_id,
                    "transition_seq": state.transition_seq + 1,
                }
            )
            connection.execute(
                "UPDATE problem_runs SET transition_seq = transition_seq + 1 "
                "WHERE problem_run_id = ?",
                (run_id,),
            )
            with self.assertRaises(StudyOSError) as conflict_error:
                PIRRuntimeMixin._persist_problem_run(connection, state, updated)
            self.assertEqual(conflict_error.exception.category, "conflict")


if __name__ == "__main__":
    unittest.main()
