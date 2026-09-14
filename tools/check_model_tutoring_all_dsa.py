#!/usr/bin/env python3
"""Acceptance gate for the generic model-tutoring DSA replay.

The runner is allowed to adapt its concept order from a model-generated plan.
This checker therefore treats the calibration corpus as an external oracle for
observable safety/presentation signals and as a differential diagnostic, while
the generated plan and deterministic controller remain authoritative for state
transitions.  Hidden ``expected`` fields are read only here, after generation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TOOLS = ROOT / "tools"
for path in (SRC, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from study_os.generic_model_tutoring import (  # noqa: E402
    GenericModelTutoringController,
    LearnerAssessment,
    ModelDiagnosis,
    ModelTutoringError,
    validate_generated_response,
)
from study_os.prompt_registry import DEFAULT_PROMPT_REGISTRY  # noqa: E402
from study_os.teaching_plan import (  # noqa: E402
    TEACHING_PLAN_SCHEMA_VERSION,
    TeachingPlan,
    TeachingPlanValidationError,
)
import run_model_tutoring_all_dsa as runner  # noqa: E402
import run_dual_luna_transcript as raw  # noqa: E402


TRACE_SCHEMA_VERSION = runner.TRACE_SCHEMA_VERSION
TRANSCRIPT_SCHEMA_VERSION = runner.TRANSCRIPT_SCHEMA_VERSION
PLAN_RECORD_SCHEMA_VERSION = runner.PLAN_RECORD_SCHEMA_VERSION
DEFAULT_CORPUS = raw.DEFAULT_CORPUS
DEFAULT_TRANSCRIPT = ROOT / "artifacts" / "model-tutoring-all-dsa-transcript.jsonl"
DEFAULT_TRACE = ROOT / "artifacts" / "model-tutoring-all-dsa-trace.jsonl"
DEFAULT_PLANS = ROOT / "artifacts" / "model-tutoring-all-dsa-plans.jsonl"
DEFAULT_REPORT = ROOT / "artifacts" / "model-tutoring-all-dsa-acceptance.json"

_INTERNAL_MARKERS = (
    "needs_compilation",
    "reviewed-asset",
    "reviewed_asset",
    "prompt_hash",
    "turn_trace_schema_version",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_no}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"JSONL record at {path}:{line_no} must be an object")
        rows.append(value)
    return rows


def _failure(category: str, scenario_id: str | None, turn: int | None, detail: str) -> dict[str, Any]:
    return {"category": category, "scenario_id": scenario_id, "turn_index": turn, "detail": detail}


def _selected(corpus: Mapping[str, Any], scenario_ids: set[str] | None) -> list[dict[str, Any]]:
    scenarios = corpus.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError("corpus.scenarios must be an array")
    result = [item for item in scenarios if isinstance(item, dict)]
    if scenario_ids is not None:
        result = [item for item in result if str(item.get("id")) in scenario_ids]
    if not result:
        raise ValueError("scenario selection is empty")
    return result


def _same_state(actual: object, expected: object) -> bool:
    return isinstance(actual, Mapping) and dict(actual) == dict(expected)


def _plan_for(
    scenario: Mapping[str, Any], plan_rows: Sequence[Mapping[str, Any]], failures: list[dict[str, Any]]
) -> TeachingPlan | None:
    scenario_id = str(scenario["id"])
    matches = [row for row in plan_rows if str(row.get("scenario_id")) == scenario_id]
    if len(matches) != 1:
        failures.append(_failure("PLAN_COUNT", scenario_id, None, f"expected one plan, found {len(matches)}"))
        return None
    row = matches[0]
    try:
        if row.get("schema_version") != PLAN_RECORD_SCHEMA_VERSION:
            raise ValueError("plan record schema version mismatch")
        if row.get("source_problem_id") != scenario_id:
            raise ValueError("plan source_problem_id mismatch")
        payload = row.get("plan_payload")
        if not isinstance(payload, Mapping):
            raise ValueError("plan_payload is missing")
        plan = TeachingPlan.from_payload(payload)
        if plan.schema_version != TEACHING_PLAN_SCHEMA_VERSION:
            raise ValueError("teaching-plan schema version mismatch")
        if plan.problem.id != scenario_id or plan.problem.statement != scenario["problem"]:
            raise ValueError("plan problem identity or statement mismatch")
        declared = set(str(item) for item in scenario.get("variables", []))
        if set(plan.variables) != declared:
            raise ValueError(f"plan variables {sorted(plan.variables)} do not preserve {sorted(declared)}")
        if row.get("plan_provenance") != dict(payload.get("provenance", {})):
            raise ValueError("plan provenance copy does not match payload")
        if row.get("run_id") != plan.provenance.run_id:
            raise ValueError("plan record run_id mismatch")
        DEFAULT_PROMPT_REGISTRY.verify(
            version=plan.provenance.prompt_version,
            prompt_hash=plan.provenance.prompt_hash,
        )
        if plan.provenance.turn_trace_schema_version != TRACE_SCHEMA_VERSION:
            raise ValueError("plan trace schema version mismatch")
        return plan
    except (ValueError, TeachingPlanValidationError, TypeError) as exc:
        failures.append(_failure("PLAN_INVALID", scenario_id, None, str(exc)))
        return None


def _calibration_signal(
    scenario: Mapping[str, Any], rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Measure corpus agreement without making its stage labels policy."""

    turns = scenario.get("turns", [])
    checks = 0
    hits = 0
    misses: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if index >= len(turns) or not isinstance(turns[index], Mapping):
            continue
        expected = turns[index].get("expected", {})
        if not isinstance(expected, Mapping):
            continue
        text = str(row.get("teacher_message", "")).casefold()
        required = [str(item).casefold() for item in expected.get("must_include_any", [])]
        if required:
            checks += 1
            if any(term in text for term in required):
                hits += 1
            else:
                misses.append({"turn_index": index, "kind": "must_include_any", "expected": required})
        forbidden = [str(item).casefold() for item in expected.get("must_not_include", [])]
        # Only source-level aliases are hard policy.  Stage labels can differ
        # under a valid adaptive plan and are intentionally diagnostic here.
        if forbidden:
            checks += 1
            if not any(term in text for term in forbidden):
                hits += 1
            else:
                misses.append({"turn_index": index, "kind": "calibration_forbidden", "expected": forbidden})
    return {"checks": checks, "hits": hits, "agreement": (hits / checks if checks else 1.0), "misses": misses}


