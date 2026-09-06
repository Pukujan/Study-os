from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch

from study_os import RuntimeConfig, StudyOSService
from study_os.errors import StudyOSError
from study_os.pir.registry import CANONICAL_PROBLEM_ID


class PIRMutationContractEdgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = RuntimeConfig.from_env(self.temp_dir.name)
        self.service = StudyOSService(self.config)
        self.session = self.service.start_session(
            idempotency_key="edge-session",
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

    def test_blank_response_is_rejected_before_controller_execution(self) -> None:
        started = self.start_problem("blank-controller-start")
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)

        with patch("study_os.services.pir_runtime.submit_response") as submit:
            submit.side_effect = AssertionError("controller must not receive a blank response")
            with self.assertRaises(StudyOSError) as caught:
                self.service.submit_problem_response(
                    idempotency_key="blank-controller-submit",
                    problem_run_id=run_id,
                    subject_id="subject-001",
                    turn_id=turn_id,
                    response="   ",
                )
        self.assertEqual(caught.exception.category, "validation_error")
        submit.assert_not_called()

    def test_blank_expansion_is_rejected_before_controller_execution(self) -> None:
        started = self.start_problem("blank-expansion-controller-start")
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)

        with patch("study_os.services.pir_runtime.build_expansion_bundle") as build:
            build.side_effect = AssertionError("controller must not receive a blank expansion")
            with self.assertRaises(StudyOSError) as caught:
                self.service.request_problem_expansion(
                    idempotency_key="blank-expansion-controller",
                    problem_run_id=run_id,
                    subject_id="subject-001",
                    turn_id=turn_id,
                    request_kind="why",
                    learner_request="   ",
                )
        self.assertEqual(caught.exception.category, "validation_error")
        build.assert_not_called()

    def test_missing_expansion_is_validation_not_stale_turn_conflict(self) -> None:
        started = self.start_problem("missing-expansion-start")
        run_id = str(started["problem_run_id"])
        turn_id = self.response_turn_id(started)

        with self.assertRaises(StudyOSError) as caught:
            self.service.request_problem_expansion(
                idempotency_key="missing-expansion",
                problem_run_id=run_id,
                subject_id="subject-001",
                turn_id=turn_id,
                request_kind="more_detail",
                learner_request="show more detail",
            )
        self.assertEqual(caught.exception.category, "validation_error")

    def test_get_problem_turn_uses_read_transaction(self) -> None:
        started = self.start_problem("read-transaction-start")
        run_id = str(started["problem_run_id"])
        original = self.service.repository.transaction

        with patch.object(self.service.repository, "transaction", wraps=original) as transaction:
            self.service.get_problem_turn(
                problem_run_id=run_id,
                subject_id="subject-001",
            )
        transaction.assert_called_once_with(immediate=False)


if __name__ == "__main__":
    unittest.main()
