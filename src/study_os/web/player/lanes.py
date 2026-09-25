"""Lane registry and /api/lanes payload builder.

The registry is the source of truth for the four lanes shown on the home
screen.  :func:`lanes_payload` combines the registry with lesson content and
per-learner progress to produce the response shape defined by the player design.
"""

from __future__ import annotations

from typing import Any

from .content import list_lessons, load_lesson


LANES: list[dict[str, Any]] = [
    {
        "lane_id": "dsa",
        "title": "Algorithms (DSA)",
        "blurb": "Learn classic algorithms step by step.",
        "legacy": {"kind": "dsa_pir", "label": "DSA PIR"},
    },
    {
        "lane_id": "hesi",
        "title": "HESI A2 prep",
        "blurb": "Nursing entrance exam topics made visual.",
        "legacy": {"kind": "hesi_topics", "label": "HESI topics"},
    },
    {
        "lane_id": "ai-from-scratch",
        "title": "AI from scratch",
        "blurb": "Build intuition for machine learning.",
        "legacy": None,
    },
    {
        "lane_id": "study-os",
        "title": "Study OS",
        "blurb": "Meta-skills for learning anything.",
        "legacy": None,
    },
]


def _lane_index(lane_id: str) -> int:
    for index, lane in enumerate(LANES):
        if lane["lane_id"] == lane_id:
            return index
    return len(LANES)  # fall back to end


def lanes_payload(
    progress_by_lesson: dict[str, str],
    open_sessions: dict[str, Any],
) -> dict[str, Any]:
    """Build the GET /api/lanes response.

    ``progress_by_lesson`` maps ``lesson_id`` to one of ``not_started``,
    ``in_progress``, or ``done``.  ``open_sessions`` maps ``lesson_id`` to a
    ``session_id`` (or to ``None`` / a dict with ``session_id``).  Lanes with
    no published lessons are still listed with status ``in_progress_content``.
    """

    lessons: list[dict[str, Any]] = []
    for lesson_id in list_lessons():
        try:
            lesson = load_lesson(lesson_id)
        except FileNotFoundError:
            continue
        lessons.append(lesson)

    # Group by lane, preserving lane order.
    lessons_by_lane: dict[str, list[dict[str, Any]]] = {lane["lane_id"]: [] for lane in LANES}
    for lesson in lessons:
        lane = lesson.get("lane")
        if lane in lessons_by_lane:
            lessons_by_lane[lane].append(lesson)

    lanes_out: list[dict[str, Any]] = []
    for lane in LANES:
        lane_id = lane["lane_id"]
        lane_lessons = lessons_by_lane.get(lane_id, [])
        items: list[dict[str, Any]] = []
        for lesson in lane_lessons:
            lesson_id = lesson["lesson_id"]
            state = progress_by_lesson.get(lesson_id, "not_started")
            total = len(lesson.get("steps", []))
            if state == "done":
                done = total
            elif state == "in_progress":
                # Best-effort: report one step done so the UI shows progress.
                done = 1
            else:
                done = 0
            items.append({
                "lesson_id": lesson_id,
                "title": lesson.get("title", lesson_id),
                "state": state,
                "progress": {"done": done, "total": total},
            })

        status = "available" if items else "in_progress_content"
        lanes_out.append({
            "lane_id": lane_id,
            "title": lane["title"],
            "blurb": lane["blurb"],
            "status": status,
            "lessons": items,
            "legacy": lane["legacy"],
        })

    # Determine a single continue target.
    continue_target: dict[str, Any] | None = None

    # 1. Most recent in-progress lesson, preferring dsa then hesi.
    for lane_id in ("dsa", "hesi", "ai-from-scratch", "study-os"):
        for item in lessons_by_lane.get(lane_id, []):
            if progress_by_lesson.get(item["lesson_id"]) == "in_progress":
                session_id = open_sessions.get(item["lesson_id"])
                if isinstance(session_id, dict):
                    session_id = session_id.get("session_id")
                continue_target = {
                    "lesson_id": item["lesson_id"],
                    "lane": lane_id,
                    "title": item.get("title", item["lesson_id"]),
                    "session_id": session_id,
                    "label": "Continue",
                }
                break
        if continue_target:
            break

    # 2. Otherwise, first not-started available lesson, preferring dsa then hesi.
    if continue_target is None:
        for lane_id in ("dsa", "hesi", "ai-from-scratch", "study-os"):
            for item in lessons_by_lane.get(lane_id, []):
                if progress_by_lesson.get(item["lesson_id"], "not_started") == "not_started":
                    session_id = open_sessions.get(item["lesson_id"])
                    if isinstance(session_id, dict):
                        session_id = session_id.get("session_id")
                    continue_target = {
                        "lesson_id": item["lesson_id"],
                        "lane": lane_id,
                        "title": item.get("title", item["lesson_id"]),
                        "session_id": session_id,
                        "label": "Start",
                    }
                    break
            if continue_target:
                break

    return {
        "continue": continue_target,
        "lanes": lanes_out,
    }
