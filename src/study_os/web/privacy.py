"""PII scrubber for learner free text (#95, P-SYS-1, P-LLM-3).

Raw pre-scrub text is never persisted or sent to a model. The scrubber is
conservative: it replaces anything that looks like contact data, network
identifiers, street addresses, or a self-introduced name with a typed token.
"""

from __future__ import annotations

import re

SCRUBBER_VERSION = "study-os.pii-scrubber.v1"

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("[email]", re.compile(r"[A-Za-z0-9._%+-]+\s*(?:@|\(at\)|\[at\])\s*[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("[url]", re.compile(r"(?i)\b(?:https?://|www\.)\S+")),
    ("[ip]", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("[ip]", re.compile(r"(?i)\b(?:[0-9a-f]{1,4}:){3,7}[0-9a-f]{1,4}\b")),
    (
        "[phone]",
        re.compile(r"(?<![\w.])(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![\w.])"),
    ),
    ("[phone]", re.compile(r"(?<![\w.])\+\d[\d\s().-]{8,}\d")),
    (
        "[address]",
        re.compile(
            r"(?i)\b\d{1,6}\s+(?:[A-Z][a-z]+\s+){0,3}"
            r"(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|court|ct|way|place|pl)\b\.?"
        ),
    ),
    ("[postcode]", re.compile(r"\b\d{5}(?:-\d{4})\b")),
    ("[card]", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    (
        "[name]",
        re.compile(
            r"(?i)\b(my name is|i am called|i'm called|call me|this is)\s+[A-Za-z][A-Za-z'-]+(?:\s+[A-Z][A-Za-z'-]+)?"
        ),
    ),
    (
        "[workplace]",
        re.compile(r"(?i)\b(i work (?:at|for|nights at|days at)|my employer is)\s+[^.,;!?\n]+"),
    ),
)

_MAX_LEN = 2000


def scrub(text: str) -> str:
    """Return ``text`` with PII-like spans replaced by typed tokens, capped in length."""

    if not isinstance(text, str):
        raise TypeError("scrub expects str")
    value = text[:_MAX_LEN]
    for token, pattern in _PATTERNS:
        if token in ("[name]", "[workplace]"):
            value = pattern.sub(lambda m: f"{m.group(1)} {token}", value)
        else:
            value = pattern.sub(token, value)
    return value


def contains_pii(text: str) -> bool:
    return scrub(text) != text[:_MAX_LEN]
