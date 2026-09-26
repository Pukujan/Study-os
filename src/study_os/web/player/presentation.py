"""Bounded presentation overlays; never change lesson identity or probe semantics."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..validator import validate_generated

SCHEMA_VERSION = "study-os.player-presentation.v1"


def context(lesson: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    step = lesson["steps"][state["step_index"]]
    return {
        "lesson_id": lesson["lesson_id"],
        "lesson_revision": lesson["revision"],
        "step_id": step["step_id"],
        "concept_id": step["kc"],
        "variant": state["variant_index"],
        "phase": state["phase"],
        "card_mode": state.get("card_mode", "probe"),
        "scaffold": state["scaffold"],
    }


def effective(lesson: dict[str, Any], state: dict[str, Any]) -> tuple[str | None, list[dict[str, Any]]]:
    """Return the teach text and frames the learner is actually shown right now."""

    step = lesson["steps"][state["step_index"]]
    teach = step.get("teach", {}) or {}
    teach_md: str | None = teach.get("md", "")
    teach_frames = list(teach.get("frames", []))

    # A collapsed intro-only step stays collapsed; regeneration cannot reopen it.
    if state.get("scaffold", 0) >= 1 and step.get("skippable"):
        return None, []

    update = current(lesson, state)
    if update:
        return update["teach_md"], list(update["teach_frames"])
    return teach_md, teach_frames


def validate_proposal(
    proposal: Any, lesson: dict[str, Any], state: dict[str, Any], forbidden: tuple[str, ...]
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    if proposal is None:
        return None, ()
    step = lesson["steps"][state["step_index"]]
    if state["phase"] == "done" or (lesson.get("mode") == "assessment" and state["phase"] == "probe"):
        return None, ("PRESENTATION_NOT_ALLOWED",)
    if state.get("scaffold", 0) >= 1 and step.get("skippable"):
        return None, ("PRESENTATION_NOT_ALLOWED",)
    if not isinstance(proposal, dict) or set(proposal) != {"teach_md", "frame_indices"}:
        return None, ("INVALID_PRESENTATION",)
    md, indices = proposal["teach_md"], proposal["frame_indices"]
    frames = step.get("teach", {}).get("frames", [])
    if (not isinstance(md, str) or not isinstance(indices, list) or len(indices) > len(frames)
            or any(type(i) is not int or i < 0 or i >= len(frames) for i in indices)
            or len(set(indices)) != len(indices) or (frames and not indices)):
        return None, ("INVALID_PRESENTATION",)
    # Fences are not allowed: the general prose validator excludes fenced code.
    if "```" in md or "~~~" in md:
        return None, ("INVALID_PRESENTATION",)
    result = validate_generated(md, forbidden_answers=forbidden, required_blocks=(), word_budget=90)
    if not result.ok:
        return None, result.codes
    return {"teach_md": md, "teach_frames": deepcopy([frames[i] for i in indices])}, ()


def apply(
    lesson: dict[str, Any], state: dict[str, Any], content: dict[str, Any], provenance: dict[str, Any]
) -> dict[str, Any]:
    """Apply already validated content, assigning the version on the server under lock."""
    prior = int(state.get("presentation_version", 0))
    update = {
        "schema_version": SCHEMA_VERSION,
        "operation": "regenerate_presentation",
        **context(lesson, state),
        "previous_version": prior,
        "version": prior + 1,
        **deepcopy(content),
        "provenance": provenance,
    }
    state["presentation_version"] = prior + 1
    state["presentation_update"] = update
    return update


def current(lesson: dict[str, Any], state: dict[str, Any]) -> dict[str, Any] | None:
    update = state.get("presentation_update")
    if update and all(update.get(k) == v for k, v in context(lesson, state).items()):
        return deepcopy(update)
    return None
