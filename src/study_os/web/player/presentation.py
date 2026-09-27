"""Bounded presentation overlays; never change lesson identity or probe semantics."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..validator import validate_generated
from . import human_rewrite, teach_visual

SCHEMA_VERSION = "study-os.player-presentation.v1"


def regeneration_allowed(lesson: dict[str, Any], state: dict[str, Any]) -> bool:
    """Whether an in-place re-render of the current card is permitted right now.

    Single source of truth for the refusals in :func:`validate_proposal` and for
    the ``regeneration_allowed`` flag the tutor prompt is grounded in, so the
    model is never left guessing whether this turn may refresh the card.
    """

    if state.get("phase") == "done":
        return False
    if lesson.get("mode") == "assessment" and state.get("phase") == "probe":
        return False
    step = lesson["steps"][state["step_index"]]
    return not (state.get("scaffold", 0) >= 1 and step.get("skippable"))


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

    # A collapsed intro-only step stays collapsed; regeneration cannot reopen it.
    if state.get("scaffold", 0) >= 1 and step.get("skippable"):
        return None, []

    update = current(lesson, state)
    if update:
        md = human_rewrite.rewrite(update["teach_md"], kind="teach")
        return md, list(update["teach_frames"])

    # teach_visual_v1 selects default metaphor frames (or presentation_raw when off).
    md, frames = teach_visual.resolve_teach(teach)
    if md:
        md = human_rewrite.rewrite(md, kind="teach")
    return md, frames


def validate_proposal(
    proposal: Any, lesson: dict[str, Any], state: dict[str, Any], forbidden: tuple[str, ...]
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    if proposal is None:
        return None, ()
    step = lesson["steps"][state["step_index"]]
    if not regeneration_allowed(lesson, state):
        return None, ("PRESENTATION_NOT_ALLOWED",)
    if not isinstance(proposal, dict) or set(proposal) != {"teach_md", "frame_indices"}:
        return None, ("INVALID_PRESENTATION",)
    md, indices = proposal["teach_md"], proposal["frame_indices"]
    if isinstance(md, str):
        md = human_rewrite.rewrite(md, kind="teach")
    frames = step.get("teach", {}).get("frames", [])
    if (not isinstance(md, str) or not isinstance(indices, list) or len(indices) > len(frames)
            or any(type(i) is not int or i < 0 or i >= len(frames) for i in indices)
            or len(set(indices)) != len(indices) or (frames and not indices)):
        return None, ("INVALID_PRESENTATION",)
    # Fences are not allowed: the general prose validator excludes fenced code.
    if "```" in md or "~~~" in md:
        return None, ("INVALID_PRESENTATION",)
    result = validate_generated(md, forbidden_answers=forbidden, required_blocks=(), word_budget=50)
    if not result.ok:
        return None, result.codes
    return {"teach_md": md, "teach_frames": deepcopy([frames[i] for i in indices])}, ()


def authored_reserve(
    lesson: dict[str, Any], state: dict[str, Any], forbidden: tuple[str, ...]
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Offer the step's authored card when no model proposal is usable.

    This is only an alternative when it actually differs from the card already on
    screen: re-publishing the identical card as a new version would fake a
    re-render. Same step, same concept, authored frames only, and no probe answer.
    Callers record it in validation codes rather than passing it off as generated.
    """

    step = lesson["steps"][state["step_index"]]
    teach = step.get("teach") or {}
    md = str(teach.get("md") or "")
    frames = list(teach.get("frames") or [])
    if not md and not frames:
        return None, ("NO_AUTHORED_CARD",)
    current_md, current_frames = effective(lesson, state)
    # Prefer an alternate metaphor (explain indices) so Explain again changes the picture.
    indices = teach_visual.alternate_indices(teach, list(current_frames))
    if not indices:
        indices = list(range(len(frames)))
    candidate_frames = [frames[i] for i in indices if 0 <= i < len(frames)]
    candidate_md = md or (current_md or "")
    rewritten = human_rewrite.rewrite(candidate_md, kind="teach") if candidate_md else ""
    if rewritten == (current_md or "") and candidate_frames == list(current_frames):
        return None, ("RENDER_UNAVAILABLE",)
    if not candidate_md:
        return None, ("NO_AUTHORED_CARD",)
    return validate_proposal(
        {"teach_md": candidate_md, "frame_indices": indices}, lesson, state, forbidden
    )


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
