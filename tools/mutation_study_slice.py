#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_os.experimental.mutation_study import (  # noqa: E402
    StudySliceError,
    get_status,
    get_turn,
    start_run,
    submit_choice,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Local mutation-testing Study OS slice")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start")
    start.add_argument("--db", type=Path, required=True)
    start.add_argument("--subject-id", required=True)

    next_turn = sub.add_parser("next")
    next_turn.add_argument("--db", type=Path, required=True)
    next_turn.add_argument("--run-id", required=True)

    respond = sub.add_parser("respond")
    respond.add_argument("--db", type=Path, required=True)
    respond.add_argument("--run-id", required=True)
    respond.add_argument("--choice", required=True)
    respond.add_argument("--assistance-level", default="A0")

    status = sub.add_parser("status")
    status.add_argument("--db", type=Path, required=True)
    status.add_argument("--run-id", required=True)

    args = parser.parse_args()
    try:
        if args.command == "start":
            result = start_run(args.db, args.subject_id)
        elif args.command == "next":
            result = get_turn(args.db, args.run_id)
        elif args.command == "respond":
            result = submit_choice(
                args.db,
                args.run_id,
                args.choice,
                args.assistance_level,
            )
        else:
            result = get_status(args.db, args.run_id)
    except StudySliceError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2

    print(json.dumps({"ok": True, "result": result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
