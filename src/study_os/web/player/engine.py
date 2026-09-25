"""Pure-Python lesson player engine.

The engine is intentionally database-free and HTTP-free.  It operates on a
lesson dictionary and a JSON-serialisable state dictionary.
"""

from __future__ import annotations

from typing import Any

from .grading import grade


_MAX_MISSES = 3


def _new_state(lesson: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_index": 0,
        "variant_index": -1,
        "phase": "probe",
        "pending": None,
        "misses_on_step": 0,
        "first_try_streak": 0,
        "scaffold": 0,
        "history": [],
        "status_by_step": {step["step_id"]: "not_started" for step in lesson.get("steps", [])},
    }


def _current_step(lesson: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    return lesson["steps"][state["step_index"]]


def _current_probe(lesson: dict[str, Any], state: dict[str, Any]) -> dict[str, Any] | None:
    step = _current_step(lesson, state)
    if state["variant_index"] == -1:
        probe = step.get("probe")
    else:
        variants = step.get("variants", [])
        if state["variant_index"] < len(variants):
            probe = variants[state["variant_index"]].get("probe")
        else:
            probe = step.get("probe")
    return probe


def _teach_frames(lesson: dict[str, Any], state: dict[str, Any]) -> tuple[str | None, list[dict[str, Any]]]:
    step = _current_step(lesson, state)
    scaffold = state.get("scaffold", 0)
    teach = step.get("teach", {})
    md = teach.get("md", "")
    frames = list(teach.get("frames", []))

    # If scaffold >= 1 and step is intro-only/skippable, collapse the teach frames.
    if scaffold >= 1 and step.get("skippable"):
        return None, []

    return md, frames


def start(lesson: dict[str, Any]) -> dict[str, Any]:
    """Return the initial state for a lesson."""

    check_lesson(lesson)
    return _new_state(lesson)


def _public_probe(probe: dict[str, Any] | None) -> dict[str, Any] | None:
    """Strip server-only fields from a probe before returning it to the client."""

    if probe is None:
        return None
    public = {
        k: v
        for k, v in probe.items()
        if k not in {"accept", "partial", "misconceptions", "solution_md", "hint_md"}
    }
    return public


def _strip_server_only(view: Any) -> Any:
    """Recursively remove server-only keys from a view dict/list."""

    if isinstance(view, dict):
        return {k: _strip_server_only(v) for k, v in view.items() if k not in {"accept", "partial", "misconceptions", "solution_md", "hint_md"}}
    if isinstance(view, list):
        return [_strip_server_only(item) for item in view]
    return view


def view(lesson: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Return the public player view for the current state.

    The view never contains ``accept``, ``partial``, ``misconceptions``,
    ``solution_md``, or ``hint_md``.
    """

    step = _current_step(lesson, state)
    teach_md, teach_frames = _teach_frames(lesson, state)
    probe = _current_probe(lesson, state)
    public_probe = _public_probe(probe)

    progress_done = sum(1 for s in state["status_by_step"].values() if s in {"done", "needs_review"})

    feedback = None
    if state["phase"] == "feedback":
        # Feedback is already built into state by attempt/confused; keep it public.
        feedback = state.get("feedback")

    return {
        "session_id": None,
        "lesson": {
            "lesson_id": lesson["lesson_id"],
            "title": lesson["title"],
            "lane": lesson["lane"],
            "representation": lesson["representation"],
            "total_steps": len(lesson["steps"]),
        },
        "step": {
            "step_id": step["step_id"],
            "index": state["step_index"],
            "teach_md": teach_md,
            "teach_frames": teach_frames,
            "teach_collapsed": teach_md is None and not teach_frames,
            "probe": public_probe,
            "variant": state["variant_index"],
        },
        "phase": state["phase"],
        "feedback": feedback,
        "scaffold": state["scaffold"],
        "progress": {
            "done": progress_done,
            "total": len(lesson["steps"]),
        },
        "is_guest": False,
    }


def _advance(lesson: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    steps = lesson["steps"]
    current = state["step_index"]
    current_step = steps[current]

    # Mark current step done unless it already has a terminal status.
    status = state["status_by_step"].get(current_step["step_id"])
    if status not in {"needs_review"}:
        state["status_by_step"][current_step["step_id"]] = "done"

    next_index = current + 1
    if next_index >= len(steps):
        state["phase"] = "done"
        state["pending"] = None
        state["misses_on_step"] = 0
        return state

    state["step_index"] = next_index
    state["variant_index"] = -1
    state["phase"] = "probe"
    state["pending"] = None
    state["misses_on_step"] = 0
    next_step = steps[next_index]
    state["status_by_step"][next_step["step_id"]] = "in_progress"
    return state


def _pick_next_variant(lesson: dict[str, Any], state: dict[str, Any]) -> int:
    """Choose a variant different from the current one."""

    step = _current_step(lesson, state)
    variants = step.get("variants", [])
    if not variants:
        return -1
    current = state["variant_index"]
    for i in range(len(variants)):
        if i != current:
            return i
    return 0


def _build_feedback(
    outcome: str,
    message_md: str,
    frames: list[dict[str, Any]],
    next_action: str,
    *,
    sticker: str | None = None,
    reassure: bool = False,
) -> dict[str, Any]:
    return {
        "outcome": outcome,
        "message_md": message_md,
        "frames": frames,
        "reassure": reassure,
        "sticker": sticker,
        "next_action": next_action,
    }


def attempt(
    lesson: dict[str, Any],
    state: dict[str, Any],
    response: str,
    modality: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Process a learner attempt.

    Returns ``(new_state, feedback)``.
    """

    probe = _current_probe(lesson, state)
    step = _current_step(lesson, state)
    step_id = step["step_id"]

    if probe is None:
        # Ready-only step; any response advances.
        state["phase"] = "feedback"
        feedback = _build_feedback(
            "correct",
            "Let's go!",
            [],
            "continue",
            sticker="correct",
        )
        state["feedback"] = _strip_server_only(feedback)
        return state, feedback

    outcome, note, misconception_id = grade(probe, response, modality)

    history_entry = {
        "step_id": step_id,
        "variant": state["variant_index"],
        "outcome": outcome,
        "modality": modality,
    }
    state["history"].append(history_entry)

    if outcome == "correct":
        # Build correct feedback: correct_md + why (explain).
        correct_text = probe.get("correct_md", "Correct!")
        explain = probe.get("explain_md", "")
        message = correct_text
        if explain:
            message += "\n\n" + explain
        frames = list(probe.get("explain_frames", []))

        # We are on a confirm/check variant when the learner is answering a
        # variant that was queued after a first-try correct (confirm) or after a
        # retry correct (check).
        is_extra_variant = (
            state["pending"] == "check"
            or (state["pending"] is None and state["variant_index"] != -1)
        )

        # Scaffold: two first-try correct in a row -> raise.  Only count the
        # very first attempt at a step (variant_index == -1 and no pending).
        if state["pending"] is None and state["variant_index"] == -1:
            state["first_try_streak"] += 1
            if state["first_try_streak"] >= 2:
                state["scaffold"] = min(2, state["scaffold"] + 1)
                state["first_try_streak"] = 0

        # Decide next action.
        if is_extra_variant:
            # Confirm/check variant answered correctly -> advance.
            feedback = _build_feedback("correct", message, frames, "continue", sticker="correct")
            state["phase"] = "feedback"
            state["pending"] = None
        elif state["pending"] == "retry":
            # Retry correct; one more check before advancing.
            next_variant = _pick_next_variant(lesson, state)
            state["variant_index"] = next_variant
            feedback = _build_feedback("correct", message, frames, "continue", sticker="correct")
            state["phase"] = "feedback"
            state["pending"] = "check"
        else:
            # First try correct.
            if step.get("confirm"):
                # Ask one confirm variant before advancing.
                next_variant = _pick_next_variant(lesson, state)
                state["variant_index"] = next_variant
                state["pending"] = "check"
                feedback = _build_feedback("correct", message, frames, "continue", sticker="correct")
                state["phase"] = "feedback"
            else:
                feedback = _build_feedback("correct", message, frames, "continue", sticker="correct")
                state["phase"] = "feedback"
                state["pending"] = None
        state["feedback"] = _strip_server_only(feedback)
        return state, feedback

    if outcome == "partial":
        # Reset streak on partial.
        state["first_try_streak"] = 0
        note_text = note or "Keep going — you're on the right track."
        feedback = _build_feedback(
            "partial",
            note_text,
            list(probe.get("explain_frames", [])),
            "retry_same",
            sticker=None,
        )
        state["phase"] = "feedback"
        state["pending"] = "retry_same"
        state["feedback"] = _strip_server_only(feedback)
        return state, feedback

    # outcome == "incorrect"
    state["first_try_streak"] = 0
    if state["scaffold"] > 0:
        state["scaffold"] -= 1

    state["misses_on_step"] += 1

    if state["misses_on_step"] >= _MAX_MISSES:
        # Max misses: advance with needs_review.
        state["status_by_step"][step_id] = "needs_review"
        message = (
            f"The right answer is **{probe.get('accept', ['?'])[0]}**.\n\n"
            f"{probe.get('explain_md', '')}\n\n"
            "That's okay — this one trips people up. We'll come back to it later."
        )
        feedback = _build_feedback(
            "incorrect",
            message,
            list(probe.get("explain_frames", [])),
            "continue",
            sticker="reassure",
            reassure=True,
        )
        state["phase"] = "feedback"
        state["pending"] = None
        state["feedback"] = _strip_server_only(feedback)
        return state, feedback

    # Normal incorrect: show answer + why + reassure, then retry different variant.
    right = probe.get("accept", ["?"])[0]
    message = (
        f"The right answer is **{right}**.\n\n"
        f"{probe.get('explain_md', '')}\n\n"
        "That's okay — this one trips people up."
    )
    feedback = _build_feedback(
        "incorrect",
        message,
        list(probe.get("explain_frames", [])),
        "retry",
        sticker="reassure",
        reassure=True,
    )

    # Pick a different variant for the retry.
    next_variant = _pick_next_variant(lesson, state)
    state["variant_index"] = next_variant
    state["phase"] = "feedback"
    state["pending"] = "retry"
    state["feedback"] = _strip_server_only(feedback)
    return state, feedback


def confused(lesson: dict[str, Any], state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Re-explain: show explain frames and switch to a different variant, same representation."""

    probe = _current_probe(lesson, state)

    if probe is None:
        feedback = _build_feedback(
            "incorrect",
            "No problem — let's take it step by step.",
            [],
            "continue",
            sticker="reassure",
            reassure=True,
        )
        state["phase"] = "feedback"
        state["pending"] = None
        state["feedback"] = _strip_server_only(feedback)
        return state, feedback

    # Show explain frames, then retry with a different variant.
    next_variant = _pick_next_variant(lesson, state)
    state["variant_index"] = next_variant
    state["phase"] = "feedback"
    state["pending"] = "retry"

    feedback = _build_feedback(
        "incorrect",
        f"Let's look at this again.\n\n{probe.get('explain_md', '')}",
        list(probe.get("explain_frames", [])),
        "retry",
        sticker="reassure",
        reassure=True,
    )
    state["feedback"] = _strip_server_only(feedback)
    return state, feedback


def next(lesson: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:  # noqa: A001
    """Acknowledge any pending feedback and move to the next probe or step."""

    if state["phase"] != "feedback":
        return state

    if state["pending"] == "retry":
        state["phase"] = "probe"
        state["pending"] = None
        return state

    if state["pending"] == "retry_same":
        state["phase"] = "probe"
        state["pending"] = None
        return state

    if state["pending"] == "check":
        state["phase"] = "probe"
        state["pending"] = None
        return state

    # No pending action: advance to the next step.
    return _advance(lesson, state)


def check_lesson(lesson: dict[str, Any]) -> list[str]:
    """Validate a lesson against the player-lesson.v1 schema and golden rules.

    Returns a list of validation errors.  An empty list means the lesson is
    conformant.
    """

    errors: list[str] = []

    if not isinstance(lesson, dict):
        return ["lesson must be a dict"]

    required_top = {"schema_version", "lesson_id", "revision", "lane", "title", "summary", "representation", "steps"}
    for key in required_top:
        if key not in lesson:
            errors.append(f"missing top-level key: {key}")

    if "steps" not in lesson or not isinstance(lesson["steps"], list):
        return errors + ["steps must be a list"]

    for idx, step in enumerate(lesson["steps"]):
        if not isinstance(step, dict):
            errors.append(f"step {idx}: must be a dict")
            continue

        step_id = step.get("step_id")
        if not step_id:
            errors.append(f"step {idx}: missing step_id")
            continue

        if "kc" not in step:
            errors.append(f"step {step_id}: missing kc")

        teach = step.get("teach", {})
        teach_md = teach.get("md", "")
        if len(teach_md.split()) > 40:
            errors.append(f"step {step_id}: teach.md exceeds 40 words")

        probe = step.get("probe")
        variants = step.get("variants", [])

        if probe is None:
            # Intro-only steps (e.g. "Ready?") don't need variants.
            continue

        if len(variants) < 2:
            errors.append(f"step {step_id}: probe step must have at least 2 variants")

        # Validate main probe.
        all_probes = [("main", probe)]
        for v_idx, variant in enumerate(variants):
            if not isinstance(variant, dict):
                errors.append(f"step {step_id} variant {v_idx}: must be a dict")
                continue
            v_probe = variant.get("probe")
            if not v_probe:
                errors.append(f"step {step_id} variant {v_idx}: missing probe")
                continue
            all_probes.append((f"variant {v_idx}", v_probe))

        for name, p in all_probes:
            if not isinstance(p, dict):
                errors.append(f"step {step_id} {name}: probe must be a dict")
                continue

            prompt = p.get("prompt_md", "")
            if prompt.count("?") > 1:
                errors.append(f"step {step_id} {name}: prompt contains more than one '?'")

            explain_md = p.get("explain_md", "")
            if len(explain_md.split()) > 50:
                errors.append(f"step {step_id} {name}: explain_md exceeds 50 words")

            # Probe frames must not contain arrows or highlights.
            for frame in p.get("frames", []):
                if not isinstance(frame, dict):
                    continue
                if frame.get("arrows"):
                    errors.append(f"step {step_id} {name}: probe frame contains arrows")
                if frame.get("highlight"):
                    errors.append(f"step {step_id} {name}: probe frame contains highlight")

            # Required server-only fields.
            for field in ("accept", "solution_md", "hint_md"):
                if field not in p:
                    errors.append(f"step {step_id} {name}: missing {field}")

    return errors