def evaluate(
    corpus: Mapping[str, Any], transcript_rows: Sequence[Mapping[str, Any]],
    trace_rows: Sequence[Mapping[str, Any]], plan_rows: Sequence[Mapping[str, Any]],
    *, scenario_ids: set[str] | None = None, allow_short_run: bool = False,
) -> dict[str, Any]:
    selected = _selected(corpus, scenario_ids)
    failures: list[dict[str, Any]] = []
    scenario_reports: list[dict[str, Any]] = []
    total_visible = 0
    for scenario in selected:
        scenario_id = str(scenario["id"])
        expected_count = len(scenario.get("turns", []))
        if not allow_short_run and expected_count != runner.TURNS_PER_SCENARIO:
            failures.append(_failure("CORPUS_SHAPE", scenario_id, None, "scenario must have 15 turns"))
        rows = sorted(
            [dict(row) for row in transcript_rows if str(row.get("scenario_id")) == scenario_id],
            key=lambda row: int(row.get("turn_index", -1)),
        )
        traces = sorted(
            [dict(row) for row in trace_rows if str(row.get("scenario_id")) == scenario_id],
            key=lambda row: int(row.get("turn_index", -1)),
        )
        if len(rows) != expected_count:
            failures.append(_failure("TURN_COUNT", scenario_id, None, f"expected {expected_count}, found {len(rows)}"))
        if len(traces) != len(rows):
            failures.append(_failure("TRACE_COUNT", scenario_id, None, f"expected {len(rows)}, found {len(traces)}"))
        total_visible += len(rows) * 2
        plan = _plan_for(scenario, plan_rows, failures)
        scenario_failure_start = len(failures)
        if plan is not None:
            try:
                controller = GenericModelTutoringController(
                    plan,
                    model_identifier=plan.provenance.model_identifier,
                    forbidden_terms=tuple(str(item) for item in scenario.get("forbidden_aliases", [])),
                    visual_required=bool(scenario.get("visual_family")),
                    visual_before_explanation=True,
                )
            except (ModelTutoringError, ValueError) as exc:
                failures.append(_failure("CONTROLLER_INIT", scenario_id, None, str(exc)))
                controller = None
            if controller is not None:
                for index, row in enumerate(rows):
                    trace = traces[index] if index < len(traces) else None
                    if trace is None:
                        continue
                    try:
                        if row.get("schema_version") != TRANSCRIPT_SCHEMA_VERSION:
                            raise ValueError("transcript schema version mismatch")
                        if trace.get("schema_version") != TRACE_SCHEMA_VERSION:
                            raise ValueError("trace schema version mismatch")
                        if row.get("turn_index") != index or trace.get("turn_index") != index:
                            raise ValueError("turn indexes are not contiguous")
                        if row.get("run_id") != plan.provenance.run_id or trace.get("run_id") != plan.provenance.run_id:
                            raise ValueError("run_id does not match plan provenance")
                        learner = row.get("learner_message")
                        teacher = row.get("teacher_message")
                        if not isinstance(learner, str) or not learner.strip() or not isinstance(teacher, str) or not teacher.strip():
                            raise ValueError("learner and teacher messages must be non-empty")
                        diagnosis = ModelDiagnosis.from_payload(row.get("model_diagnosis", {}))
                        assessment = LearnerAssessment.from_payload(
                            row.get("model_assessment", {}), learner_message=learner
                        )
                        before = controller.state
                        authorization = controller.authorize(
                            diagnosis, assessment, learner_message=learner, turn_index=index
                        )
                        validate_generated_response(teacher, authorization.contract)
                        expected_trace = authorization.trace
                        for key, expected in expected_trace.items():
                            if trace.get(key) != expected:
                                raise ValueError(f"trace field {key!r} does not match controller")
                        if trace.get("forbidden_variables") != list(authorization.contract.forbidden_variables):
                            raise ValueError("trace forbidden_variables mismatch")
                        after = authorization.next_state
                        if not _same_state(row.get("controller_state_before"), {
                            "concept_index": before.concept_index,
                            "turns_seen": before.turns_seen,
                            "active_concept_id": authorization.contract.active_concept_id,
                        }):
                            raise ValueError("transcript controller_state_before mismatch")
                        if not _same_state(trace.get("controller_state_before"), row.get("controller_state_before")):
                            raise ValueError("trace/transcript before state mismatch")
                        expected_after = {
                            "concept_index": after.concept_index,
                            "turns_seen": after.turns_seen,
                            "active_concept_id": plan.concepts[after.concept_index].id,
                        }
                        if not _same_state(row.get("controller_state_after"), expected_after):
                            raise ValueError("transcript controller_state_after mismatch")
                        if not _same_state(trace.get("controller_state_after"), expected_after):
                            raise ValueError("trace controller_state_after mismatch")
                        if row.get("plan_provenance") != dict(plan.to_payload()["provenance"]):
                            raise ValueError("transcript plan provenance mismatch")
                        if row.get("plan_payload_reference", {}).get("scenario_id") != scenario_id:
                            raise ValueError("transcript plan reference mismatch")
                        leaked = [marker for marker in _INTERNAL_MARKERS if marker in teacher.casefold()]
                        if leaked:
                            raise ValueError(f"internal marker leaked: {leaked}")
                        controller.commit(authorization)
                    except (KeyError, TypeError, ValueError, ModelTutoringError) as exc:
                        failures.append(_failure("TURN_INVALID", scenario_id, index, str(exc)))
                        break
        calibration = _calibration_signal(scenario, rows)
        scenario_reports.append({
            "scenario_id": scenario_id,
            "exchange_count": len(rows),
            "visible_message_count": len(rows) * 2,
            "calibration": calibration,
            "failure_count": len(failures) - scenario_failure_start,
        })
    expected_scenarios = {str(item["id"]) for item in selected}
    observed_scenarios = {str(row.get("scenario_id")) for row in transcript_rows}
    if not allow_short_run and observed_scenarios != expected_scenarios:
        failures.append(_failure("SCENARIO_SET", None, None, f"observed {sorted(observed_scenarios)} != expected {sorted(expected_scenarios)}"))
    expected_exchanges = sum(len(item.get("turns", [])) for item in selected)
    if not allow_short_run and total_visible != expected_exchanges * 2:
        failures.append(_failure("VISIBLE_COUNT", None, None, f"expected {expected_exchanges * 2}, found {total_visible}"))
    aggregate_checks = sum(item["calibration"]["checks"] for item in scenario_reports)
    aggregate_hits = sum(item["calibration"]["hits"] for item in scenario_reports)
    return {
        "schema_version": "study-os.model-tutoring-all-dsa-acceptance.v0.1",
        "status": "passed" if not failures else "failed",
        "scenario_count": len(selected),
        "exchange_count": sum(item["exchange_count"] for item in scenario_reports),
        "visible_message_count": total_visible,
        "expected_exchange_count": expected_exchanges,
        "expected_visible_message_count": expected_exchanges * 2,
        "calibration": {
            "checks": aggregate_checks,
            "hits": aggregate_hits,
            "agreement": aggregate_hits / aggregate_checks if aggregate_checks else 1.0,
            "note": "stage wording/order is diagnostic; generated-plan/controller invariants are authoritative",
        },
        "scenario_reports": scenario_reports,
        "failures": failures,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check generic all-DSA model tutoring evidence")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--transcript", type=Path, default=DEFAULT_TRANSCRIPT)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--plans", type=Path, default=DEFAULT_PLANS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--allow-short-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    corpus = raw.load_corpus(args.corpus)
    report = evaluate(
        corpus,
        load_jsonl(args.transcript),
        load_jsonl(args.trace),
        load_jsonl(args.plans),
        scenario_ids=set(args.scenario) or None,
        allow_short_run=args.allow_short_run,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "failures": len(report["failures"]), "exchanges": report["exchange_count"], "visible_messages": report["visible_message_count"]}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
