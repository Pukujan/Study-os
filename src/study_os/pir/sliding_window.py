"""Canonical sliding-window lesson built from the two reviewed goldens.

Source goldens (owned by Study OS):

- ``domains/dsa/sliding-window/golden/beginner-progressive-box-index-sum.v0.1.md``
- ``domains/dsa/sliding-window/golden/beginner-sum-enumerate-append.v0.1.md``

Scope stops where the second golden stops (``enumerate(a)`` and ``append``). Loop
assembly, ``max``, the ``else`` bridge, the stop condition, and ``range(k)`` are
recorded as follow-up in ``tasks/TASK-SOS-0002-sliding-window-golden-lesson.md``.

Every golden concept follows the same deterministic feedback graph:

- introduce the relation once (arrows or highlights allowed);
- ask one tiny question on an exercise chart without answer-revealing parts;
- correct answer: show why on the same chart, then ask again until the concept's
  required number of consecutive correct answers is reached;
- wrong answer: show the right answer on the same chart, reassure, retry with a
  different example, and require one more correct check before advancing;
- partial answer: keep the correct part and ask only for the missing step.

Step ids encode ``<concept>.e<example>.n<correct answers still needed>``. The
controller keeps no counters, so the counter lives in the step id.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from .contracts import (
    AssessmentKind,
    AssessmentSpec,
    ExpansionKind,
    ExpansionSpec,
    LearnerOutcome,
    RepresentationSpec,
    ResponseKind,
    RunStatus,
    StepKind,
    TeachingStep,
    TransitionSpec,
)

PROBLEM_STATEMENT = "Find the largest sum of any 3 numbers next to each other in the array."
REASSURANCE = "It’s okay, let’s keep trying."
MASTERY_DISCLAIMER = "Independent mastery is not established by finishing these checks."

A = (4, 7, 2, 6, 1, 9)
B = (3, 8, 1, 5, 2, 7)
C = (5, 2, 8, 4, 7, 1)

LABEL_WIDTH = 15
CELL = 4
ENUM_LABEL_WIDTH = 18
ENUM_CELL = 7

# Components that may never appear on an exercise chart, per concept. The
# independent oracle in domains/dsa/sliding-window/golden/ re-checks these.
PROBE_FORBIDDEN: dict[str, tuple[str, ...]] = {
    "position": ("highlight", "answer_marked"),
    "index": ("highlight", "answer_marked"),
    "box_size_k": ("highlight", "answer_marked", "window_box"),
    "box_start_i": ("highlight", "answer_marked", "window_box"),
    "window_sum": ("highlight", "answer_marked"),
    "successive_sums": ("highlight", "answer_marked"),
    "recurrence_repetition": ("highlight", "answer_marked"),
    "enumerate": (
        "highlight",
        "answer_marked",
        "pair_row",
        "current_pair_highlight",
        "window_box",
    ),
    "append": ("highlight", "answer_marked", "append_form", "value_bracket"),
}


@dataclass(frozen=True)
class Rep:
    markdown: str
    components: tuple[str, ...]


# ---------------------------------------------------------------------------
# Chart rendering. Every chart is produced from structured parameters, and the
# components are declared by the same function, so declarations match the text.
# ---------------------------------------------------------------------------


def _place(buffer: list[str], column: int, text: str) -> None:
    while len(buffer) < column + len(text):
        buffer.append(" ")
    for offset, character in enumerate(text):
        buffer[column + offset] = character


def _line(placements: Sequence[tuple[int, str]]) -> str:
    buffer: list[str] = []
    for column, text in placements:
        _place(buffer, column, text)
    return "".join(buffer).rstrip()


def _col(index: int) -> int:
    return LABEL_WIDTH + CELL * index


def _grid_row(label: str, values: Sequence[int], circled: int | None) -> str:
    placements: list[tuple[int, str]] = [(0, label)]
    for index, value in enumerate(values):
        if index == circled:
            placements.append((_col(index) - 1, f"({value})"))
        else:
            placements.append((_col(index), str(value)))
    return _line(placements)


@dataclass(frozen=True)
class Box:
    start: int
    size: int
    labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class Grid:
    """One array chart: optional position/index rows, numbers, pointers, boxes."""

    numbers: Sequence[int]
    show_index: bool = True
    show_position: bool = False
    top_pointer: tuple[int, str] | None = None
    bottom_pointer: tuple[int, tuple[str, ...]] | None = None
    circled: int | None = None
    boxes: tuple[Box, ...] = ()
    free_labels: tuple[str, ...] = ()
    extra_components: tuple[str, ...] = field(default_factory=tuple)

    def render(self) -> tuple[str, tuple[str, ...]]:
        lines: list[str] = []
        components: list[str] = ["numbers_row"]
        highlight = False
        if self.top_pointer is not None:
            column, label = self.top_pointer
            lines.append(_line([(_col(column) - 2, label)]))
            lines.append(_line([(_col(column), "↓")]))
            highlight = True
        if self.show_index:
            lines.append(_grid_row("index(i):", range(len(self.numbers)), self.circled))
            components.append("index_row")
        if self.show_position:
            lines.append(
                _grid_row("positions(p):", range(1, len(self.numbers) + 1), self.circled)
            )
            components.append("position_row")
        lines.append(_grid_row("numbers(a):", self.numbers, self.circled))
        if self.circled is not None:
            highlight = True
        if self.bottom_pointer is not None:
            column, labels = self.bottom_pointer
            lines.append(_line([(_col(column), "↑")]))
            for label in labels:
                lines.append(_line([(_col(column) - 2, label)]))
            highlight = True
        for number, box in enumerate(self.boxes):
            if number:
                lines.append("")
            first, last = _col(box.start), _col(box.start + box.size - 1)
            lines.append(_line([(_col(box.start + k), "↑") for k in range(box.size)]))
            width = last - first + 1
            inner = width - 2
            title = " box "
            if inner >= len(title) + 2:
                left = (inner - len(title)) // 2
                fill = "─" * left + title + "─" * (inner - len(title) - left)
            else:
                fill = "─" * inner
            lines.append(_line([(first, "└" + fill + "┘")]))
            for label in box.labels:
                lines.append(_line([(first, label)]))
        if self.boxes:
            components.append("window_box")
        if len(self.boxes) > 1:
            components.append("next_box")
        if self.free_labels:
            lines.append("")
            lines.extend(self.free_labels)
        labels = [*self.free_labels, *(label for box in self.boxes for label in box.labels)]
        if any(label.startswith("k = ") for label in labels):
            components.append("k_label")
        if any(label.startswith("i = ") for label in labels):
            components.append("i_label")
        if any(label.startswith("sum[") for label in labels):
            components.append("sum_label")
        if highlight:
            components.append("highlight")
        components.extend(self.extra_components)
        return "```text\n" + "\n".join(lines) + "\n```", tuple(components)


def _rep(*parts: str | Grid, components: Sequence[str] = ()) -> Rep:
    rendered: list[str] = []
    collected: list[str] = []
    for part in parts:
        if isinstance(part, Grid):
            text, grid_components = part.render()
            rendered.append(text)
            collected.extend(grid_components)
        else:
            rendered.append(part)
    collected.extend(components)
    unique = tuple(dict.fromkeys(collected))
    return Rep(markdown="\n\n".join(rendered), components=unique)


def _code(text: str, language: str = "text") -> str:
    return f"```{language}\n{text}\n```"


def _values(values: Sequence[int]) -> str:
    return ", ".join(str(value) for value in values)


def _and(values: Sequence[int]) -> str:
    items = [str(value) for value in values]
    if len(items) <= 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _plus(values: Sequence[int]) -> str:
    return " + ".join(str(value) for value in values)


# ---------------------------------------------------------------------------
# Lesson data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Partial:
    """Correct part acknowledged, missing step isolated as its own probe."""

    acknowledge: Rep
    finish_probe: Rep
    finish_assessment: AssessmentSpec
    finish_response: ResponseKind
    finish_why: Rep
    finish_fix: Rep


@dataclass(frozen=True)
class Example:
    probe: Rep
    why: Rep
    fix: Rep
    assessment: AssessmentSpec
    response: ResponseKind
    partial: Partial | None = None


@dataclass(frozen=True)
class Concept:
    concept_id: str
    intro: Rep
    examples: tuple[Example, ...]
    initial_need: int = 2
    why_expansion: Rep | None = None
    easier_expansion: Rep | None = None


def _tag(concept_id: str) -> str:
    return f"relation:{concept_id}"


def _fix_text(answer: str) -> str:
    return f"The right answer is **{answer}**."


def _correct_text(answer: str) -> str:
    return f"Correct — **{answer}**."


# ---------------------------------------------------------------------------
# Golden 1: beginner-progressive-box-index-sum.v0.1
# ---------------------------------------------------------------------------


def _problem() -> Rep:
    return _rep(
        "We’re learning how to solve this question:",
        f"**{PROBLEM_STATEMENT}**",
        "I’ll help you learn this step by step.",
        _code("numbers(a): [" + ", ".join(str(value) for value in A) + "]"),
        "`a = numbers`",
        components=("numbers_row", "problem_anchor", _tag("problem")),
    )


def _position_chart(index: int | None) -> Grid:
    if index is None:
        return Grid(numbers=A, show_index=False, show_position=True)
    return Grid(
        numbers=A,
        show_index=False,
        show_position=True,
        top_pointer=(index, f"p = {index + 1}"),
        bottom_pointer=(index, (f"a = {A[index]}",)),
    )


def _position() -> Concept:
    tag = _tag("position")

    def example(index: int) -> Example:
        value, position = A[index], index + 1
        relation = f"`number(a)` is `{value}` and its `position(p)` is `{position}`."
        return Example(
            probe=_rep(
                _position_chart(None),
                f"**What is `position(p)` of `number(a) {value}`?**",
                components=(tag,),
            ),
            why=_rep(
                _correct_text(str(position)),
                _position_chart(index),
                relation,
                components=(tag, "answer_marked"),
            ),
            fix=_rep(
                _fix_text(str(position)),
                _position_chart(index),
                relation,
                REASSURANCE,
                components=(tag, "answer_marked", "reassurance"),
            ),
            assessment=AssessmentSpec(
                assessment_id=f"a.position.v{value}",
                kind=AssessmentKind.INTEGER,
                expected_values=(position,),
            ),
            response=ResponseKind.INTEGER,
        )

    return Concept(
        concept_id="position",
        intro=_rep(
            "Each number has a **position(p)**. Positions count from 1.",
            _position_chart(2),
            "`number(a)` is `2` and its `position(p)` is `3`.",
            components=(tag,),
        ),
        examples=(example(3), example(4), example(5), example(1)),
        why_expansion=_rep(
            "`position(p)` counts the numbers from the left, starting at 1.",
            _position_chart(0),
            components=(tag,),
        ),
    )


def _index_chart(index: int | None) -> Grid:
    if index is None:
        return Grid(numbers=A, show_position=True)
    return Grid(
        numbers=A,
        show_position=True,
        top_pointer=(index, f"i = {index}"),
        bottom_pointer=(index, (f"p = {index + 1}", f"a = {A[index]}")),
        circled=index,
    )


def _index() -> Concept:
    tag = _tag("index")

    def example(index: int) -> Example:
        value = A[index]
        relation = f"`i = p - 1 = {index + 1} - 1 = {index}`"
        return Example(
            probe=_rep(
                _index_chart(None),
                f"**What is the `index(i)` of `number(a) {value}`?**",
                components=(tag,),
            ),
            why=_rep(
                _correct_text(str(index)),
                _index_chart(index),
                relation,
                components=(tag, "answer_marked"),
            ),
            fix=_rep(
                _fix_text(str(index)),
                _index_chart(index),
                relation,
                REASSURANCE,
                components=(tag, "answer_marked", "reassurance"),
            ),
            assessment=AssessmentSpec(
                assessment_id=f"a.index.v{value}",
                kind=AssessmentKind.INTEGER,
                expected_values=(index,),
            ),
            response=ResponseKind.INTEGER,
        )

    return Concept(
        concept_id="index",
        intro=_rep(
            _index_chart(2),
            "`index(i) = position(p) - 1`",
            "`i = p - 1`",
            components=(tag,),
        ),
        examples=(example(3), example(5), example(1), example(4)),
        why_expansion=_rep(
            "Python counts from 0, so every index is one less than its position.",
            _index_chart(0),
            components=(tag,),
        ),
    )


def _box_size() -> Concept:
    tag = _tag("box_size_k")

    def example(size: int) -> Example:
        inside = A[:size]
        box = Grid(numbers=A, boxes=(Box(0, size, (f"k = {size}",)),))
        meaning = f"`k = {size}` means the box holds **{size} numbers**."
        return Example(
            probe=_rep(
                Grid(numbers=A, free_labels=(f"k = {size}",)),
                "**What numbers go inside the box?**",
                components=(tag,),
            ),
            why=_rep(
                _correct_text(_values(inside)),
                box,
                meaning,
                components=(tag, "answer_marked"),
            ),
            fix=_rep(
                _fix_text(_values(inside)),
                box,
                meaning,
                REASSURANCE,
                components=(tag, "answer_marked", "reassurance"),
            ),
            assessment=AssessmentSpec(
                assessment_id=f"a.box_size_k.k{size}",
                kind=AssessmentKind.INTEGER_SEQUENCE,
                expected_values=tuple(inside),
            ),
            response=ResponseKind.INTEGER_SEQUENCE,
        )

    return Concept(
        concept_id="box_size_k",
        intro=_rep(
            "`k` = how many numbers go inside the box.",
            "Here: `k = 3`",
            Grid(numbers=A, boxes=(Box(0, 3, ("k = 3",)),)),
            "The box holds `4, 7, 2`.",
            components=(tag,),
        ),
        examples=(example(5), example(2), example(4), example(6)),
        why_expansion=_rep(
            "`k` only counts how many numbers fit in the box. Start at the left and "
            "count `k` numbers.",
            Grid(numbers=A, boxes=(Box(0, 2, ("k = 2",)),)),
            components=(tag,),
        ),
    )


def _box_start() -> Concept:
    tag = _tag("box_start_i")

    def example(start: int, size: int) -> Example:
        inside = A[start : start + size]
        box = Grid(numbers=A, boxes=(Box(start, size, (f"i = {start}", f"k = {size}")),))
        meaning = f"The box starts at `i = {start}` and holds `k = {size}` numbers."
        return Example(
            probe=_rep(
                Grid(numbers=A, free_labels=(f"i = {start}", f"k = {size}")),
                "**What numbers go inside the box?**",
                components=(tag,),
            ),
            why=_rep(
                _correct_text(_values(inside)),
                box,
                meaning,
                components=(tag, "answer_marked"),
            ),
            fix=_rep(
                _fix_text(_values(inside)),
                box,
                meaning,
                REASSURANCE,
                components=(tag, "answer_marked", "reassurance"),
            ),
            assessment=AssessmentSpec(
                assessment_id=f"a.box_start_i.i{start}k{size}",
                kind=AssessmentKind.INTEGER_SEQUENCE,
                expected_values=tuple(inside),
            ),
            response=ResponseKind.INTEGER_SEQUENCE,
        )

    return Concept(
        concept_id="box_start_i",
        intro=_rep(
            "`i` = where the box starts.",
            Grid(numbers=A, boxes=(Box(0, 2, ("i = 0", "k = 2")),)),
            "Here, the box starts at `i = 0`.",
            components=(tag,),
        ),
        examples=(
            example(1, 2),
            example(3, 2),
            example(2, 3),
            example(4, 2),
            example(1, 3),
        ),
        why_expansion=_rep(
            "`k` says how many numbers. `i` says where the box starts. Move the box so "
            "its first number is at index `i`.",
            Grid(numbers=A, boxes=(Box(2, 2, ("i = 2", "k = 2")),)),
            components=(tag,),
        ),
    )


def _window_sum() -> Concept:
    tag = _tag("window_sum")

    def boxed(start: int, size: int, *extra: str) -> Grid:
        return Grid(
            numbers=A,
            boxes=(Box(start, size, (f"k = {size}", f"sum[i={start}]", *extra)),),
        )

    def example(start: int, size: int, *, show_box: bool) -> Example:
        inside = A[start : start + size]
        total = sum(inside)
        equation = f"`sum[i={start}] = {_plus(inside)} = {total}`"
        probe_chart = (
            boxed(start, size)
            if show_box
            else Grid(numbers=A, free_labels=(f"i = {start}", f"k = {size}"))
        )
        return Example(
            probe=_rep(
                probe_chart,
                f"**What is `sum[i={start}]`?**",
                components=(tag,),
            ),
            why=_rep(
                _correct_text(str(total)),
                boxed(start, size),
                equation,
                components=(tag, "answer_marked"),
            ),
            fix=_rep(
                _fix_text(str(total)),
                boxed(start, size),
                equation,
                REASSURANCE,
                components=(tag, "answer_marked", "reassurance"),
            ),
            assessment=AssessmentSpec(
                assessment_id=f"a.window_sum.i{start}k{size}",
                kind=AssessmentKind.INTEGER,
                expected_values=(total,),
                partial_values=tuple(inside),
            ),
            response=ResponseKind.INTEGER,
            partial=Partial(
                acknowledge=_rep(
                    f"Those are the right numbers: **{_and(inside)}**.",
                    boxed(start, size),
                    "Now only the adding is left.",
                    components=(tag, "partial_ack"),
                ),
                finish_probe=_rep(
                    boxed(start, size),
                    f"**`{_plus(inside)} = ?`**",
                    components=(tag,),
                ),
                finish_assessment=AssessmentSpec(
                    assessment_id=f"a.window_sum.i{start}k{size}.add",
                    kind=AssessmentKind.INTEGER,
                    expected_values=(total,),
                ),
                finish_response=ResponseKind.INTEGER,
                finish_why=_rep(
                    _correct_text(str(total)),
                    boxed(start, size),
                    equation,
                    components=(tag, "answer_marked"),
                ),
                finish_fix=_rep(
                    _fix_text(str(total)),
                    boxed(start, size),
                    equation,
                    REASSURANCE,
                    components=(tag, "answer_marked", "reassurance"),
                ),
            ),
        )

    return Concept(
        concept_id="window_sum",
        intro=_rep(
            "Now we introduce `sum[i]`: add the numbers inside the box that starts at `i`.",
            boxed(0, 3),
            "`sum[i=0] = 4 + 7 + 2 = 13`",
            components=(tag,),
        ),
        examples=(
            example(2, 3, show_box=True),
            example(2, 2, show_box=False),
            example(3, 3, show_box=False),
            example(0, 2, show_box=False),
            example(1, 3, show_box=False),
        ),
        why_expansion=_rep(
            "`i` tells us where the box starts. `k` tells us how many numbers it holds. "
            "`sum[i]` adds exactly those numbers.",
            boxed(1, 2),
            components=(tag,),
        ),
        easier_expansion=_rep(
            "Smaller example: the box at `i = 0` with `k = 2` holds `4` and `7`, so "
            "`sum[i=0] = 4 + 7 = 11`. Use the same box-to-sum steps on the question.",
            boxed(0, 2),
            components=(tag,),
        ),
    )


# ---------------------------------------------------------------------------
# Golden 2: beginner-sum-enumerate-append.v0.1
# ---------------------------------------------------------------------------


def _sum_label(offset: int) -> str:
    return "sum[i]" if offset == 0 else f"sum[i+{offset}]"


def _successive() -> Concept:
    tag = _tag("successive_sums")

    def chart(size: int, offset: int, known: int, answer: int | None) -> Grid:
        shown = "?" if answer is None else str(answer)
        return Grid(
            numbers=B,
            boxes=(
                Box(offset, size, (f"{_sum_label(offset)} = {known}",)),
                Box(offset + 1, size, (f"{_sum_label(offset + 1)} = {shown}",)),
            ),
            free_labels=(f"k = {size}",),
        )

    def example(size: int, offset: int) -> Example:
        known = sum(B[offset : offset + size])
        answer = sum(B[offset + 1 : offset + 1 + size])
        leaving, entering = B[offset], B[offset + size]
        update = _code(f"{known} - {leaving} + {entering} = {answer}")
        label = _sum_label(offset + 1)
        return Example(
            probe=_rep(
                chart(size, offset, known, None),
                f"**What is `{label}`?**",
                components=(tag,),
            ),
            why=_rep(
                _correct_text(str(answer)),
                chart(size, offset, known, answer),
                update,
                components=(tag, "answer_marked"),
            ),
            fix=_rep(
                _fix_text(str(answer)),
                chart(size, offset, known, answer),
                update,
                REASSURANCE,
                components=(tag, "answer_marked", "reassurance"),
            ),
            assessment=AssessmentSpec(
                assessment_id=f"a.successive_sums.k{size}o{offset + 1}",
                kind=AssessmentKind.INTEGER,
                expected_values=(answer,),
            ),
            response=ResponseKind.INTEGER,
        )

    return Concept(
        concept_id="successive_sums",
        intro=_rep(
            "Same box, new numbers. The box starts at `i`, and `k = 3`.",
            Grid(numbers=B, boxes=(Box(0, 3, ("sum[i] = 12",)),), free_labels=("k = 3",)),
            "`sum[i] = 3 + 8 + 1 = 12`. Next, the box moves one step to the right.",
            components=(tag,),
        ),
        # The first three examples are the golden sequence sum[i+1] -> sum[i+3];
        # all three must be answered before the recurrence appears.
        examples=(example(3, 0), example(3, 1), example(3, 2), example(2, 0), example(2, 1)),
        initial_need=3,
        why_expansion=_rep(
            "When the box moves one step right, one number leaves on the left and one "
            "number enters on the right. Every other number stays inside.",
            chart(3, 0, 12, 14),
            components=(tag,),
        ),
    )


def _recurrence() -> Concept:
    tag = _tag("recurrence_repetition")
    formula = "S[i] = S[i-1] - a[i-1] + a[i+j]"

    def chart(numbers: Sequence[int], index: int, label: str) -> Grid:
        return Grid(numbers=numbers, boxes=(Box(index, 3, (label,)),), free_labels=("k = 3",))

    def example(numbers: Sequence[int], index: int) -> Example:
        previous = sum(numbers[index - 1 : index + 2])
        answer = sum(numbers[index : index + 3])
        leaving, entering = numbers[index - 1], numbers[index + 2]
        instance = f"S[{index}] = S[{index - 1}] - a[{index - 1}] + a[{index}+2]"
        given = f"S[{index - 1}] = {previous}"
        solved = _code(f"{instance}\nS[{index}] = {previous} - {leaving} + {entering} = {answer}")
        return Example(
            probe=_rep(
                chart(numbers, index, f"S[{index}] = ?"),
                _code(f"j = k - 1 = 2\n{formula}\n\n{given}\ni = {index}\n{instance}"),
                f"**What is `S[{index}]`?**",
                components=(tag, "recurrence_equation"),
            ),
            why=_rep(
                _correct_text(str(answer)),
                chart(numbers, index, f"S[{index}] = {answer}"),
                solved,
                "Same formula, new `i`.",
                components=(tag, "recurrence_equation", "answer_marked"),
            ),
            fix=_rep(
                _fix_text(str(answer)),
                chart(numbers, index, f"S[{index}] = {answer}"),
                solved,
                REASSURANCE,
                components=(tag, "recurrence_equation", "answer_marked", "reassurance"),
            ),
            assessment=AssessmentSpec(
                assessment_id=f"a.recurrence_repetition.{''.join(map(str, numbers))}.i{index}",
                kind=AssessmentKind.INTEGER,
                expected_values=(answer,),
            ),
            response=ResponseKind.INTEGER,
        )

    instances = "\n\n".join(
        f"i = {i}\nS[{i}] = S[{i - 1}] - a[{i - 1}] + a[{i}+2]" for i in (1, 2, 3)
    )
    return Concept(
        concept_id="recurrence_repetition",
        intro=_rep(
            chart(B, 0, "S[0] = 12"),
            _code("j = k - 1 = 2"),
            _code(formula),
            _code(instances),
            _code("same formula\n↓\nnew i each turn\n↓\nrepeat"),
            components=(tag, "recurrence_equation", "j_label", "recurrence_instances"),
        ),
        examples=(example(B, 1), example(B, 2), example(B, 3), example(A, 1), example(A, 2)),
        why_expansion=_rep(
            "`S[i-1]` is the previous box sum. `a[i-1]` is the number that leaves. "
            "`a[i+j]` is the number that enters.",
            chart(B, 1, "S[1]"),
            components=(tag, "recurrence_equation"),
        ),
    )


def _enum_line(label: str, cells: Sequence[str]) -> str:
    placements: list[tuple[int, str]] = [(0, label)]
    for index, cell in enumerate(cells):
        column = ENUM_LABEL_WIDTH + ENUM_CELL * index
        # A marked cell opens its bracket one column early so the value stays aligned.
        placements.append((column - 1 if cell.startswith("[") else column, cell))
    return _line(placements)


def _enumerate_chart(
    numbers: Sequence[int], *, pairs: bool, marked: int | None = None
) -> tuple[str, tuple[str, ...]]:
    def cell(index: int, text: str) -> str:
        return f"[{text}]" if index == marked else text

    lines = [
        "numbers(a):      [" + ",  ".join(str(value) for value in numbers) + "]",
        "",
        "enumerate(a)",
        "      ↓",
        "",
        _enum_line("index(i):", [cell(i, str(i)) for i in range(len(numbers))]),
        _enum_line("", ["│"] * len(numbers)),
        _enum_line("number(num):", [cell(i, str(v)) for i, v in enumerate(numbers)]),
    ]
    components = ["numbers_row", "index_row", "number_row", "enumerate_relation"]
    if pairs:
        lines.append(_enum_line("", ["│"] * len(numbers)))
        lines.append(
            _enum_line("pair:", [cell(i, f"({i},{v})") for i, v in enumerate(numbers)])
        )
        components.append("pair_row")
    if marked is not None:
        components.extend(["current_pair_highlight", "highlight"])
    return "```text\n" + "\n".join(lines) + "\n```", tuple(components)


def _enumerate() -> Concept:
    tag = _tag("enumerate")

    def chart_rep(
        numbers: Sequence[int], *text: str, pairs: bool, marked: int | None, extra: Sequence[str]
    ) -> Rep:
        chart, components = _enumerate_chart(numbers, pairs=pairs, marked=marked)
        before = [part for part in text if part.startswith(("Correct", "The right"))]
        after = [part for part in text if part not in before]
        return Rep(
            markdown="\n\n".join([*before, chart, *after]),
            components=tuple(dict.fromkeys([*components, tag, *extra])),
        )

    def example(numbers: Sequence[int], value: int) -> Example:
        index = numbers.index(value)
        pair = f"({index}, {value})"
        meaning = f"At `a = {value}`, the index is `{index}`, so the pair is `({index},{value})`."
        return Example(
            probe=chart_rep(
                numbers,
                f"**When the loop reaches `a = {value}`, what pair does `enumerate(a)` give us?**",
                pairs=False,
                marked=None,
                extra=(),
            ),
            why=chart_rep(
                numbers,
                _correct_text(pair),
                meaning,
                pairs=True,
                marked=index,
                extra=("answer_marked",),
            ),
            fix=chart_rep(
                numbers,
                _fix_text(pair),
                meaning,
                REASSURANCE,
                pairs=True,
                marked=index,
                extra=("answer_marked", "reassurance"),
            ),
            assessment=AssessmentSpec(
                assessment_id=f"a.enumerate.{''.join(map(str, numbers))}.v{value}",
                kind=AssessmentKind.INTEGER_SEQUENCE,
                expected_values=(index, value),
            ),
            response=ResponseKind.INTEGER_SEQUENCE,
        )

    intro_chart, intro_components = _enumerate_chart(A, pairs=True)
    return Concept(
        concept_id="enumerate",
        intro=Rep(
            markdown="\n\n".join(
                [
                    intro_chart,
                    "`enumerate(a)` goes through `a` and gives the **index and number together**.",
                    _code("for i, num in enumerate(a):", "python"),
                    "means each turn takes one `(index, number)` pair.",
                ]
            ),
            components=(*intro_components, tag),
        ),
        # Golden: two successful checks were enough (6 -> (3,6), then 8 -> (2,8)).
        examples=(example(A, 6), example(C, 8), example(C, 7), example(A, 9)),
        why_expansion=chart_rep(
            A,
            "Each turn, `enumerate(a)` hands over the index from the top row and the number "
            "from the row below it, together.",
            pairs=False,
            marked=None,
            extra=(),
        ),
    )


def _append_chart() -> Grid:
    return Grid(numbers=B, boxes=(Box(1, 3, ("S[i]",)),), free_labels=("k = 3",))


def _mapping(value: str) -> str:
    width = len(value) + 2
    return _code(
        "Algebra:\n"
        f"S[i] = {value}\n"
        f"       └{'─' * (width - 2)}┘\n"
        "        value to store\n\n"
        "Append:\n"
        f"S.append( {value} )\n"
        f"          └{'─' * (width - 2)}┘\n"
        "            same value"
    )


def _append() -> Concept:
    tag = _tag("append")

    def example(value: str) -> Example:
        answer = f"S.append({value})"
        algebra = _code(f"S[i] = {value}")
        return Example(
            probe=_rep(
                _append_chart(),
                algebra,
                "**How do you write this line with `S.append(...)`?**",
                components=(tag, "algebra_form"),
            ),
            why=_rep(
                f"Correct — `{answer}`.",
                _append_chart(),
                _mapping(value),
                "Only the storage changes. The value stays the same.",
                components=(
                    tag,
                    "algebra_form",
                    "append_form",
                    "value_bracket",
                    "answer_marked",
                ),
            ),
            fix=_rep(
                f"The right answer is `{answer}`.",
                _append_chart(),
                _mapping(value),
                "Only the storage changes. The value stays the same.",
                REASSURANCE,
                components=(
                    tag,
                    "algebra_form",
                    "append_form",
                    "value_bracket",
                    "answer_marked",
                    "reassurance",
                ),
            ),
            assessment=AssessmentSpec(
                assessment_id=f"a.append.{value.replace(' ', '')}",
                kind=AssessmentKind.TEXT,
                expected_text=(answer,),
                partial_text=(value,),
            ),
            response=ResponseKind.CODE,
            partial=Partial(
                acknowledge=_rep(
                    f"That value is right: `{value}`.",
                    _append_chart(),
                    algebra,
                    "Only the storage part is missing: `S[i] = ...` becomes `S.append(...)`.",
                    components=(tag, "algebra_form", "partial_ack"),
                ),
                finish_probe=_rep(
                    _append_chart(),
                    algebra,
                    f"**Put `{value}` inside `S.append(...)`. What is the full line?**",
                    components=(tag, "algebra_form"),
                ),
                finish_assessment=AssessmentSpec(
                    assessment_id=f"a.append.{value.replace(' ', '')}.storage",
                    kind=AssessmentKind.TEXT,
                    expected_text=(answer,),
                ),
                finish_response=ResponseKind.CODE,
                finish_why=_rep(
                    f"Correct — `{answer}`.",
                    _append_chart(),
                    _mapping(value),
                    components=(
                        tag,
                        "algebra_form",
                        "append_form",
                        "value_bracket",
                        "answer_marked",
                    ),
                ),
                finish_fix=_rep(
                    f"The right answer is `{answer}`.",
                    _append_chart(),
                    _mapping(value),
                    REASSURANCE,
                    components=(
                        tag,
                        "algebra_form",
                        "append_form",
                        "value_bracket",
                        "answer_marked",
                        "reassurance",
                    ),
                ),
            ),
        )

    recurrence_value = "S[i-1] - a[i-1] + a[i+j]"
    return Concept(
        concept_id="append",
        intro=_rep(
            _append_chart(),
            _mapping(recurrence_value),
            _code("S[i] = ...\n   ↓\nS.append(...)"),
            "The expression on the right does not change.",
            components=(tag, "algebra_form", "append_form", "value_bracket"),
        ),
        examples=(
            example("S[i-1] + a[i]"),
            example("S[i-1] + num"),
            example("S[i-1] - a[i-1]"),
            example("a[i] + a[i+1]"),
        ),
        why_expansion=_rep(
            "`S[i] = ...` stores a value at index `i`. `S.append(...)` stores the same value "
            "at the end of `S`, which is index `i` when `S` is built one box at a time.",
            _append_chart(),
            components=(tag,),
        ),
    )


def _frontier() -> Rep:
    return _rep(
        "This is where the reviewed lesson stops for now.",
        _append_chart(),
        _code(
            "consecutive sums     sum[i] → sum[i+1] → sum[i+2] → sum[i+3]\n"
            "same formula, new i  S[i] = S[i-1] - a[i-1] + a[i+j]\n"
            "enumerate(a)         one (i, num) pair each turn\n"
            "append               S[i] = ...  becomes  S.append(...)"
        ),
        "The next lesson joins these pieces into one Python loop, one piece at a time.",
        MASTERY_DISCLAIMER,
        components=("frontier_summary",),
    )


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

GOLDEN_CONCEPTS: tuple[Callable[[], Concept], ...] = (
    _position,
    _index,
    _box_size,
    _box_start,
    _window_sum,
    _successive,
    _recurrence,
    _enumerate,
    _append,
)

ENTRY_STEP_ID = "problem.intro"
FRONTIER_STEP_ID = "frontier.assembled"


@dataclass
class _Builder:
    representations: dict[str, RepresentationSpec] = field(default_factory=dict)
    assessments: dict[str, AssessmentSpec] = field(default_factory=dict)
    steps: list[TeachingStep] = field(default_factory=list)
    expansions: list[ExpansionSpec] = field(default_factory=list)

    def rep(self, representation_id: str, rep: Rep) -> str:
        spec = RepresentationSpec(
            representation_id=representation_id,
            learner_visible_markdown=rep.markdown,
            visible_components=rep.components,
        )
        existing = self.representations.get(representation_id)
        if existing is not None and existing != spec:
            raise RuntimeError(f"conflicting representation {representation_id}")
        self.representations[representation_id] = spec
        return representation_id

    def assessment(self, spec: AssessmentSpec) -> str:
        existing = self.assessments.get(spec.assessment_id)
        if existing is not None and existing != spec:
            raise RuntimeError(f"conflicting assessment {spec.assessment_id}")
        self.assessments[spec.assessment_id] = spec
        return spec.assessment_id

    def auto(
        self,
        step_id: str,
        kind: StepKind,
        representation_id: str,
        target: str | None,
        exit_status: RunStatus | None = None,
    ) -> None:
        spec = self.representations[representation_id]
        self.steps.append(
            TeachingStep(
                step_id=step_id,
                kind=kind,
                representation_id=representation_id,
                required_components=spec.visible_components,
                automatic_transition=(
                    TransitionSpec(exit_status=exit_status)
                    if exit_status is not None
                    else TransitionSpec(next_step_id=target)
                ),
            )
        )

    def probe(
        self,
        step_id: str,
        concept_id: str,
        representation_id: str,
        assessment_id: str,
        response: ResponseKind,
        routes: Sequence[tuple[LearnerOutcome, str]],
    ) -> None:
        spec = self.representations[representation_id]
        self.steps.append(
            TeachingStep(
                step_id=step_id,
                kind=StepKind.PROBE,
                representation_id=representation_id,
                required_components=spec.visible_components,
                forbidden_components=PROBE_FORBIDDEN[concept_id],
                response_kind=response,
                assessment_id=assessment_id,
                outcome_transitions=tuple(
                    TransitionSpec(outcome=outcome, next_step_id=target)
                    for outcome, target in routes
                ),
            )
        )


def _probe_id(concept_id: str, example: int, need: int) -> str:
    return f"{concept_id}.e{example}.n{need}"


def _add_concept(builder: _Builder, concept: Concept, next_entry: str) -> str:
    """Add one concept's graph and return its entry step id."""

    cid = concept.concept_id
    count = len(concept.examples)
    intro_id = f"{cid}.intro"
    builder.rep(f"r.{intro_id}", concept.intro)
    builder.auto(intro_id, StepKind.EXPLAIN, f"r.{intro_id}", _probe_id(cid, 0, concept.initial_need))

    why_rep = (
        builder.rep(f"r.{cid}.why", concept.why_expansion)
        if concept.why_expansion is not None
        else None
    )
    easier_rep = (
        builder.rep(f"r.{cid}.easier", concept.easier_expansion)
        if concept.easier_expansion is not None
        else None
    )

    def after_correct(example: int, need: int) -> str:
        return next_entry if need <= 1 else _probe_id(cid, (example + 1) % count, need - 1)

    def after_error(example: int) -> str:
        return _probe_id(cid, (example + 1) % count, 2)

    pending = [(0, concept.initial_need)]
    seen: set[tuple[int, int]] = set()
    while pending:
        example_index, need = pending.pop(0)
        if (example_index, need) in seen:
            continue
        seen.add((example_index, need))
        example = concept.examples[example_index]
        base = f"r.{cid}.e{example_index}"
        probe_rep = builder.rep(f"{base}.probe", example.probe)
        why = builder.rep(f"{base}.why", example.why)
        fix = builder.rep(f"{base}.fix", example.fix)
        assessment_id = builder.assessment(example.assessment)
        step_id = _probe_id(cid, example_index, need)

        routes: list[tuple[LearnerOutcome, str]] = [
            (LearnerOutcome.CORRECT, f"{step_id}.why"),
            (LearnerOutcome.INCORRECT, f"{step_id}.fix"),
        ]
        if example.partial is not None:
            routes.append((LearnerOutcome.PARTIAL, f"{step_id}.partial"))
        builder.probe(step_id, cid, probe_rep, assessment_id, example.response, routes)
        builder.auto(f"{step_id}.why", StepKind.EXPLAIN, why, after_correct(example_index, need))
        builder.auto(f"{step_id}.fix", StepKind.CORRECT, fix, after_error(example_index))
        if why_rep is not None:
            builder.expansions.append(
                ExpansionSpec(step_id=step_id, kind=ExpansionKind.WHY, representation_id=why_rep)
            )
        if easier_rep is not None:
            builder.expansions.append(
                ExpansionSpec(
                    step_id=step_id,
                    kind=ExpansionKind.EASIER_EXAMPLE,
                    representation_id=easier_rep,
                )
            )

        following = (example_index + 1) % count
        if need > 1:
            pending.append((following, need - 1))
        pending.append((following, 2))

        partial = example.partial
        if partial is not None:
            ack = builder.rep(f"{base}.partial", partial.acknowledge)
            finish_rep = builder.rep(f"{base}.finish", partial.finish_probe)
            finish_why = builder.rep(f"{base}.finish.why", partial.finish_why)
            finish_fix = builder.rep(f"{base}.finish.fix", partial.finish_fix)
            finish_assessment = builder.assessment(partial.finish_assessment)
            finish_id = f"{step_id}.finish"
            builder.auto(f"{step_id}.partial", StepKind.CORRECT, ack, finish_id)
            builder.probe(
                finish_id,
                cid,
                finish_rep,
                finish_assessment,
                partial.finish_response,
                (
                    (LearnerOutcome.CORRECT, f"{finish_id}.why"),
                    (LearnerOutcome.INCORRECT, f"{finish_id}.fix"),
                ),
            )
            # Golden: after the partial answer is completed, verify with one more example.
            verify = _probe_id(cid, (example_index + 1) % count, 1)
            builder.auto(f"{finish_id}.why", StepKind.EXPLAIN, finish_why, verify)
            builder.auto(f"{finish_id}.fix", StepKind.CORRECT, finish_fix, after_error(example_index))
            pending.append(((example_index + 1) % count, 1))
    return intro_id


