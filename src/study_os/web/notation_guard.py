"""Fail-closed gate for new learner-visible mathematical function notation.

Prevent the LLM from inventing symbols such as W(n), T(n), or S[i] that have
not been *authored and defined* in this lesson step. This intentionally checks
a bounded syntax family. It does not replace the PIR lexical/ontology adapter
or prove that all mathematical symbols and semantics are correct.
"""
from __future__ import annotations

import re
from typing import Any

# Mathematical function / indexed-symbol notation, not ordinary prose.
_SYMBOL = re.compile(r"(?<![A-Za-z0-9_])([A-Z][A-Za-z0-9_]*)\s*(?:\([^()\n]{1,36}\)|\[[^\[\]\n]{1,36}\])")
_IDENTIFIER = re.compile(r"^[A-Z][A-Za-z0-9_]*$")


def approved_symbols(lesson: dict[str, Any], state: dict[str, Any]) -> tuple[str, ...]:
    """Only curated step metadata can authorize new symbols, never model output.

    teach.approved_notation entries are {symbol: "W", definition: "..."}.
    An undefined, malformed or model-provided declaration does not count.
    """
    step = lesson["steps"][state["step_index"]]
    teach = step.get("teach") or {}
    raw = teach.get("approved_notation") or []
    if not isinstance(raw, list):
        return ()
    symbols: set[str] = set()
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        name, definition = entry.get("symbol"), entry.get("definition")
        if (isinstance(name, str) and _IDENTIFIER.fullmatch(name)
                and isinstance(definition, str) and len(definition.strip()) >= 12):
            symbols.add(name)
    return tuple(sorted(symbols))


def notation_violations(markdown: str, authorized: tuple[str, ...]) -> tuple[str, ...]:
    """Reject unregistered function-like notation (e.g. W(3), S[i])."""
    allowed = set(authorized)
    invented = {match.group(1) for match in _SYMBOL.finditer(markdown or "") if match.group(1) not in allowed}
    return tuple(f"UNAPPROVED_NOTATION:{name}" for name in sorted(invented))
