#!/usr/bin/env python3
"""Replay realistic DSA tutoring conversations against a local Study OS/Luna surface.

The harness has two lanes:
1. run: drive the actor through the corpus and grade each visible assistant reply.
2. grade: independently grade an already-captured JSONL transcript.

The actor never receives the expected assertions. That prevents the tutor from
"passing the test" by reading the answer key.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "datasets" / "dsa-conversation-replay.v0.1.json"


@dataclass(frozen=True)
class Violation:
    code: str
    detail: str


def load_corpus(path: Path = DEFAULT_CORPUS) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def corpus_counts(corpus: dict[str, Any]) -> tuple[int, int]:
    scenarios = corpus.get("scenarios", [])
    return len(scenarios), sum(len(item.get("turns", [])) for item in scenarios)


def validate_corpus(corpus: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    minimums = corpus.get("minimums", {})
    min_problems = int(minimums.get("problems", 10))
    min_turns = int(minimums.get("learner_turns", 150))
    problem_count, turn_count = corpus_counts(corpus)
    if problem_count < min_problems:
        errors.append(f"corpus has {problem_count} problems; requires >= {min_problems}")
    if turn_count < min_turns:
        errors.append(f"corpus has {turn_count} learner turns; requires >= {min_turns}")

    scenario_ids: set[str] = set()
    for scenario in corpus.get("scenarios", []):
        scenario_id = str(scenario.get("id", ""))
        if not scenario_id:
            errors.append("scenario missing id")
            continue
        if scenario_id in scenario_ids:
            errors.append(f"duplicate scenario id: {scenario_id}")
        scenario_ids.add(scenario_id)

        stages = scenario.get("stage_order", [])
        stage_positions = {stage: index for index, stage in enumerate(stages)}
        previous_stage = -1
        signals: set[str] = set()
        has_visual = False
        for turn_index, turn in enumerate(scenario.get("turns", [])):
            stage = turn.get("stage")
            if stage not in stage_positions:
                errors.append(f"{scenario_id} turn {turn_index}: unknown stage {stage!r}")
            else:
                position = stage_positions[stage]
                if position < previous_stage:
                    errors.append(
                        f"{scenario_id} turn {turn_index}: stage regressed from "
                        f"{previous_stage} to {position}"
                    )
                previous_stage = position
            if not str(turn.get("learner_message", "")).strip():
                errors.append(f"{scenario_id} turn {turn_index}: empty learner message")
            signals.add(str(turn.get("learner_signal", "")))
            expected = turn.get("expected", {})
            has_visual = has_visual or bool(expected.get("visual_required"))

        required_signals = {"clarification", "wrong_or_uncertain", "recovery_or_check"}
        missing_signals = required_signals - signals
        if missing_signals:
            errors.append(
                f"{scenario_id}: missing learner signals {sorted(missing_signals)}"
            )
        if not has_visual:
            errors.append(f"{scenario_id}: no visual-required turn")

    return errors


def _contains_term(text: str, term: str) -> bool:
    return term.casefold() in text.casefold()


def _looks_visual(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    if "```" in text:
        return True
    visual_markers = ("|", "->", "→", "↓", "↑", "[", "]", "index:", "stack:", "queue:")
    marked_lines = sum(any(marker in line for marker in visual_markers) for line in lines)
    return marked_lines >= 2


def evaluate_response(turn: dict[str, Any], assistant_message: str) -> list[Violation]:
    expected = turn["expected"]
    violations: list[Violation] = []
    text = assistant_message.strip()

    if not text:
        return [Violation("EMPTY_RESPONSE", "assistant response is empty")]

    required_any = [str(term) for term in expected.get("must_include_any", [])]
    if required_any and not any(_contains_term(text, term) for term in required_any):
        violations.append(
            Violation(
                "WRONG_DIRECTION",
                "response contains none of the stage anchors: " + ", ".join(required_any),
            )
        )

    for forbidden in expected.get("must_not_include", []):
        forbidden = str(forbidden)
        if forbidden and _contains_term(text, forbidden):
            violations.append(
                Violation(
                    "FUTURE_OR_RENAMED_CONCEPT",
                    f"response introduced forbidden term {forbidden!r}",
                )
            )

    if expected.get("visual_required") and not _looks_visual(text):
        violations.append(
            Violation(
                "REPRESENTATION_DROPPED",
                "turn requires a visible chart/trace but response has no detectable visual",
            )
        )

    max_lines = int(expected.get("max_nonempty_lines", 0) or 0)
    nonempty_lines = sum(bool(line.strip()) for line in text.splitlines())
    if max_lines and nonempty_lines > max_lines:
        violations.append(
            Violation(
                "OUTPUT_BUDGET_EXCEEDED",
                f"response has {nonempty_lines} non-empty lines; max is {max_lines}",
            )
        )

    if expected.get("must_ask_question") and "?" not in text:
        violations.append(
            Violation(
                "BACK_AND_FORTH_DROPPED",
                "turn should end in a learner-sized check/question",
            )
        )

    return violations


class JsonLineActor:
    """Long-running local actor using one JSON request/response per line.

    A small local wrapper can connect this protocol to the normal Study OS
    GPT/MCP path or Luna. The request deliberately excludes hidden assertions.
    """

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

    def ask(self, payload: dict[str, Any]) -> str:
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
        if isinstance(raw, str):
            return raw
        if isinstance(raw, dict) and isinstance(raw.get("assistant_message"), str):
            return raw["assistant_message"]
        raise RuntimeError("actor response must be JSON string or {assistant_message: string}")


def _actor_payload(
    scenario: dict[str, Any],
    turn: dict[str, Any],
    turn_index: int,
    history: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "type": "study_os_replay_turn",
        "scenario_id": scenario["id"],
        "title": scenario["title"],
        "problem": scenario["problem"],
        "variables": scenario["variables"],
        "visual_family": scenario["visual_family"],
        "stage": turn["stage"],
        "turn_index": turn_index,
        "learner_message": turn["learner_message"],
        "history": history,
    }


def _iter_selected(
    corpus: dict[str, Any],
    scenario_ids: set[str] | None,
) -> Iterable[dict[str, Any]]:
    for scenario in corpus["scenarios"]:
        if scenario_ids is None or scenario["id"] in scenario_ids:
            yield scenario


def run_actor(
    corpus: dict[str, Any],
    command: str,
    *,
    scenario_ids: set[str] | None,
    max_turns: int | None,
) -> dict[str, Any]:
    actor = JsonLineActor(command)
    records: list[dict[str, Any]] = []
    executed = 0
    try:
        for scenario in _iter_selected(corpus, scenario_ids):
            history: list[dict[str, str]] = []
            for turn_index, turn in enumerate(scenario["turns"]):
                if max_turns is not None and executed >= max_turns:
                    break
                payload = _actor_payload(scenario, turn, turn_index, history[-12:])
                assistant_message = actor.ask(payload)
                violations = evaluate_response(turn, assistant_message)
                records.append(
                    {
                        "scenario_id": scenario["id"],
                        "turn_index": turn_index,
                        "stage": turn["stage"],
                        "learner_message": turn["learner_message"],
                        "assistant_message": assistant_message,
                        "violations": [
                            {"code": item.code, "detail": item.detail}
                            for item in violations
                        ],
                    }
                )
                history.extend(
                    [
                        {"role": "learner", "content": turn["learner_message"]},
                        {"role": "assistant", "content": assistant_message},
                    ]
                )
                executed += 1
            if max_turns is not None and executed >= max_turns:
                break
    finally:
        actor.close()

    return build_report(corpus, records, source="actor")


def _load_transcript(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            raw = json.loads(line)
            if not isinstance(raw, dict):
                raise ValueError(f"line {line_number}: expected JSON object")
            records.append(raw)
    return records


def grade_transcript(
    corpus: dict[str, Any],
    transcript_path: Path,
) -> dict[str, Any]:
    source_records = _load_transcript(transcript_path)
    by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for record in source_records:
        key = (str(record["scenario_id"]), int(record["turn_index"]))
        if key in by_key:
            raise ValueError(f"duplicate transcript turn: {key}")
        by_key[key] = record

    graded: list[dict[str, Any]] = []
    for scenario in corpus["scenarios"]:
        for turn_index, turn in enumerate(scenario["turns"]):
            key = (scenario["id"], turn_index)
            source = by_key.get(key)
            if source is None:
                continue
            assistant_message = str(source.get("assistant_message", ""))
            violations = evaluate_response(turn, assistant_message)
            graded.append(
                {
                    "scenario_id": scenario["id"],
                    "turn_index": turn_index,
                    "stage": turn["stage"],
                    "learner_message": turn["learner_message"],
                    "assistant_message": assistant_message,
                    "violations": [
                        {"code": item.code, "detail": item.detail}
                        for item in violations
                    ],
                }
            )
    return build_report(corpus, graded, source=str(transcript_path))


def build_report(
    corpus: dict[str, Any],
    records: list[dict[str, Any]],
    *,
    source: str,
) -> dict[str, Any]:
    problem_count, corpus_turn_count = corpus_counts(corpus)
    failed_records = [item for item in records if item["violations"]]
    violation_counts: dict[str, int] = {}
    scenario_summary: dict[str, dict[str, int]] = {}
    for record in records:
        summary = scenario_summary.setdefault(
            record["scenario_id"], {"turns": 0, "failed_turns": 0}
        )
        summary["turns"] += 1
        if record["violations"]:
            summary["failed_turns"] += 1
        for violation in record["violations"]:
            code = violation["code"]
            violation_counts[code] = violation_counts.get(code, 0) + 1

    first_divergence = failed_records[0] if failed_records else None
    return {
        "schema_version": "study-os.dsa-conversation-replay-report.v0.1",
        "source": source,
        "corpus": {
            "problems": problem_count,
            "learner_turns": corpus_turn_count,
        },
        "executed_turns": len(records),
        "passed_turns": len(records) - len(failed_records),
        "failed_turns": len(failed_records),
        "pass_rate": (
            (len(records) - len(failed_records)) / len(records)
            if records
            else 0.0
        ),
        "violation_counts": dict(sorted(violation_counts.items())),
        "scenario_summary": scenario_summary,
        "first_divergence": first_divergence,
        "records": records,
    }


def _print_summary(report: dict[str, Any]) -> None:
    corpus = report["corpus"]
    print(
        f"corpus: {corpus['problems']} problems / "
        f"{corpus['learner_turns']} learner turns"
    )
    print(
        f"executed: {report['executed_turns']} | "
        f"passed: {report['passed_turns']} | "
        f"failed: {report['failed_turns']} | "
        f"pass_rate: {report['pass_rate']:.1%}"
    )
    if report["violation_counts"]:
        print("violations:")
        for code, count in report["violation_counts"].items():
            print(f"  {code}: {count}")
    first = report["first_divergence"]
    if first:
        print(
            "first divergence: "
            f"{first['scenario_id']} turn {first['turn_index']} "
            f"({first['stage']})"
        )
        print(f"learner: {first['learner_message']}")
        print(f"assistant: {first['assistant_message']}")
        for violation in first["violations"]:
            print(f"  - {violation['code']}: {violation['detail']}")


def _write_report(report: dict[str, Any], path: Path | None) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"report: {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="validate the replay corpus")

    run_parser = subparsers.add_parser(
        "run",
        help="drive a local Luna/Study OS actor over the realistic learner corpus",
    )
    run_parser.add_argument("--actor-cmd", required=True)
    run_parser.add_argument("--scenario", action="append", default=[])
    run_parser.add_argument("--max-turns", type=int)
    run_parser.add_argument("--report", type=Path)

    grade_parser = subparsers.add_parser(
        "grade",
        help="independently grade a captured JSONL transcript",
    )
    grade_parser.add_argument("--transcript", type=Path, required=True)
    grade_parser.add_argument("--report", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    corpus = load_corpus(args.corpus)
    corpus_errors = validate_corpus(corpus)
    if corpus_errors:
        for error in corpus_errors:
            print(f"corpus error: {error}", file=sys.stderr)
        return 2

    if args.command == "validate":
        problem_count, turn_count = corpus_counts(corpus)
        print(f"valid: {problem_count} problems / {turn_count} learner turns")
        return 0

    if args.command == "run":
        scenario_ids = set(args.scenario) or None
        report = run_actor(
            corpus,
            args.actor_cmd,
            scenario_ids=scenario_ids,
            max_turns=args.max_turns,
        )
        _print_summary(report)
        _write_report(report, args.report)
        return 1 if report["failed_turns"] else 0

    report = grade_transcript(corpus, args.transcript)
    _print_summary(report)
    _write_report(report, args.report)
    return 1 if report["failed_turns"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
