#!/usr/bin/env python3
"""Gate a UX defect summary: fail on ANY P0 or P1.

Fail policy (Alex, 2026-09-27 — ed-tech frontend must work):
- ANY defect with severity P0 or P1 fails the gate (local FE claim or any caller), regardless of confidence.
- Confidence (when present on defects, decisions, or actions) is recorded for
  humans and agents: low confidence => investigate why the model was unsure;
  high confidence => ship the fix without re-litigating the finding.
- Do NOT soft-gate on confidence thresholds. Confidence never skips a P0/P1.

Accepts either:
- schema ``ux-defect-report.v1`` summaries, or
- legacy crawl summaries with a top-level ``defects`` list (bench 2026-09-27).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


BLOCKING = frozenset({"P0", "P1"})


def load_summary(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: summary must be a JSON object")
    defects = data.get("defects")
    if not isinstance(defects, list):
        raise ValueError(f"{path}: missing defects[] array")
    return data


def blocking_defects(defects: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in defects:
        if not isinstance(item, dict):
            continue
        sev = str(item.get("severity") or "").upper()
        if sev in BLOCKING:
            out.append(item)
    return out


def format_defect(d: dict[str, Any]) -> str:
    did = d.get("id") or "?"
    sev = d.get("severity") or "?"
    title = d.get("title") or d.get("component") or d.get("control_label") or ""
    conf = d.get("confidence")
    conf_s = f" confidence={conf}" if isinstance(conf, (int, float)) else ""
    url = d.get("url") or ""
    return f"  - {did} {sev}{conf_s}: {title} @ {url}"


def gate(summary: dict[str, Any], *, path: Path) -> int:
    defects = summary.get("defects") or []
    blocking = blocking_defects(defects)
    p0 = sum(1 for d in blocking if str(d.get("severity")).upper() == "P0")
    p1 = sum(1 for d in blocking if str(d.get("severity")).upper() == "P1")
    p2 = sum(1 for d in defects if isinstance(d, dict) and str(d.get("severity")).upper() == "P2")

    print(f"UX defect gate: {path}")
    print(f"  defects total={len(defects)}  P0={p0}  P1={p1}  P2={p2}")
    print(
        "  fail policy: ANY P0/P1 fails (confidence recorded for investigation,"
        " never a soft-skip)"
    )

    if summary.get("schema_version") == "ux-defect-report.v1":
        print(f"  schema_version=ux-defect-report.v1 pass_field={summary.get('pass')!r}")

    if not blocking:
        print("  RESULT: PASS (no P0/P1)")
        return 0

    print("  RESULT: FAIL — blocking P0/P1 defects:")
    for d in blocking:
        print(format_defect(d))
        conf = d.get("confidence")
        if isinstance(conf, (int, float)) and conf < 0.7:
            print(
                "      note: low confidence — agents should investigate why;"
                " still failing the job"
            )
        elif isinstance(conf, (int, float)):
            print("      note: high confidence — ship the fix without re-litigating")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "summary",
        type=Path,
        help="Path to summary.json (schema v1 or legacy crawl shape)",
    )
    args = parser.parse_args(argv)
    try:
        summary = load_summary(args.summary)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"UX defect gate: ERROR loading {args.summary}: {exc}", file=sys.stderr)
        return 2
    return gate(summary, path=args.summary)


if __name__ == "__main__":
    raise SystemExit(main())
