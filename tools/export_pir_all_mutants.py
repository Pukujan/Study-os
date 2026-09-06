from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

UNRESOLVED_STATUSES = ("survived", "timeout")


def unresolved_mutants(results: str) -> tuple[tuple[str, str], ...]:
    unresolved: list[tuple[str, str]] = []
    for raw_line in results.splitlines():
        line = raw_line.strip()
        for status in UNRESOLVED_STATUSES:
            suffix = f": {status}"
            if line.endswith(suffix):
                unresolved.append((line.removesuffix(suffix), status))
                break
    return tuple(unresolved)


def export_unresolved_diffs(results_path: Path, output_path: Path) -> int:
    unresolved = unresolved_mutants(results_path.read_text(encoding="utf-8"))
    survivor_count = sum(status == "survived" for _, status in unresolved)
    timeout_count = sum(status == "timeout" for _, status in unresolved)
    with output_path.open("w", encoding="utf-8") as output:
        output.write(f"unresolved={len(unresolved)}\n")
        output.write(f"survivors={survivor_count}\n")
        output.write(f"timeouts={timeout_count}\n")
        for mutant, status in unresolved:
            output.write("\n" + "=" * 100 + "\n")
            output.write(f"{mutant}: {status}\n")
            completed = subprocess.run(
                ["mutmut", "show", mutant],
                check=False,
                capture_output=True,
                text=True,
            )
            output.write(completed.stdout)
            if completed.stderr:
                output.write("\n[stderr]\n")
                output.write(completed.stderr)
            if completed.returncode != 0:
                output.write(f"\n[mutmut show exit={completed.returncode}]\n")
    return len(unresolved)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export diffs for every unresolved PIR mutant")
    parser.add_argument("results", nargs="?", type=Path, default=Path("mutmut-results.txt"))
    parser.add_argument(
        "output", nargs="?", type=Path, default=Path("pir-all-unresolved-diffs.txt")
    )
    args = parser.parse_args()
    count = export_unresolved_diffs(args.results, args.output)
    print(f"exported {count} unresolved PIR mutant diffs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
