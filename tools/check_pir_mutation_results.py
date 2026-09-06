from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

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
HARD_BLOCKING_KEYS = tuple(
    key for key in STATUS_KEYS if key not in {"killed", "survived"}
)

AUDIT_SOURCE_BLOBS = {
    "src/study_os/pir/contracts.py": "6368763e90d1d44d0cbb6dd085a860d679cc8ee1",
    "src/study_os/pir/controller.py": "d7ca54f109e53f9900d5d1bf75c36c4b9586b2b4",
    "src/study_os/services/pir_runtime.py": "b73638f37b8e62269c7f212e3ca15ce801f521af",
}


def _mutants(prefix: str, *numbers: int) -> frozenset[str]:
    return frozenset(f"{prefix}__mutmut_{number}" for number in numbers)


DIAGNOSTIC_MUTANTS = frozenset().union(
    _mutants("study_os.pir.controller.x__apply_transition", 12, 13, 14),
    _mutants("study_os.pir.controller.x__parse_integer", 8, 9, 10),
    _mutants("study_os.pir.controller.x__parse_integer_sequence", 11, 12, 13, 21, 22, 23),
    _mutants("study_os.pir.controller.x__require_matching_state", 5),
    _mutants(
        "study_os.pir.controller.x_build_expansion_bundle",
        9, 10, 11, 18, 19, 20, 26, 27, 28, 36,
    ),
    _mutants(
        "study_os.pir.controller.x_build_interaction_bundle",
        7, 8, 9, 20, 21, 22, 26, 53, 54, 55, 62, 63, 64,
    ),
    _mutants(
        "study_os.pir.controller.x_submit_response",
        9, 10, 11, 18, 19, 20, 27, 35, 36, 37, 48,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_asset_for_state",
        4, 5, 7, 8, 9, 10, 14, 15, 17, 18, 19, 20,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_current_problem_bundle",
        11, 12, 13, 14, 15, 16, 17,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_load_problem_run",
        10, 11, 12, 14, 15, 16, 17, 18,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_persist_problem_run",
        14, 15, 17, 18, 19, 20,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_problem_operation_check",
        4, 5, 6, 23, 24, 25, 27, 28, 29, 30, 31,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_require_fresh_problem_turn",
        4, 5, 6, 15, 16, 17, 19, 20, 21, 22, 25, 26, 27, 28, 30, 31, 32, 33, 34,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁrequest_problem_expansion",
        4, 5, 6, 9, 10, 11, 59, 60,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁresolve_problem",
        6, 7, 19, 20, 21, 32, 33, 34,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁstart_problem",
        29, 30, 31, 32, 33, 34, 35,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁsubmit_problem_response",
        4, 5, 6, 53, 54,
    ),
)

EQUIVALENT_MUTANTS = frozenset().union(
    _mutants("study_os.pir.controller.x_build_expansion_bundle", 60, 68, 72),
    _mutants("study_os.pir.controller.x_build_interaction_bundle", 49, 50, 78),
    _mutants("study_os.pir.controller.x_submit_response", 33, 75, 93),
    _mutants("study_os.pir.controller.x_validate_asset", 72, 100, 102),
    _mutants("study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_load_problem_run", 7, 8),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_persist_problem_run",
        7, 8, 10, 11,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_problem_operation_check",
        13, 14, 16, 17, 20, 35,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_problem_operation_record",
        6, 7, 9, 11, 12,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_state_from_row",
        28, 30, 32, 34, 36, 38, 40, 42, 44, 47, 49,
    ),
    _mutants("study_os.services.pir_runtime.xǁPIRRuntimeMixinǁ_terminal_bundle", 20, 39),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁrequest_problem_expansion",
        85, 86, 88, 90, 92, 101, 102,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁstart_problem",
        52, 53, 55, 57, 59, 61, 62,
    ),
    _mutants(
        "study_os.services.pir_runtime.xǁPIRRuntimeMixinǁsubmit_problem_response",
        79, 80, 82, 84, 86, 102, 103, 105, 107, 109,
    ),
)

