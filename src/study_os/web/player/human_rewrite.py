"""Mandatory post-gen plain-human rewrite for learner-visible teach copy.

Applies at generation/regen and at serve time so live player/pack cards stay
short, numbered, and free of AI-blog voice (Refs #126).

Structure (study-os-golden-tutor):
- Numbered sentences: ``1) … 2) …``
- For teach / decomposition, sentence 1 grounds the problem, goal, and what
  the learner will practice (when the source already says that; we never invent
  new facts).
- No walls of text: long paragraphs are split; word budgets trim the tail.

Voice (human-sounding-writing / CGM hsw):
- Concrete short sentences, active verbs.
- Scrub common AI-tell words and participle tails.
- Never expand cognitive load: result is shorter or equal, never longer in
  word count than the input (except a leading number prefix when numbering
  was missing — that overhead is capped and content words do not grow).
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

REWRITE_VERSION = "study-os.human-rewrite.v1"

# Soft word budgets (content words). Tail sentences drop when over budget.
_BUDGET: dict[str, int] = {
    "teach": 90,
    "explain": 50,
    "correct": 40,
    "worked_example": 90,
    "decomposition": 120,
    "rationale": 70,
}

_MAX_SENTENCE_WORDS = 28

# Error-severity AI tells → short replacements (CGM human-sounding-writing).
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
    """Count content tokens; ignore ``1)`` / ``2.`` number prefixes."""

    stripped = re.sub(r"(?m)^\s*\d+[.)]\s*", "", text or "")
    return len(re.findall(r"[A-Za-z0-9']+", stripped))


def _scrub(text: str) -> str:
    out = text
    out = _PARTICIPLE_TAIL.sub("", out)
    for pattern, repl in _WORD_REPLACEMENTS:
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
    # Debris from empty replacements / clause cuts.
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
    """Split into sentences; keep markdown list items as their own units."""

    chunks: list[str] = []
    for block in re.split(r"\n+", text.strip()):
        block = block.strip()
        if not block:
            continue
        if _NUMBERED_LINE.match(block) and not re.search(r"[.!?]\s+[A-Z]", block):
            chunks.append(_strip_number_prefix(block))
            continue
        parts = _SENTENCE_SPLIT.split(block)
        for part in parts:
            clean = _strip_number_prefix(part)
            if clean:
                chunks.append(clean)
    return chunks


def _break_long(sentence: str) -> list[str]:
    words = sentence.split()
    if len(words) <= _MAX_SENTENCE_WORDS:
        return [sentence]
    # Prefer a comma/semicolon cut near the middle.
    mid = len(words) // 2
    for cut in range(mid, max(8, mid - 8), -1):
        token = words[cut - 1]
        if token.endswith((",", ";", ":")):
            left = " ".join(words[:cut]).rstrip(",;:")
            right = " ".join(words[cut:])
            if left and right:
                return _break_long(left + ".") + _break_long(right[0].upper() + right[1:] if right else right)
    # Hard split.
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
            # Keep a shortened first sentence rather than a wall.
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


def _number(sentences: list[str]) -> str:
    lines = []
    for i, sentence in enumerate(sentences, start=1):
        body = _ensure_terminal(_strip_number_prefix(sentence))
        lines.append(f"{i}) {body}")
    return "\n".join(lines)


def rewrite(markdown: str | None, *, kind: Kind = "teach") -> str:
    """Rewrite learner-visible markdown. Idempotent. Never invents facts."""

    if markdown is None:
        return ""
    raw = str(markdown)
    if not raw.strip():
        return ""

    original_words = _content_words(raw)
    scrubbed = _scrub(raw)
    # Preserve fenced blocks untouched by refusing to rewrite if present.
    if "```" in scrubbed or "~~~" in scrubbed:
        return raw.strip()

    sentences: list[str] = []
    for piece in _split_sentences(scrubbed):
        sentences.extend(_break_long(piece))
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return raw.strip()

    budget = _BUDGET.get(kind, 90)
    sentences = _apply_budget(sentences, budget)

    _FLUFF_OPEN = re.compile(
        r"^(?:also|moreover|in this (?:lesson|section)|today we|we (?:look|explore)|"
        r"let us explore|this (?:full|strong|key))\b",
        re.IGNORECASE,
    )
    # Only reorder when the opener is fluff; keep a concrete authored opener as #1.
    if kind in ("teach", "decomposition") and sentences and _FLUFF_OPEN.match(sentences[0]):
        for idx in range(1, min(len(sentences), 4)):
            if _looks_grounded(sentences[idx]) and not _FLUFF_OPEN.match(sentences[idx]):
                sentences = [sentences[idx]] + sentences[:idx] + sentences[idx + 1 :]
                break

    numbered = _number(sentences)

    # Never grow content-word count vs input (number prefixes excluded).
    if _content_words(numbered) > original_words and original_words > 0:
        flat = []
        for piece in _split_sentences(_scrub(raw)):
            flat.extend(_break_long(piece))
        numbered = _number(_apply_budget(flat, budget))
        if _content_words(numbered) > original_words:
            # Still prefer numbered short form: trim words to fit.
            while _content_words(numbered) > original_words and len(flat) > 1:
                flat = flat[:-1]
                numbered = _number(flat)
            if _content_words(numbered) > original_words:
                numbered = _number(flat[:1])

    return numbered


@lru_cache(maxsize=512)
def rewrite_cached(markdown: str, kind: Kind = "teach") -> str:
    """LRU wrapper for hot serve paths (identical lesson strings)."""

    return rewrite(markdown, kind=kind)
