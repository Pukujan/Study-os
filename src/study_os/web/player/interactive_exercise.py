"""Catalog-wide interactive visual exercise generator (Refs #161 / #126).

Reads content/teach-visuals/step-visual-map.v1.json + exercise-templates.v1.json
(+ provenance) and emits player frames.

Alex's 3-graph Big-O pick/draw is the *example pattern* for
multi_class_growth_curve — not a one-off probe. Every mapped visual_type
gets a template-driven interactive exercise.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[4]
_PACK = _ROOT / "content" / "teach-visuals"
_TEMPLATES = _PACK / "exercise-templates.v1.json"
_STEP_MAP = _PACK / "step-visual-map.v1.json"
_PROVENANCE = _PACK / "provenance.v1.json"


@lru_cache(maxsize=1)
def _load_json(path_str: str) -> dict[str, Any]:
    return json.loads(Path(path_str).read_text(encoding="utf-8"))


def load_templates() -> dict[str, Any]:
    return _load_json(str(_TEMPLATES))


def load_step_map() -> dict[str, Any]:
    return _load_json(str(_STEP_MAP))


def load_provenance() -> dict[str, Any]:
    return _load_json(str(_PROVENANCE))


def template_for(visual_type: str) -> dict[str, Any] | None:
    for t in load_templates().get("templates") or []:
        if t.get("visual_type") == visual_type:
            return t
    return None


def step_entry(lesson_id: str, step_id: str) -> dict[str, Any] | None:
    for e in load_step_map().get("entries") or []:
        if e.get("lesson_id") == lesson_id and e.get("step_id") == step_id:
            return e
    return None


def _asset_public_src(asset_id: str) -> str | None:
    for a in load_provenance().get("assets") or []:
        if a.get("asset_id") == asset_id:
            return a.get("public_src")
    return None


def _prompt(template: dict[str, Any], kind: str, ctx: dict[str, Any]) -> str:
    raw = (template.get("prompt_templates") or {}).get(kind) or ""
    try:
        return raw.format(**ctx)
    except (KeyError, ValueError):
        return raw


def _match_curves_frame(template: dict[str, Any], entry: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    params = dict(template.get("params") or {})
    panels = params.get("panels") or [
        {"id": "A", "shape": "flat"},
        {"id": "B", "shape": "linear"},
        {"id": "C", "shape": "steep"},
    ]
    asset_ids = entry.get("asset_ids") or []
    return {
        "type": "interactive_visual",
        "exercise_kind": "match_curves",
        "prompt": _prompt(template, "match_curves", ctx),
        "n_values": list(params.get("n_values") or [1, 2, 4, 8, 16]),
        "panels": panels,
        "labels": list(params.get("labels") or ["O(1)", "O(n)", "O(n²)"]),
        "axis_numbers_only": bool(params.get("axis_numbers_only", True)),
        "asset_id": asset_ids[0] if asset_ids else None,
        "caption": None,
    }


def _plot_curve_frame(template: dict[str, Any], entry: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    params = dict(template.get("params") or {})
    target = ctx.get("target") or (params.get("plot_targets") or ["O(1)"])[0]
    ctx = {**ctx, "target": target}
    asset_ids = entry.get("asset_ids") or []
    return {
        "type": "interactive_visual",
        "exercise_kind": "plot_curve",
        "prompt": _prompt(template, "plot_curve", ctx),
        "n_values": list(params.get("n_values") or [1, 2, 4, 8, 16]),
        "target_shape": target,
        "axis_numbers_only": True,
        "asset_id": asset_ids[0] if asset_ids else None,
        "caption": None,
    }


def _place_number_line_frame(template: dict[str, Any], entry: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    params = dict(template.get("params") or {})
    fraction = ctx.get("fraction") or "1/2"
    ctx = {**ctx, "fraction": fraction}
    asset_ids = entry.get("asset_ids") or []
    target = 0.5
    if isinstance(fraction, str) and "/" in fraction:
        try:
            a, b = fraction.split("/", 1)
            target = float(a) / float(b)
        except ValueError:
            target = 0.5
    return {
        "type": "interactive_visual",
        "exercise_kind": "place_number_line",
        "prompt": _prompt(template, "place_number_line", ctx),
        "line_max": float(params.get("line_max") or 1),
        "ticks": list(params.get("ticks") or [0, 0.25, 0.5, 0.75, 1]),
        "target": target,
        "tolerance": float(ctx.get("tolerance") or 0.08),
        "asset_id": asset_ids[0] if asset_ids else None,
        "asset_src": _asset_public_src(asset_ids[0]) if asset_ids else None,
        "caption": None,
    }


def _tap_boxes_frame(template: dict[str, Any], entry: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    params = dict(template.get("params") or {})
    array = list(ctx.get("array") or [2, 1, 3, 4, 2])
    return {
        "type": "box_index",
        "array": array,
        "interactive": bool(params.get("interactive", True)),
        "caption": _prompt(template, "tap_boxes", ctx) or None,
    }


_KIND_BUILDERS = {
    "match_curves": _match_curves_frame,
    "plot_curve": _plot_curve_frame,
    "place_number_line": _place_number_line_frame,
    "tap_boxes": _tap_boxes_frame,
}


def generate(
    lesson_id: str,
    step_id: str,
    *,
    kind: str | None = None,
    ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = step_entry(lesson_id, step_id)
    if not entry:
        raise KeyError(f"No step-visual-map entry for {lesson_id}/{step_id}")
    visual_type = str(entry.get("visual_type") or "")
    template = template_for(visual_type)
    if not template:
        raise KeyError(f"No exercise template for visual_type={visual_type!r}")
    exercise_kind = kind or str(template.get("default_kind") or "")
    if exercise_kind not in (template.get("exercise_kinds") or []):
        raise KeyError(f"Kind {exercise_kind!r} not allowed for {visual_type}")
    builder = _KIND_BUILDERS.get(exercise_kind)
    if not builder:
        raise KeyError(f"No builder for exercise_kind={exercise_kind!r}")
    frame = builder(template, entry, dict(ctx or {}))
    frame["provenance"] = {
        "lesson_id": lesson_id,
        "step_id": step_id,
        "visual_type": visual_type,
        "exercise_kind": exercise_kind,
        "asset_ids": list(entry.get("asset_ids") or []),
        "research_cites": list(entry.get("research_cites") or template.get("research_cites") or []),
    }
    return frame


def generate_all(
    *,
    kind_overrides: dict[str, str] | None = None,
    ctx_by_step: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    overrides = kind_overrides or {}
    ctx_map = ctx_by_step or {}
    for entry in load_step_map().get("entries") or []:
        lesson_id = entry.get("lesson_id")
        step_id = entry.get("step_id")
        if not lesson_id or not step_id:
            continue
        if not template_for(str(entry.get("visual_type") or "")):
            continue
        key = f"{lesson_id}/{step_id}"
        try:
            out.append(generate(str(lesson_id), str(step_id), kind=overrides.get(key), ctx=ctx_map.get(key)))
        except KeyError:
            continue
    return out


def attachable_for_lesson(lesson: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lesson_id = str(lesson.get("lesson_id") or "")
    result: dict[str, dict[str, Any]] = {}
    for step in lesson.get("steps") or []:
        step_id = str(step.get("step_id") or "")
        if not step_id:
            continue
        try:
            result[step_id] = generate(lesson_id, step_id)
        except KeyError:
            continue
    return result
