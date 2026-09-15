#!/usr/bin/env python3
"""Run one isolated local-Luna lane per DSA problem and merge checkpoints.

Each lane owns its student/teacher Codex actors and four JSONL/Markdown files.
The parent process only schedules lanes and merges completed, structurally
complete outputs; it never combines partial rows into the learner transcript.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import run_dual_luna_transcript as raw
import run_model_tutoring_all_dsa as runner

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LANE_ROOT = ROOT / "artifacts" / "model-tutoring-lanes"
AGGREGATE_PLAN_ARTIFACT = "artifacts/model-tutoring-all-dsa-plans.jsonl"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    temporary.replace(path)


def _lane_paths(lane_root: Path, scenario_id: str) -> dict[str, Path]:
    directory = lane_root / scenario_id
    return {
        "transcript": directory / "transcript.jsonl",
        "markdown": directory / "transcript.md",
        "trace": directory / "trace.jsonl",
        "plans": directory / "plans.jsonl",
        "log": directory / "lane.log",
    }


def _lane_command(
    *, scenario_id: str, paths: dict[str, Path], args: argparse.Namespace
) -> list[str]:
    command = [
        args.python_bin,
        str(ROOT / "tools" / "run_model_tutoring_all_dsa.py"),
        "--scenario",
        scenario_id,
        "--allow-short-run",
        "--skip-local-setup",
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
    if args.fresh:
        command.append("--fresh")
    if getattr(args, "completion_driven", False):
        command.extend(("--completion-driven", "--max-exchanges-per-problem", str(args.max_exchanges_per_problem)))
    return command


def merge_complete_lanes(
    corpus: dict[str, Any], lane_root: Path, *, transcript_path: Path, markdown_path: Path, trace_path: Path, plans_path: Path,
    scenario_ids: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    transcript: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    plans: list[dict[str, Any]] = []
    incomplete: list[str] = []
    selected = raw.select_scenarios(corpus, scenario_ids)
    for scenario in selected:
        scenario_id = str(scenario["id"])
        paths = _lane_paths(lane_root, scenario_id)
        lane_transcript = _load_jsonl(paths["transcript"])
        lane_trace = _load_jsonl(paths["trace"])
        lane_plans = _load_jsonl(paths["plans"])
        if len(lane_transcript) != runner.TURNS_PER_SCENARIO or len(lane_trace) != runner.TURNS_PER_SCENARIO or len(lane_plans) != 1:
            incomplete.append(scenario_id)
            continue
        # Lane-local paths are implementation details.  Normalize references
        # in the merged evidence so reviewers can resolve every record from the
        # committed aggregate plan artifact without the private lane tree.
        for row in (*lane_transcript, *lane_trace, *lane_plans):
            reference = row.get("plan_payload_reference")
            if isinstance(reference, dict):
                reference["artifact"] = AGGREGATE_PLAN_ARTIFACT
        transcript.extend(lane_transcript)
        trace.extend(lane_trace)
        plans.extend(lane_plans)
    if incomplete:
        raise RuntimeError("cannot merge incomplete lanes: " + ", ".join(incomplete))
    order = {str(item["id"]): index for index, item in enumerate(selected)}
    transcript.sort(key=lambda row: (order[str(row["scenario_id"])], int(row["turn_index"])))
    trace.sort(key=lambda row: (order[str(row["scenario_id"])], int(row["turn_index"])))
    plans.sort(key=lambda row: order[str(row["scenario_id"])])
    _write_jsonl(transcript, transcript_path)
    _write_jsonl(trace, trace_path)
    _write_jsonl(plans, plans_path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = markdown_path.with_name(markdown_path.name + ".tmp")
    temporary.write_text(runner.render_markdown(transcript), encoding="utf-8")
    temporary.replace(markdown_path)
    return transcript, trace, plans


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run isolated local Luna lanes for all DSA scenarios")
    parser.add_argument("--corpus", type=Path, default=raw.DEFAULT_CORPUS)
    parser.add_argument("--lane-root", type=Path, default=DEFAULT_LANE_ROOT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--allow-short-run", action="store_true", help="compatibility flag; selected lanes are always short runs")
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--model", default=runner.DEFAULT_MODEL)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--mcp-name", default=runner.DEFAULT_MCP_NAME)
    parser.add_argument("--turn-timeout-seconds", type=int, default=runner.DEFAULT_TURN_TIMEOUT_SECONDS)
    parser.add_argument("--skip-local-setup", action="store_true")
    parser.add_argument("--completion-driven", action="store_true")
    parser.add_argument("--max-exchanges-per-problem", type=int, default=250)
    parser.add_argument("--transcript", type=Path, default=runner.DEFAULT_TRANSCRIPT)
    parser.add_argument("--markdown", type=Path, default=runner.DEFAULT_MARKDOWN)
    parser.add_argument("--trace", type=Path, default=runner.DEFAULT_TRACE)
    parser.add_argument("--plans", type=Path, default=runner.DEFAULT_PLANS)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.workers < 1:
        raise SystemExit("--workers must be >= 1")
    corpus = raw.load_corpus(args.corpus)
    # Register the shared local MCP once before creating isolated actors.  The
    # lane processes skip setup so they cannot race while editing Codex config.
    if not args.skip_local_setup:
        runner.local.ensure_codex_available(args.codex_bin)
        runner.local.ensure_local_runtime(args.python_bin)
        runner.local.configure_local_study_os_mcp(args.codex_bin, args.python_bin, args.mcp_name)
    args.lane_root.mkdir(parents=True, exist_ok=True)
    scenario_ids = set(args.scenario) or None
    scenarios = raw.select_scenarios(corpus, scenario_ids)
    pending: list[tuple[str, dict[str, Path], subprocess.Popen[Any]]] = []
    completed: dict[str, int] = {}
    next_index = 0
    while next_index < len(scenarios) or pending:
        while next_index < len(scenarios) and len(pending) < args.workers:
            scenario_id = str(scenarios[next_index]["id"])
            next_index += 1
            paths = _lane_paths(args.lane_root, scenario_id)
            if (
                not args.fresh
                and len(_load_jsonl(paths["transcript"])) == runner.TURNS_PER_SCENARIO
                and len(_load_jsonl(paths["trace"])) == runner.TURNS_PER_SCENARIO
                and len(_load_jsonl(paths["plans"])) == 1
            ):
                completed[scenario_id] = 0
                print(f"skipping complete lane {scenario_id}", flush=True)
                continue
            paths["log"].parent.mkdir(parents=True, exist_ok=True)
            log = paths["log"].open("a", encoding="utf-8")
            process = subprocess.Popen(
                _lane_command(scenario_id=scenario_id, paths=paths, args=args),
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=os.environ.copy(),
            )
            # Keep the descriptor alive until the child exits; Windows closes
            # inherited handles safely when the parent drops this reference.
            pending.append((scenario_id, paths, process))
            print(f"started lane {scenario_id} pid={process.pid}", flush=True)
        still_pending: list[tuple[str, dict[str, Path], subprocess.Popen[Any]]] = []
        failed_now = False
        for scenario_id, paths, process in pending:
            code = process.poll()
            if code is None:
                still_pending.append((scenario_id, paths, process))
                continue
            completed[scenario_id] = int(code)
            print(f"finished lane {scenario_id} exit={code}", flush=True)
            if code != 0:
                failed_now = True
        if failed_now and still_pending:
            # A batch is indivisible evidence: once one lane fails, sibling
            # lanes cannot make the batch pass. Stop them promptly instead of
            # spending more Luna calls on an already-invalid candidate.
            for scenario_id, _paths, process in still_pending:
                print(f"stopping sibling lane {scenario_id} after batch failure", flush=True)
                process.terminate()
            for scenario_id, _paths, process in still_pending:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                completed[scenario_id] = int(process.returncode or -1)
            still_pending = []
        pending = still_pending
        if pending:
            import time

            time.sleep(2)
    failed = [scenario_id for scenario_id, code in completed.items() if code != 0]
    if failed:
        raise SystemExit("lane failures: " + ", ".join(sorted(failed)))
    transcript, trace, plans = merge_complete_lanes(
        corpus,
        args.lane_root,
        transcript_path=args.transcript,
        markdown_path=args.markdown,
        trace_path=args.trace,
        plans_path=args.plans,
        scenario_ids=scenario_ids,
    )
    print(f"merged {len(plans)} plans / {len(transcript)} exchanges / {len(transcript) * 2} visible messages", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
