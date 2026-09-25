"""Compact ASCII rendering of player frames for tutor grounding."""

from __future__ import annotations

from typing import Any


def _render_box_index(frame: dict[str, Any]) -> str:
    """Render a ``box_index`` frame as compact ASCII.

    The output mirrors the golden sliding-window diagrams::

        positions(p):  1  2  3  4  5  6
        numbers(a):   [4, 7, 2, 6, 1, 9]
                      └─── box ───┘
                        k = 3
    """

    lines: list[str] = []
    array = frame.get("array", [])
    box = frame.get("box")
    show_positions = frame.get("show_positions", False)
    show_indices = frame.get("show_indices", False)
    arrows = frame.get("arrows", [])
    sum_label = frame.get("sum_label")
    caption = frame.get("caption")

    if caption:
        lines.append(caption)

    # Render positions row if requested.
    if show_positions:
        positions = [str(i + 1) for i in range(len(array))]
        lines.append("positions(p):  " + "  ".join(positions))

    # Render indices row if requested.
    if show_indices:
        indices = [str(i) for i in range(len(array))]
        lines.append("index(i):      " + "  ".join(indices))

    # Numbers row, possibly enclosed in a box.
    nums = [str(v) for v in array]
    if box is not None:
        start = box.get("start", 0)
        k = box.get("k", 1)
        # Simple bracket placement: put brackets around the sub-slice.
        left = "[" + ", ".join(nums[:start]) if start > 0 else ""
        if start > 0:
            left = left + ", "
        middle = ", ".join(nums[start : start + k])
        right_parts = nums[start + k :]
        right = (", ".join(right_parts) + "]") if right_parts else "]"
        if start == 0:
            numbers_line = "[" + middle + right
        else:
            numbers_line = left + middle + ", " + right if right_parts else left + middle + "]"
        lines.append(f"numbers(a):   {numbers_line}")
        # Underline bracket row.
        box_label = f"k = {k}"
        underline = " " * 14 + "" * len(nums) + box_label
        # Approximate underline using └─ ... ─┘ under the boxed slice.
        pre = 14 + sum(len(n) + 2 for n in nums[:start])
        span = sum(len(n) + 2 for n in nums[start : start + k]) - 2
        if start == 0:
            pre -= 1
        underline = " " * pre + "└" + "─" * span + "┘" + f"  {box_label}"
        lines.append(underline)
    else:
        lines.append("numbers(a):   [" + ", ".join(nums) + "]")

    # Arrows / labels.
    if arrows:
        for arrow in arrows:
            at = arrow.get("at", 0)
            label = arrow.get("label", "")
            lines.append(f"{label:>14} (at {at + 1})")

    if sum_label:
        lines.append(f"{sum_label}")

    return "\n".join(lines)


def _render_fraction_bar(frame: dict[str, Any]) -> str:
    """Render a ``fraction_bar`` frame as compact ASCII.

    Example output::

        [###.] 3/4
        [##..] 2/4
    """

    lines: list[str] = []
    caption = frame.get("caption")
    bars = frame.get("bars", [])

    if caption:
        lines.append(caption)

    for bar in bars:
        parts = bar.get("parts", 1)
        shaded = bar.get("shaded", 0)
        label = bar.get("label")
        shaded_char = "#"
        bar_text = "[" + shaded_char * shaded + "." * (parts - shaded) + "]"
        if label:
            bar_text += f" {label}"
        lines.append(bar_text)

    number_line = frame.get("number_line")
    if number_line:
        lines.append("number line: 0 " + "-" * number_line.get("ticks", 12) + " 1")
        for mark in number_line.get("marks", []):
            lines.append(f"  mark at {mark.get('at')} -> {mark.get('label')}")

    return "\n".join(lines)


def frame_to_text(frame: dict[str, Any]) -> str:
    """Return a compact ASCII rendering of a single frame.

    Supports the ``box_index`` and ``fraction_bar`` representations used by the
    player.  Frames that cannot be dispatched are rendered as a JSON-ish
    string so tutors still have something to ground on.
    """

    frame_type = frame.get("type")
    if frame_type == "box_index":
        return _render_box_index(frame)
    if frame_type == "fraction_bar":
        return _render_fraction_bar(frame)

    # Fallback for unknown frames.
    items = [f"{k}={v!r}" for k, v in frame.items()]
    return " | ".join(items)
