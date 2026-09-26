#!/usr/bin/env python3
"""Minimal scripted learner/tutor roleplay for the live player API.

The run uses a throwaway Postgres database.  Its JSON output is synthetic
evaluation data and is never imported into learner evidence.

Usage:
  TEST_DATABASE_URL=postgresql://... python tools/run_player_agent_evals.py --seeds 1
  STUDY_OS_EVAL_LIVE=1 TEST_DATABASE_URL=... python tools/run_player_agent_evals.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

SCORECARD_VERSION = "study-os.player-agent-evals.v1"
ORACLE_RELATIVE = "domains/dsa/sliding-window/golden/conformance-oracle.v0.1.json"
PLAYER_TO_GOLDEN = {
    "problem": "problem",
    "position": "position",
    "index": "index",
    "box-size": "box_size_k",
    "box-start": "box_start_i",
    "window-sum": "window_sum",
}
ANSWERS = {"position": "4", "index": "2", "box-size": "3", "box-start": "2", "window-sum": "9"}


def golden_prefix() -> tuple[list[str], str, bool]:
    """Return the player-sized prefix, oracle digest, and canonical conformance."""

    path = ROOT / ORACLE_RELATIVE
    raw = path.read_bytes()
    oracle = json.loads(raw)
    prefix = [item["concept_id"] for item in oracle["required_bridges"][:6]]
    try:
        from study_os.pir.conformance import GoldenOracle, evaluate_asset
        from study_os.pir.registry import CANONICAL_PROBLEM_ID, get_asset

        asset = get_asset(CANONICAL_PROBLEM_ID)
        conforms = bool(asset and evaluate_asset(GoldenOracle.model_validate_json(raw), asset).passed)
    except Exception:
        conforms = False
    return prefix, hashlib.sha256(raw).hexdigest(), conforms


def capability_detector(tutor: dict[str, Any], before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, str]]:
    """Detect the product contract required for chat-triggered re-render."""

    if "regenerate_presentation" not in tutor:
        return [{"code": "MISSING_REGENERATE_PRESENTATION", "detail": "tutor response has no regenerate_presentation capability"}]
    render = tutor.get("regenerate_presentation")
    if not isinstance(render, dict) or render.get("step_id") != before.get("step", {}).get("step_id"):
        return [{"code": "INVALID_REGENERATE_PRESENTATION", "detail": "render payload must preserve the current step identity"}]
    if after.get("step", {}).get("step_id") != before.get("step", {}).get("step_id"):
        return [{"code": "RENDER_MOVED_STEP", "detail": "chat render changed the current step"}]
    return []


def learner_response(persona: str, step_id: str, attempt: int) -> str:
    if persona == "wrong_then_right" and attempt == 0:
        return "not this"
    if persona == "partial_then_right" and step_id == "window-sum" and attempt == 0:
        return "2 6 1"
    if persona == "confused_then_right" and attempt == 0:
        return "not this"
    return ANSWERS.get(step_id, "ok")


def _record(events: list[dict[str, Any]], kind: str, payload: dict[str, Any]) -> None:
    events.append({"kind": kind, **payload})


def run_roleplay(app: Any, persona: str, seed: int) -> dict[str, Any]:
    from fastapi.testclient import TestClient
    from web_testkit import ApiClient

    client = ApiClient(TestClient(app))
    client.signup(f"a2a-{persona}-{seed}-{uuid.uuid4().hex[:8]}@example.com")
    events: list[dict[str, Any]] = []
    violations: list[dict[str, str]] = []
    response_attempts: Counter[str] = Counter()
    tutor_checked = False
    view = client.post("/api/player/sessions", {"lesson_id": "sliding-window-box"}).json()
    session_id = view["session_id"]

    for _ in range(120):
        step = view.get("step", {})
        step_id = step.get("step_id")
        _record(events, "view", {"step_id": step_id, "phase": view.get("phase"), "variant": step.get("variant"), "representation": view.get("lesson", {}).get("representation")})
        if view.get("phase") == "done":
            break
        if not tutor_checked and step.get("probe") is not None:
            tutor = client.post(f"/api/player/sessions/{session_id}/tutor", {"message": "I am stuck. Show me this same idea another way."})
            tutor_checked = True
            if tutor.status_code != 200:
                violations.append({"code": "TUTOR_HTTP_ERROR", "detail": tutor.text[:200]})
                tutor_body: dict[str, Any] = {}
            else:
                tutor_body = tutor.json()
                _record(events, "tutor", {"step_id": step_id, "reply_md": tutor_body.get("reply_md", ""), "suggested_action": tutor_body.get("suggested_action")})
                before = view
                after = view
                adapted_success = False
                if tutor_body.get("suggested_action") in {"example", "easier", "harder", "reexplain"}:
                    adapted = client.post(f"/api/player/sessions/{session_id}/adapt", {"kind": "example" if tutor_body["suggested_action"] == "reexplain" else tutor_body["suggested_action"]})
                    if adapted.status_code == 200:
                        after = adapted.json()
                        adapted_success = True
                    else:
                        violations.append({"code": "ADAPT_HTTP_ERROR", "detail": adapted.text[:200]})
                violations.extend(capability_detector(tutor_body, before, after))
                view = after
                if adapted_success:
                    continue
        if view.get("phase") == "feedback" or step.get("probe") is None:
            result = client.post(f"/api/player/sessions/{session_id}/next", {})
            if result.status_code != 200:
                violations.append({"code": "NEXT_HTTP_ERROR", "detail": result.text[:200]})
                break
            view = result.json()
            _record(events, "next", {"step_id": view.get("step", {}).get("step_id"), "phase": view.get("phase")})
            continue
        if persona == "confused_then_right" and response_attempts[step_id] == 0:
            result = client.post(f"/api/player/sessions/{session_id}/confused", {})
            if result.status_code != 200:
                violations.append({"code": "CONFUSED_HTTP_ERROR", "detail": result.text[:200]})
                break
            view = result.json()
            response_attempts[step_id] += 1
            _record(events, "confused", {"step_id": step_id, "variant": view.get("step", {}).get("variant")})
            continue
        attempt = response_attempts[step_id]
        response = learner_response(persona, step_id, attempt)
        result = client.post(
            f"/api/player/sessions/{session_id}/attempt",
            {"response": response, "modality": "text", "idempotency_key": f"{persona}-{seed}-{len(events)}"},
        )
        response_attempts[step_id] += 1
        if result.status_code != 200:
            violations.append({"code": "ATTEMPT_HTTP_ERROR", "detail": result.text[:200]})
            break
        view = result.json()
        feedback = view.get("feedback") or {}
        _record(events, "attempt", {"step_id": step_id, "response": response, "outcome": feedback.get("outcome"), "next_action": feedback.get("next_action")})
    else:
        violations.append({"code": "STEP_CAP_REACHED", "detail": "roleplay exceeded 120 turns"})

    observed: list[str] = []
    for event in events:
        concept = PLAYER_TO_GOLDEN.get(event.get("step_id"))
        if concept and concept not in observed:
            observed.append(concept)
    expected, _, _ = golden_prefix()
    if observed[: len(expected)] != expected:
        violations.append({"code": "GOLDEN_PATH_MISMATCH", "detail": f"expected prefix {expected}, observed {observed}"})
    return {"persona": persona, "seed": seed, "session_id": session_id, "observed_path": observed, "events": events, "violations": violations, "end_phase": view.get("phase")}


def build_scorecard(results: list[dict[str, Any]], live: bool) -> dict[str, Any]:
    expected, oracle_sha256, oracle_conforms = golden_prefix()
    counts = Counter(v["code"] for result in results for v in result["violations"])
    if not oracle_conforms:
        counts["GOLDEN_ORACLE_NONCONFORMANT"] += 1
    return {
        "schema_version": SCORECARD_VERSION,
        "mode": "live_inferhub" if live else "stub",
        "synthetic_only": True,
        "oracle": {"path": ORACLE_RELATIVE, "sha256": oracle_sha256, "expected_player_prefix": expected, "canonical_asset_conforms": oracle_conforms},
        "runs": len(results),
        "violations_by_code": dict(sorted(counts.items())),
        "passed": not counts,
        "runs_detail": [{k: value for k, value in result.items() if k != "events"} for result in results],
        "transcripts": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--personas", default="golden,wrong_then_right,partial_then_right,confused_then_right")
    parser.add_argument("--out", default="evals/out/player-a2a-scorecard.json")
    args = parser.parse_args(argv)
    if not os.environ.get("TEST_DATABASE_URL"):
        raise SystemExit("set TEST_DATABASE_URL (a Postgres role that may create databases)")

    from fastapi.testclient import TestClient
    from study_os.web.api import create_app
    from study_os.web.models import InferHubLLM, StubLLM
    from web_testkit import make_settings, temp_database

    live = os.environ.get("STUDY_OS_EVAL_LIVE") == "1"
    if live:
        key = os.environ.get("INFERHUB_API_KEY")
        if not key:
            raise SystemExit("STUDY_OS_EVAL_LIVE=1 needs INFERHUB_API_KEY")
        llm = InferHubLLM(key, os.environ.get("INFERHUB_API_URL", "https://api.inferhub.dev/v1"))
    else:
        def policy(_name: str, _messages: list[dict[str, str]]) -> dict[str, Any]:
            return {"reply_md": "Point to one part of the box. What do you notice?", "suggested_action": "example"}
        llm = StubLLM(policy)

    personas = [name.strip() for name in args.personas.split(",") if name.strip()]
    results: list[dict[str, Any]] = []
    with ExitStack() as stack:
        db_url = stack.enter_context(temp_database())
        settings = make_settings(db_url, llm_enabled=True)
        app = create_app(settings, jev=None, llm=llm, use_env_models=False)
        stack.enter_context(TestClient(app))
        for seed in range(args.seeds):
            for persona in personas:
                results.append(run_roleplay(app, persona, seed))
    scorecard = build_scorecard(results, live)
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(scorecard, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(destination), "passed": scorecard["passed"], "violations_by_code": scorecard["violations_by_code"]}, indent=2))
    return 0 if scorecard["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
