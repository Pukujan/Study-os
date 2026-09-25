"""Compact ASCII rendering of player frames for tutor grounding."""

from __future__ import annotations

from typing import Any


def _cell_widths(array: list[int]) -> list[int]:
    return [max(len(str(v)), 1) for v in array]


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
    circles = frame.get("circles", [])
    sum_label = frame.get("sum_label")
    caption = frame.get("caption")

    if caption:
        lines.append(caption)

    # Render indices row if requested.
    if show_indices:
        parts = [str(i) for i in range(len(array))]
        lines.append("index(i):      " + "  ".join(parts))

    # Render positions row if requested.
    if show_positions:
        parts = [str(i + 1) for i in range(len(array))]
        lines.append("positions(p):  " + "  ".join(parts))

    # Numbers row.
    nums = [str(v) for v in array]
    box_start = box.get("start", 0) if box else 0
    box_k = box.get("k", 1) if box else 0
    numbers_line = "[" + ", ".join(nums) + "]"
    lines.append(f"numbers(a):   {numbers_line}")

    # Circles represented by parentheses around the value.
    if circles:
        line = " " * 14
        pos = 14
        for i in sorted(circles):
            if 0 <= i < len(array):
                # crude alignment; enough for tutor grounding
                line += f"  ({array[i]})"
        if line.strip():
            lines.append(line.rstrip())

    # Brace line.
    if box:
        brace_label = box.get("brace_label") or f"k = {box_k}"
        pre = 14 + sum(len(nums[i]) + 2 for i in range(box_start))
        span = sum(len(nums[i]) + 2 for i in range(box_start, box_start + box_k)) - 2
        line = " " * pre + "└" + "─" * max(2, span) + "┘" + f"  {brace_label}"
        lines.append(line)

    # Arrows / labels.
    if arrows:
        for arrow in arrows:
            at = arrow.get("at", 0)
            label = arrow.get("label", "")
            row = arrow.get("row", "numbers")
            dir_ = arrow.get("dir", "down")
            symbol = "↓" if dir_ == "down" else "↑"
            lines.append(f"{symbol} {label} (at {row} {at + 1})")

    if sum_label:
        lines.append(str(sum_label))

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


def _render_mermaid_flow(frame: dict[str, Any]) -> str:
    """Render a ``mermaid_flow`` frame as a compact note."""

    lines: list[str] = []
    caption = frame.get("caption")
    source = frame.get("source", "")
    revealed = frame.get("revealed_nodes", [])
    direction = frame.get("direction", "TD")
    if caption:
        lines.append(caption)
    lines.append(f"[mermaid flowchart {direction}]")
    if revealed:
        lines.append(f"revealed nodes: {', '.join(str(n) for n in revealed)}")
    # Include the source lines for grounding context.
    for line in source.splitlines()[:8]:
        lines.append(line)
    return "\n".join(lines)


def _render_code_tree(frame: dict[str, Any]) -> str:
    """Render a ``code_tree`` frame as compact text."""

    lines: list[str] = []
    caption = frame.get("caption")
    code_lines = frame.get("lines", [])
    highlight = set(frame.get("highlight", []))
    underlines = frame.get("underlines", [])
    tree = frame.get("tree")

    if caption:
        lines.append(caption)

    if code_lines:
        lines.append("```" + (frame.get("language") or ""))
        for i, line in enumerate(code_lines):
            prefix = ">>> " if i in highlight else "    "
            lines.append(prefix + line)
            for u in underlines:
                if u.get("line") == i:
                    span = u.get("span", [0, 0])
                    label = u.get("label", "")
                    underline = " " * (span[0] + 4) + "^" * max(1, span[1] - span[0])
                    if label:
                        underline += f"  {label}"
                    lines.append(underline)
        lines.append("```")

    if tree:
        lines.append("tree: " + tree.get("label", ""))
        for child in tree.get("children", []):
            lines.append("  - " + child.get("label", ""))

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
    if frame_type == "mermaid_flow":
        return _render_mermaid_flow(frame)
    if frame_type == "code_tree":
        return _render_code_tree(frame)

    # Fallback for unknown frames.
    items = [f"{k}={v!r}" for k, v in frame.items()]
    return " | ".join(items)
