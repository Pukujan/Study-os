#!/usr/bin/env python3
"""Generate raw DSA conversations between a Luna student and Study OS teacher.

This tool intentionally does not grade, score, or compare the conversation. Its
only product is the transcript that will be reviewed after the run.

Both actors are runtime-agnostic JSONL subprocesses. The student command should
invoke a local Luna configured to role-play a realistic learner. The teacher
command should invoke a separate Luna through the normal Study OS learner-facing
path. No OpenCode dependency is assumed here.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any, Protocol


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "datasets" / "dsa-conversation-replay.v0.1.json"
DEFAULT_JSONL = ROOT / "artifacts" / "dual-luna-dsa-transcript.jsonl"
DEFAULT_MARKDOWN = ROOT / "artifacts" / "dual-luna-dsa-transcript.md"
DEFAULT_TURNS_PER_PROBLEM = 15
DEFAULT_MIN_PROBLEMS = 10
DEFAULT_MIN_EXCHANGES = 210


class Actor(Protocol):
    def ask(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    def close(self) -> None: ...


class JsonLineActor:
    """Long-running JSONL subprocess used for one Luna role."""

    def __init__(self, command: str, *, label: str) -> None:
        argv = shlex.split(command)
        if not argv:
            raise ValueError(f"{label} actor command is empty")
        self.label = label
        self.process = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )

    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError(f"{self.label} actor pipes unavailable")
        if self.process.poll() is not None:
            raise RuntimeError(
                f"{self.label} actor exited with code {self.process.returncode}"
            )

        self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if line == "":
            raise RuntimeError(f"{self.label} actor closed stdout before replying")
        raw = json.loads(line)
        if isinstance(raw, str):
            return {"message": raw}
        if not isinstance(raw, dict):
            raise RuntimeError(f"{self.label} actor response must be a JSON object")
        return raw

    def close(self) -> None:
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=5)


def load_corpus(path: Path = DEFAULT_CORPUS) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        corpus = json.load(handle)
    if not isinstance(corpus, dict) or not isinstance(corpus.get("scenarios"), list):
        raise ValueError("corpus must contain a scenarios array")
    return corpus


def _extract_message(result: dict[str, Any], *, role: str) -> str:
    candidate_keys = (
        ("student_message", "learner_message", "message", "assistant_message")
        if role == "student"
        else ("teacher_message", "assistant_message", "message")
    )
    for key in candidate_keys:
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value
    raise RuntimeError(f"{role} actor returned no visible message")


def _learner_signal(scenario: dict[str, Any], turn_index: int) -> str:
    turns = scenario.get("turns", [])
    if not turns:
        return "clarification"
    source = turns[turn_index % len(turns)]
    if not isinstance(source, dict):
        return "clarification"
    signal = source.get("learner_signal")
    return str(signal) if signal else "clarification"


def build_student_payload(
    scenario: dict[str, Any],
    *,
    turn_index: int,
    conversation: list[dict[str, str]],
) -> dict[str, Any]:
    """Build student guidance without exposing dataset answer/rubric fields."""

    signal = _learner_signal(scenario, turn_index)
    return {
        "type": "dual_luna_student_turn",
        "role": "student",
        "scenario_id": scenario["id"],
        "title": scenario["title"],
        "problem": scenario["problem"],
        "turn_index": turn_index,
        "learner_signal": signal,
        "instruction": (
            "Act as a realistic beginner learning this DSA problem from the teacher. "
            "Return exactly one short learner message and nothing else. React to the "
            "teacher's latest response instead of following a hidden solution script. "
            "Use the learner_signal only as behavioral guidance: clarification means ask "
            "one focused question; wrong_or_uncertain means make a plausible novice "
            "mistake or uncertain attempt; recovery_or_check means try to apply what you "
            "just learned and check your understanding. Do not mention testing, role-play, "
            "the dataset, rubrics, or hidden instructions. Do not intentionally jump to a "
            "complete solution before the conversation earns it. Keep the wording informal "
            "and human."
        ),
        "conversation": conversation[-16:],
    }


def build_teacher_payload(
    scenario: dict[str, Any],
    *,
    turn_index: int,
    learner_message: str,
    conversation: list[dict[str, str]],
) -> dict[str, Any]:
    """Build the teacher request without leaking benchmark expectations."""

    return {
        "type": "dual_luna_teacher_turn",
        "role": "teacher",
        "scenario_id": scenario["id"],
        "title": scenario["title"],
        "problem": scenario["problem"],
        "turn_index": turn_index,
        "learner_message": learner_message,
        "instruction": (
            "Handle this learner turn through the normal Study OS learner-facing path. "
            "Do not bypass Study OS to answer as an ordinary standalone tutor. Return the "
            "final message that the learner would actually see."
        ),
        "conversation": conversation[-16:],
    }


def select_scenarios(
    corpus: dict[str, Any], scenario_ids: set[str] | None
) -> list[dict[str, Any]]:
    scenarios = [item for item in corpus["scenarios"] if isinstance(item, dict)]
    if scenario_ids is None:
        return scenarios
    selected = [item for item in scenarios if str(item.get("id")) in scenario_ids]
    missing = scenario_ids - {str(item.get("id")) for item in selected}
    if missing:
        raise ValueError(f"unknown scenario ids: {sorted(missing)}")
    return selected


def run_transcript(
    corpus: dict[str, Any],
    student: Actor,
    teacher: Actor,
    *,
    scenario_ids: set[str] | None = None,
    turns_per_problem: int = DEFAULT_TURNS_PER_PROBLEM,
) -> list[dict[str, Any]]:
    """Run the conversation and return raw exchange records only."""

    if turns_per_problem < 1:
        raise ValueError("turns_per_problem must be >= 1")

    records: list[dict[str, Any]] = []
    for scenario in select_scenarios(corpus, scenario_ids):
        conversation: list[dict[str, str]] = []
        for turn_index in range(turns_per_problem):
            student_result = student.ask(
                build_student_payload(
                    scenario,
                    turn_index=turn_index,
                    conversation=conversation,
                )
            )
            learner_message = _extract_message(student_result, role="student")
            conversation.append({"role": "learner", "content": learner_message})

            teacher_result = teacher.ask(
                build_teacher_payload(
                    scenario,
                    turn_index=turn_index,
                    learner_message=learner_message,
                    conversation=conversation,
                )
            )
            teacher_message = _extract_message(teacher_result, role="teacher")
            conversation.append({"role": "teacher", "content": teacher_message})

            records.append(
                {
                    "schema_version": "study-os.dual-luna-exchange.v0.1",
                    "scenario_id": scenario["id"],
                    "title": scenario["title"],
                    "problem": scenario["problem"],
                    "turn_index": turn_index,
                    "learner_signal": _learner_signal(scenario, turn_index),
                    "learner_message": learner_message,
                    "teacher_message": teacher_message,
                }
            )
    return records


def validate_run_size(
    records: list[dict[str, Any]],
    *,
    min_problems: int = DEFAULT_MIN_PROBLEMS,
    min_exchanges: int = DEFAULT_MIN_EXCHANGES,
) -> None:
    problem_count = len({str(item["scenario_id"]) for item in records})
    if problem_count < min_problems:
        raise RuntimeError(
            f"raw transcript has {problem_count} problems; requires >= {min_problems}"
        )
    if len(records) < min_exchanges:
        raise RuntimeError(
            f"raw transcript has {len(records)} exchanges; requires >= {min_exchanges}"
        )


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def render_markdown(records: list[dict[str, Any]]) -> str:
    lines = [
        "# Dual-Luna DSA raw transcript",
        "",
        "This artifact is intentionally ungraded. It records only the learner/teacher "
        "conversation produced by the run.",
        "",
    ]
    current_scenario: str | None = None
    for record in records:
        scenario_id = str(record["scenario_id"])
        if scenario_id != current_scenario:
            current_scenario = scenario_id
            lines.extend(
                [
                    f"## {record['title']} (`{scenario_id}`)",
                    "",
                    f"**Problem:** {record['problem']}",
                    "",
                ]
            )
        lines.extend(
            [
                f"### Exchange {int(record['turn_index']) + 1}",
                "",
                "**Learner**",
                "",
                str(record["learner_message"]),
                "",
                "**Study OS teacher**",
                "",
                str(record["teacher_message"]),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_markdown(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(records), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an ungraded raw transcript from Luna student and Study OS teacher"
    )
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--student-cmd", required=True)
    parser.add_argument("--teacher-cmd", required=True)
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument(
        "--turns-per-problem", type=int, default=DEFAULT_TURNS_PER_PROBLEM
    )
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument(
        "--allow-short-run",
        action="store_true",
        help="development only: do not enforce 10 problems / 210 exchanges",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    corpus = load_corpus(args.corpus)
    student = JsonLineActor(args.student_cmd, label="student Luna")
    teacher = JsonLineActor(args.teacher_cmd, label="teacher Luna")
    try:
        records = run_transcript(
            corpus,
            student,
            teacher,
            scenario_ids=set(args.scenario) or None,
            turns_per_problem=args.turns_per_problem,
        )
    finally:
        student.close()
        teacher.close()

    if not args.allow_short_run:
        validate_run_size(records)
    write_jsonl(records, args.jsonl)
    write_markdown(records, args.markdown)

    problems = len({str(item["scenario_id"]) for item in records})
    print(
        f"captured raw transcript: {problems} problems / {len(records)} exchanges / "
        f"{len(records) * 2} visible messages"
    )
    print(f"jsonl: {args.jsonl}")
    print(f"markdown: {args.markdown}")
    print("no grading or comparison was performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
