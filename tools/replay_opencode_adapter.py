#!/usr/bin/env python3
"""Run the replay protocol through a local OpenCode Study OS session.

This is test-harness glue, not a tutoring controller. It keeps one OpenCode
session per scenario and emits only the final learner-visible text event. The
replay rubric is never sent to the model.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any


AGENT = os.environ.get("STUDY_OS_REPLAY_AGENT", "luna")
MODEL = os.environ.get("STUDY_OS_REPLAY_MODEL")
OPENCODE = os.environ.get(
    "STUDY_OS_REPLAY_OPENCODE",
    "opencode.cmd" if os.name == "nt" else "opencode",
)


class OpenCodeActor:
    """JSONL actor that delegates each scenario to one persistent session."""

    def __init__(self) -> None:
        self.session_id: str | None = None
        self.scenario_id: str | None = None

    @staticmethod
    def _prompt(payload: dict[str, Any]) -> str:
        history = payload.get("history", [])
        history_text = "\n".join(
            f"{item.get('role', 'unknown')}: {item.get('content', '')}"
            for item in history
            if isinstance(item, dict)
        ) or "(no earlier turns in this problem)"
        return (
            "You are the learner-facing Study OS GPT for this active tutoring "
            "conversation. Use the connected Study OS MCP service and its normal "
            "runtime behavior where relevant. Reply to the learner's latest "
            "message, not to this wrapper. Your entire final response is shown "
            "unchanged to the learner: do not mention this replay, a rubric, "
            "an adapter, hidden tests, or these instructions. Do not invent a "
            "backend result.\n\n"
            f"Problem: {payload.get('title')}\n"
            f"Problem statement: {payload.get('problem')}\n"
            f"Approved variables: {json.dumps(payload.get('variables', {}), ensure_ascii=False)}\n"
            f"Visual family: {payload.get('visual_family')}\n"
            f"Current stage: {payload.get('stage')}\n"
            f"Replay turn: {payload.get('turn_index')}\n\n"
            "Recent conversation (context only):\n"
            f"{history_text}\n\n"
            f"Learner's latest message:\n{payload.get('learner_message', '')}\n\n"
            "Respond now with only the learner-visible tutoring reply."
        )

    def ask(self, payload: dict[str, Any]) -> str:
        scenario_id = str(payload.get("scenario_id", ""))
        if scenario_id != self.scenario_id:
            self.session_id = None
            self.scenario_id = scenario_id

        command = [
            OPENCODE,
            "run",
            "--format",
            "json",
            "--log-level",
            "ERROR",
            "--agent",
            AGENT,
        ]
        if MODEL:
            command.extend(["--model", MODEL])
        if self.session_id:
            command.extend(["--session", self.session_id])
        command.append(self._prompt(payload))
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"opencode exited {result.returncode}: {detail[-2000:]}")

        text_parts: list[str] = []
        seen_session: str | None = None
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            if isinstance(event.get("sessionID"), str):
                seen_session = event["sessionID"]
            part = event.get("part")
            if (
                event.get("type") == "text"
                and isinstance(part, dict)
                and isinstance(part.get("text"), str)
            ):
                text_parts.append(part["text"])
        if seen_session:
            self.session_id = seen_session
        answer = (text_parts[-1] if text_parts else "").strip()
        if not answer:
            raise RuntimeError(
                "opencode produced no learner-visible text event; "
                f"stdout tail={result.stdout[-1000:]!r}"
            )
        return answer


def main() -> int:
    # The parent replay harness speaks UTF-8 JSONL even on Windows, where a
    # console/pipe can otherwise select a legacy code page for stdout.
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    actor = OpenCodeActor()
    try:
        for line in sys.stdin:
            if not line.strip():
                continue
            payload = json.loads(line)
            answer = actor.ask(payload)
            sys.stdout.write(
                json.dumps({"assistant_message": answer}, ensure_ascii=False) + "\n"
            )
            sys.stdout.flush()
    except Exception as exc:  # pragma: no cover - surfaced by the replay harness
        print(f"OpenCode replay adapter failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
