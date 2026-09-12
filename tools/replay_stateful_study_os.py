#!/usr/bin/env python3
"""Truthful state-driven Study OS + Luna learner-visible replay.

Unlike the broad 210-turn benchmark, this runner follows the deterministic
backend's *actual* current step.  It asks the actor for backend state, chooses a
realistic learner move that is valid for that state, lets Luna finish normally,
and records three independent verdicts:

- routing/state: did the requested Study OS action and state transition make sense?
- authority: did Luna's final visible text equal the backend-authorized text?
- pedagogy: did the authorized text satisfy the calibrated visible contract?

Hidden move conditions and grading expectations are never sent to Luna.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "datasets" / "dsa-live-stateful.v0.1.json"


def load_plan(path: Path = DEFAULT_PLAN) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _contains_term(text: str, term: str) -> bool:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", term):
        pattern = rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])"
        return re.search(pattern, text, flags=re.IGNORECASE) is not None
    return term.casefold() in text.casefold()


def _looks_visual(text: str) -> bool:
    if "```" in text:
        return True
    lines = [line for line in text.splitlines() if line.strip()]
    markers = ("|", "->", "→", "[", "]", "index:", "box:")
    return sum(any(marker in line for marker in markers) for line in lines) >= 2


def grade_pedagogy(expected: dict[str, Any], text: str) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if not text.strip():
        return [{"code": "EMPTY_BACKEND_OUTPUT", "detail": "authorized output is empty"}]

    required = [str(term) for term in expected.get("must_include_any", [])]
    if required and not any(_contains_term(text, term) for term in required):
        violations.append(
            {
                "code": "WRONG_DIRECTION",
                "detail": "authorized output contains none of: " + ", ".join(required),
            }
        )
    for term in expected.get("must_not_include", []):
        term = str(term)
        if term and _contains_term(text, term):
            violations.append(
                {
                    "code": "FUTURE_OR_RENAMED_CONCEPT",
                    "detail": f"authorized output introduced forbidden term {term!r}",
                }
            )
    if expected.get("visual_required") and not _looks_visual(text):
        violations.append(
            {
                "code": "REPRESENTATION_DROPPED",
                "detail": "authorized output does not contain the required visual",
            }
        )
    max_lines = int(expected.get("max_nonempty_lines", 0) or 0)
    line_count = sum(bool(line.strip()) for line in text.splitlines())
    if max_lines and line_count > max_lines:
        violations.append(
            {
                "code": "OUTPUT_BUDGET_EXCEEDED",
                "detail": f"authorized output has {line_count} non-empty lines; max {max_lines}",
            }
        )
    if expected.get("must_ask_question") and "?" not in text:
        violations.append(
            {
                "code": "BACK_AND_FORTH_DROPPED",
                "detail": "authorized output contains no learner-sized question",
            }
        )
    return violations


class JsonLineActor:
    def __init__(self, command: str) -> None:
        argv = shlex.split(command)
        if not argv:
            raise ValueError("actor command is empty")
        self.process = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )

    def close(self) -> None:
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=5)

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("actor pipes unavailable")
        if self.process.poll() is not None:
            raise RuntimeError(f"actor exited with code {self.process.returncode}")
        self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if line == "":
            raise RuntimeError("actor closed stdout before replying")
        raw = json.loads(line)
        if not isinstance(raw, dict):
            raise RuntimeError("stateful actor response must be a JSON object")
        return raw


def _public_context(scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": scenario["id"],
        "title": scenario["title"],
        "problem": scenario["problem"],
        "variables": scenario["variables"],
        "visual_family": scenario["visual_family"],
    }


def _select_move(
    moves: list[dict[str, Any]], used: set[int], backend_step: str
) -> tuple[int, dict[str, Any]] | None:
    for index, move in enumerate(moves):
        if index in used:
            continue
        if backend_step in move.get("when_steps", []):
            return index, move
    return None


def _tool_matches(actual_tools: list[str], expected_suffixes: list[str]) -> bool:
    if not expected_suffixes:
        return True
    return any(
        actual.endswith(expected)
        for actual in actual_tools
        for expected in expected_suffixes
    )


def run_scenario(
    scenario: dict[str, Any], command: str, *, max_turns: int | None = None
) -> dict[str, Any]:
    actor = JsonLineActor(command)
    records: list[dict[str, Any]] = []
    used: set[int] = set()
    history: list[dict[str, str]] = []
    moves = list(scenario["moves"])
    expectations = scenario["step_expectations"]
    terminal_steps = set(scenario.get("terminal_steps", []))
    context = _public_context(scenario)

    try:
        state = actor.request({"type": "study_os_replay_state", **context})
        current_step = state.get("backend_step")
        if not isinstance(current_step, str) or not current_step:
            raise RuntimeError(f"actor returned invalid initial backend step: {state!r}")

        while current_step not in terminal_steps:
            if max_turns is not None and len(records) >= max_turns:
                break
            selected = _select_move(moves, used, current_step)
            if selected is None:
                records.append(
                    {
                        "scenario_id": scenario["id"],
                        "turn_index": len(records),
                        "backend_step_before": current_step,
                        "learner_message": None,
                        "assistant_message": None,
                        "backend_message": None,
                        "routing_violations": [
                            {
                                "code": "NO_LEARNER_MOVE_FOR_BACKEND_STEP",
                                "detail": f"no unused learner move is valid for {current_step}",
                            }
                        ],
                        "authority_violations": [],
                        "pedagogy_violations": [],
                    }
                )
                break

            move_index, move = selected
            used.add(move_index)
            payload = {
                "type": "study_os_replay_turn",
                **context,
                "turn_index": len(records),
                "learner_message": move["learner_message"],
                "history": history[-12:],
            }
            response = actor.request(payload)
            assistant_message = response.get("assistant_message")
            backend_message = response.get("backend_message")
            before = response.get("backend_step_before")
            after = response.get("backend_step_after")
            raw_tools = response.get("tool_names")
            if not isinstance(raw_tools, list):
                single_tool = response.get("tool_name")
                raw_tools = [single_tool] if isinstance(single_tool, str) else []
            actual_tools = [str(item) for item in raw_tools if item]

            routing: list[dict[str, str]] = []
            authority: list[dict[str, str]] = []
            pedagogy: list[dict[str, str]] = []

            if before != current_step:
                routing.append(
                    {
                        "code": "BACKEND_STATE_MISMATCH",
                        "detail": f"expected pre-step {current_step!r}, actor reported {before!r}",
                    }
                )
            if not _tool_matches(actual_tools, list(move.get("expected_tool_any", []))):
                routing.append(
                    {
                        "code": "WRONG_STUDY_OS_ACTION",
                        "detail": f"tools {actual_tools!r} did not match {move.get('expected_tool_any', [])!r}",
                    }
                )
            if not isinstance(after, str) or not after:
                routing.append(
                    {
                        "code": "MISSING_BACKEND_STEP_AFTER",
                        "detail": "actor did not report the refreshed deterministic backend step",
                    }
                )
            if not isinstance(assistant_message, str):
                authority.append(
                    {"code": "MISSING_LUNA_FINAL_TEXT", "detail": "no final Luna text captured"}
                )
                assistant_message = ""
            if not isinstance(backend_message, str):
                authority.append(
                    {"code": "MISSING_BACKEND_TEXT", "detail": "no authoritative tool text captured"}
                )
                backend_message = ""
            if assistant_message != backend_message:
                authority.append(
                    {
                        "code": "AUTHORITY_DIVERGENCE",
                        "detail": "Luna final text differs from Study OS learner-visible markdown",
                    }
                )

            if isinstance(after, str):
                expected = expectations.get(after)
                if expected is None:
                    pedagogy.append(
                        {
                            "code": "UNCLASSIFIED_BACKEND_STEP",
                            "detail": f"no pedagogical expectation exists for backend step {after!r}",
                        }
                    )
                else:
                    pedagogy.extend(grade_pedagogy(expected, backend_message))

            records.append(
                {
                    "scenario_id": scenario["id"],
                    "turn_index": len(records),
                    "move_id": move["id"],
                    "backend_step_before": before,
                    "learner_message": move["learner_message"],
                    "tool_names": actual_tools,
                    "backend_message": backend_message,
                    "backend_step_after": after,
                    "assistant_message": assistant_message,
                    "routing_violations": routing,
                    "authority_violations": authority,
                    "pedagogy_violations": pedagogy,
                }
            )
            history.extend(
                [
                    {"role": "learner", "content": move["learner_message"]},
                    {"role": "assistant", "content": assistant_message},
                ]
            )
            if not isinstance(after, str) or not after:
                break
            current_step = after

        if current_step in terminal_steps and len(used) != len(moves):
            records.append(
                {
                    "scenario_id": scenario["id"],
                    "turn_index": len(records),
                    "backend_step_before": current_step,
                    "learner_message": None,
                    "assistant_message": None,
                    "backend_message": None,
                    "routing_violations": [
                        {
                            "code": "UNUSED_LEARNER_MOVES",
                            "detail": f"terminal state reached with {len(moves) - len(used)} scripted learner moves unused",
                        }
                    ],
                    "authority_violations": [],
                    "pedagogy_violations": [],
                }
            )
    finally:
        actor.close()

    return build_report(scenario, records, used_moves=len(used), total_moves=len(moves))


def build_report(
    scenario: dict[str, Any],
    records: list[dict[str, Any]],
    *,
    used_moves: int,
    total_moves: int,
) -> dict[str, Any]:
    failed = [
        record
        for record in records
        if record["routing_violations"]
        or record["authority_violations"]
        or record["pedagogy_violations"]
    ]
    routing_failures = sum(bool(item["routing_violations"]) for item in records)
    authority_failures = sum(bool(item["authority_violations"]) for item in records)
    pedagogy_failures = sum(bool(item["pedagogy_violations"]) for item in records)
    return {
        "schema_version": "study-os.dsa-stateful-live-report.v0.1",
        "scenario_id": scenario["id"],
        "executed_turns": sum(item.get("learner_message") is not None for item in records),
        "used_moves": used_moves,
        "total_moves": total_moves,
        "failed_records": len(failed),
        "routing_failed_records": routing_failures,
        "authority_failed_records": authority_failures,
        "pedagogy_failed_records": pedagogy_failures,
        "first_divergence": failed[0] if failed else None,
        "records": records,
    }


def _print_report(report: dict[str, Any]) -> None:
    print(
        f"{report['scenario_id']}: executed={report['executed_turns']} "
        f"routing_failures={report['routing_failed_records']} "
        f"authority_failures={report['authority_failed_records']} "
        f"pedagogy_failures={report['pedagogy_failed_records']}"
    )
    first = report["first_divergence"]
    if first:
        print(
            "first divergence: "
            f"turn={first['turn_index']} step={first.get('backend_step_before')} "
            f"move={first.get('move_id')}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--actor-cmd", required=True)
    parser.add_argument("--scenario", default="two-sum-dictionary")
    parser.add_argument("--max-turns", type=int)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    plan = load_plan(args.plan)
    scenarios = {item["id"]: item for item in plan["scenarios"]}
    if args.scenario not in scenarios:
        raise SystemExit(f"unknown live scenario: {args.scenario}")
    report = run_scenario(
        scenarios[args.scenario], args.actor_cmd, max_turns=args.max_turns
    )
    _print_report(report)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"report: {args.report}")
    return 1 if report["failed_records"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
