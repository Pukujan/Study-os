"""Model transports: hosted Jev via the OpenRouter Decisions API (tier 2) and InferHub
OpenAI-compatible chat completions (tier 3). Keys come from the environment only and are
never logged. Stubs with the same interface serve CI and offline evals."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

# Route floor prices per 1M tokens (docs/webapp/LLM_ROUTE.md §3), used when a response has no cost.
ROUTE_PRICES = {
    "cb/glm-5.3": (0.0378, 0.1188),
    "cb/deepseek-v4.1-flash": (0.0001, 0.0006),
}


class ModelUnavailable(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class DecisionResponse:
    model_version: str
    answers: dict[str, Any]
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0


@dataclass
class LLMResponse:
    route: str
    args: dict[str, Any] | None
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    attempts: list[dict[str, Any]] = field(default_factory=list)


class DecisionTransport(Protocol):
    model: str

    def decide(self, state: str, questions: dict[str, Any]) -> DecisionResponse: ...


class LLMTransport(Protocol):
    def complete(
        self, routes: tuple[str, ...], messages: list[dict[str, str]], tool: dict[str, Any], max_tokens: int = 700
    ) -> LLMResponse: ...


class OpenRouterJev:
    def __init__(self, api_key: str, url: str, model: str, timeout: float = 8.0) -> None:
        self._key = api_key
        self.url = url
        self.model = model
        self.timeout = timeout

    def decide(self, state: str, questions: dict[str, Any]) -> DecisionResponse:
        started = time.monotonic()
        try:
            resp = httpx.post(
                self.url,
                headers={"Authorization": f"Bearer {self._key}"},
                json={"model": self.model, "state": state, "questions": questions},
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise ModelUnavailable(f"transport:{type(exc).__name__}") from exc
        latency = int((time.monotonic() - started) * 1000)
        if resp.status_code != 200:
            raise ModelUnavailable(f"http:{resp.status_code}")
        body = resp.json()
        usage = body.get("usage") or {}
        return DecisionResponse(
            model_version=str(body.get("model") or self.model),
            answers=body.get("answers") or {},
            tokens_in=int(usage.get("input_tokens") or 0),
            tokens_out=int(usage.get("output_tokens") or 0),
            cost_usd=float(usage.get("cost") or 0.0),
            latency_ms=latency,
        )


class InferHubLLM:
    def __init__(self, api_key: str, base_url: str, timeout: float = 25.0) -> None:
        self._key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(
        self, routes: tuple[str, ...], messages: list[dict[str, str]], tool: dict[str, Any], max_tokens: int = 700
    ) -> LLMResponse:
        attempts: list[dict[str, Any]] = []
        name = tool["function"]["name"]
        for route in routes:
            started = time.monotonic()
            try:
                resp = httpx.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._key}"},
                    json={
                        "model": route,
                        "messages": messages,
                        "tools": [tool],
                        "tool_choice": {"type": "function", "function": {"name": name}},
                        "temperature": 0.2,
                        "max_tokens": max_tokens,
                    },
                    timeout=self.timeout,
                )
            except httpx.HTTPError as exc:
                attempts.append({"route": route, "error": f"transport:{type(exc).__name__}"})
                continue
            latency = int((time.monotonic() - started) * 1000)
            if resp.status_code != 200:
                attempts.append({"route": route, "error": f"http:{resp.status_code}", "latency_ms": latency})
                continue
            body = resp.json()
            usage = body.get("usage") or {}
            tin = int(usage.get("prompt_tokens") or 0)
            tout = int(usage.get("completion_tokens") or 0)
            cost = usage.get("cost")
            if cost is None:
                pin, pout = ROUTE_PRICES.get(route, (0.3, 1.0))
                cost = (tin * pin + tout * pout) / 1_000_000
            args = None
            try:
                calls = body["choices"][0]["message"].get("tool_calls") or []
                if calls:
                    args = json.loads(calls[0]["function"]["arguments"])
            except (KeyError, IndexError, ValueError, TypeError):
                args = None
            if args is None:
                attempts.append({"route": route, "error": "no_tool_call", "latency_ms": latency})
                continue
            attempts.append({"route": route, "ok": True, "latency_ms": latency})
            return LLMResponse(route, args, tin, tout, float(cost), latency, attempts)
        raise ModelUnavailable("all_routes_failed:" + ",".join(a.get("error", "") for a in attempts))


class StubJev:
    """Deterministic tier-2 stand-in. ``policy(state, questions) -> answers``."""

    def __init__(self, policy: Callable[[str, dict[str, Any]], dict[str, Any]], model: str = "typesafe/jev-1.13") -> None:
        self.policy = policy
        self.model = model
        self.calls = 0

    def decide(self, state: str, questions: dict[str, Any]) -> DecisionResponse:
        self.calls += 1
        answers = self.policy(state, questions)
        if answers is None:
            raise ModelUnavailable("stub_unavailable")
        return DecisionResponse(model_version=self.model + "-stub", answers=answers, latency_ms=1)


class StubLLM:
    def __init__(self, policy: Callable[[str, list[dict[str, str]]], dict[str, Any] | None]) -> None:
        self.policy = policy
        self.calls = 0
        self.requests: list[list[dict[str, str]]] = []

    def complete(
        self, routes: tuple[str, ...], messages: list[dict[str, str]], tool: dict[str, Any], max_tokens: int = 700
    ) -> LLMResponse:
        self.calls += 1
        self.requests.append(messages)
        args = self.policy(tool["function"]["name"], messages)
        if args is None:
            raise ModelUnavailable("stub_unavailable")
        return LLMResponse(routes[0], args, 10, 10, 0.0, 1, [{"route": routes[0], "ok": True}])
