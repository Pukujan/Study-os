#!/usr/bin/env python3
"""Run the raw dual-Luna transcript using two resumable local Codex sessions.

This is the low-friction local execution path. It does not create hosted child
threads and it does not require persistent JSONL actor subprocesses. Each Luna
role is a normal local Codex CLI session that is resumed turn-by-turn.

By default Codex is launched with --dangerously-bypass-approvals-and-sandbox so
local Study OS MCP calls do not pause for sandbox/approval prompts. Use
--keep-codex-sandbox to opt back into the local Codex sandbox.

The runner performs no grading or comparison. Its only output is the raw
learner/teacher transcript.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

import run_dual_luna_transcript as raw


ROOT = Path(__file__).resolve().parents[1]

RunFn = Callable[..., subprocess.CompletedProcess[str]]


class CodexCliActor:
    """One resumable local Codex conversation per DSA scenario."""

    def __init__(
        self,
        *,
        role: str,
        codex_bin: str = "codex",
        model: str | None = None,
        cwd: Path = ROOT,
        full_access: bool = True,
        runner: RunFn = subprocess.run,
    ) -> None:
        if role not in {"student", "teacher"}:
            raise ValueError("role must be student or teacher")
        self.role = role
        self.codex_bin = codex_bin
        self.model = model
        self.cwd = cwd
        self.full_access = full_access
        self._runner = runner
        self._scenario_id: str | None = None
        self._thread_id: str | None = None

    def _role_contract(self) -> str:
        if self.role == "student":
            return (
                "You are Luna acting only as a realistic beginner learner in a DSA "
                "conversation. Do not inspect the repository, call Study OS, or use tools "
                "to solve the problem. React naturally to the teacher. Follow the supplied "
                "learner_signal as behavioral guidance. Return exactly one short learner "
                "utterance and nothing else."
            )
        return (
            "You are Luna acting as the learner-facing Study OS teacher in a product test. "
            "For every learner turn, use the configured Study OS MCP/product path rather "
            "than answering as a standalone tutor. Do not edit the repository or do "
            "unrelated coding work. Return only the final learner-visible teaching response "
            "that the learner would actually see."
        )

    def _prompt(self, payload: dict[str, Any]) -> str:
        return (
            self._role_contract()
            + "\n\nCurrent turn payload:\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        )

    def _command(self, *, resume_id: str | None) -> list[str]:
        command = [self.codex_bin, "exec", "--json"]
        if self.model:
            command.extend(["--model", self.model])
        if self.full_access:
            command.append("--dangerously-bypass-approvals-and-sandbox")
        if resume_id:
            command.extend(["resume", resume_id, "-"])
        else:
            command.append("-")
        return command

    @staticmethod
    def _parse_events(stdout: str) -> tuple[str | None, str]:
        thread_id: str | None = None
        messages: list[str] = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            if event.get("type") == "thread.started":
                value = event.get("thread_id")
                if isinstance(value, str) and value:
                    thread_id = value
                continue
            if event.get("type") != "item.completed":
                continue
            item = event.get("item")
            if not isinstance(item, dict) or item.get("type") != "agent_message":
                continue
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                messages.append(text.strip())
        if not messages:
            raise RuntimeError("local Codex turn returned no agent_message")
        return thread_id, messages[-1]

    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        scenario_id = str(payload.get("scenario_id", ""))
        if not scenario_id:
            raise RuntimeError("dual-Luna payload is missing scenario_id")

        if scenario_id != self._scenario_id:
            self._scenario_id = scenario_id
            self._thread_id = None

        resume_id = self._thread_id
        result = self._runner(
            self._command(resume_id=resume_id),
            input=self._prompt(payload),
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=self.cwd,
            check=False,
        )
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            raise RuntimeError(
                f"local Codex {self.role} turn failed with exit {result.returncode}: {stderr}"
            )

        observed_thread_id, message = self._parse_events(result.stdout or "")
        if resume_id is None:
            if observed_thread_id is None:
                raise RuntimeError("new local Codex session did not report thread_id")
            self._thread_id = observed_thread_id
        elif observed_thread_id is not None and observed_thread_id != resume_id:
            raise RuntimeError(
                "Codex resume returned a different thread id; refusing to silently start "
                "a fresh conversation"
            )

        key = "student_message" if self.role == "student" else "teacher_message"
        return {key: message}

    def close(self) -> None:
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the ungraded 210-exchange dual-Luna transcript with two local "
            "resumable Codex sessions and no hosted child tasks"
        )
    )
    parser.add_argument("--corpus", type=Path, default=raw.DEFAULT_CORPUS)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--model", default=None)
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument(
        "--turns-per-problem", type=int, default=raw.DEFAULT_TURNS_PER_PROBLEM
    )
    parser.add_argument("--jsonl", type=Path, default=raw.DEFAULT_JSONL)
    parser.add_argument("--markdown", type=Path, default=raw.DEFAULT_MARKDOWN)
    parser.add_argument(
        "--keep-codex-sandbox",
        action="store_true",
        help=(
            "keep the normal Codex sandbox/approval boundary; by default this local test "
            "uses --dangerously-bypass-approvals-and-sandbox to avoid manual pauses"
        ),
    )
    parser.add_argument(
        "--allow-short-run",
        action="store_true",
        help="development only: do not enforce 10 problems / 210 exchanges",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    corpus = raw.load_corpus(args.corpus)
    full_access = not args.keep_codex_sandbox
    student = CodexCliActor(
        role="student",
        codex_bin=args.codex_bin,
        model=args.model,
        full_access=full_access,
    )
    teacher = CodexCliActor(
        role="teacher",
        codex_bin=args.codex_bin,
        model=args.model,
        full_access=full_access,
    )
    records = raw.run_transcript(
        corpus,
        student,
        teacher,
        scenario_ids=set(args.scenario) or None,
        turns_per_problem=args.turns_per_problem,
    )

    if not args.allow_short_run:
        raw.validate_run_size(records)
    raw.write_jsonl(records, args.jsonl)
    raw.write_markdown(records, args.markdown)

    problems = len({str(item["scenario_id"]) for item in records})
    print(
        f"captured raw transcript: {problems} problems / {len(records)} exchanges / "
        f"{len(records) * 2} visible messages"
    )
    print(f"jsonl: {args.jsonl}")
    print(f"markdown: {args.markdown}")
    print("no hosted child tasks; no grading or comparison was performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
