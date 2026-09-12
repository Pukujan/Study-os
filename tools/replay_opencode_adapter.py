#!/usr/bin/env python3
"""Run truthful learner-visible replay turns through Luna and Study OS MCP.

The adapter deliberately preserves two separate pieces of evidence for every turn:
1. the learner-visible markdown returned by the Study OS tool; and
2. Luna's final completed assistant text after the tool call.

The replay must never substitute (1) for (2).  Their equality is an acceptance
condition when the active presentation contract requires verbatim rendering.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


AGENT = os.environ.get("STUDY_OS_REPLAY_AGENT", "luna")
OPENCODE_URL = os.environ.get(
    "STUDY_OS_REPLAY_OPENCODE_URL", "http://127.0.0.1:4097"
)
MCP_URL = os.environ.get("STUDY_OS_REPLAY_MCP_URL", "http://127.0.0.1:18766/mcp")
TIMEOUT = float(os.environ.get("STUDY_OS_REPLAY_TIMEOUT", "300"))


class JsonHttpClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> Any:
        body = (
            json.dumps(payload, ensure_ascii=False).encode("utf-8")
            if payload is not None
            else None
        )
        request = Request(
            self.base_url + path,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method=method,
        )
        try:
            with urlopen(request, timeout=TIMEOUT) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            detail = getattr(exc, "read", lambda: b"")()
            if isinstance(detail, bytes):
                detail = detail.decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP request failed: {detail or exc}") from exc
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("HTTP endpoint returned invalid JSON") from exc

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        value = self.request("POST", path, payload)
        if not isinstance(value, dict):
            raise RuntimeError("HTTP POST endpoint response must be an object")
        return value


class McpClient:
    def __init__(self, url: str) -> None:
        self.client = JsonHttpClient(url.rsplit("/", 1)[0])
        self.path = "/" + url.rsplit("/", 1)[1]
        self.request_id = 0

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.request_id += 1
        result = self.client.post(
            self.path,
            {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            },
        )
        payload = result.get("result", {})
        content = payload.get("content", []) if isinstance(payload, dict) else []
        text = content[0].get("text") if content and isinstance(content[0], dict) else None
        if not isinstance(text, str):
            raise RuntimeError(f"MCP {name} returned no text result")
        value = json.loads(text)
        if not isinstance(value, dict):
            raise RuntimeError(f"MCP {name} result was not an object")
        if "error" in value:
            raise RuntimeError(f"MCP {name} failed: {value['error']}")
        return value


class LunaActor:
    """JSONL actor backed by the normal Luna -> Study OS MCP product path."""

    def __init__(self) -> None:
        self.opencode = JsonHttpClient(OPENCODE_URL)
        self.mcp = McpClient(MCP_URL)
        self.session_id: str | None = None
        self.scenario_id: str | None = None
        self.problem_run_id: str | None = None
        self.subject_id: str | None = None
        self.current_turn: dict[str, Any] | None = None

    @staticmethod
    def _markdown_from_bundle(bundle: dict[str, Any]) -> str:
        turns = bundle.get("turns", [])
        if not turns or not isinstance(turns[-1], dict):
            return ""
        return str(turns[-1].get("learner_visible_markdown", ""))

    @staticmethod
    def _step_from_bundle(bundle: dict[str, Any] | None) -> str | None:
        if not bundle:
            return None
        turns = bundle.get("turns", [])
        if not turns or not isinstance(turns[-1], dict):
            return None
        value = turns[-1].get("canonical_step_id")
        return str(value) if value is not None else None

    @staticmethod
    def _assistant_text(message: dict[str, Any]) -> str:
        chunks: list[str] = []
        for part in message.get("parts", []):
            if not isinstance(part, dict) or part.get("type") != "text":
                continue
            text = part.get("text")
            if isinstance(text, str):
                chunks.append(text)
        return "".join(chunks)

    @staticmethod
    def _tool_name(part: dict[str, Any]) -> str | None:
        for candidate in (
            part.get("tool"),
            part.get("name"),
            part.get("tool_name"),
        ):
            if isinstance(candidate, str) and candidate:
                return candidate
        state = part.get("state")
        if isinstance(state, dict):
            for key in ("tool", "name", "tool_name"):
                candidate = state.get(key)
                if isinstance(candidate, str) and candidate:
                    return candidate
        return None

    @classmethod
    def _tool_snapshots(cls, response: dict[str, Any]) -> list[dict[str, Any]]:
        snapshots: list[dict[str, Any]] = []
        for part in response.get("parts", []):
            if not isinstance(part, dict) or part.get("type") != "tool":
                continue
            state = part.get("state", {})
            raw = state.get("output") if isinstance(state, dict) else None
            if not isinstance(raw, str):
                continue
            try:
                output = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(output, dict) or not isinstance(output.get("turn"), dict):
                continue
            bundle = output["turn"]
            snapshots.append(
                {
                    "tool_name": cls._tool_name(part),
                    "backend_message": cls._markdown_from_bundle(bundle),
                    "backend_step": cls._step_from_bundle(bundle),
                }
            )
        return snapshots

    def _prepare_run(self, payload: dict[str, Any]) -> None:
        scenario_id = str(payload["scenario_id"])
        self.subject_id = f"replay-{scenario_id}"
        session = self.mcp.call(
            "start_session",
            {
                "idempotency_key": f"{self.subject_id}-session",
                "subject_id": self.subject_id,
                "project_id": "study-os",
                "domain_id": "dsa",
                "source_client": "dsa-conversation-replay",
            },
        )
        runtime_session_id = session["session_id"]
        resolution = self.mcp.call(
            "resolve_problem",
            {"problem_text": payload["problem"], "domain": "dsa"},
        )
        if resolution.get("status") != "known":
            raise RuntimeError(f"replay problem was not known: {resolution}")
        started = self.mcp.call(
            "start_problem",
            {
                "idempotency_key": f"{self.subject_id}-problem",
                "session_id": runtime_session_id,
                "subject_id": self.subject_id,
                "canonical_problem_id": resolution["canonical_problem_id"],
            },
        )
        self.problem_run_id = str(started["problem_run_id"])
        self.current_turn = started.get("turn")

    def _ensure_run(self, payload: dict[str, Any]) -> None:
        scenario_id = str(payload.get("scenario_id", ""))
        if not scenario_id:
            raise RuntimeError("replay payload is missing scenario_id")
        if scenario_id != self.scenario_id:
            self.scenario_id = scenario_id
            self._prepare_run(payload)

    def state(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return actual backend state without asking Luna to produce a turn."""
        self._ensure_run(payload)
        return {
            "backend_step": self._step_from_bundle(self.current_turn),
            "backend_message": self._markdown_from_bundle(self.current_turn or {}),
            "problem_run_id": self.problem_run_id,
        }

    @staticmethod
    def _prompt(
        payload: dict[str, Any],
        run_id: str,
        subject_id: str,
        turn: dict[str, Any] | None,
    ) -> str:
        history = payload.get("history", [])
        history_text = "\n".join(
            f"{item.get('role', 'unknown')}: {item.get('content', '')}"
            for item in history
            if isinstance(item, dict)
        ) or "(no earlier turns in this problem)"
        turn_id = turn.get("response_turn_id") if turn else None
        if not turn_id and turn and turn.get("turns"):
            turn_id = turn["turns"][-1].get("turn_id")
        visible = LunaActor._markdown_from_bundle(turn or {})
        current = turn.get("turns", [])[-1] if turn and turn.get("turns") else {}
        allowed_actions = current.get("allowed_actions", []) if isinstance(current, dict) else []
        step_id = current.get("canonical_step_id") if isinstance(current, dict) else None
        return (
            "You are Luna handling exactly one bounded learner turn in an "
            "already-active Study OS PIR run. Use the connected Study OS MCP "
            "tool for this turn. Do not create a second run. If the learner is "
            "answering the current probe, call submit_problem_response with the "
            "learner's exact response. If they request why, clarification, or "
            "more detail, call request_problem_expansion only when the current "
            "probe supports that expansion. Otherwise call get_problem_turn. "
            "After a successful tool returns, your final text must equal its "
            "`turn.turns[-1].learner_visible_markdown` exactly, copied unchanged. "
            "Do not author, summarize, or reformat it; do not mention this replay "
            "or hidden checks. If a tool returns a validation error, do not retry "
            "it and do not use any file, shell, patch, or other non-Study-OS tool; "
            "call get_problem_turn once and copy that backend text.\n\n"
            f"problem_run_id: {run_id}\nsubject_id: {subject_id}\n"
            f"current_turn_id: {turn_id}\ncurrent_backend_step: {step_id}\n"
            f"current_backend_allowed_actions: {json.dumps(allowed_actions)}\n"
            f"current_backend_text:\n{visible}\n\n"
            f"Problem: {payload.get('title')}\n"
            f"Problem statement: {payload.get('problem')}\n"
            f"Approved variables: {json.dumps(payload.get('variables', {}), ensure_ascii=False)}\n"
            f"Learner's latest message:\n{payload.get('learner_message', '')}\n\n"
            f"Recent conversation:\n{history_text}\n\n"
            "Return only the exact learner-visible backend text."
        )

    def _create_luna_session(self, scenario_id: str, turn_index: int) -> None:
        result = self.opencode.post(
            "/session",
            {"title": f"Study OS replay: {scenario_id} turn {turn_index}"},
        )
        self.session_id = str(result["id"])

    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._ensure_run(payload)
        if not self.problem_run_id or not self.subject_id:
            raise RuntimeError("Luna replay state is not initialized")

        scenario_id = str(payload["scenario_id"])
        turn_index = int(payload.get("turn_index", 0))
        backend_step_before = self._step_from_bundle(self.current_turn)
        self._create_luna_session(scenario_id, turn_index)
        if not self.session_id:
            raise RuntimeError("Luna session was not created")

        # Use the synchronous message endpoint.  It returns only after Luna has
        # completed the assistant response, so the replay can inspect what the
        # learner would actually see rather than aborting at the first tool result.
        response = self.opencode.post(
            f"/session/{self.session_id}/message",
            {
                "agent": AGENT,
                "tools": {
                    "study-os-replay_get_problem_turn": True,
                    "study-os-replay_submit_problem_response": True,
                    "study-os-replay_request_problem_expansion": True,
                },
                "parts": [
                    {
                        "type": "text",
                        "text": self._prompt(
                            payload,
                            self.problem_run_id,
                            self.subject_id,
                            self.current_turn,
                        ),
                    }
                ],
            },
        )
        info = response.get("info", {})
        if isinstance(info, dict):
            role = info.get("role")
            response_agent = info.get("agent")
            if role not in (None, "assistant"):
                raise RuntimeError(f"OpenCode returned non-assistant response: {info!r}")
            if response_agent not in (None, AGENT):
                raise RuntimeError(
                    f"response was not produced by {AGENT!r}: {response_agent!r}"
                )

        snapshots = self._tool_snapshots(response)
        snapshots = [item for item in snapshots if item["backend_message"]]
        if not snapshots:
            raise RuntimeError("Luna completed without a Study OS learner-visible tool result")
        authoritative = snapshots[-1]
        assistant_message = self._assistant_text(response)
        if not assistant_message:
            raise RuntimeError("Luna completed without final learner-visible text")

        refreshed = self.mcp.call(
            "get_problem_turn",
            {"problem_run_id": self.problem_run_id, "subject_id": self.subject_id},
        )
        self.current_turn = refreshed.get("turn")
        backend_step_after = self._step_from_bundle(self.current_turn)

        return {
            "assistant_message": assistant_message,
            "backend_message": authoritative["backend_message"],
            "backend_step_before": backend_step_before,
            "backend_step_after": backend_step_after,
            "tool_backend_step": authoritative["backend_step"],
            "tool_name": authoritative["tool_name"],
            "verbatim_match": assistant_message == authoritative["backend_message"],
        }


def main() -> int:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    actor = LunaActor()
    try:
        for line in sys.stdin:
            if not line.strip():
                continue
            payload = json.loads(line)
            if payload.get("type") == "study_os_replay_state":
                result = actor.state(payload)
            else:
                result = actor.ask(payload)
            sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    except Exception as exc:  # pragma: no cover - surfaced by replay harness
        print(f"Luna replay adapter failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
