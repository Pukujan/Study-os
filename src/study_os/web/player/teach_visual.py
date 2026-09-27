"""Versioned teach visuals (teach_visual_v1) for reversible diagram upgrades.

Flip off with ``STUDY_OS_TEACH_VISUAL_V1=0`` (or ``false`` / ``off``) to restore each
step's ``presentation_raw`` teach md+frames without deleting the upgraded frames.
Default is on when the env var is unset.
"""

from __future__ import annotations

import os
from typing import Any


FLAG_ENV = "STUDY_OS_TEACH_VISUAL_V1"
FLAG_NAME = "teach_visual_v1"


def enabled() -> bool:
    """Return whether teach_visual_v1 diagrams are active."""

    raw = os.environ.get(FLAG_ENV)
    if raw is None or raw.strip() == "":
        return True
    return raw.strip().lower() not in {"0", "false", "off", "no"}


def authored_frames(teach: dict[str, Any]) -> list[dict[str, Any]]:
    """Full authored frame pool used for Explain-again index selection."""

    return list(teach.get("frames") or [])


def _indices(teach: dict[str, Any], key: str, fallback: list[int]) -> list[int]:
    cfg = teach.get(FLAG_NAME) or {}
    raw = cfg.get(key)
    if not isinstance(raw, list) or not raw:
        return list(fallback)
    out: list[int] = []
    frames = authored_frames(teach)
    for item in raw:
        if type(item) is int and 0 <= item < len(frames) and item not in out:
            out.append(item)
    return out or list(fallback)


def default_frame_indices(teach: dict[str, Any]) -> list[int]:
    frames = authored_frames(teach)
    if not frames:
        return []
    return _indices(teach, "default_frame_indices", [0])


def explain_frame_indices(teach: dict[str, Any]) -> list[int]:
    """Alternate picture indices for Explain again / Worked example rotation."""

    frames = authored_frames(teach)
    if not frames:
        return []
    default = set(default_frame_indices(teach))
    fallback = [i for i in range(len(frames)) if i not in default] or [0]
    return _indices(teach, "explain_frame_indices", fallback)


def select_frames(teach: dict[str, Any], indices: list[int]) -> list[dict[str, Any]]:
    frames = authored_frames(teach)
    return [frames[i] for i in indices if 0 <= i < len(frames)]


def resolve_teach(teach: dict[str, Any]) -> tuple[str | None, list[dict[str, Any]]]:
    """Return (md, frames) for the learner card under the current flag."""

    if not isinstance(teach, dict):
        return None, []

    if not enabled():
        raw = teach.get("presentation_raw")
        if isinstance(raw, dict) and (raw.get("frames") or raw.get("md")):
            return raw.get("md") or teach.get("md") or "", list(raw.get("frames") or [])
        return teach.get("md") or "", authored_frames(teach)

    if teach.get(FLAG_NAME):
        md = teach.get("md") or ""
        return md, select_frames(teach, default_frame_indices(teach))

    return teach.get("md") or "", authored_frames(teach)


def alternate_indices(teach: dict[str, Any], current_frames: list[dict[str, Any]] | None = None) -> list[int]:
    """Pick authored indices that differ from what is currently on screen."""

    frames = authored_frames(teach)
    if not frames:
        return []
    explain = explain_frame_indices(teach)
    if not current_frames:
        return explain
    # Prefer explain indices when they are not identical to the current card.
    candidate = select_frames(teach, explain)
    if candidate != list(current_frames):
        return explain
    default = default_frame_indices(teach)
    if select_frames(teach, default) != list(current_frames):
        return default
    # Last resort: first frame that is not byte-identical to the sole current frame.
    for i, frame in enumerate(frames):
        if [frame] != list(current_frames):
            return [i]
    return explain or default or [0]
