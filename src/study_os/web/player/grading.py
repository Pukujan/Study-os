"""Answer normalisation and grading.

The public entry point is :func:`grade`.  :func:`normalise` implements all the
rules mandated by the player design, including Unicode fractions, spelled-out
numbers, and voice phrases.  :func:`semantic_match` is a disabled phase-2 hook
that always returns ``None``.
"""

from __future__ import annotations

import fractions
import re
from typing import Any


_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}

# Unicode fraction mappings (U+00BC .. U+00BE, U+2150 .. U+215E, U+2189).
_UNICODE_FRACTIONS = {
    "½": "1/2",
    "¼": "1/4",
    "¾": "3/4",
    "⅐": "1/10",
    "⅑": "1/9",
    "⅒": "1/12",
    "⅓": "1/3",
    "⅔": "2/3",
    "⅕": "1/5",
    "⅖": "2/5",
    "⅗": "3/5",
    "⅘": "4/5",
    "⅙": "1/6",
    "⅚": "5/6",
    "⅛": "1/8",
    "⅜": "3/8",
    "⅝": "5/8",
    "⅞": "7/8",
    "↉": "0/3",
}


_VoiceFractions: list[tuple[tuple[str, ...], str]] = [
    # Order matters: longer / more specific phrases first.
    (("three quarters", "three fourths"), "3/4"),
    (("two thirds",), "2/3"),
    (("one half", "a half"), "1/2"),
    (("one third", "a third"), "1/3"),
    (("one quarter", "a quarter", "one fourth", "a fourth"), "1/4"),
    (("one fifth",), "1/5"),
    (("two quarters",), "2/4"),
    (("three halves",), "3/2"),
]


_NORMAL_FRACTION_PATTERNS = [
    re.compile(r"(?P<num>\d+)\s*\/\s*(?P<den>\d+)"),
]


def _safe_fraction(value: str) -> fractions.Fraction | None:
    """Parse a string as a fraction or decimal, returning None if it fails."""

    value = value.strip()
    if not value:
        return None
    try:
        if "/" in value:
            num, den = value.split("/", 1)
            return fractions.Fraction(int(num), int(den))
        return fractions.Fraction(value)
    except (ValueError, ZeroDivisionError):
        return None


def normalise(response: str, answer_kind: str) -> str:  # noqa: PLR0912
    """Normalise a raw learner response.

    The order of transformations is deliberate:

    1. Strip whitespace and coerce to lower-case.
    2. Replace Unicode minus with ASCII hyphen.
    3. Replace Unicode fraction glyphs with ASCII ``num/den``.
    4. Expand voice phrases such as ``three quarters`` -> ``3/4``.
    5. Expand ``<x> over <y>`` / ``<x> out of <y>`` -> ``x/y``.
    6. Expand spelled-out numbers zero..twenty -> digits.
    7. Strip trailing punctuation.
    8. Collapse internal whitespace.
    """

    if not isinstance(response, str):
        response = str(response)
    text = response.strip().lower()

    # Unicode minus -> hyphen.
    text = text.replace("−", "-")

    # Unicode fractions -> ASCII.
    for glyph, ascii_form in _UNICODE_FRACTIONS.items():
        text = text.replace(glyph, ascii_form)

    # Voice phrases (three quarters, two thirds, one half, etc.).
    for phrases, replacement in _VoiceFractions:
        for phrase in phrases:
            text = re.sub(rf"\b{re.escape(phrase)}\b", replacement, text)

    # Spelled-out numbers zero..twenty -> digits, but only as whole words.
    for word, digit in _NUMBER_WORDS.items():
        text = re.sub(rf"\b{word}\b", str(digit), text)

    # "x over y" and "x out of y" -> x/y (works on digits expanded above).
    text = re.sub(
        r"(\d+)\s+over\s+(\d+)",
        r"\1/\2",
        text,
    )
    text = re.sub(
        r"(\d+)\s+out\s+of\s+(\d+)",
        r"\1/\2",
        text,
    )

    # Remove trailing punctuation.
    text = re.sub(r"[.!?;,]+$", "", text)

    # Collapse whitespace.
    text = " ".join(text.split())

    return text.strip()


def _matches_literal(normalised: str, candidate: str) -> bool:
    """Check whether the normalised response matches a literal accept string."""

    cand_norm = normalise(candidate, "text")
    if normalised == cand_norm:
        return True
    # Allow optional leading "the" on text answers.
    if normalised.lstrip("the ") == cand_norm:
        return True
    return False


def _value_equivalent_fractions(normalised: str, accept: list[str]) -> tuple[str | None, str | None]:
    """Return (simplest_name, note_md) if the response is value-equivalent to an accepted answer.

    If the response is exactly one of the accepted values, no note is returned.
    """

    resp_frac = _safe_fraction(normalised)
    if resp_frac is None:
        return None, None

    # Exact string match: no note needed.
    if any(normalised == a.strip() for a in accept):
        return None, None

    # Value match against a different accepted form.
    for candidate in accept:
        cand_frac = _safe_fraction(candidate)
        if cand_frac is None:
            continue
        if resp_frac == cand_frac:
            simplest = _simplest_name(candidate)
            note = f"same amount — **{simplest}** is the simplest name"
            return simplest, note

    return None, None


def _simplest_name(fraction_str: str) -> str:
    """Return the simplest form of a fraction string."""

    frac = _safe_fraction(fraction_str)
    if frac is None:
        return fraction_str
    return f"{frac.numerator}/{frac.denominator}"


def semantic_match(response: str, candidates: list[str]) -> str | None:
    """Phase-2 semantic matching hook (disabled).

    Currently returns ``None`` unconditionally.  When enabled, this hook will
    use a small embedding model such as MiniLM or bge-small to compare the
    learner response against a list of accepted answers.
    """

    return None


def grade(
    probe: dict[str, Any],
    response: str,
    modality: str,
) -> tuple[str, str | None, str | None]:
    """Grade a learner response against a probe.

    Returns a tuple of ``(outcome, note_or_none, misconception_id_or_none)``.

    * ``outcome`` is ``"correct"``, ``"partial"``, or ``"incorrect"``.
    * ``note`` is an optional markdown note (e.g. value-equivalent fraction note).
    * ``misconception_id`` is set only when a misconception pattern matches.
    """

    answer_kind = probe.get("answer_kind", "text")
    normalised = normalise(response, answer_kind)

    # 1. Semantic hook (disabled for phase 1).
    accept = list(probe.get("accept", []))
    semantic = semantic_match(normalised, accept) if answer_kind == "text" else None
    if semantic:
        return "correct", None, None

    # 2. Direct / value-equivalent correctness.
    if answer_kind == "fraction":
        if any(_matches_literal(normalised, cand) for cand in accept):
            return "correct", None, None
        simplest, note = _value_equivalent_fractions(normalised, accept)
        if simplest:
            return "correct", note, None
    else:
        if any(_matches_literal(normalised, cand) for cand in accept):
            return "correct", None, None

    # 3. Partial matches.
    for partial in probe.get("partial", []):
        for match in partial.get("match", []):
            if _matches_literal(normalised, match):
                return "partial", partial.get("note_md"), None

    # 4. Misconceptions.
    for misc in probe.get("misconceptions", []):
        for match in misc.get("match", []):
            if _matches_literal(normalised, match):
                return "incorrect", misc.get("note_md"), misc.get("id")

    return "incorrect", None, None