AUDITED_NONBLOCKING_MUTANTS = DIAGNOSTIC_MUTANTS | EQUIVALENT_MUTANTS

if DIAGNOSTIC_MUTANTS & EQUIVALENT_MUTANTS:
    raise RuntimeError("mutation audit classifications overlap")
if len(AUDITED_NONBLOCKING_MUTANTS) != 204:
    raise RuntimeError(
        "mutation audit inventory drifted: "
        f"expected 204 entries, found {len(AUDITED_NONBLOCKING_MUTANTS)}"
    )


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


def load_results(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise ValueError(f"mutation results file is missing: {path}") from exc

    results: dict[str, str] = {}
    for raw_line in lines:
        line = raw_line.strip()
        mutant, separator, status = line.rpartition(": ")
        if not separator or status not in STATUS_KEYS or not mutant:
            continue
        if mutant in results:
            raise ValueError(f"mutation results contain duplicate mutant: {mutant}")
        results[mutant] = status
    return results


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def validate_source_audit(root: Path) -> tuple[str, ...]:
    errors: list[str] = []
    for relative_path, expected_sha in AUDIT_SOURCE_BLOBS.items():
        path = root / relative_path
        try:
            observed_sha = git_blob_sha(path)
        except FileNotFoundError:
            errors.append(f"audited production source is missing: {relative_path}")
            continue
        if observed_sha != expected_sha:
            errors.append(
                "audited production source changed and survivor classifications must be redone: "
                f"{relative_path} expected={expected_sha} observed={observed_sha}"
            )
    return tuple(errors)


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

    for key in HARD_BLOCKING_KEYS:
        if stats[key] != 0:
            errors.append(f"blocking mutation status {key}={stats[key]}")

    return tuple(errors)


def validate_results(stats: dict[str, int], results: dict[str, str]) -> tuple[str, ...]:
    errors: list[str] = []
    if len(results) != stats["total"]:
        errors.append(
            "mutation results do not contain the complete measured population: "
            f"total={stats['total']}, results={len(results)}"
        )

    for status in STATUS_KEYS:
        observed = sum(result == status for result in results.values())
        if observed != stats[status]:
            errors.append(
                f"mutation results disagree with stats for {status}: "
                f"stats={stats[status]}, results={observed}"
            )

    survivors = {mutant for mutant, status in results.items() if status == "survived"}
    unclassified = sorted(survivors - AUDITED_NONBLOCKING_MUTANTS)
    if unclassified:
        errors.append(
            "unresolved non-equivalent or unaudited survivors remain: "
            + ", ".join(unclassified)
        )
    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce the Study OS PIR mutation gate")
    parser.add_argument(
        "stats",
        nargs="?",
        type=Path,
        default=Path("mutants/mutmut-cicd-stats.json"),
    )
    parser.add_argument(
        "results",
        nargs="?",
        type=Path,
        default=Path("mutmut-results.txt"),
    )
    args = parser.parse_args()

    try:
        stats = load_stats(args.stats)
        results = load_results(args.results)
    except ValueError as exc:
        print(f"PIR mutation gate failed: {exc}")
        return 1

    errors = [*validate_stats(stats), *validate_results(stats, results)]
    if stats["survived"]:
        errors.extend(validate_source_audit(ROOT))

    print(
        "PIR mutation results: "
        + ", ".join(f"{key}={stats[key]}" for key in ("total", *STATUS_KEYS))
    )
    survived = {mutant for mutant, status in results.items() if status == "survived"}
    print(
        "PIR mutation audit: "
        f"diagnostic={len(survived & DIAGNOSTIC_MUTANTS)}, "
        f"equivalent={len(survived & EQUIVALENT_MUTANTS)}, "
        f"unclassified={len(survived - AUDITED_NONBLOCKING_MUTANTS)}"
    )

    if errors:
        for error in errors:
            print(f"PIR mutation gate failed: {error}")
        return 1

    print(
        "PIR mutation gate passed: no unresolved non-equivalent semantic survivors "
        "or runner failures remain."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
