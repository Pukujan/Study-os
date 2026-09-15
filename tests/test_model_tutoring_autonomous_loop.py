from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from run_model_tutoring_autonomous_loop import (  # noqa: E402
    BatchExecution,
    build_parser,
    run_qualification,
    validate_agent_boundaries,
)
from study_os.decomposition_qualification import (  # noqa: E402
    CandidateFingerprint,
    QualificationBatch,
    QualificationLedger,
    STATUS_NOT_YET_QUALIFIED,
    STATUS_PUBLIC_EPOCH_PASSED,
    read_ledger,
    write_ledger,
    plan_batches,
)


def _candidate(tag: str = "a") -> CandidateFingerprint:
    fields = {
        name: f"{name}-{tag}"
        for name in CandidateFingerprint.__dataclass_fields__
    }
    return CandidateFingerprint(**fields)


class QualificationStateTests(unittest.TestCase):
    def test_batches_are_seeded_complete_and_non_overlapping(self) -> None:
        ids = ["a", "b", "c", "d", "e", "f", "g"]
        first = plan_batches(ids, batch_size=4, seed=17)
        second = plan_batches(ids, batch_size=4, seed=17)
        self.assertEqual([item.to_payload() for item in first], [item.to_payload() for item in second])
        self.assertEqual({value for item in first for value in item.scenario_ids}, set(ids))
        self.assertEqual(sum(len(item.scenario_ids) for item in first), len(ids))

    def test_candidate_change_invalidates_previous_epoch(self) -> None:
        ledger = QualificationLedger.new(
            goal="decomposition-reliability-qualified",
            public_scenario_ids=("a", "b"),
            hidden_scenario_ids=(),
            candidate=_candidate("a"),
            batch_size=1,
        )
        batch = ledger.public_batches_plan[0]
        ledger.record_batch(batch, passed=True, model_calls=3)
        self.assertEqual(ledger.next_public_batch, 1)
        old_epoch = ledger.epoch
        changed = ledger.reconcile_candidate(_candidate("b"))
        self.assertTrue(changed)
        self.assertEqual(ledger.epoch, old_epoch + 1)
        self.assertEqual(ledger.next_public_batch, 0)
        self.assertEqual(ledger.public_batches, [])
        self.assertEqual(ledger.candidate_count, 2)

    def test_batch_order_and_failed_batch_are_fail_closed(self) -> None:
        ledger = QualificationLedger.new(
            goal="goal",
            public_scenario_ids=("a", "b"),
            hidden_scenario_ids=(),
            candidate=_candidate(),
            batch_size=1,
        )
        with self.assertRaises(ValueError):
            ledger.record_batch(ledger.public_batches_plan[1], passed=True)
        ledger.record_batch(ledger.public_batches_plan[0], passed=False, report="report.json")
        self.assertEqual(ledger.status, STATUS_NOT_YET_QUALIFIED)
        self.assertEqual(ledger.next_public_batch, 0)

    def test_batch_contents_are_bound_to_frozen_schedule(self) -> None:
        ledger = QualificationLedger.new(
            goal="goal",
            public_scenario_ids=("a", "b"),
            hidden_scenario_ids=(),
            candidate=_candidate(),
            batch_size=1,
        )
        wrong = QualificationBatch(index=0, scenario_ids=("b",), seed=ledger.seed)
        with self.assertRaises(ValueError):
            ledger.record_batch(wrong, passed=True)

    def test_hidden_pass_is_the_only_terminal_qualification(self) -> None:
        ledger = QualificationLedger.new(
            goal="goal",
            public_scenario_ids=("a",),
            hidden_scenario_ids=("private",),
            candidate=_candidate(),
            batch_size=1,
        )
        ledger.record_batch(ledger.public_batches_plan[0], passed=True)
        self.assertEqual(ledger.status, STATUS_PUBLIC_EPOCH_PASSED)
        ledger.record_batch(ledger.hidden_batches_plan[0], passed=True)
        self.assertEqual(ledger.status, "DECOMPOSITION_RELIABILITY_QUALIFIED")

    def test_checkpoint_round_trip(self) -> None:
        ledger = QualificationLedger.new(
            goal="goal",
            public_scenario_ids=("a",),
            hidden_scenario_ids=(),
            candidate=_candidate(),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            write_ledger(path, ledger)
            restored = read_ledger(path)
        self.assertEqual(restored.to_payload(), ledger.to_payload())

    def test_role_boundary_validator_rejects_holdout_access(self) -> None:
        valid = ROOT / "contracts" / "model-tutoring-agent-boundaries.v0.1.json"
        validate_agent_boundaries(valid)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "boundaries.json"
            path.write_text(
                '{"roles": {"engineering_orchestrator": '
                '{"holdout_directory_read": true, "hidden_oracle_read": false}, '
                '"measured_decomposer": {"repo_write": false}, '
                '"measured_teacher": {"repo_write": false}, '
                '"measured_student": {"repo_write": false}}}',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                validate_agent_boundaries(path)


def _args(path: Path, *, dry_run: bool = False, hidden: list[str] | None = None) -> argparse.Namespace:
    return argparse.Namespace(
        corpus=ROOT / "datasets" / "dsa-conversation-replay.v0.1.json",
        state=path,
        artifact_root=path.parent / "artifacts",
        goal="decomposition-reliability-qualified",
        batch_size=4,
        seed=11,
        model="test-luna",
        codex_bin="codex",
        python_bin=sys.executable,
        mcp_name="study-os",
        turn_timeout_seconds=30,
        max_candidates=3,
        max_model_calls=1000,
        model_calls_per_batch=10,
        max_runtime_seconds=None,
        hidden_scenario=hidden or [],
        repair_command=None,
        hidden_command=None,
        resume=False,
        fresh=False,
        dry_run=dry_run,
        skip_local_setup=True,
        fresh_batch=False,
    )


class QualificationRunnerTests(unittest.TestCase):
    def test_qualification_defaults_to_completion_driven_mode(self) -> None:
        args = build_parser().parse_args([])
        self.assertTrue(args.completion_driven)
        fixed = build_parser().parse_args(["--fixed-turn-development"])
        self.assertFalse(fixed.completion_driven)

    def test_dry_run_only_checkpoints_and_makes_no_model_calls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            ledger = run_qualification(_args(path, dry_run=True))
            self.assertEqual(ledger.status, STATUS_NOT_YET_QUALIFIED)
            self.assertEqual(ledger.model_calls, 0)
            self.assertTrue(path.exists())

    def test_same_frozen_candidate_must_pass_all_public_batches(self) -> None:
        calls: list[tuple[int, str, tuple[str, ...]]] = []

        def fake_executor(batch: QualificationBatch, ledger: QualificationLedger, _args: argparse.Namespace) -> BatchExecution:
            calls.append((ledger.epoch, ledger.candidate.candidate_id, batch.scenario_ids))
            return BatchExecution(True, f"batch-{batch.index}.json", 10, {"fake": True})

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            ledger = run_qualification(_args(path), executor=fake_executor)
            self.assertEqual(ledger.status, STATUS_PUBLIC_EPOCH_PASSED)
            self.assertEqual(len(calls), 4)
            self.assertEqual(len({epoch for epoch, _candidate, _ids in calls}), 1)
            self.assertEqual(len({candidate for _epoch, candidate, _ids in calls}), 1)
            self.assertEqual(ledger.model_calls, 40)
            self.assertEqual(len(ledger.public_batches), 4)

    def test_public_pass_does_not_claim_hidden_qualification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            ledger = run_qualification(_args(path, dry_run=True, hidden=["private-1"]))
            # The dry-run path is intentionally not a public pass; the hidden
            # gate is separately tested by the state-machine tests above.  This
            # assertion documents that no hidden fixture is inferred locally.
            self.assertEqual(ledger.status, STATUS_NOT_YET_QUALIFIED)


if __name__ == "__main__":
    unittest.main()
