"""Deterministic offline LLM stand-in for the browser E2E vision gate (SOS-0017).

``web/e2e`` must exercise the real player against a real server without paying
for model calls, so this module can replace the hosted tutor transport when
*both* of these environment variables are set:

- ``STUDY_OS_E2E=1`` marks the process as a gate-only local server;
- ``STUDY_OS_E2E_STUB_LLM=1`` explicitly opts in to the stub.

It is never enabled by default, it is not reachable from the deployed app, and
it returns only deterministic, validator-clean content. A stub reply is not
learner evidence and must never be recorded as such.
"""

from __future__ import annotations

import json
import os
from typing import Any

# Answer-free, mastery-free, one-question-free prose that passes
# ``study_os.web.validator.validate_generated`` for any step.
REPLY_MD = (
    "Here is the same step drawn another way. Look at the equal parts and the "
    "shaded parts together, then read what the picture is counting."
)
REGEN_MD = (
    "Same idea, different picture. Count the equal parts first, then count the "
    "parts that are shaded, and read the pair from the drawing."
)

# The player asks for another render of the same step/concept with this wording
# (see REGEN_PROMPTS in web/src/pages/Player.tsx).
REGEN_MARKER = "different picture"


def enabled() -> bool:
    """True only when the gate server has explicitly opted in to the stub."""

    return (
        os.environ.get("STUDY_OS_E2E") == "1"
        and os.environ.get("STUDY_OS_E2E_STUB_LLM") == "1"
    )


def _context(messages: list[dict[str, str]]) -> dict[str, Any]:
    for message in messages:
        if message.get("role") != "user":
            continue
        try:
            payload = json.loads(message.get("content") or "")
        except (TypeError, ValueError):
            continue
        if isinstance(payload, dict) and "current_step" in payload:
            return payload
    return {}


def _asked_to_regenerate(messages: list[dict[str, str]]) -> bool:
    return any(
        message.get("role") == "user" and REGEN_MARKER in (message.get("content") or "")
        for message in messages
    )


def policy(name: str, messages: list[dict[str, str]]) -> dict[str, Any] | None:
    """``StubLLM`` policy: a plain hint, or a valid re-render proposal on request."""

    if name != "tutor_reply":
        return None
    if not _asked_to_regenerate(messages):
        return {"reply_md": REPLY_MD, "suggested_action": None, "regenerate_presentation": None}

    frames = _context(messages).get("teach_frames") or []
    return {
        "reply_md": REPLY_MD,
        "suggested_action": None,
        "regenerate_presentation": {
            "teach_md": REGEN_MD,
            "frame_indices": [0] if frames else [],
        },
    }
