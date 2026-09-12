#!/usr/bin/env python3
"""Run replay turns through isolated Luna sessions and Study OS MCP."""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


AGENT = os.environ.get("STUDY_OS_REPLAY_AGENT", "luna")
MODEL = os.environ.get("STUDY_OS_REPLAY_MODEL")
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
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("HTTP endpoint returned invalid JSON") from exc
        if not isinstance(value, dict):
            return value
        return value

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        value = self.request("POST", path, payload)
        if not isinstance(value, dict):
            raise RuntimeError("HTTP POST endpoint response must be an object")
        return value

    def post_async(self, path: str, payload: dict[str, Any]) -> None:
        self.request("POST", path, payload)

    def get(self, path: str) -> Any:
        return self.request("GET", path)


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
    """JSONL actor with one direct Luna session for each replay scenario."""

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

    @staticmethod
    def _prompt(payload: dict[str, Any], run_id: str, subject_id: str, turn: dict[str, Any] | None) -> str:
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
        return (
            "You are Luna handling exactly one bounded learner turn in an "
            "already-active Study OS PIR run. Use the connected Study OS MCP "
            "tool for this turn. Do not create a second run. If the learner is "
            "answering the current probe, call submit_problem_response with the "
            "learner's exact response. If they request why, clarification, or "
            "more detail, call request_problem_expansion only when the current "
            "probe supports that expansion. Otherwise call get_problem_turn. "
            "After the tool returns, "
            "your final text must equal its `turn.turns[-1].learner_visible_markdown` "
            "exactly, copied unchanged. Do not author, summarize, or reformat it; "
            "do not mention this replay or hidden checks.\n\n"
            f"problem_run_id: {run_id}\nsubject_id: {subject_id}\n"
            f"current_turn_id: {turn_id}\ncurrent_backend_text:\n{visible}\n\n"
            f"Problem: {payload.get('title')}\n"
            f"Problem statement: {payload.get('problem')}\n"
            f"Approved variables: {json.dumps(payload.get('variables', {}), ensure_ascii=False)}\n"
            f"Current stage: {payload.get('stage')}\n"
            f"Learner's latest message:\n{payload.get('learner_message', '')}\n\n"
            f"Recent conversation:\n{history_text}\n\n"
            "Return only the exact learner-visible backend text."
        )

    @staticmethod
    def _tool_backend_text(response: dict[str, Any]) -> str:
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
            if isinstance(output, dict) and isinstance(output.get("turn"), dict):
                return LunaActor._markdown_from_bundle(output["turn"])
        return ""

    def _create_luna_session(self, scenario_id: str, turn_index: int) -> None:
        result = self.opencode.post(
            "/session",
            {
                "title": f"Study OS replay: {scenario_id} turn {turn_index}",
                "agent": AGENT,
            },
        )
        if result.get("agent") != AGENT:
            raise RuntimeError(
                f"headless server created {result.get('agent')!r}, expected {AGENT!r}"
            )
        self.session_id = str(result["id"])

    def _wait_for_backend_text(self, known_message_ids: set[str]) -> str:
        if not self.session_id:
            raise RuntimeError("Luna session is not initialized")
        deadline = time.monotonic() + TIMEOUT
        while time.monotonic() < deadline:
            messages = self.opencode.get(
                f"/session/{self.session_id}/message?limit=50"
            )
            if not isinstance(messages, list):
                raise RuntimeError("OpenCode message list was not an array")
            for message in messages:
                if not isinstance(message, dict):
                    continue
                info = message.get("info", {})
                message_id = info.get("id") if isinstance(info, dict) else None
                if message_id in known_message_ids:
                    continue
                if not isinstance(info, dict) or info.get("role") != "assistant":
                    continue
                if info.get("agent") != AGENT:
                    raise RuntimeError(f"response was not produced by {AGENT!r}: {info!r}")
                backend_text = self._tool_backend_text(message)
                if backend_text:
                    # The backend result is authoritative. Stop any later free-form
                    # continuation before it can rewrite the learner-visible text.
                    try:
                        self.opencode.post(f"/session/{self.session_id}/abort", {})
                    except RuntimeError:
                        pass
                    return backend_text
            time.sleep(0.5)
        try:
            self.opencode.post(f"/session/{self.session_id}/abort", {})
        except RuntimeError:
            pass
        raise RuntimeError("Luna did not return a backend learner-visible turn")

    def ask(self, payload: dict[str, Any]) -> str:
        scenario_id = str(payload.get("scenario_id", ""))
        if scenario_id != self.scenario_id:
            self.scenario_id = scenario_id
            self._prepare_run(payload)
        if not self.problem_run_id or not self.subject_id:
            raise RuntimeError("Luna replay state is not initialized")
        self._create_luna_session(scenario_id, int(payload.get("turn_index", 0)))
        known_messages = self.opencode.get(
            f"/session/{self.session_id}/message?limit=50"
        )
        known_message_ids = {
            message.get("info", {}).get("id")
            for message in known_messages
            if isinstance(message, dict) and isinstance(message.get("info"), dict)
        }
        self.opencode.post_async(
            f"/session/{self.session_id}/prompt_async",
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
        answer = self._wait_for_backend_text(known_message_ids)
        refreshed = self.mcp.call(
            "get_problem_turn",
            {"problem_run_id": self.problem_run_id, "subject_id": self.subject_id},
        )
        self.current_turn = refreshed.get("turn")
        if not answer:
            raise RuntimeError("Luna response contained no learner-visible text")
        return answer


def main() -> int:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    actor = LunaActor()
    try:
        for line in sys.stdin:
            if not line.strip():
                continue
            answer = actor.ask(json.loads(line))
            sys.stdout.write(
                json.dumps({"assistant_message": answer}, ensure_ascii=False) + "\n"
            )
            sys.stdout.flush()
    except Exception as exc:  # pragma: no cover - surfaced by replay harness
        print(f"Luna replay adapter failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
