from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

CRITICAL_MARKERS = (
    "study_os.pir.controller.x_classify_response__mutmut_",
    "study_os.pir.controller.x__require_matching_state__mutmut_",
    "study_os.pir.controller.x__apply_transition__mutmut_",
    "study_os.pir.controller.x_build_interaction_bundle__mutmut_",
    "study_os.pir.controller.x_submit_response__mutmut_",
    "study_os.pir.controller.x_build_expansion_bundle__mutmut_",
    "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_problem_operation_check__mutmut_",
    "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_asset_for_state__mutmut_",
    "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_current_problem_bundle__mutmut_",
    "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_persist_problem_run__mutmut_",
    "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_require_fresh_problem_turn__mutmut_",
    "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁstart_problem__mutmut_",
    "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁget_problem_turn__mutmut_",
    "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁsubmit_problem_response__mutmut_",
    "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁrequest_problem_expansion__mutmut_",
)
UNRESOLVED_STATUSES = ("survived", "timeout")


def critical_unresolved(results: str) -> tuple[tuple[str, str], ...]:
    unresolved: list[tuple[str, str]] = []
    for raw_line in results.splitlines():
        line = raw_line.strip()
        for status in UNRESOLVED_STATUSES:
            suffix = f": {status}"
            if not line.endswith(suffix):
                continue
            mutant = line.removesuffix(suffix)
            if any(marker in mutant for marker in CRITICAL_MARKERS):
                unresolved.append((mutant, status))
            break
    return tuple(unresolved)


def critical_survivors(results: str) -> tuple[str, ...]:
    return tuple(
        mutant for mutant, status in critical_unresolved(results) if status == "survived"
    )


def export_unresolved_diffs(results_path: Path, output_path: Path) -> int:
    results = results_path.read_text(encoding="utf-8")
    unresolved = critical_unresolved(results)
    survivor_count = sum(status == "survived" for _, status in unresolved)
    timeout_count = sum(status == "timeout" for _, status in unresolved)
    with output_path.open("w", encoding="utf-8") as output:
        output.write(f"critical_unresolved={len(unresolved)}\n")
        output.write(f"critical_survivors={survivor_count}\n")
        output.write(f"critical_timeouts={timeout_count}\n")
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


def export_survivor_diffs(results_path: Path, output_path: Path) -> int:
    return export_unresolved_diffs(results_path, output_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export diffs for critical surviving or timed-out PIR mutants"
    )
    parser.add_argument("results", nargs="?", type=Path, default=Path("mutmut-results.txt"))
    parser.add_argument(
        "output", nargs="?", type=Path, default=Path("pir-critical-survivor-diffs.txt")
    )
    args = parser.parse_args()
    count = export_unresolved_diffs(args.results, args.output)
    print(f"exported {count} critical unresolved PIR mutant diffs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
