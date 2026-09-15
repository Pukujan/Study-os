#!/usr/bin/env python3
"""Run bounded qualification epochs for the generic Luna decomposer.

The command checkpoints before and after every batch.  It never counts output
from a changed code/prompt/schema candidate, and it never reports qualification
until an explicit hidden-promotion command has passed.  The default executor
uses the existing generic all-DSA runner for a deterministic four-problem
batch; callers may provide a repair command for an autonomous local-Luna fix
cycle, subject to the candidate and runtime bounds.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TOOLS = ROOT / "tools"
for path in (SRC, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import run_dual_luna_transcript as raw  # noqa: E402
import run_model_tutoring_all_dsa as all_dsa  # noqa: E402
from study_os.decomposition_qualification import (  # noqa: E402
    CandidateFingerprint,
    QualificationBatch,
    QualificationLedger,
    STATUS_NOT_YET_QUALIFIED,
    STATUS_PUBLIC_EPOCH_PASSED,
    STATUS_QUALIFIED,
    read_ledger,
    sha256_file,
    sha256_text,
    write_ledger,
)
from study_os.prompt_registry import (  # noqa: E402
    DEFAULT_PROMPT_REGISTRY,
    DECOMPOSITION_PROMPT_VERSION,
    DIAGNOSIS_PROMPT_VERSION,
    GENERATION_PROMPT_VERSION,
)
from study_os.teaching_plan import TEACHING_PLAN_SCHEMA_VERSION  # noqa: E402


DEFAULT_STATE = ROOT / "artifacts" / "model-tutoring-qualification-ledger.json"
DEFAULT_ARTIFACT_ROOT = ROOT / "artifacts" / "model-tutoring-qualification"
DEFAULT_MAX_CANDIDATES = 10
DEFAULT_MAX_MODEL_CALLS = 5000
DEFAULT_MODEL_CALLS_PER_BATCH = 200


def _tracked_revision() -> str:
    """Return HEAD plus a hash of tracked working-tree changes.

    A dirty worktree therefore cannot accidentally reuse a committed epoch's
    evidence.  Untracked runtime artifacts are deliberately excluded.
    """

    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
        diff = subprocess.run(
            ["git", "diff", "HEAD", "--binary"], cwd=ROOT, check=True, capture_output=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        head = "working-tree"
        diff = b""
    if isinstance(diff, str):
        diff = diff.encode("utf-8")
    return f"{head}+tracked-{sha256_text(diff.hex())[:16]}"


def _file_hash_or_missing(path: Path) -> str:
    if not path.exists():
        return f"missing:{path.as_posix()}"
    return sha256_file(path)


def _combined_file_hash(paths: Sequence[Path]) -> str:
    """Hash the ordered contents of a versioned skill/checklist bundle."""

    payload: list[dict[str, str]] = []
    for path in paths:
        payload.append({"path": path.as_posix(), "hash": _file_hash_or_missing(path)})
    return sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def current_candidate(*, model_identifier: str, code_revision: str | None = None) -> CandidateFingerprint:
    """Build the frozen identity of the currently checked-out candidate."""

    decomposition = DEFAULT_PROMPT_REGISTRY.get(DECOMPOSITION_PROMPT_VERSION)
    diagnosis = DEFAULT_PROMPT_REGISTRY.get(DIAGNOSIS_PROMPT_VERSION)
    generation = DEFAULT_PROMPT_REGISTRY.get(GENERATION_PROMPT_VERSION)
    skill_path = ROOT / "plugins" / "study-os-dsa-decomposer" / "skill.md"
    checklist_path = ROOT / "plugins" / "study-os-dsa-decomposer" / "checklist.md"
    return CandidateFingerprint(
        code_revision=code_revision or _tracked_revision(),
        decomposition_prompt_version=decomposition.version,
        decomposition_prompt_hash=decomposition.prompt_hash,
        diagnosis_prompt_version=diagnosis.version,
        diagnosis_prompt_hash=diagnosis.prompt_hash,
        generation_prompt_version=generation.version,
        generation_prompt_hash=generation.prompt_hash,
        teaching_plan_schema_version=TEACHING_PLAN_SCHEMA_VERSION,
        turn_trace_schema_version=all_dsa.TRACE_SCHEMA_VERSION,
        decomposer_skill_version="study-os-dsa-decomposer.v1",
        checklist_version="study-os-dsa-decomposer-checklist.v1",
        evaluation_policy_version="study-os.model-tutoring-rotating-holdout-eval.v1",
        decomposer_skill_hash=_file_hash_or_missing(skill_path),
        checklist_hash=_file_hash_or_missing(checklist_path),
        evaluation_policy_hash=_combined_file_hash(
            [
                TOOLS / "check_model_tutoring_all_dsa.py",
                ROOT / "docs" / "MODEL_TUTORING_ROTATING_HOLDOUT_EVAL_V1.md",
            ]
        ),
        model_identifier=model_identifier,
    )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL record in {path} must be an object")
            rows.append(value)
    return rows


@dataclass(frozen=True)
class BatchExecution:
    passed: bool
    report_path: str | None
    model_calls: int
    details: Mapping[str, Any]


Executor = Callable[[QualificationBatch, QualificationLedger, argparse.Namespace], BatchExecution]


def _batch_paths(ledger: QualificationLedger, batch: QualificationBatch, root: Path) -> dict[str, Path]:
    directory = root / f"epoch-{ledger.epoch}" / f"{batch.kind}-batch-{batch.index:03d}"
    return {
        "directory": directory,
        "transcript": directory / "transcript.jsonl",
        "markdown": directory / "transcript.md",
        "trace": directory / "trace.jsonl",
        "plans": directory / "plans.jsonl",
        "report": directory / "acceptance.json",
        "log": directory / "run.log",
    }


def execute_public_batch(
    batch: QualificationBatch, ledger: QualificationLedger, args: argparse.Namespace
) -> BatchExecution:
    """Execute one selected public batch through the existing generic path."""

    paths = _batch_paths(ledger, batch, args.artifact_root)
    paths["directory"].mkdir(parents=True, exist_ok=True)
    command = [
        args.python_bin,
        str(TOOLS / "run_model_tutoring_all_dsa.py"),
        "--allow-short-run",
        "--model",
        args.model,
        "--codex-bin",
        args.codex_bin,
        "--python-bin",
        args.python_bin,
        "--mcp-name",
        args.mcp_name,
        "--turn-timeout-seconds",
        str(args.turn_timeout_seconds),
        "--transcript",
        str(paths["transcript"]),
        "--markdown",
        str(paths["markdown"]),
        "--trace",
        str(paths["trace"]),
        "--plans",
        str(paths["plans"]),
    ]
    for scenario_id in batch.scenario_ids:
        command.extend(("--scenario", scenario_id))
    if args.skip_local_setup:
        command.append("--skip-local-setup")
    if args.fresh_batch:
        command.append("--fresh")
    with paths["log"].open("a", encoding="utf-8") as log:
        run = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    if run.returncode != 0:
        return BatchExecution(False, str(paths["log"]), args.model_calls_per_batch, {"runner_exit": run.returncode})

    check = [
        args.python_bin,
        str(TOOLS / "check_model_tutoring_all_dsa.py"),
        "--transcript",
        str(paths["transcript"]),
        "--trace",
        str(paths["trace"]),
        "--plans",
        str(paths["plans"]),
        "--report",
        str(paths["report"]),
        "--allow-short-run",
    ]
    for scenario_id in batch.scenario_ids:
        check.extend(("--scenario", scenario_id))
    checked = subprocess.run(check, cwd=ROOT, capture_output=True, text=True)
    report: dict[str, Any] = {}
    if paths["report"].exists():
        value = json.loads(paths["report"].read_text(encoding="utf-8"))
        if isinstance(value, dict):
            report = value
    passed = checked.returncode == 0 and report.get("status") == "passed"
    return BatchExecution(
        passed,
        str(paths["report"]),
        args.model_calls_per_batch,
        {"checker_exit": checked.returncode, "acceptance_status": report.get("status")},
    )


def _run_repair(command_template: str, *, ledger: QualificationLedger, failure: BatchExecution) -> int:
    rendered = command_template.format(
        candidate_id=ledger.candidate.candidate_id,
        epoch=ledger.epoch,
        report_path=failure.report_path or "",
    )
    return subprocess.run(rendered, cwd=ROOT, shell=True).returncode


def _validate_resume_config(ledger: QualificationLedger, args: argparse.Namespace, public_ids: Sequence[str]) -> None:
    if ledger.goal != args.goal:
        raise ValueError(f"ledger goal {ledger.goal!r} does not match requested {args.goal!r}")
    if ledger.batch_size != args.batch_size or ledger.seed != args.seed:
        raise ValueError("resume batch_size/seed differs from the checkpoint")
    if tuple(public_ids) != ledger.public_scenario_ids:
        raise ValueError("resume public corpus differs from the checkpoint")


def run_qualification(
    args: argparse.Namespace,
    *,
    executor: Executor | None = None,
    now: Callable[[], float] = time.monotonic,
) -> QualificationLedger:
    corpus = raw.load_corpus(args.corpus)
    public_ids = tuple(str(item["id"]) for item in corpus["scenarios"])
    hidden_ids = tuple(str(item) for item in args.hidden_scenario)
    candidate = current_candidate(model_identifier=args.model)
    state_path: Path = args.state
    if state_path.exists() and args.resume and not args.fresh:
        ledger = read_ledger(state_path)
        _validate_resume_config(ledger, args, public_ids)
        ledger.reconcile_candidate(candidate)
    elif state_path.exists() and not args.fresh:
        raise ValueError(f"checkpoint exists at {state_path}; pass --resume or --fresh")
    else:
        ledger = QualificationLedger.new(
            goal=args.goal,
            public_scenario_ids=public_ids,
            hidden_scenario_ids=hidden_ids,
            candidate=candidate,
            batch_size=args.batch_size,
            seed=args.seed,
            max_candidates=args.max_candidates,
            max_model_calls=args.max_model_calls,
            max_runtime_seconds=args.max_runtime_seconds,
        )
    write_ledger(state_path, ledger)
    if ledger.status == STATUS_QUALIFIED:
        return ledger
    if args.dry_run:
        ledger.status = STATUS_NOT_YET_QUALIFIED
        ledger._event("dry_run", next_public_batch=ledger.next_public_batch)
        write_ledger(state_path, ledger)
        return ledger
    executor = executor or execute_public_batch
    started = now()
    while ledger.next_public_batch < len(ledger.public_batches_plan):
        if ledger.max_runtime_seconds is not None and now() - started >= ledger.max_runtime_seconds:
            ledger.status = STATUS_NOT_YET_QUALIFIED
            ledger._event("runtime_bound_reached")
            break
        if not ledger.budget_available(additional_model_calls=args.model_calls_per_batch):
            ledger.status = STATUS_NOT_YET_QUALIFIED
            ledger._event("model_call_bound_reached")
            break
        batch = ledger.public_batches_plan[ledger.next_public_batch]
        result = executor(batch, ledger, args)
        ledger.record_batch(
            batch,
            passed=result.passed,
            report=result.report_path,
            model_calls=result.model_calls,
            details=result.details,
        )
        write_ledger(state_path, ledger)
        if result.passed:
            continue
        if args.repair_command and ledger.candidate_count < ledger.max_candidates:
            repair_exit = _run_repair(args.repair_command, ledger=ledger, failure=result)
            ledger._event("repair_attempted", exit_code=repair_exit, report=result.report_path)
            replacement = current_candidate(model_identifier=args.model)
            if replacement.digest != ledger.candidate.digest:
                ledger.start_new_candidate(replacement, reason="repair_command")
                write_ledger(state_path, ledger)
                continue
            ledger._event("repair_did_not_change_candidate")
        break

    if ledger.next_public_batch == len(ledger.public_batches_plan) and ledger.status != STATUS_NOT_YET_QUALIFIED:
        if not ledger.hidden_scenario_ids:
            ledger.status = STATUS_PUBLIC_EPOCH_PASSED
            ledger._event("hidden_promotion_pending", reason="no hidden scenarios/evaluator configured")
        elif not args.hidden_command:
            ledger.status = STATUS_PUBLIC_EPOCH_PASSED
            ledger._event("hidden_promotion_pending", reason="hidden command not configured")
        else:
            while ledger.next_hidden_batch < len(ledger.hidden_batches_plan):
                if not ledger.budget_available(additional_model_calls=args.model_calls_per_batch):
                    ledger.status = STATUS_NOT_YET_QUALIFIED
                    ledger._event("model_call_bound_reached_during_hidden")
                    break
                batch = ledger.hidden_batches_plan[ledger.next_hidden_batch]
                rendered = args.hidden_command.format(
                    epoch=ledger.epoch,
                    batch_index=batch.index,
                    scenario_ids=",".join(batch.scenario_ids),
                    candidate_id=ledger.candidate.candidate_id,
                )
                code = subprocess.run(rendered, cwd=ROOT, shell=True).returncode
                result = BatchExecution(code == 0, None, args.model_calls_per_batch, {"hidden_exit": code})
                ledger.record_batch(batch, passed=result.passed, model_calls=result.model_calls, details=result.details)
                write_ledger(state_path, ledger)
                if not result.passed:
                    break
    write_ledger(state_path, ledger)
    return ledger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run bounded resumable decomposition-reliability qualification")
    parser.add_argument("--corpus", type=Path, default=raw.DEFAULT_CORPUS)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--goal", default="decomposition-reliability-qualified")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--model", default=all_dsa.DEFAULT_MODEL)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--mcp-name", default=all_dsa.DEFAULT_MCP_NAME)
    parser.add_argument("--turn-timeout-seconds", type=int, default=all_dsa.DEFAULT_TURN_TIMEOUT_SECONDS)
    parser.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_CANDIDATES)
    parser.add_argument("--max-model-calls", type=int, default=DEFAULT_MAX_MODEL_CALLS)
    parser.add_argument("--model-calls-per-batch", type=int, default=DEFAULT_MODEL_CALLS_PER_BATCH)
    parser.add_argument("--max-runtime-seconds", type=int, default=None)
    parser.add_argument("--hidden-scenario", action="append", default=[])
    parser.add_argument("--repair-command", help="bounded shell command; supports {candidate_id}, {epoch}, {report_path}")
    parser.add_argument("--hidden-command", help="external hidden evaluator command; supports {epoch}, {batch_index}, {scenario_ids}, {candidate_id}")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--fresh", action="store_true", help="start a new ledger, discarding only this ledger's checkpoint")
    parser.add_argument("--dry-run", action="store_true", help="checkpoint the plan without making model calls")
    parser.add_argument("--skip-local-setup", action="store_true")
    parser.add_argument("--fresh-batch", action="store_true", help="discard each batch's persisted prefix before running")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        ledger = run_qualification(args)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"qualification error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": ledger.status,
        "candidate_id": ledger.candidate.candidate_id,
        "epoch": ledger.epoch,
        "public_batches_passed": sum(1 for item in ledger.public_batches if item.get("passed")),
        "public_batches_total": len(ledger.public_batches_plan),
        "hidden_batches_passed": sum(1 for item in ledger.hidden_batches if item.get("passed")),
        "model_calls": ledger.model_calls,
        "checkpoint": str(args.state),
    }, indent=2))
    return 0 if ledger.status in {STATUS_PUBLIC_EPOCH_PASSED, STATUS_QUALIFIED} else 1


if __name__ == "__main__":
    raise SystemExit(main())
