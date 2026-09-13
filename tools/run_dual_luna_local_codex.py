#!/usr/bin/env python3
"""Run the raw dual-Luna transcript with two local resumable Codex sessions.

This is the preferred local execution path for PR #77. It deliberately avoids
hosted child tasks, OpenCode, inherited cloud sandboxes, and persistent actor
daemons. The script:

1. checks/migrates the local Study OS runtime if needed;
2. installs a test-only local Study OS MCP entry into Codex;
3. runs one Luna student and one Luna teacher as local Codex sessions;
4. verifies the teacher actually called the Study OS MCP on every turn;
5. checkpoints the raw transcript after every exchange;
6. resumes an interrupted transcript automatically on the next invocation.

No pedagogical grading or comparison happens here.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import run_dual_luna_transcript as raw


ROOT = Path(__file__).resolve().parents[1]
STUDY_OS_CLI = ROOT / "cli" / "study_os.py"
DEFAULT_MCP_NAME = "study-os-local-test"
DEFAULT_TURN_TIMEOUT_SECONDS = 240

RunFn = Callable[..., subprocess.CompletedProcess[str]]


def _run(
    runner: RunFn,
    args: list[str],
    *,
    cwd: Path = ROOT,
    input_text: str | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    return runner(
        args,
        input=input_text,
        text=True,
        encoding="utf-8",
        capture_output=True,
        cwd=cwd,
        check=False,
        timeout=timeout,
    )


def ensure_codex_available(codex_bin: str, *, runner: RunFn = subprocess.run) -> str:
    result = _run(runner, [codex_bin, "--version"], timeout=30)
    if result.returncode != 0:
        raise RuntimeError(
            "local Codex CLI is not runnable: "
            + ((result.stderr or result.stdout or "unknown error").strip())
        )
    return (result.stdout or result.stderr or "codex").strip()


def ensure_local_runtime(
    python_bin: str,
    *,
    runner: RunFn = subprocess.run,
) -> None:
    """Make the repo-local Study OS runtime usable before asking Luna to call it."""

    doctor_cmd = [python_bin, str(STUDY_OS_CLI), "doctor"]
    doctor = _run(runner, doctor_cmd, timeout=60)
    if doctor.returncode == 0:
        return

    migrate = _run(
        runner,
        [python_bin, str(STUDY_OS_CLI), "migrate"],
        timeout=120,
    )
    if migrate.returncode != 0:
        detail = (migrate.stderr or migrate.stdout or "migration failed").strip()
        raise RuntimeError(f"Study OS local runtime migration failed: {detail}")

    doctor = _run(runner, doctor_cmd, timeout=60)
    if doctor.returncode != 0:
        detail = (doctor.stderr or doctor.stdout or "doctor failed").strip()
        raise RuntimeError(f"Study OS local runtime is still unhealthy after migration: {detail}")


def configure_local_study_os_mcp(
    codex_bin: str,
    python_bin: str,
    mcp_name: str,
    *,
    runner: RunFn = subprocess.run,
) -> None:
    """Install an isolated test MCP entry that always points at this checkout."""

    # We own only this test-specific entry. Replacing it avoids stale paths after
    # branch/worktree moves without touching any normal user MCP configuration.
    _run(runner, [codex_bin, "mcp", "remove", mcp_name], timeout=30)
    add = _run(
        runner,
        [
            codex_bin,
            "mcp",
            "add",
            mcp_name,
            "--",
            python_bin,
            str(STUDY_OS_CLI),
            "mcp",
        ],
        timeout=60,
    )
    if add.returncode != 0:
        detail = (add.stderr or add.stdout or "MCP registration failed").strip()
        raise RuntimeError(f"unable to configure local Study OS MCP: {detail}")

    check = _run(
        runner,
        [codex_bin, "mcp", "get", mcp_name, "--json"],
        timeout=30,
    )
    if check.returncode != 0:
        detail = (check.stderr or check.stdout or "MCP lookup failed").strip()
        raise RuntimeError(f"Codex cannot read the configured Study OS MCP: {detail}")


class CodexCliActor:
    """One local Codex conversation per role, reset for each DSA scenario."""

    def __init__(
        self,
        *,
        role: str,
        codex_bin: str = "codex",
        model: str | None = None,
        mcp_name: str = DEFAULT_MCP_NAME,
        cwd: Path = ROOT,
        full_access: bool = True,
        timeout_seconds: int = DEFAULT_TURN_TIMEOUT_SECONDS,
        runner: RunFn = subprocess.run,
    ) -> None:
        if role not in {"student", "teacher"}:
            raise ValueError("role must be student or teacher")
        self.role = role
        self.codex_bin = codex_bin
        self.model = model
        self.mcp_name = mcp_name
        self.cwd = cwd
        self.full_access = full_access
        self.timeout_seconds = timeout_seconds
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
            f"On EVERY learner turn you MUST call the MCP server named {self.mcp_name!r} "
            "and use the Study OS problem-solving tools. Do not answer from your own "
            "standalone tutoring knowledge. If Study OS reports that a problem is unknown "
            "or needs compilation, preserve that real system behavior instead of "
            "improvising a lesson. Do not edit the repository or do unrelated coding work. "
            "Return only the final learner-visible response after using Study OS."
        )

    def _prompt(self, payload: dict[str, Any]) -> str:
        return (
            self._role_contract()
            + "\n\nCurrent turn payload:\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        )

    def _command(self, *, resume_id: str | None) -> list[str]:
        command = [self.codex_bin, "exec", "--json", "--color", "never"]
        if self.model:
            command.extend(["--model", self.model])
        if self.full_access:
            # In non-interactive `codex exec`, this is the reliable way to avoid
            # MCP approval pauses. This harness is explicitly local and disposable.
            command.append("--dangerously-bypass-approvals-and-sandbox")
        if resume_id:
            command.extend(["resume", resume_id, "-"])
        else:
            command.append("-")
        return command

    def _parse_events(self, stdout: str) -> tuple[str | None, str, bool, list[str]]:
        thread_id: str | None = None
        messages: list[str] = []
        study_os_call_completed = False
        mcp_errors: list[str] = []

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
            if not isinstance(item, dict):
                continue
            if item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    messages.append(text.strip())
                continue
            if item.get("type") != "mcp_tool_call":
                continue
            if str(item.get("server", "")) != self.mcp_name:
                continue
            status = str(item.get("status", ""))
            if status == "completed":
                study_os_call_completed = True
            elif status == "failed":
                error = item.get("error")
                if isinstance(error, dict):
                    message = error.get("message")
                    if isinstance(message, str) and message:
                        mcp_errors.append(message)
                if not mcp_errors:
                    mcp_errors.append(f"{item.get('tool', 'unknown tool')} failed")

        if not messages:
            raise RuntimeError("local Codex turn returned no agent_message")
        return thread_id, messages[-1], study_os_call_completed, mcp_errors

    def _invoke(self, payload: dict[str, Any], *, resume_id: str | None) -> tuple[str, str | None]:
        try:
            result = _run(
                self._runner,
                self._command(resume_id=resume_id),
                cwd=self.cwd,
                input_text=self._prompt(payload),
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"local Codex {self.role} turn timed out after {self.timeout_seconds}s"
            ) from exc

        if result.returncode != 0:
            stderr = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                f"local Codex {self.role} turn failed with exit {result.returncode}: {stderr}"
            )

        observed_thread_id, message, study_os_call_completed, mcp_errors = self._parse_events(
            result.stdout or ""
        )
        if self.role == "teacher" and not study_os_call_completed:
            detail = "; ".join(mcp_errors) if mcp_errors else "no Study OS MCP call completed"
            raise RuntimeError(f"teacher did not complete the required Study OS MCP call: {detail}")
        return message, observed_thread_id

    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        scenario_id = str(payload.get("scenario_id", ""))
        if not scenario_id:
            raise RuntimeError("dual-Luna payload is missing scenario_id")

        if scenario_id != self._scenario_id:
            self._scenario_id = scenario_id
            self._thread_id = None

        # First try the persistent session. If Codex resume is stale, hangs, or
        # silently changes thread, restart the role locally. The payload contains
        # the entire current-problem conversation, so the logical dialogue survives.
        first_resume_id = self._thread_id
        last_error: Exception | None = None
        for attempt in range(2):
            resume_id = first_resume_id if attempt == 0 else None
            try:
                message, observed_thread_id = self._invoke(payload, resume_id=resume_id)
            except RuntimeError as exc:
                last_error = exc
                self._thread_id = None
                continue

            if observed_thread_id is None:
                if resume_id is None:
                    last_error = RuntimeError("new local Codex session did not report thread_id")
                    self._thread_id = None
                    continue
                observed_thread_id = resume_id

            # A stale/missing resume can cause Codex to create a fresh thread. That is
            # safe here because the complete scenario conversation is in the payload.
            self._thread_id = observed_thread_id
            key = "student_message" if self.role == "student" else "teacher_message"
            return {key: message}

        if last_error is not None:
            raise last_error
        raise RuntimeError(f"local Codex {self.role} turn failed without a diagnostic")

    def close(self) -> None:
        return None


def _filter_existing_records(
    records: list[dict[str, Any]],
    scenario_ids: set[str] | None,
) -> list[dict[str, Any]]:
    if scenario_ids is None:
        return records
    return [item for item in records if str(item.get("scenario_id")) in scenario_ids]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the ungraded 210-exchange dual-Luna transcript with two local "
            "Codex sessions; no hosted child tasks or manual approval loop"
        )
    )
    parser.add_argument("--corpus", type=Path, default=raw.DEFAULT_CORPUS)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--model", default=None)
    parser.add_argument("--mcp-name", default=DEFAULT_MCP_NAME)
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument(
        "--turns-per-problem", type=int, default=raw.DEFAULT_TURNS_PER_PROBLEM
    )
    parser.add_argument("--jsonl", type=Path, default=raw.DEFAULT_JSONL)
    parser.add_argument("--markdown", type=Path, default=raw.DEFAULT_MARKDOWN)
    parser.add_argument(
        "--turn-timeout-seconds",
        type=int,
        default=DEFAULT_TURN_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="ignore any existing transcript instead of resuming it",
    )
    parser.add_argument(
        "--skip-local-setup",
        action="store_true",
        help="do not doctor/migrate Study OS or install the test MCP entry",
    )
    parser.add_argument(
        "--keep-codex-sandbox",
        action="store_true",
        help=(
            "keep the normal Codex sandbox/approval boundary; by default this local test "
            "uses --dangerously-bypass-approvals-and-sandbox to avoid MCP approval pauses"
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
    scenario_ids = set(args.scenario) or None

    if not args.skip_local_setup:
        version = ensure_codex_available(args.codex_bin)
        print(f"local Codex: {version}")
        ensure_local_runtime(args.python_bin)
        configure_local_study_os_mcp(
            args.codex_bin,
            args.python_bin,
            args.mcp_name,
        )
        print(f"Study OS MCP ready: {args.mcp_name}")

    if args.fresh:
        existing_records: list[dict[str, Any]] = []
    else:
        existing_records = _filter_existing_records(
            raw.load_jsonl(args.jsonl),
            scenario_ids,
        )
        if existing_records:
            print(f"resuming raw transcript from {len(existing_records)} captured exchanges")

    full_access = not args.keep_codex_sandbox
    student = CodexCliActor(
        role="student",
        codex_bin=args.codex_bin,
        model=args.model,
        mcp_name=args.mcp_name,
        full_access=full_access,
        timeout_seconds=args.turn_timeout_seconds,
    )
    teacher = CodexCliActor(
        role="teacher",
        codex_bin=args.codex_bin,
        model=args.model,
        mcp_name=args.mcp_name,
        full_access=full_access,
        timeout_seconds=args.turn_timeout_seconds,
    )

    def checkpoint(record: dict[str, Any], records: list[dict[str, Any]]) -> None:
        raw.write_jsonl(records, args.jsonl)
        raw.write_markdown(records, args.markdown)
        print(
            f"captured {record['scenario_id']} exchange {int(record['turn_index']) + 1}; "
            f"total={len(records)}"
        )

    records = raw.run_transcript(
        corpus,
        student,
        teacher,
        scenario_ids=scenario_ids,
        turns_per_problem=args.turns_per_problem,
        existing_records=existing_records,
        on_record=checkpoint,
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
    print("no hosted child tasks; no pedagogical grading or comparison was performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
