#!/usr/bin/env python3
"""Minimal Study OS transcript evidence ingester.

This utility intentionally performs only the deterministic first stage of ingest:
- preserve the source transcript without rewriting it;
- create the session folder boundaries;
- compute SHA-256 evidence hashes;
- create a schema-shaped session manifest.

Semantic normalization, learning-event extraction, and episode inference are later
stages because they require provider-aware parsing and/or model review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_slug(value: str) -> str:
    chars = []
    previous_dash = False
    for char in value.strip().lower():
        if char.isalnum():
            chars.append(char)
            previous_dash = False
        elif not previous_dash:
            chars.append("-")
            previous_dash = True
    return "".join(chars).strip("-") or "session"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preserve a transcript as Study OS session evidence.")
    parser.add_argument("transcript", type=Path, help="Path to the transcript/export to preserve.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--subject", default="subject-001")
    parser.add_argument("--domain", default="dsa")
    parser.add_argument("--concept", action="append", default=[])
    parser.add_argument("--lesson", action="append", default=[])
    parser.add_argument("--provider", default="unknown")
    parser.add_argument("--model", default=None)
    parser.add_argument("--conversation-id", default=None)
    parser.add_argument(
        "--capture-method",
        choices=["export", "copy", "api", "manual", "other"],
        default="export",
    )
    parser.add_argument("--started-at", default=None, help="ISO-8601 timestamp; defaults to current UTC time.")
    parser.add_argument("--session-id", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.transcript.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Transcript does not exist: {source}")

    if args.started_at:
        started = datetime.fromisoformat(args.started_at.replace("Z", "+00:00"))
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
    else:
        started = datetime.now(timezone.utc)

    date_part = started.date().isoformat()
    session_id = args.session_id or f"{started.strftime('%H%M%S')}-{safe_slug(args.domain)}"
    root = args.repo_root.expanduser().resolve()
    session_dir = root / "sessions" / date_part / session_id

    for relative in ["raw", "normalized", "events", "episodes", "derived", "knowledge"]:
        (session_dir / relative).mkdir(parents=True, exist_ok=True)

    suffix = "".join(source.suffixes) or ".bin"
    raw_target = session_dir / "raw" / f"transcript.original{suffix}"
    if raw_target.exists():
        raise SystemExit(f"Refusing to overwrite immutable evidence: {raw_target}")
    shutil.copyfile(source, raw_target)

    raw_hash = sha256_file(raw_target)
    (session_dir / "raw" / "SHA256SUMS").write_text(
        f"{raw_hash}  {raw_target.name}\n", encoding="utf-8"
    )

    # Convenience Markdown mirror only when the source is already text-like.
    if source.suffix.lower() in {".md", ".txt"}:
        markdown_target = session_dir / "raw" / "transcript.md"
        markdown_target.write_bytes(raw_target.read_bytes())

    manifest = {
        "schema_version": "0.1.0",
        "session_id": session_id,
        "subject_id": args.subject,
        "started_at": started.isoformat(),
        "ended_at": None,
        "domain": args.domain,
        "concepts": args.concept,
        "lesson_ids": args.lesson,
        "source": {
            "provider": args.provider,
            "model": args.model,
            "conversation_id": args.conversation_id,
            "capture_method": args.capture_method,
        },
        "raw_artifacts": [
            {
                "path": str(raw_target.relative_to(root)).replace("\\", "/"),
                "media_type": None,
                "sha256": raw_hash,
            }
        ],
        "notes": "Raw evidence captured. Normalization/event extraction not yet performed.",
    }

    manifest_path = session_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "session_id": session_id,
        "session_path": str(session_dir),
        "raw_sha256": raw_hash,
        "next_stage": "normalize transcript, extract learning events, propose episodes",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
