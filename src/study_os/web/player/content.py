"""Lesson content loader.

Lessons are stored as package data under ``src/study_os/web/player/lessons/*.v1.json``
and accessed through :mod:`importlib.resources` so the player stays pure-Python and
database-free.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    from importlib.resources import files
except ImportError:  # pragma: no cover
    from importlib_resources import files  # type: ignore

_LESSON_GLOB = "*.v1.json"


def _lesson_package() -> str:
    return "study_os.web.player.lessons"


@lru_cache(maxsize=128)
def _load_lesson_data(lesson_id: str) -> tuple[dict[str, Any], str, str]:
    """Return (lesson dict, revision, sha256_hex)."""

    resource_name = f"{lesson_id}.v1.json"
    try:
        raw = files(_lesson_package()).joinpath(resource_name).read_bytes()
    except (FileNotFoundError, OSError) as exc:
        raise FileNotFoundError(f"Lesson not found: {lesson_id}") from exc

    lesson = json.loads(raw.decode("utf-8"))
    revision = lesson.get("revision", f"{lesson_id}.v1")
    digest = hashlib.sha256(raw).hexdigest()
    return lesson, revision, digest


def load_lesson(lesson_id: str) -> dict[str, Any]:
    """Load a lesson by id and cache the result.

    Returns the lesson dict with two extra keys injected:
    ``_revision`` and ``_sha256``.
    """

    lesson, revision, digest = _load_lesson_data(lesson_id)
    lesson = dict(lesson)
    lesson["_revision"] = revision
    lesson["_sha256"] = digest
    return lesson


def list_lessons() -> list[str]:
    """Return all lesson ids in the package data directory."""

    package = files(_lesson_package())
    lesson_ids: list[str] = []
    for path in package.iterdir():  # type: ignore[union-attr]
        if path.is_file() and path.name.endswith(".v1.json"):
            lesson_id = Path(path.name).stem
            # The glob is *.v1.json, so stem already ends with .v1; strip it.
            if lesson_id.endswith(".v1"):
                lesson_id = lesson_id[:-3]
            lesson_ids.append(lesson_id)
    lesson_ids.sort()
    return lesson_ids
