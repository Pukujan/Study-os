from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

STATUS_KEYS = (
    "killed",
    "survived",
    "no_tests",
    "skipped",
    "suspicious",
    "timeout",
    "check_was_interrupted_by_user",
    "segfault",
)
BLOCKING_KEYS = tuple(key for key in STATUS_KEYS if key != "killed")


def load_stats(path: Path) -> dict[str, int]:
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"mutation stats file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"mutation stats file is not valid JSON: {path}") from exc

    if not isinstance(raw, dict):
        raise ValueError("mutation stats must be a JSON object")

    required = {"total", *STATUS_KEYS}
    missing = sorted(required - raw.keys())
    if missing:
        raise ValueError(f"mutation stats are missing required keys: {', '.join(missing)}")

    stats: dict[str, int] = {}
    for key in required:
        value = raw[key]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"mutation stat {key} must be a non-negative integer")
        stats[key] = value
    return stats


def validate_stats(stats: dict[str, int]) -> tuple[str, ...]:
    errors: list[str] = []
    total = stats["total"]
    if total <= 0:
        errors.append("mutation run produced no mutants")

    accounted = sum(stats[key] for key in STATUS_KEYS)
    if accounted != total:
        errors.append(
            "mutation run is incomplete or contains an unmodeled status: "
            f"total={total}, accounted={accounted}"
        )

    if stats["killed"] <= 0:
        errors.append("mutation run killed no mutants")

    for key in BLOCKING_KEYS:
        if stats[key] != 0:
            errors.append(f"blocking mutation status {key}={stats[key]}")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce the Study OS PIR mutation gate")
    parser.add_argument(
        "stats",
        nargs="?",
        type=Path,
        default=Path("mutants/mutmut-cicd-stats.json"),
    )
    args = parser.parse_args()

    try:
        stats = load_stats(args.stats)
    except ValueError as exc:
        print(f"PIR mutation gate failed: {exc}")
        return 1

    errors = validate_stats(stats)
    print(
        "PIR mutation results: "
        + ", ".join(f"{key}={stats[key]}" for key in ("total", *STATUS_KEYS))
    )
    if errors:
        for error in errors:
            print(f"PIR mutation gate failed: {error}")
        return 1

    print("PIR mutation gate passed: every measured mutant was killed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
