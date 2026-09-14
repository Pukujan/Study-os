#!/usr/bin/env python3
"""Acceptance gate for the first model/schema-driven Study OS tutoring pilot.

This checker is deliberately implementation-independent. It evaluates the learner-visible
transcript against the calibrated DSA corpus and, for final acceptance, requires a small
machine-readable decision trace proving that the turn came from the model-tutoring path.

The first required pilot is `contains-duplicate-set`, which currently fails closed with
`needs_compilation`. Passing this gate means the unsupported problem is taught dynamically
without exposing product-internal compilation state and without jumping ahead of the
calibrated teaching progression.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "datasets" / "dsa-conversation-replay.v0.1.json"
DEFAULT_TRANSCRIPT = ROOT / "artifacts" / "model-tutoring-contains-duplicate.jsonl"
DEFAULT_TRACE = ROOT / "artifacts" / "model-tutoring-contains-duplicate-trace.jsonl"
DEFAULT_SCENARIO = "contains-duplicate-set"
TRACE_SCHEMA_VERSION = "study-os.model-tutoring-trace.v0.1"

INTERNAL_LEAKAGE = (
    "needs_compilation",
    "needs compilation",
    "reviewed problem asset",
    "reviewed asset",
    "canonical asset",
    "problem alias",
    "compile the problem",
)

ALLOWED_DIAGNOSES = {
    "none",
    "missing_prerequisite",
    "concept_failure",
    "representation_interference",
    "identifier_interference",
    "information_overload",
    "information_underload",
    "decomposition_too_coarse",
    "over_decomposition",
    "over_help",
    "uncertain_mixed",
}

ALLOWED_OPERATIONS = {
    "explain",
    "clarify",
    "probe",
    "smaller_step",
    "show_trace",
    "change_representation",
    "give_hint",
    "assemble",
}

STAGE_TO_CONCEPT = {
    "anchor": "duplicate_meaning",
    "box-meaning": "box_meaning",
    "membership": "membership",
    "order": "check_before_add",
    "loop": "loop_assembly",
}

STAGE_REQUIRED_VARIABLES = {
    "anchor": {"nums"},
    "box-meaning": {"box", "num"},
    "membership": {"box", "num"},
    "order": {"box", "num"},
    "loop": {"nums", "box", "num"},
}

REQUIRED_TRACE_FIELDS = {
    "schema_version",
    "scenario_id",
    "turn_index",
    "path_kind",
    "target_concept",
    "diagnosis_family",
    "operation",
    "assistance_level",
    "advance",
    "allowed_variables",
    "forbidden_variables",
    "visual_required",
    "prompt_version",
    "model_identifier",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_number} must contain a JSON object")
        rows.append(row)
    return rows


def find_scenario(corpus: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    scenarios = corpus.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError("corpus scenarios must be a list")
    for scenario in scenarios:
        if isinstance(scenario, dict) and scenario.get("id") == scenario_id:
            return scenario
    raise ValueError(f"scenario {scenario_id!r} not found in corpus")


def nonempty_line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def has_visual(text: str) -> bool:
    """Conservative visual signal: fenced block, table/box lines, or explicit arrows."""

    return (
        "```" in text
        or "|" in text
        or "→" in text
        or "->" in text
        or "[" in text and "]" in text and "\n" in text
    )


def _failure(code: str, turn_index: int | None, detail: str) -> dict[str, Any]:
    return {"code": code, "turn_index": turn_index, "detail": detail}


def _scenario_rows(rows: list[dict[str, Any]], scenario_id: str) -> list[dict[str, Any]]:
    selected = [row for row in rows if row.get("scenario_id") == scenario_id]
    return sorted(selected, key=lambda row: int(row.get("turn_index", -1)))


def evaluate_transcript(
    transcript_rows: list[dict[str, Any]],
    scenario: dict[str, Any],
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    scenario_id = str(scenario["id"])
    expected_turns = scenario.get("turns")
    if not isinstance(expected_turns, list):
        raise ValueError("scenario turns must be a list")

    rows = _scenario_rows(transcript_rows, scenario_id)
    if len(rows) != len(expected_turns):
        failures.append(
            _failure(
                "TURN_COUNT",
                None,
                f"expected {len(expected_turns)} exchanges, found {len(rows)}",
            )
        )

    by_index = {row.get("turn_index"): row for row in rows}
    for index, calibration_turn in enumerate(expected_turns):
        row = by_index.get(index)
        if row is None:
            failures.append(_failure("MISSING_TURN", index, "exchange is missing"))
            continue

        learner_signal = str(row.get("learner_signal", ""))
        expected_signal = str(calibration_turn.get("learner_signal", ""))
        if learner_signal != expected_signal:
            failures.append(
                _failure(
                    "LEARNER_SIGNAL_DRIFT",
                    index,
                    f"expected {expected_signal!r}, found {learner_signal!r}",
                )
            )

        teacher = row.get("teacher_message")
        if not isinstance(teacher, str) or not teacher.strip():
            failures.append(_failure("EMPTY_TEACHER_RESPONSE", index, "teacher response is empty"))
            continue

        lowered = teacher.lower()
        for phrase in INTERNAL_LEAKAGE:
            if phrase in lowered:
                failures.append(
                    _failure(
                        "PRODUCT_INTERNAL_STATE_LEAK",
                        index,
                        f"learner-visible response contains {phrase!r}",
                    )
                )

        expected = calibration_turn.get("expected")
        if not isinstance(expected, dict):
            raise ValueError(f"calibration turn {index} is missing expected contract")

        must_include_any = expected.get("must_include_any", [])
        if must_include_any and not any(str(term).lower() in lowered for term in must_include_any):
            failures.append(
                _failure(
                    "CALIBRATED_ANCHOR_MISSING",
                    index,
                    f"expected at least one of {must_include_any!r}",
                )
            )

        for forbidden in expected.get("must_not_include", []):
            forbidden_text = str(forbidden).lower()
            if forbidden_text and forbidden_text in lowered:
                failures.append(
                    _failure(
                        "FUTURE_OR_FORBIDDEN_CONCEPT",
                        index,
                        f"response contains forbidden term {forbidden!r}",
                    )
                )

        for forbidden_alias in scenario.get("forbidden_aliases", []):
            alias = str(forbidden_alias).lower()
            if alias and alias in lowered:
                failures.append(
                    _failure(
                        "FORBIDDEN_VARIABLE_ALIAS",
                        index,
                        f"response uses forbidden alias {forbidden_alias!r}",
                    )
                )

        if bool(expected.get("visual_required")) and not has_visual(teacher):
            failures.append(_failure("VISUAL_DROPPED", index, "calibrated turn requires a visual"))

        if bool(expected.get("must_ask_question")) and "?" not in teacher:
            failures.append(_failure("BACK_AND_FORTH_DROPPED", index, "teacher must ask a learner-sized question"))

        max_lines = expected.get("max_nonempty_lines")
        if isinstance(max_lines, int) and nonempty_line_count(teacher) > max_lines:
            failures.append(
                _failure(
                    "OUTPUT_BUDGET_EXCEEDED",
                    index,
                    f"{nonempty_line_count(teacher)} nonempty lines exceeds {max_lines}",
                )
            )

        stage = str(calibration_turn.get("stage", ""))
        if stage != "loop" and ("def " in lowered or "class " in lowered):
            failures.append(
                _failure(
                    "FULL_SOLUTION_LEAK",
                    index,
                    "full implementation appeared before loop assembly",
                )
            )

    return failures


def evaluate_trace(
    trace_rows: list[dict[str, Any]],
    scenario: dict[str, Any],
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    scenario_id = str(scenario["id"])
    expected_turns = scenario.get("turns")
    if not isinstance(expected_turns, list):
        raise ValueError("scenario turns must be a list")

    rows = _scenario_rows(trace_rows, scenario_id)
    if len(rows) != len(expected_turns):
        failures.append(
            _failure(
                "TRACE_TURN_COUNT",
                None,
                f"expected {len(expected_turns)} trace rows, found {len(rows)}",
            )
        )

    by_index = {row.get("turn_index"): row for row in rows}
    for index, calibration_turn in enumerate(expected_turns):
        row = by_index.get(index)
        if row is None:
            failures.append(_failure("MISSING_TRACE", index, "model decision trace is missing"))
            continue

        missing = sorted(REQUIRED_TRACE_FIELDS.difference(row))
        if missing:
            failures.append(
                _failure("TRACE_SCHEMA", index, f"missing required fields: {missing}")
            )
            continue

        if row.get("schema_version") != TRACE_SCHEMA_VERSION:
            failures.append(
                _failure(
                    "TRACE_SCHEMA_VERSION",
                    index,
                    f"expected {TRACE_SCHEMA_VERSION!r}",
                )
            )
        if row.get("path_kind") != "model_generated":
            failures.append(
                _failure(
                    "NOT_MODEL_GENERATED",
                    index,
                    "accepted pilot turns must identify path_kind='model_generated'",
                )
            )

        stage = str(calibration_turn.get("stage", ""))
        expected_concept = STAGE_TO_CONCEPT.get(stage)
        if expected_concept is None:
            failures.append(_failure("UNKNOWN_CALIBRATION_STAGE", index, stage))
        elif row.get("target_concept") != expected_concept:
            failures.append(
                _failure(
                    "TARGET_CONCEPT_DRIFT",
                    index,
                    f"stage {stage!r} expects target_concept {expected_concept!r}",
                )
            )

        diagnosis = row.get("diagnosis_family")
        if diagnosis not in ALLOWED_DIAGNOSES:
            failures.append(_failure("TRACE_DIAGNOSIS", index, f"unsupported diagnosis {diagnosis!r}"))

        operation = row.get("operation")
        if operation not in ALLOWED_OPERATIONS:
            failures.append(_failure("TRACE_OPERATION", index, f"unsupported operation {operation!r}"))

        assistance = row.get("assistance_level")
        if assistance not in {"A0", "A1", "A2"}:
            failures.append(
                _failure(
                    "ASSISTANCE_CEILING",
                    index,
                    f"pilot must stay at A0-A2, found {assistance!r}",
                )
            )

        if calibration_turn.get("learner_signal") in {"clarification", "wrong_or_uncertain"} and row.get("advance") is not False:
            failures.append(
                _failure(
                    "UNSUPPORTED_ADVANCE",
                    index,
                    "clarification/wrong turns may not advance the calibrated concept",
                )
            )

        allowed_variables = row.get("allowed_variables")
        if not isinstance(allowed_variables, list) or not all(isinstance(item, str) for item in allowed_variables):
            failures.append(_failure("TRACE_ALLOWED_VARIABLES", index, "allowed_variables must be strings"))
        else:
            required = STAGE_REQUIRED_VARIABLES.get(stage, set())
            missing_variables = sorted(required.difference(allowed_variables))
            if missing_variables:
                failures.append(
                    _failure(
                        "REQUIRED_VARIABLES_MISSING",
                        index,
                        f"stage {stage!r} requires {missing_variables}",
                    )
                )

        forbidden_variables = row.get("forbidden_variables")
        if not isinstance(forbidden_variables, list) or not all(isinstance(item, str) for item in forbidden_variables):
            failures.append(_failure("TRACE_FORBIDDEN_VARIABLES", index, "forbidden_variables must be strings"))
        else:
            aliases = set(str(item) for item in scenario.get("forbidden_aliases", []))
            if not aliases.issubset(set(forbidden_variables)):
                failures.append(
                    _failure(
                        "FORBIDDEN_VARIABLE_POLICY_MISSING",
                        index,
                        f"trace must forbid calibrated aliases {sorted(aliases)}",
                    )
                )

        expected = calibration_turn.get("expected", {})
        if row.get("visual_required") is not bool(expected.get("visual_required")):
            failures.append(
                _failure(
                    "VISUAL_POLICY_DRIFT",
                    index,
                    "trace visual_required disagrees with calibration",
                )
            )

        for version_field in ("prompt_version", "model_identifier"):
            value = row.get(version_field)
            if not isinstance(value, str) or not value.strip():
                failures.append(
                    _failure(
                        "TRACE_PROVENANCE",
                        index,
                        f"{version_field} must be a nonempty string",
                    )
                )

    return failures


def evaluate(
    *,
    transcript_rows: list[dict[str, Any]],
    scenario: dict[str, Any],
    trace_rows: list[dict[str, Any]] | None,
    require_trace: bool,
) -> dict[str, Any]:
    failures = evaluate_transcript(transcript_rows, scenario)
    if require_trace:
        if trace_rows is None:
            failures.append(_failure("TRACE_REQUIRED", None, "final acceptance requires model decision trace"))
        else:
            failures.extend(evaluate_trace(trace_rows, scenario))

    scenario_id = str(scenario["id"])
    exchange_count = len(_scenario_rows(transcript_rows, scenario_id))
    return {
        "schema_version": "study-os.model-tutoring-acceptance.v0.1",
        "scenario_id": scenario_id,
        "exchange_count": exchange_count,
        "accepted": not failures,
        "failure_count": len(failures),
        "failures": failures,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check the model/schema-driven tutoring pilot against calibrated learner-visible behavior"
    )
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--transcript", type=Path, default=DEFAULT_TRANSCRIPT)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument(
        "--transcript-only",
        action="store_true",
        help="development diagnostic only; final acceptance requires the structured model trace",
    )
    parser.add_argument("--report", type=Path, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    corpus = load_json(args.corpus)
    scenario = find_scenario(corpus, args.scenario)
    transcript_rows = load_jsonl(args.transcript)
    trace_rows = None if args.transcript_only else load_jsonl(args.trace)
    report = evaluate(
        transcript_rows=transcript_rows,
        scenario=scenario,
        trace_rows=trace_rows,
        require_trace=not args.transcript_only,
    )

    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    print(encoded)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded + "\n", encoding="utf-8")
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
