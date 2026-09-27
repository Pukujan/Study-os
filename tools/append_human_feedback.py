#!/usr/bin/env python3
"""Append one Alex/product critique to content/human-feedback/feedback.jsonl.

Does NOT write Postgres. Live in-app reviews stay in ux.feedback;
decomposer ratings stay in ux.decomposer_review; verbatim pedagogy chats
stay under sessions/. This tool only maintains the git JSONL + assets pack
(issue #164).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path

ALLOWED_TAGS = frozenset(
    {
        "too_complex",
        "crash",
        "prefer_graph",
        "no_bullets",
        "simpler_charts",
        "research_first",
        "interactive",
        "invent_forbidden",
        "prefer_dark",
        "design_system",
        "pet_jitter",
        "author_name",
        "catalog_wide",
        "navigation",
        "probe_missing",
        "latency",
        "fractions",
        "other",
    }
)
ALLOWED_SOURCES = frozenset(
    {"chat", "live_player", "issue_comment", "decomposer_review", "session"}
)
ALLOWED_STORES = frozenset(
    {"git.jsonl", "ux.feedback", "ux.decomposer_review", "session"}
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Append a human-feedback JSONL entry (no new DB)."
    )
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    p.add_argument("--text", required=True, help="Scrubbed critique text.")
    p.add_argument(
        "--tag",
        action="append",
        default=[],
        dest="tags",
        help=f"Calibration tag; repeatable. Allowed: {sorted(ALLOWED_TAGS)}",
    )
    p.add_argument("--source", default="chat", choices=sorted(ALLOWED_SOURCES))
    p.add_argument(
        "--store",
        default="git.jsonl",
        choices=sorted(ALLOWED_STORES),
        help="Canonical store pointer (default git.jsonl for this pack).",
    )
    p.add_argument("--author", default="Pukujan")
    p.add_argument("--lesson", default=None, dest="lesson_id")
    p.add_argument("--step", default=None, dest="step_id")
    p.add_argument("--target-kind", default=None)
    p.add_argument("--target-id", default=None)
    p.add_argument("--screenshot", type=Path, default=None)
    p.add_argument("--screenshot-note", default=None)
    p.add_argument("--issue", type=int, action="append", default=[], dest="issues")
    p.add_argument("--session-path", default=None)
    p.add_argument(
        "--ts",
        default=None,
        help="ISO-8601 timestamp (default: now, local offset if available).",
    )
    return p.parse_args()


def load_existing(jsonl: Path) -> list[dict]:
    if not jsonl.is_file():
        return []
    rows = []
    for line in jsonl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    pack = root / "content" / "human-feedback"
    jsonl = pack / "feedback.jsonl"
    assets = pack / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    tags = list(dict.fromkeys(args.tags))  # stable unique
    if not tags:
        print("error: at least one --tag is required", file=sys.stderr)
        return 2
    unknown = set(tags) - ALLOWED_TAGS
    if unknown:
        print(f"error: unknown tags {sorted(unknown)}", file=sys.stderr)
        return 2

    text = args.text.strip()
    if not text:
        print("error: --text must be non-blank", file=sys.stderr)
        return 2

    screenshot = None
    if args.screenshot is not None:
        src = args.screenshot.expanduser().resolve()
        if not src.is_file():
            print(f"error: screenshot not found: {src}", file=sys.stderr)
            return 2
        digest = sha256_file(src)
        dest_name = src.name
        dest = assets / dest_name
        if dest.exists():
            if sha256_file(dest) != digest:
                dest = assets / f"{digest[:12]}-{src.name}"
        if not dest.exists():
            shutil.copy2(src, dest)
        rel = dest.relative_to(root).as_posix()
        screenshot = {"path": rel, "sha256": digest}
        if args.screenshot_note:
            screenshot["note"] = args.screenshot_note

    existing = load_existing(jsonl)
    for row in existing:
        if row.get("text", "").strip() == text and (
            (row.get("screenshot") or {}).get("sha256")
            == (screenshot or {}).get("sha256")
        ):
            print(
                f"error: duplicate text+screenshot already present as {row.get('id')}",
                file=sys.stderr,
            )
            return 3

    ts = args.ts or datetime.now().astimezone().isoformat(timespec="seconds")
    entry = {
        "id": str(uuid.uuid4()),
        "ts": ts,
        "source": args.source,
        "author": args.author,
        "lesson_id": args.lesson_id,
        "step_id": args.step_id,
        "target_kind": args.target_kind or ("step" if args.step_id else None),
        "target_id": args.target_id or args.step_id,
        "text": text,
        "tags": tags,
        "screenshot": screenshot,
        "store": args.store,
        "related_issues": args.issues or [164],
        "promotion": (
            {"session_path": args.session_path}
            if args.session_path
            else {"note": "git.jsonl only; reuse ux.feedback / ux.decomposer_review for live ratings."}
        ),
    }

    with jsonl.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")

    print(json.dumps({"appended": entry["id"], "path": jsonl.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
