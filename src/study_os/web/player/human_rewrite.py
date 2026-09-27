"""Mandatory post-gen plain-human rewrite for learner-visible teach copy.

Applies at generation/regen and at serve time so live player/pack cards stay
short, plain, and free of AI-blog voice (Refs #126).

Structure (A19 revised after live feedback):
- Prefer 2–3 short plain sentences for teach (hard cap 3).
- No digit-prefixed lists (``1) 2) 3)``) — those distract more than they help.
- Step-1 still grounds problem/goal/learn as the first prose sentence when the
  source already says that; we never invent new facts.
- No walls of text: long paragraphs are split; word budgets trim the tail.

Voice (human-sounding-writing / CGM hsw):
- Concrete short sentences, active verbs.
- Scrub common AI-tell words and participle tails.
- Never expand cognitive load: result is shorter or equal in content-word count.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Literal

Kind = Literal[
    "teach",
    "explain",
    "correct",
    "worked_example",
    "decomposition",
    "rationale",
]

REWRITE_VERSION = "study-os.human-rewrite.v2"

_BUDGET: dict[str, int] = {
    "teach": 42,
    "explain": 36,
    "correct": 28,
    "worked_example": 48,
    "decomposition": 64,
    "rationale": 40,
}

_MAX_SENTENCES: dict[str, int] = {
    "teach": 3,
    "explain": 3,
    "correct": 2,
    "worked_example": 3,
    "decomposition": 4,
    "rationale": 3,
}

_MAX_SENTENCE_WORDS = 22

_WORD_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bdelving\b", "looking"),
    (r"\bdelves\b", "looks"),
    (r"\bdelved\b", "looked"),
    (r"\bdelve\b", "look"),
    (r"\bunderscoring\b", "showing"),
    (r"\bunderscores\b", "shows"),
    (r"\bunderscored\b", "showed"),
    (r"\bunderscore\b", "show"),
    (r"\bshowcasing\b", "showing"),
    (r"\bshowcases\b", "shows"),
    (r"\bshowcased\b", "showed"),
    (r"\bshowcase\b", "show"),
    (r"\bhighlighting\b", "showing"),
    (r"\bhighlights\b", "shows"),
    (r"\bhighlighted\b", "showed"),
    (r"\bhighlight\b", "show"),
    (r"\bleveraging\b", "using"),
    (r"\bleverages\b", "uses"),
    (r"\bleverage\b", "use"),
    (r"\butilizing\b", "using"),
    (r"\butilizes\b", "uses"),
    (r"\butilization\b", "use"),
    (r"\butilize\b", "use"),
    (r"\bfacilitating\b", "helping"),
    (r"\bfacilitates\b", "helps"),
    (r"\bfacilitate\b", "help"),
    (r"\bcomprehensive\b", "full"),
    (r"\brobust\b", "strong"),
    (r"\bseamless(?:ly)?\b", "smooth"),
    (r"\bholistic\b", "whole"),
    (r"\bmultifaceted\b", "many-sided"),
    (r"\bpivotal\b", "key"),
    (r"\bcrucial\b", "key"),
    (r"\bintricate\b", "detailed"),
    (r"\bintricacies\b", "details"),
    (r"\brealm\b", "area"),
    (r"\btapestry\b", "mix"),
    (r"\btestament\b", "sign"),
    (r"\bvibrant\b", "lively"),
    (r"\bpalpable\b", "clear"),
    (r"\bamidst\b", "among"),
    (r"(?m)^(?:furthermore|moreover|additionally),?\s*", ""),
    (r"(?<=[.!?])\s+(?:furthermore|moreover|additionally),?\s*", " "),
    (r"\bin order to\b", "to"),
    (r"\bdue to the fact that\b", "because"),
    (r"\ba wide range of\b", "many"),
    (r"\bserves as\b", "is"),
    (r"\bstands as\b", "is"),
    (r"\bit is important to note that\b", ""),
    (r"\bit's important to note that\b", ""),
    (r"\bin conclusion,?\b", ""),
    (r"\bin summary,?\b", ""),
    (r"\bto summarize,?\b", ""),
)

_PARTICIPLE_TAIL = re.compile(
    r",\s+(?:highlighting|underscoring|reflecting|emphasizing)\b[^.!?]*",
    re.IGNORECASE,
)

_NUMBERED_LINE = re.compile(
    r"^\s*(?:\*\*)?(?:\d+[.)]|[-*])\s*(?:\*\*)?(.*)$",
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")

_GROUNDING_CUES = re.compile(
    r"\b(?:you will|you'll|we will|we'll|goal|learn|practice|look at|here|"
    r"this step|problem|compare|find|read|track|start|today)\b",
    re.IGNORECASE,
)


def _content_words(text: str) -> int:
    stripped = re.sub(r"(?m)^\s*(?:\d+[.)]|[-*])\s*", "", text or "")
    return len(re.findall(r"[A-Za-z0-9']+", stripped))


def _scrub(text: str) -> str:
    out = text
    out = _PARTICIPLE_TAIL.sub("", out)
    for pattern, repl in _WORD_REPLACEMENTS:
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
    out = re.sub(r"(?m)^(?:also|but),\s*", "", out, flags=re.I)
    out = re.sub(r"\b(also|but|and|so),\s*(also|but|and)\b", r"\1", out, flags=re.I)
    out = re.sub(r"^[\s,;:]+", "", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r" +([,.;:!?])", r"\1", out)
    out = re.sub(r"([.!?])\s*([a-z])", lambda m: m.group(1) + " " + m.group(2).upper(), out)
    out = re.sub(r"\s+\n", "\n", out)
    out = out.strip()
    if out and out[0].islower():
        out = out[0].upper() + out[1:]
    return out


def _strip_number_prefix(sentence: str) -> str:
    m = _NUMBERED_LINE.match(sentence.strip())
    if m:
        return m.group(1).strip()
    return sentence.strip()


def _split_sentences(text: str) -> list[str]:
    chunks: list[str] = []
    for block in re.split(r"\n+", text.strip()):
        block = block.strip()
        if not block:
            continue
        block = re.sub(r"(?<=[.!?])\s+(?=\d+[.)]\s)", "\n", block)
        block = re.sub(r"(?<![.\d])\s+(?=\d+[.)]\s)", "\n", block)
        for piece in re.split(r"\n+", block):
            piece = piece.strip()
            if not piece:
                continue
            if _NUMBERED_LINE.match(piece) and not re.search(r"[.!?]\s+[A-Z0-9]", piece):
                clean = _strip_number_prefix(piece)
                if clean:
                    chunks.append(clean)
                continue
            for part in _SENTENCE_SPLIT.split(piece):
                clean = _strip_number_prefix(part)
                if clean:
                    chunks.append(clean)
    return chunks


def _break_long(sentence: str) -> list[str]:
    words = sentence.split()
    if len(words) <= _MAX_SENTENCE_WORDS:
        return [sentence]
    mid = len(words) // 2
    for cut in range(mid, max(8, mid - 8), -1):
        token = words[cut - 1]
        if token.endswith((",", ";", ":")):
            left = " ".join(words[:cut]).rstrip(",;:")
            right = " ".join(words[cut:])
            if left and right:
                return _break_long(left + ".") + _break_long(
                    right[0].upper() + right[1:] if right else right
                )
    left = " ".join(words[:mid]).rstrip(",;:")
    right = " ".join(words[mid:])
    if not left.endswith((".", "!", "?")):
        left += "."
    return [left, right[0].upper() + right[1:] if right else right]


def _ensure_terminal(sentence: str) -> str:
    s = sentence.strip()
    if not s:
        return s
    if s[-1] not in ".!?":
        s += "."
    return s


def _looks_grounded(sentence: str) -> bool:
    return bool(_GROUNDING_CUES.search(sentence))


def _apply_budget(sentences: list[str], budget: int) -> list[str]:
    kept: list[str] = []
    used = 0
    for sentence in sentences:
        n = _content_words(sentence)
        if kept and used + n > budget:
            break
        if not kept and n > budget:
            words = sentence.split()
            cut = max(8, budget)
            piece = " ".join(words[:cut]).rstrip(",;:")
            if piece and piece[-1] not in ".!?":
                piece += "."
            kept.append(piece)
            break
        kept.append(sentence)
        used += n
        if used >= budget:
            break
    return kept or sentences[:1]


def _format_prose(sentences: list[str]) -> str:
    lines = []
    for sentence in sentences:
        body = _ensure_terminal(_strip_number_prefix(sentence))
        if body:
            lines.append(body)
    return "\n".join(lines)


def rewrite(markdown: str | None, *, kind: Kind = "teach") -> str:
    if markdown is None:
        return ""
    raw = str(markdown)
    if not raw.strip():
        return ""

    original_words = _content_words(raw)
    scrubbed = _scrub(raw)
    if "```" in scrubbed or "~~~" in scrubbed:
        return raw.strip()

    sentences: list[str] = []
    for piece in _split_sentences(scrubbed):
        sentences.extend(_break_long(piece))
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return raw.strip()

    budget = _BUDGET.get(kind, 42)
    max_sents = _MAX_SENTENCES.get(kind, 3)
    sentences = _apply_budget(sentences, budget)[:max_sents]

    _FLUFF_OPEN = re.compile(
        r"^(?:also|moreover|in this (?:lesson|section)|today we|we (?:look|explore)|"
        r"let us explore|this (?:full|strong|key))\b",
        re.IGNORECASE,
    )
    if kind in ("teach", "decomposition") and sentences and _FLUFF_OPEN.match(sentences[0]):
        for idx in range(1, min(len(sentences), 4)):
            if _looks_grounded(sentences[idx]) and not _FLUFF_OPEN.match(sentences[idx]):
                sentences = [sentences[idx]] + sentences[:idx] + sentences[idx + 1 :]
                break

    prose = _format_prose(sentences)

    if _content_words(prose) > original_words and original_words > 0:
        flat = []
        for piece in _split_sentences(_scrub(raw)):
            flat.extend(_break_long(piece))
        flat = _apply_budget(flat, budget)[:max_sents]
        prose = _format_prose(flat)
        if _content_words(prose) > original_words:
            while _content_words(prose) > original_words and len(flat) > 1:
                flat = flat[:-1]
                prose = _format_prose(flat)
            if _content_words(prose) > original_words:
                prose = _format_prose(flat[:1])

    return prose


@lru_cache(maxsize=512)
def rewrite_cached(markdown: str, kind: Kind = "teach") -> str:
    return rewrite(markdown, kind=kind)