def build_sliding_window_graph() -> tuple[
    str,
    tuple[RepresentationSpec, ...],
    tuple[AssessmentSpec, ...],
    tuple[TeachingStep, ...],
    tuple[ExpansionSpec, ...],
]:
    builder = _Builder()
    concepts = [factory() for factory in GOLDEN_CONCEPTS]

    builder.rep("r.problem.intro", _problem())
    # Entry ids are deterministic, so the problem step can point at the first concept.
    builder.auto(ENTRY_STEP_ID, StepKind.EXPLAIN, "r.problem.intro", f"{concepts[0].concept_id}.intro")
    for position, concept in enumerate(concepts):
        next_entry = (
            f"{concepts[position + 1].concept_id}.intro"
            if position + 1 < len(concepts)
            else FRONTIER_STEP_ID
        )
        _add_concept(builder, concept, next_entry)

    builder.rep("r.frontier.assembled", _frontier())
    builder.auto(
        FRONTIER_STEP_ID,
        StepKind.ASSEMBLE,
        "r.frontier.assembled",
        None,
        exit_status=RunStatus.ASSEMBLED_MASTERY_UNPROVEN,
    )
    return (
        ENTRY_STEP_ID,
        tuple(builder.representations.values()),
        tuple(builder.assessments.values()),
        tuple(builder.steps),
        tuple(builder.expansions),
    )
