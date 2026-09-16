#!/usr/bin/env python3
"""Acceptance gate for the model/schema-driven Contains Duplicate pilot.

The gate checks learner-visible behavior, evidence-bound progression, and calibrated
semantic meaning. It does not require canonical wording.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "datasets" / "dsa-conversation-replay.v0.1.json"
DEFAULT_TRANSCRIPT = ROOT / "artifacts" / "model-tutoring-contains-duplicate.jsonl"
DEFAULT_TRACE = ROOT / "artifacts" / "model-tutoring-contains-duplicate-trace.jsonl"
DEFAULT_SCENARIO = "contains-duplicate-set"
TRACE_SCHEMA_VERSION = "study-os.model-tutoring-trace.v0.2"
TRANSCRIPT_SCHEMA_VERSION = "study-os.model-tutoring-exchange.v0.2"

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
    "none", "missing_prerequisite", "concept_failure", "representation_interference",
    "identifier_interference", "information_overload", "information_underload",
    "decomposition_too_coarse", "over_decomposition", "over_help", "uncertain_mixed",
}
ALLOWED_OPERATIONS = {
    "explain", "clarify", "probe", "smaller_step", "show_trace",
    "change_representation", "give_hint", "assemble",
}
ALLOWED_OUTCOMES = {"demonstrated", "not_yet", "uncertain"}
STAGE_TO_CONCEPT = {
    "anchor": "duplicate_meaning",
    "box-meaning": "box_meaning",
    "membership": "membership",
    "order": "check_before_add",
    "loop": "loop_assembly",
}
CONCEPT_ORDER = tuple(STAGE_TO_CONCEPT.values())
CONCEPT_TO_STAGE = {concept: stage for stage, concept in STAGE_TO_CONCEPT.items()}
STAGE_REQUIRED_VARIABLES = {
    "anchor": {"nums"},
    "box-meaning": {"box", "num"},
    "membership": {"box", "num"},
    "order": {"box", "num"},
    "loop": {"nums", "box", "num"},
}
REQUIRED_TRACE_FIELDS = {
    "schema_version", "scenario_id", "turn_index", "path_kind", "target_concept",
    "diagnosis_family", "operation", "assistance_level", "learner_outcome",
    "evidence_quote", "advance", "allowed_variables", "forbidden_variables",
    "visual_required", "prompt_version", "model_identifier",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_number} must contain a JSON object")
        rows.append(row)
    return rows


def find_scenario(corpus: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    for scenario in corpus.get("scenarios", []):
        if isinstance(scenario, dict) and scenario.get("id") == scenario_id:
            return scenario
    raise ValueError(f"scenario {scenario_id!r} not found in corpus")


def nonempty_line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def has_visual(text: str) -> bool:
    return (
        "```" in text
        or "|" in text
        or "→" in text
        or "->" in text
        or ("[" in text and "]" in text and "\n" in text)
    )


def _failure(code: str, turn_index: int | None, detail: str) -> dict[str, Any]:
    return {"code": code, "turn_index": turn_index, "detail": detail}


def _scenario_rows(rows: list[dict[str, Any]], scenario_id: str) -> list[dict[str, Any]]:
    selected = [row for row in rows if row.get("scenario_id") == scenario_id]
    return sorted(selected, key=lambda row: int(row.get("turn_index", -1)))


def _stage_contracts(scenario: dict[str, Any]) -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    for turn in scenario.get("turns", []):
        if isinstance(turn, dict) and isinstance(turn.get("expected"), dict):
            contracts.setdefault(str(turn.get("stage", "")), turn["expected"])
    return contracts


def _box_boolean_drift(text: str) -> bool:
    lowered = text.casefold()
    return bool(
        re.search(
            r"\bbox\s*(?:=|is|becomes?|holds?)\s*(?:true|false|yes/no|boolean)",
            lowered,
        )
        or "box holds the yes/no" in lowered
        or "box holds yes/no" in lowered
    )


def evaluate_turn_semantics(
    stage: str,
    teacher: str,
    turn_index: int,
) -> list[dict[str, Any]]:
    """Validate calibrated meaning without enforcing exact prose."""
    failures: list[dict[str, Any]] = []
    lowered = teacher.casefold()

    if stage != "anchor" and _box_boolean_drift(teacher):
        failures.append(
            _failure(
                "BOX_SEMANTIC_DRIFT",
                turn_index,
                "`box` was used as a boolean/result; calibration defines box as earlier values",
            )
        )

    if stage == "anchor":
        if "duplicate" not in lowered or not any(
            phrase in lowered
            for phrase in ("repeat", "twice", "same number", "same value", "appears again")
        ):
            failures.append(
                _failure(
                    "DUPLICATE_MEANING_DRIFT",
                    turn_index,
                    "duplicate must mean the same value occurs at least twice",
                )
            )

    elif stage == "box-meaning":
        prior_signal = any(
            phrase in lowered
            for phrase in (
                "earlier", "prior", "already passed", "already checked",
                "previous", "values already", "numbers already",
            )
        )
        if "box" not in lowered or "num" not in lowered or not prior_signal:
            failures.append(
                _failure(
                    "BOX_MEANING_DRIFT",
                    turn_index,
                    "box-meaning must explain box as earlier/prior nums values",
                )
            )

    elif stage == "membership":
        membership_signal = (
            re.search(r"\bnum\s+in\s+box\b", lowered) is not None
            or (
                "num" in lowered
                and "box" in lowered
                and any(word in lowered for word in ("match", "already", "contains"))
            )
        )
        if not membership_signal:
            failures.append(
                _failure(
                    "MEMBERSHIP_SEMANTIC_DRIFT",
                    turn_index,
                    "membership must connect current num to an equal value already in box",
                )
            )

    elif stage == "order":
        check_pos = lowered.find("check")
        add_pos = lowered.find("add")
        if check_pos < 0 or add_pos < 0 or check_pos > add_pos:
            failures.append(
                _failure(
                    "ORDER_SEMANTIC_DRIFT",
                    turn_index,
                    "order must be check-before-add",
                )
            )

    elif stage == "loop":
        if "num" not in lowered or "box" not in lowered or "check" not in lowered:
            failures.append(
                _failure(
                    "LOOP_SEMANTIC_DRIFT",
                    turn_index,
                    "loop must preserve checking current num against box",
                )
            )

    return failures


def evaluate_transcript(
    transcript_rows: list[dict[str, Any]],
    scenario: dict[str, Any],
    trace_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    scenario_id = str(scenario["id"])
    expected_count = len(scenario.get("turns", []))
    rows = _scenario_rows(transcript_rows, scenario_id)
    traces = _scenario_rows(trace_rows or [], scenario_id)
    trace_by_index = {int(row.get("turn_index", -1)): row for row in traces}
    stage_contracts = _stage_contracts(scenario)

    if len(rows) != expected_count:
        failures.append(
            _failure("TURN_COUNT", None, f"expected {expected_count} exchanges, found {len(rows)}")
        )

    for index, row in enumerate(rows):
        if row.get("schema_version") != TRANSCRIPT_SCHEMA_VERSION:
            failures.append(
                _failure(
                    "TRANSCRIPT_SCHEMA_VERSION",
                    index,
                    f"expected {TRANSCRIPT_SCHEMA_VERSION}",
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
                    _failure("PRODUCT_INTERNAL_STATE_LEAK", index, f"contains {phrase!r}")
                )
        for alias in scenario.get("forbidden_aliases", []):
            alias_text = str(alias).lower()
            if re.search(
                rf"(?<![a-z0-9_]){re.escape(alias_text)}(?![a-z0-9_])",
                lowered,
            ):
                failures.append(
                    _failure("FORBIDDEN_VARIABLE_ALIAS", index, f"uses {alias!r}")
                )

        trace = trace_by_index.get(index)
        stage = None
        if trace is not None:
            stage = CONCEPT_TO_STAGE.get(str(trace.get("target_concept", "")))
        if stage is None:
            stage = str(row.get("controller_stage", ""))
        if stage not in STAGE_TO_CONCEPT and index < expected_count:
            stage = str(scenario["turns"][index].get("stage", ""))
        expected = stage_contracts.get(stage or "", {})

        must_include_any = expected.get("must_include_any", [])
        if must_include_any and not any(
            str(term).lower() in lowered for term in must_include_any
        ):
            failures.append(
                _failure(
                    "CALIBRATED_ANCHOR_MISSING",
                    index,
                    f"expected one of {must_include_any!r}",
                )
            )
        for forbidden in expected.get("must_not_include", []):
            forbidden_text = str(forbidden).lower()
            if forbidden_text and forbidden_text in lowered:
                failures.append(
                    _failure(
                        "FUTURE_OR_FORBIDDEN_CONCEPT",
                        index,
                        f"contains {forbidden!r}",
                    )
                )
        if bool(expected.get("visual_required")) and not has_visual(teacher):
            failures.append(
                _failure("VISUAL_DROPPED", index, "calibrated stage requires a visual")
            )
        if bool(expected.get("must_ask_question")) and "?" not in teacher:
            failures.append(
                _failure(
                    "BACK_AND_FORTH_DROPPED",
                    index,
                    "teacher must ask a learner-sized question",
                )
            )
        max_lines = expected.get("max_nonempty_lines")
        if isinstance(max_lines, int) and nonempty_line_count(teacher) > max_lines:
            failures.append(
                _failure(
                    "OUTPUT_BUDGET_EXCEEDED",
                    index,
                    f"{nonempty_line_count(teacher)} > {max_lines}",
                )
            )
        if stage != "loop" and ("def " in lowered or "class " in lowered):
            failures.append(
                _failure(
                    "FULL_SOLUTION_LEAK",
                    index,
                    "implementation leaked before loop assembly",
                )
            )
        if stage in STAGE_TO_CONCEPT:
            failures.extend(evaluate_turn_semantics(stage, teacher, index))

    if rows:
        final_teacher = str(rows[-1].get("teacher_message", "")).lower()
        if "return false" not in final_teacher:
            failures.append(
                _failure(
                    "LOOP_COMPLETION_MISSING",
                    int(rows[-1].get("turn_index", len(rows) - 1)),
                    "final learner-visible turn must explicitly establish `return False` when the scan finishes without a duplicate",
                )
            )
    return failures


def evaluate_trace(
    trace_rows: list[dict[str, Any]],
    scenario: dict[str, Any],
    transcript_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    scenario_id = str(scenario["id"])
    expected_count = len(scenario.get("turns", []))
    rows = _scenario_rows(trace_rows, scenario_id)
    transcripts = _scenario_rows(transcript_rows or [], scenario_id)
    transcript_by_index = {int(row.get("turn_index", -1)): row for row in transcripts}

    if len(rows) != expected_count:
        failures.append(
            _failure(
                "TRACE_TURN_COUNT",
                None,
                f"expected {expected_count} trace rows, found {len(rows)}",
            )
        )

    previous_concept_index: int | None = None
    previous_advance = False
    for position, row in enumerate(rows):
        index = int(row.get("turn_index", -1))
        missing = sorted(REQUIRED_TRACE_FIELDS.difference(row))
        if missing:
            failures.append(
                _failure("TRACE_SCHEMA", index, f"missing required fields: {missing}")
            )
            continue
        if row.get("schema_version") != TRACE_SCHEMA_VERSION:
            failures.append(
                _failure("TRACE_SCHEMA_VERSION", index, f"expected {TRACE_SCHEMA_VERSION}")
            )
        if row.get("path_kind") != "model_generated":
            failures.append(
                _failure("NOT_MODEL_GENERATED", index, "path_kind must be model_generated")
            )

        concept = str(row.get("target_concept", ""))
        if concept not in CONCEPT_ORDER:
            failures.append(
                _failure("TARGET_CONCEPT_DRIFT", index, f"unsupported concept {concept!r}")
            )
            continue
        concept_index = CONCEPT_ORDER.index(concept)
        if position == 0 and concept_index != 0:
            failures.append(
                _failure(
                    "PROGRESSION_START",
                    index,
                    "pilot must begin at duplicate_meaning",
                )
            )
        if previous_concept_index is not None:
            expected_index = previous_concept_index + (1 if previous_advance else 0)
            expected_index = min(expected_index, len(CONCEPT_ORDER) - 1)
            if concept_index != expected_index:
                failures.append(
                    _failure(
                        "PROGRESSION_DRIFT",
                        index,
                        f"expected concept index {expected_index}, found {concept_index}",
                    )
                )

        if row.get("diagnosis_family") not in ALLOWED_DIAGNOSES:
            failures.append(
                _failure(
                    "TRACE_DIAGNOSIS",
                    index,
                    f"unsupported diagnosis {row.get('diagnosis_family')!r}",
                )
            )
        if row.get("operation") not in ALLOWED_OPERATIONS:
            failures.append(
                _failure(
                    "TRACE_OPERATION",
                    index,
                    f"unsupported operation {row.get('operation')!r}",
                )
            )
        if row.get("assistance_level") not in {"A0", "A1", "A2"}:
            failures.append(
                _failure(
                    "ASSISTANCE_CEILING",
                    index,
                    f"invalid assistance {row.get('assistance_level')!r}",
                )
            )

        outcome = row.get("learner_outcome")
        quote = row.get("evidence_quote")
        if outcome not in ALLOWED_OUTCOMES:
            failures.append(
                _failure("LEARNER_OUTCOME", index, f"invalid outcome {outcome!r}")
            )
        if not isinstance(quote, str):
            failures.append(
                _failure("EVIDENCE_QUOTE", index, "evidence_quote must be text")
            )
            quote = ""
        transcript = transcript_by_index.get(index)
        learner_message = str(transcript.get("learner_message", "")) if transcript else ""
        if quote and transcript and quote.casefold() not in learner_message.casefold():
            failures.append(
                _failure(
                    "EVIDENCE_NOT_IN_LEARNER_MESSAGE",
                    index,
                    "evidence_quote is not verbatim learner text",
                )
            )
        if outcome == "demonstrated" and not quote.strip():
            failures.append(
                _failure(
                    "DEMONSTRATION_WITHOUT_EVIDENCE",
                    index,
                    "demonstrated requires a verbatim evidence quote",
                )
            )
        advance = row.get("advance")
        if advance is True and outcome != "demonstrated":
            failures.append(
                _failure(
                    "UNSUPPORTED_ADVANCE",
                    index,
                    "advance requires demonstrated learner outcome",
                )
            )
        if concept_index == len(CONCEPT_ORDER) - 1 and advance is True:
            failures.append(
                _failure(
                    "ADVANCE_PAST_FINAL_CONCEPT",
                    index,
                    "loop_assembly is final pilot concept",
                )
            )

        stage = CONCEPT_TO_STAGE[concept]
        allowed_variables = row.get("allowed_variables")
        if not isinstance(allowed_variables, list) or not all(
            isinstance(item, str) for item in allowed_variables
        ):
            failures.append(
                _failure(
                    "TRACE_ALLOWED_VARIABLES",
                    index,
                    "allowed_variables must be strings",
                )
            )
        else:
            missing_variables = sorted(
                STAGE_REQUIRED_VARIABLES[stage].difference(allowed_variables)
            )
            if missing_variables:
                failures.append(
                    _failure(
                        "REQUIRED_VARIABLES_MISSING",
                        index,
                        f"missing {missing_variables}",
                    )
                )
        forbidden_variables = row.get("forbidden_variables")
        aliases = set(str(item) for item in scenario.get("forbidden_aliases", []))
        if not isinstance(forbidden_variables, list) or not aliases.issubset(
            set(forbidden_variables)
        ):
            failures.append(
                _failure(
                    "FORBIDDEN_VARIABLE_POLICY_MISSING",
                    index,
                    f"must forbid {sorted(aliases)}",
                )
            )
        if row.get("visual_required") is not True:
            failures.append(
                _failure(
                    "VISUAL_POLICY_DRIFT",
                    index,
                    "pilot stages require visuals",
                )
            )
        for version_field in ("prompt_version", "model_identifier"):
            value = row.get(version_field)
            if not isinstance(value, str) or not value.strip():
                failures.append(
                    _failure(
                        "TRACE_PROVENANCE",
                        index,
                        f"{version_field} must be nonempty",
                    )
                )

        previous_concept_index = concept_index
        previous_advance = advance is True

    if rows and str(rows[-1].get("target_concept")) != CONCEPT_ORDER[-1]:
        failures.append(
            _failure(
                "PILOT_DID_NOT_REACH_LOOP",
                int(rows[-1].get("turn_index", -1)),
                "final concept must be loop_assembly",
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
    failures = evaluate_transcript(transcript_rows, scenario, trace_rows)
    if require_trace:
        if trace_rows is None:
            failures.append(
                _failure(
                    "TRACE_REQUIRED",
                    None,
                    "final acceptance requires model decision trace",
                )
            )
        else:
            failures.extend(evaluate_trace(trace_rows, scenario, transcript_rows))
    scenario_id = str(scenario["id"])
    return {
        "schema_version": "study-os.model-tutoring-acceptance.v0.3",
        "scenario_id": scenario_id,
        "exchange_count": len(_scenario_rows(transcript_rows, scenario_id)),
        "accepted": not failures,
        "failure_count": len(failures),
        "failures": failures,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check bounded model tutoring against learner-visible, semantic, and evidence contracts"
    )
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--transcript", type=Path, default=DEFAULT_TRANSCRIPT)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument(
        "--transcript-only",
        action="store_true",
        help="development diagnostic only; final acceptance requires trace",
    )
    parser.add_argument("--report", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    corpus = load_json(args.corpus)
    scenario = find_scenario(corpus, args.scenario)
    transcript = load_jsonl(args.transcript)
    trace = None if args.transcript_only else load_jsonl(args.trace)
    report = evaluate(
        transcript_rows=transcript,
        scenario=scenario,
        trace_rows=trace,
        require_trace=not args.transcript_only,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
