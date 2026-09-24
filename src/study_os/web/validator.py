"""Deterministic validator for learner-visible generated text (P-LLM-1, P-LLM-2)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .privacy import contains_pii

VALIDATOR_VERSION = "study-os.web-validator.v1"
MASTERY_PATTERNS = (
    r"\bmaster",
    r"\byou(?:'ve|’ve| have)? (?:now )?(?:learned|mastered|know)\b",
    r"\bfully understand",
    r"\bproficien",
)
_NUMBER_WORDS = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
    8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
    15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty",
}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    codes: tuple[str, ...]


def _answer_patterns(forbidden: tuple[str, ...]) -> list[re.Pattern[str]]:
    pats: list[re.Pattern[str]] = []
    for token in forbidden:
        token = token.strip()
        if not token:
            continue
        pats.append(re.compile(r"(?<![\w.])" + re.escape(token) + r"(?![\w])", re.IGNORECASE))
        if token.lstrip("-").isdigit() and int(token) in _NUMBER_WORDS:
            pats.append(re.compile(r"\b" + _NUMBER_WORDS[int(token)] + r"\b", re.IGNORECASE))
    return pats


def validate_generated(
    markdown: str,
    *,
    forbidden_answers: tuple[str, ...],
    required_blocks: tuple[str, ...],
    word_budget: int = 140,
    new_relations: int = 1,
) -> ValidationResult:
    codes: list[str] = []
    text = markdown or ""
    prose = re.sub(r"```.*?```", " ", text, flags=re.S)
    for pat in _answer_patterns(forbidden_answers):
        if pat.search(prose):
            codes.append("ANSWER_REVEAL_FORBIDDEN")
            break
    if any(re.search(p, text, re.IGNORECASE) for p in MASTERY_PATTERNS):
        codes.append("MASTERY_CLAIM")
    if text.count("?") > 1:
        codes.append("MULTI_QUESTION")
    if new_relations != 1:
        codes.append("MULTI_RELATION")
    for block in required_blocks:
        if block and block not in text:
            codes.append("MISSING_REPRESENTATION")
            break
    if len(prose.split()) > word_budget:
        codes.append("WORD_BUDGET")
    if re.search(r"(?i)\b(?:https?://|www\.)", text):
        codes.append("LINK")
    if contains_pii(prose):
        codes.append("PII")
    if not prose.strip():
        codes.append("EMPTY")
    return ValidationResult(ok=not codes, codes=tuple(codes))


def code_blocks(markdown: str) -> tuple[str, ...]:
    return tuple(m.group(0) for m in re.finditer(r"```.*?```", markdown or "", flags=re.S))
