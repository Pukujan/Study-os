#!/usr/bin/env python3
"""Run the generic model-tutoring path over the complete DSA replay corpus.

The runner is deliberately an orchestration boundary.  Luna proposes a plan,
diagnosis, and response; the validated generic Study OS contract owns evidence,
progression, assistance, and the commit decision.  The corpus learner signal is
sent only through the existing raw student payload and is never sent to the
teacher.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import run_dual_luna_local_codex as local  # noqa: E402
import run_dual_luna_transcript as raw  # noqa: E402
from study_os.generic_model_tutoring import (  # noqa: E402
    Authorization,
    GenericModelTutoringController,
    LearnerAssessment,
    LearnerState,
    ModelDiagnosis,
    ModelTutoringError,
    build_generation_prompt,
    parse_generation_response,
    parse_model_decision,
    validate_generated_response,
)
from study_os.prompt_registry import (  # noqa: E402
    DEFAULT_PROMPT_REGISTRY,
    DECOMPOSITION_PROMPT_VERSION,
    PromptRegistry,
)
from study_os.teaching_plan import (  # noqa: E402
    TEACHING_PLAN_SCHEMA_VERSION,
    TeachingPlan,
    TeachingPlanProvenance,
    TeachingPlanValidationError,
)


DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_MCP_NAME = local.DEFAULT_MCP_NAME
DEFAULT_TURN_TIMEOUT_SECONDS = local.DEFAULT_TURN_TIMEOUT_SECONDS
TURNS_PER_SCENARIO = 15
REQUIRED_SCENARIO_COUNT = 14
PLAN_RETRIES = 3
DIAGNOSIS_RETRIES = 3
GENERATION_RETRIES = 4

PLAN_RECORD_SCHEMA_VERSION = "study-os.model-tutoring-plan-record.v0.1"
TRANSCRIPT_SCHEMA_VERSION = "study-os.model-tutoring-exchange.v0.3"
TRACE_SCHEMA_VERSION = "study-os.model-tutoring-trace.v0.3"

DEFAULT_TRANSCRIPT = ROOT / "artifacts" / "model-tutoring-all-dsa-transcript.jsonl"
DEFAULT_MARKDOWN = ROOT / "artifacts" / "model-tutoring-all-dsa-transcript.md"
DEFAULT_TRACE = ROOT / "artifacts" / "model-tutoring-all-dsa-trace.jsonl"
DEFAULT_PLANS = ROOT / "artifacts" / "model-tutoring-all-dsa-plans.jsonl"


class Actor(Protocol):
    def ask(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    def close(self) -> None: ...


class AllDSATeacherActor(local.CodexCliActor):
    """Local teacher actor with a resolve_problem call as a hard transport gate."""

    def _role_contract(self) -> str:
        return (
            "You are Luna acting as the learner-facing Study OS teacher in a generic "
            "DSA model-tutoring experiment. For EVERY decomposition, diagnosis, and "
            f"generation request, first call the local MCP server {self.mcp_name!r} "
            "and complete its `resolve_problem` tool with the supplied problem text "
            "and domain `dsa`. Treat the tool result as internal routing context. If "
            "the result says the problem needs compilation, keep that status internal "
            "and continue through the generic model-tutoring contract; never expose "
            "that status, reviewed-asset language, or MCP details to the learner. Do "
            "not edit the repository or use hosted tasks.\n\n"
            "In decomposition phase, return JSON only for the generic TeachingPlan "
            "shape requested by the payload. Do not write a lesson or infer learner "
            "mastery. In diagnosis phase, return JSON with `diagnosis` and "
            "`assessment`, judging only the actual learner message. A demonstrated "
            "assessment must quote an exact substring of that message. In generation "
            "phase, return JSON only with a `response` string. The deterministic "
            "controller owns progression, variable bindings, assistance ceilings, "
            "and mastery boundaries."
        )

    def _parse_events(self, stdout: str) -> tuple[str | None, str, bool, list[str]]:
        thread_id, message, _completed, errors = super()._parse_events(stdout)
        resolved = False
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            item = event.get("item") if isinstance(event, dict) else None
            if not isinstance(item, dict):
                continue
            if (
                item.get("type") == "mcp_tool_call"
                and item.get("server") == self.mcp_name
                and item.get("tool") == "resolve_problem"
                and item.get("status") == "completed"
            ):
                resolved = True
        if not resolved:
            detail = "; ".join(errors) if errors else "resolve_problem did not complete"
            raise RuntimeError(
                "teacher did not complete the required Study OS resolve_problem MCP call: "
                + detail
            )
        return thread_id, message, True, errors


def _json_object(raw_response: str, *, label: str) -> dict[str, Any]:
    """Extract the first complete JSON object from a model response."""

    if not isinstance(raw_response, str) or not raw_response.strip():
        raise ModelTutoringError(f"{label} must be non-empty text")
    text = raw_response.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    decoder = json.JSONDecoder()
    for offset, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _end = decoder.raw_decode(text[offset:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ModelTutoringError(f"{label} must contain a JSON object")


def _public_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _public_problem(scenario: Mapping[str, Any]) -> dict[str, Any]:
    """Return public problem identity and declared variable bindings.

    Variable names are part of the learner-facing problem contract.  Turn
    annotations (signals, stages, and expected assertions) remain excluded.
    """

    variables = scenario.get("variables", [])
    if not isinstance(variables, list) or not all(
        isinstance(item, str) and item.strip() for item in variables
    ):
        raise ValueError("scenario.variables must be a non-empty list of names")
    if len(set(variables)) != len(variables):
        raise ValueError("scenario.variables must contain unique names")
    return {
        "scenario_id": _public_text(scenario.get("id"), "scenario.id"),
        "title": _public_text(scenario.get("title"), "scenario.title"),
        "problem": _public_text(scenario.get("problem"), "scenario.problem"),
        "domain": "dsa",
        "variable_names": list(variables),
    }


def build_decomposer_payload(
    scenario: Mapping[str, Any], *, repair_feedback: str | None = None
) -> dict[str, Any]:
    """Build a plan request from public problem data only."""

    payload: dict[str, Any] = {
        "type": "model_tutoring_plan_request",
        "role": "teacher",
        "phase": "decomposition",
        **_public_problem(scenario),
        "instruction": (
            "Return one JSON-compatible generic TeachingPlan for this problem. Include "
            "the required schema fields: problem, ordered concepts with prerequisites, "
            "variables and meanings, representation requirements, semantic invariants, "
            "completion evidence, terminal behavior, assistance ceiling, and schema "
            "version. Use the supplied problem identity and statement exactly. Do not "
            "include learner data, evaluation material, or lesson prose."
        ),
        "teaching_plan_schema_version": TEACHING_PLAN_SCHEMA_VERSION,
        "declared_variable_names": list(_public_problem(scenario)["variable_names"]),
    }
    if repair_feedback:
        payload["repair_feedback"] = repair_feedback
    return payload


def parse_plan_response(
    raw_response: str,
    *,
    scenario: Mapping[str, Any],
    run_id: str,
    model_identifier: str,
    prompt_registry: PromptRegistry = DEFAULT_PROMPT_REGISTRY,
) -> TeachingPlan:
    """Parse and validate one model-generated plan with runtime provenance."""

    payload = _json_object(raw_response, label="teaching plan")
    public = _public_problem(scenario)
    problem = payload.get("problem")
    if not isinstance(problem, Mapping):
        raise TeachingPlanValidationError("model plan problem must be an object")
    if problem.get("id") != public["scenario_id"]:
        raise TeachingPlanValidationError("model plan problem.id does not match source problem")
    if problem.get("statement") != public["problem"]:
        raise TeachingPlanValidationError(
            "model plan problem.statement does not match source problem"
        )

    decomposition_prompt = prompt_registry.for_role(
        "decomposition", version=DECOMPOSITION_PROMPT_VERSION
    )
    provenance = decomposition_prompt.provenance(
        model_identifier=_public_text(model_identifier, "model_identifier"),
        teaching_plan_schema_version=TEACHING_PLAN_SCHEMA_VERSION,
        turn_trace_schema_version=TRACE_SCHEMA_VERSION,
        run_id=_public_text(run_id, "run_id"),
        source_problem_id=public["scenario_id"],
    )
    plan_provenance = TeachingPlanProvenance.from_prompt_provenance(provenance)

    # Provenance is runtime-owned metadata, not a model authority.  Replacing a
    # model-supplied value prevents a proposal from changing the recorded run.
    normalized = dict(payload)
    normalized["provenance"] = {
        "prompt_version": plan_provenance.prompt_version,
        "prompt_hash": plan_provenance.prompt_hash,
        "model_identifier": plan_provenance.model_identifier,
        "teaching_plan_schema_version": plan_provenance.teaching_plan_schema_version,
        "turn_trace_schema_version": plan_provenance.turn_trace_schema_version,
        "run_id": plan_provenance.run_id,
        "source_problem_id": plan_provenance.source_problem_id,
    }
    plan = TeachingPlan.from_payload(normalized)
    _validate_source_variable_bindings(plan, scenario)
    return plan


def _validate_source_variable_bindings(
    plan: TeachingPlan, scenario: Mapping[str, Any]
) -> None:
    """Keep generated and resumed plans aligned with declared source names."""

    declared = tuple(_public_problem(scenario)["variable_names"])
    if set(plan.variables) != set(declared):
        raise TeachingPlanValidationError(
            "model plan variable bindings must preserve the source problem's "
            "declared variable names exactly"
        )


def build_diagnosis_payload(
    scenario: Mapping[str, Any],
    *,
    controller: GenericModelTutoringController,
    turn_index: int,
    learner_message: str,
    conversation: Sequence[Mapping[str, str]],
    repair_feedback: str | None = None,
) -> dict[str, Any]:
    """Build diagnosis input without corpus annotations or future concepts."""

    concept = controller.active_concept
    plan = controller.plan
    requirements = {item.id: item for item in plan.representation_requirements}
    invariants = {item.id: item for item in plan.semantic_invariants}
    completion = {item.id: item for item in plan.completion_evidence}
    payload: dict[str, Any] = {
        "type": "model_tutoring_teacher_turn",
        "role": "teacher",
        "phase": "diagnosis",
        **_public_problem(scenario),
        "turn_index": turn_index,
        "learner_message": learner_message,
        "active_concept": {
            "id": concept.id,
            "allowed_variables": list(concept.allowed_variables),
            "representation_requirements": [
                {
                    "id": requirements[item_id].id,
                    "kind": requirements[item_id].kind,
                    "operation": requirements[item_id].operation,
                    "required": requirements[item_id].required,
                }
                for item_id in concept.representation_requirement_ids
            ],
            "semantic_invariants": [
                {"id": invariants[item_id].id, "statement": invariants[item_id].statement}
                for item_id in concept.semantic_invariant_ids
            ],
            "completion_evidence": [
                {
                    "id": completion[item_id].id,
                    "evidence_type": completion[item_id].evidence_type,
                    "description": completion[item_id].description,
                }
                for item_id in concept.completion_evidence_ids
            ],
            "assistance_ceiling": plan.assistance_ceiling,
        },
        "instruction": (
            "Return JSON with diagnosis and assessment. Diagnose only the actual learner "
            "message against the active concept. Use a generic operation and assistance "
            "level no higher than the ceiling. Mark demonstrated only when the learner "
            "message itself demonstrates the concept, and quote that exact substring. "
            "Questions, confidence, and unsupported guesses are not demonstrated."
        ),
        "decision_schema": {
            "diagnosis": {
                "diagnosis_family": "string",
                "operation": "string",
                "assistance_level": "A0, A1, or A2",
                "decomposition": "short string",
            },
            "assessment": {
                "learner_outcome": "demonstrated, not_yet, or uncertain",
                "evidence_quote": "exact substring when demonstrated, otherwise empty",
                "rationale": "short derived rationale",
            },
        },
        "conversation": [dict(item) for item in conversation],
    }
    if repair_feedback:
        payload["repair_feedback"] = repair_feedback
    return payload


def build_generation_payload(
    scenario: Mapping[str, Any],
    *,
    authorization: Authorization,
    learner_message: str,
    conversation: Sequence[Mapping[str, str]],
    prompt_registry: PromptRegistry = DEFAULT_PROMPT_REGISTRY,
    repair_feedback: str | None = None,
) -> dict[str, Any]:
    """Build generation input from the authorized generic contract."""

    contract = authorization.contract
    payload: dict[str, Any] = {
        "type": "model_tutoring_teacher_turn",
        "role": "teacher",
        "phase": "generation",
        **_public_problem(scenario),
        "turn_index": contract.turn_index,
        "learner_message": learner_message,
        "generation_contract": contract.to_payload(),
        "generation_prompt": build_generation_prompt(
            contract,
            learner_message=learner_message,
            history=conversation,
            prompt_registry=prompt_registry,
        ),
        "instruction": (
            "Return JSON only with a response string. Write exactly one bounded learner-"
            "visible teaching turn from the authorized contract. Do not claim mastery, "
            "change the active concept, expose internal routing, or jump beyond the "
            "assistance ceiling."
        ),
        "conversation": [dict(item) for item in conversation],
    }
    if repair_feedback:
        payload["repair_feedback"] = repair_feedback
    return payload


def _extract_actor_message(result: Mapping[str, Any], *, role: str) -> str:
    return raw._extract_message(dict(result), role=role)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"JSONL record at {path}:{line_number} is not an object")
        rows.append(value)
    return rows


def _atomic_write_jsonl(rows: Sequence[Mapping[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        "".join(json.dumps(dict(row), ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    temporary.replace(path)


def render_markdown(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# All-DSA model tutoring transcript",
        "",
        "This artifact records model-generated tutoring harness exchanges and their "
        "generic plan references. It is not human learning or mastery evidence.",
        "",
    ]
    current: str | None = None
    for row in rows:
        scenario_id = str(row["scenario_id"])
        if scenario_id != current:
            current = scenario_id
            lines.extend(
                [
                    f"## {row['title']} (`{scenario_id}`)",
                    "",
                    f"**Problem:** {row['problem']}",
                    "",
                    f"**Plan run:** {row['plan_provenance']['run_id']}",
                    "",
                ]
            )
        lines.extend(
            [
                f"### Exchange {int(row['turn_index']) + 1}",
                "",
                "**Learner**",
                "",
                str(row["learner_message"]),
                "",
                "**Study OS teacher**",
                "",
                str(row["teacher_message"]),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _atomic_write_markdown(rows: Sequence[Mapping[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(render_markdown(rows), encoding="utf-8")
    temporary.replace(path)


def _plan_reference(plan_path: Path, plan: TeachingPlan) -> dict[str, str]:
    return {
        "artifact": str(plan_path),
        "scenario_id": plan.problem.id,
        "source_problem_id": plan.provenance.source_problem_id,
        "run_id": plan.provenance.run_id,
    }


def _plan_record(plan: TeachingPlan, *, plan_path: Path) -> dict[str, Any]:
    payload = plan.to_payload()
    return {
        "schema_version": PLAN_RECORD_SCHEMA_VERSION,
        "scenario_id": plan.problem.id,
        "source_problem_id": plan.provenance.source_problem_id,
        "run_id": plan.provenance.run_id,
        "plan_payload": payload,
        "plan_provenance": dict(payload["provenance"]),
        "plan_payload_reference": _plan_reference(plan_path, plan),
    }


def _checkpoint(
    transcript_rows: Sequence[Mapping[str, Any]],
    trace_rows: Sequence[Mapping[str, Any]],
    plan_rows: Sequence[Mapping[str, Any]],
    *,
    transcript_path: Path,
    markdown_path: Path,
    trace_path: Path,
    plans_path: Path,
) -> None:
    """Replace every snapshot through a same-directory atomic rename."""

    _atomic_write_jsonl(transcript_rows, transcript_path)
    _atomic_write_markdown(transcript_rows, markdown_path)
    _atomic_write_jsonl(trace_rows, trace_path)
    _atomic_write_jsonl(plan_rows, plans_path)


def _scenario_rows(rows: Sequence[Mapping[str, Any]], scenario_id: str) -> list[dict[str, Any]]:
    matching = [dict(row) for row in rows if str(row.get("scenario_id")) == scenario_id]
    matching.sort(key=lambda row: int(row.get("turn_index", -1)))
    return matching


def _validate_trace_shape(
    trace: Mapping[str, Any], *, scenario_id: str, plan: TeachingPlan
) -> None:
    required = {
        "schema_version",
        "scenario_id",
        "turn_index",
        "path_kind",
        "active_concept_id",
        "target_concept",
        "learner_outcome",
        "evidence_quote",
        "advance",
        "plan_provenance",
        "plan_payload_reference",
    }
    missing = sorted(field for field in required if field not in trace)
    if missing:
        raise ValueError(f"trace is missing required generic fields: {missing}")
    if trace["schema_version"] != TRACE_SCHEMA_VERSION:
        raise ValueError("trace schema version is not the all-DSA generic version")
    if trace["scenario_id"] != scenario_id or trace["source_problem_id"] != scenario_id:
        raise ValueError("trace source problem identity does not match scenario")
    if trace["path_kind"] != "model_generated":
        raise ValueError("trace path_kind must be model_generated")
    if trace["plan_provenance"] != dict(plan.to_payload()["provenance"]):
        raise ValueError("trace plan provenance does not match persisted plan")
    reference = trace["plan_payload_reference"]
    if not isinstance(reference, Mapping) or reference.get("scenario_id") != scenario_id:
        raise ValueError("trace plan payload reference does not match scenario")


def _replay_prefix(
    plan: TeachingPlan,
    transcript_rows: Sequence[Mapping[str, Any]],
    trace_rows: Sequence[Mapping[str, Any]],
    *,
    scenario_id: str,
    forbidden_terms: Sequence[str] = (),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], GenericModelTutoringController]:
    """Return only the validated matching prefix and reconstruct controller state."""

    controller = GenericModelTutoringController(
        plan,
        model_identifier=plan.provenance.model_identifier,
        forbidden_terms=forbidden_terms,
    )
    transcript = _scenario_rows(transcript_rows, scenario_id)
    traces = _scenario_rows(trace_rows, scenario_id)
    by_turn_trace = {
        int(row["turn_index"]): row
        for row in traces
        if isinstance(row.get("turn_index"), int) and not isinstance(row["turn_index"], bool)
    }
    valid_transcript: list[dict[str, Any]] = []
    valid_trace: list[dict[str, Any]] = []
    for expected_turn, row in enumerate(transcript):
        try:
            if row.get("schema_version") != TRANSCRIPT_SCHEMA_VERSION:
                break
            if int(row.get("turn_index", -1)) != expected_turn:
                break
            trace = by_turn_trace.get(expected_turn)
            if trace is None:
                break
            if str(row.get("scenario_id")) != scenario_id:
                break
            learner_message = row["learner_message"]
            teacher_message = row["teacher_message"]
            if not isinstance(learner_message, str) or not learner_message.strip():
                break
            if not isinstance(teacher_message, str) or not teacher_message.strip():
                break
            diagnosis = ModelDiagnosis.from_payload(row["model_diagnosis"])
            assessment = LearnerAssessment.from_payload(
                row["model_assessment"], learner_message=learner_message
            )
            authorization = controller.authorize(
                diagnosis,
                assessment,
                learner_message=learner_message,
                turn_index=expected_turn,
            )
            validate_generated_response(teacher_message, authorization.contract)
            _validate_trace_shape(trace, scenario_id=scenario_id, plan=plan)
            if trace.get("active_concept_id") != authorization.contract.active_concept_id:
                break
            if trace.get("advance") != authorization.contract.advance_allowed:
                break
            if trace.get("evidence_quote") != assessment.evidence_quote:
                break
        except (KeyError, TypeError, ValueError, ModelTutoringError):
            break
        controller.commit(authorization)
        valid_transcript.append(row)
        valid_trace.append(trace)
    return valid_transcript, valid_trace, controller


def _validate_plan_record(
    row: Mapping[str, Any], *, scenario: Mapping[str, Any], prompt_registry: PromptRegistry
) -> TeachingPlan:
    public = _public_problem(scenario)
    if row.get("schema_version") != PLAN_RECORD_SCHEMA_VERSION:
        raise ValueError("plan record schema version is not the all-DSA version")
    if row.get("scenario_id") != public["scenario_id"]:
        raise ValueError("plan record scenario does not match corpus")
    payload = row.get("plan_payload")
    if not isinstance(payload, Mapping):
        raise ValueError("plan record does not contain a plan payload")
    plan = TeachingPlan.from_payload(payload)
    if plan.problem.id != public["scenario_id"] or plan.problem.statement != public["problem"]:
        raise ValueError("persisted plan is not source-matched")
    _validate_source_variable_bindings(plan, scenario)
    prompt_registry.verify(
        version=plan.provenance.prompt_version,
        prompt_hash=plan.provenance.prompt_hash,
    )
    if plan.provenance.turn_trace_schema_version != TRACE_SCHEMA_VERSION:
        raise ValueError("persisted plan uses an incompatible trace schema")
    if row.get("plan_provenance") != dict(payload["provenance"]):
        raise ValueError("plan record provenance does not match plan payload")
    return plan


def _prepare_existing(
    selected: Sequence[Mapping[str, Any]],
    *,
    transcript_rows: Sequence[Mapping[str, Any]],
    trace_rows: Sequence[Mapping[str, Any]],
    plan_rows: Sequence[Mapping[str, Any]],
    scenario_ids: set[str] | None,
    fresh: bool,
    prompt_registry: PromptRegistry,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, TeachingPlan]]:
    selected_ids = {str(item["id"]) for item in selected}
    if fresh:
        transcript = [row for row in transcript_rows if str(row.get("scenario_id")) not in selected_ids]
        trace = [row for row in trace_rows if str(row.get("scenario_id")) not in selected_ids]
        plans = [row for row in plan_rows if str(row.get("scenario_id")) not in selected_ids]
    else:
        transcript = [dict(row) for row in transcript_rows]
        trace = [dict(row) for row in trace_rows]
        plans = [dict(row) for row in plan_rows]

    plan_by_id: dict[str, TeachingPlan] = {}
    plan_rows_by_id: dict[str, dict[str, Any]] = {}
    for row in plans:
        scenario_id = str(row.get("scenario_id", ""))
        if scenario_id not in selected_ids:
            continue
        if scenario_id in plan_rows_by_id:
            raise ValueError(f"multiple persisted plans for scenario {scenario_id}")
        plan_rows_by_id[scenario_id] = row

    normalized_transcript = [row for row in transcript if str(row.get("scenario_id")) not in selected_ids]
    normalized_trace = [row for row in trace if str(row.get("scenario_id")) not in selected_ids]
    normalized_plans = [row for row in plans if str(row.get("scenario_id")) not in selected_ids]

    for scenario in selected:
        scenario_id = str(scenario["id"])
        plan_row = plan_rows_by_id.get(scenario_id)
        if plan_row is None:
            continue
        plan = _validate_plan_record(
            plan_row,
            scenario=scenario,
            prompt_registry=prompt_registry,
        )
        plan_by_id[scenario_id] = plan
        prefix_transcript, prefix_trace, _controller = _replay_prefix(
            plan,
            transcript_rows,
            trace_rows,
            scenario_id=scenario_id,
            forbidden_terms=tuple(scenario.get("forbidden_aliases", ())),
        )
        normalized_transcript.extend(prefix_transcript)
        normalized_trace.extend(prefix_trace)
        normalized_plans.append(plan_row)

    normalized_transcript.sort(key=lambda row: (str(row.get("scenario_id")), int(row.get("turn_index", -1))))
    normalized_trace.sort(key=lambda row: (str(row.get("scenario_id")), int(row.get("turn_index", -1))))
    return normalized_transcript, normalized_trace, normalized_plans, plan_by_id


def _new_run_id() -> str:
    return "all-dsa-" + uuid.uuid4().hex


def _diagnose(
    *,
    teacher: Actor,
    scenario: Mapping[str, Any],
    controller: GenericModelTutoringController,
    turn_index: int,
    learner_message: str,
    conversation: Sequence[Mapping[str, str]],
) -> Authorization:
    error: str | None = None
    last_response = ""
    for _attempt in range(DIAGNOSIS_RETRIES):
        result = teacher.ask(
            build_diagnosis_payload(
                scenario,
                controller=controller,
                turn_index=turn_index,
                learner_message=learner_message,
                conversation=conversation,
                repair_feedback=error,
            )
        )
        last_response = _extract_actor_message(result, role="teacher")
        try:
            payload = _json_object(last_response, label="model decision")
            diagnosis, assessment = parse_model_decision(
                json.dumps(payload, ensure_ascii=False),
                learner_message=learner_message,
            )
            return controller.authorize(
                diagnosis,
                assessment,
                learner_message=learner_message,
                turn_index=turn_index,
            )
        except (ModelTutoringError, ValueError) as exc:
            error = str(exc)
    raise RuntimeError(
        f"teacher diagnosis failed at turn {turn_index}: {error}; "
        f"last response={last_response[:800]!r}"
    )


def _generate(
    *,
    teacher: Actor,
    scenario: Mapping[str, Any],
    authorization: Authorization,
    learner_message: str,
    conversation: Sequence[Mapping[str, str]],
    prompt_registry: PromptRegistry,
) -> str:
    error: str | None = None
    last_response = ""
    for _attempt in range(GENERATION_RETRIES):
        result = teacher.ask(
            build_generation_payload(
                scenario,
                authorization=authorization,
                learner_message=learner_message,
                conversation=conversation,
                prompt_registry=prompt_registry,
                repair_feedback=error,
            )
        )
        last_response = _extract_actor_message(result, role="teacher")
        try:
            payload = _json_object(last_response, label="model generation")
            generated = parse_generation_response(json.dumps(payload, ensure_ascii=False))
            validate_generated_response(generated, authorization.contract)
            return generated
        except (ModelTutoringError, ValueError) as exc:
            error = str(exc)
    raise RuntimeError(
        f"teacher generation failed at turn {authorization.contract.turn_index}: {error}; "
        f"last response={last_response[:800]!r}"
    )


def _decompose(
    *,
    teacher: Actor,
    scenario: Mapping[str, Any],
    run_id: str,
    model_identifier: str,
    prompt_registry: PromptRegistry,
) -> TeachingPlan:
    error: str | None = None
    last_response = ""
    for _attempt in range(PLAN_RETRIES):
        result = teacher.ask(
            build_decomposer_payload(scenario, repair_feedback=error)
        )
        last_response = _extract_actor_message(result, role="teacher")
        try:
            return parse_plan_response(
                last_response,
                scenario=scenario,
                run_id=run_id,
                model_identifier=model_identifier,
                prompt_registry=prompt_registry,
            )
        except (TeachingPlanValidationError, ModelTutoringError, ValueError) as exc:
            error = str(exc)
    raise RuntimeError(
        f"teacher decomposition failed for {scenario['id']}: {error}; "
        f"last response={last_response[:800]!r}"
    )


def _state_payload(state: LearnerState, *, active_concept_id: str) -> dict[str, Any]:
    return {
        "concept_index": state.concept_index,
        "turns_seen": state.turns_seen,
        "active_concept_id": active_concept_id,
    }


def _turn_trace(
    authorization: Authorization,
    *,
    scenario: Mapping[str, Any],
    plan: TeachingPlan,
    plan_path: Path,
    state_before: LearnerState,
    state_after: LearnerState,
) -> dict[str, Any]:
    trace = dict(authorization.trace)
    trace.update(
        {
            "schema_version": TRACE_SCHEMA_VERSION,
            "scenario_id": str(scenario["id"]),
            "target_concept": authorization.contract.active_concept_id,
            "forbidden_variables": list(authorization.contract.forbidden_variables),
            "plan_payload_reference": _plan_reference(plan_path, plan),
            "controller_state_before": _state_payload(
                state_before, active_concept_id=authorization.contract.active_concept_id
            ),
            "controller_state_after": _state_payload(
                state_after,
                active_concept_id=plan.concepts[state_after.concept_index].id,
            ),
        }
    )
    _validate_trace_shape(trace, scenario_id=str(scenario["id"]), plan=plan)
    return trace


def _transcript_record(
    authorization: Authorization,
    *,
    scenario: Mapping[str, Any],
    learner_message: str,
    learner_signal: str,
    teacher_message: str,
    plan: TeachingPlan,
    plan_path: Path,
    state_before: LearnerState,
    state_after: LearnerState,
) -> dict[str, Any]:
    return {
        "schema_version": TRANSCRIPT_SCHEMA_VERSION,
        "scenario_id": str(scenario["id"]),
        "title": str(scenario["title"]),
        "problem": str(scenario["problem"]),
        "turn_index": authorization.contract.turn_index,
        "run_id": plan.provenance.run_id,
        "learner_signal": learner_signal,
        "learner_message": learner_message,
        "teacher_message": teacher_message,
        "model_diagnosis": asdict(authorization.diagnosis),
        "model_assessment": asdict(authorization.assessment),
        "controller_state_before": _state_payload(
            state_before, active_concept_id=authorization.contract.active_concept_id
        ),
        "controller_state_after": _state_payload(
            state_after,
            active_concept_id=plan.concepts[state_after.concept_index].id,
        ),
        "plan_provenance": dict(plan.to_payload()["provenance"]),
        "plan_payload_reference": _plan_reference(plan_path, plan),
    }


def run_all_dsa(
    corpus: Mapping[str, Any],
    student: Actor,
    teacher: Actor,
    *,
    scenario_ids: set[str] | None = None,
    turns_per_scenario: int = TURNS_PER_SCENARIO,
    model_identifier: str = DEFAULT_MODEL,
    transcript_path: Path = DEFAULT_TRANSCRIPT,
    markdown_path: Path = DEFAULT_MARKDOWN,
    trace_path: Path = DEFAULT_TRACE,
    plans_path: Path = DEFAULT_PLANS,
    fresh: bool = False,
    allow_short_run: bool = False,
    run_id: str | None = None,
    prompt_registry: PromptRegistry = DEFAULT_PROMPT_REGISTRY,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Run selected scenarios, checkpointing and resuming validated prefixes."""

    if turns_per_scenario < 1:
        raise ValueError("turns_per_scenario must be >= 1")
    selected = raw.select_scenarios(corpus, scenario_ids)
    if not selected:
        raise ValueError("corpus selection is empty")
    if not allow_short_run:
        if scenario_ids is not None or len(selected) != REQUIRED_SCENARIO_COUNT:
            raise RuntimeError(
                "default all-DSA run requires all corpus scenarios; use --allow-short-run "
                "for a selected development run"
            )
        if any(len(item.get("turns", [])) != TURNS_PER_SCENARIO for item in selected):
            raise RuntimeError("default all-DSA run requires 15 learner turns per scenario")

    transcript_path = Path(transcript_path)
    markdown_path = Path(markdown_path)
    trace_path = Path(trace_path)
    plans_path = Path(plans_path)
    existing_transcript = _load_jsonl(transcript_path)
    existing_trace = _load_jsonl(trace_path)
    existing_plans = _load_jsonl(plans_path)
    transcript, trace, plans, plan_by_id = _prepare_existing(
        selected,
        transcript_rows=existing_transcript,
        trace_rows=existing_trace,
        plan_rows=existing_plans,
        scenario_ids=scenario_ids,
        fresh=fresh,
        prompt_registry=prompt_registry,
    )

    existing_run_ids = {plan.provenance.run_id for plan in plan_by_id.values()}
    if run_id is None and not fresh and len(existing_run_ids) == 1:
        run_id = next(iter(existing_run_ids))
    run_id = run_id or _new_run_id()
    _checkpoint(
        transcript,
        trace,
        plans,
        transcript_path=transcript_path,
        markdown_path=markdown_path,
        trace_path=trace_path,
        plans_path=plans_path,
    )

    for scenario in selected:
        scenario_id = str(scenario["id"])
        plan = plan_by_id.get(scenario_id)
        if plan is None:
            plan = _decompose(
                teacher=teacher,
                scenario=scenario,
                run_id=run_id,
                model_identifier=model_identifier,
                prompt_registry=prompt_registry,
            )
            plan_by_id[scenario_id] = plan
            plans = [row for row in plans if str(row.get("scenario_id")) != scenario_id]
            plans.append(_plan_record(plan, plan_path=plans_path))
            plans.sort(key=lambda row: str(row.get("scenario_id")))
            _checkpoint(
                transcript,
                trace,
                plans,
                transcript_path=transcript_path,
                markdown_path=markdown_path,
                trace_path=trace_path,
                plans_path=plans_path,
            )

        previous_transcript, previous_trace, controller = _replay_prefix(
            plan,
            transcript,
            trace,
            scenario_id=scenario_id,
            forbidden_terms=tuple(scenario.get("forbidden_aliases", ())),
        )
        transcript = [row for row in transcript if str(row.get("scenario_id")) != scenario_id]
        trace = [row for row in trace if str(row.get("scenario_id")) != scenario_id]
        transcript.extend(previous_transcript)
        trace.extend(previous_trace)
        conversation = raw._conversation_from_records(previous_transcript)

        for turn_index in range(len(previous_transcript), turns_per_scenario):
            student_payload = raw.build_student_payload(
                scenario,
                turn_index=turn_index,
                conversation=conversation,
            )
            student_result = student.ask(student_payload)
            learner_message = _extract_actor_message(student_result, role="student")
            learner_signal = str(student_payload.get("learner_signal", ""))
            conversation_with_learner = conversation + [
                {"role": "learner", "content": learner_message}
            ]
            state_before = controller.state
            authorization = _diagnose(
                teacher=teacher,
                scenario=scenario,
                controller=controller,
                turn_index=turn_index,
                learner_message=learner_message,
                conversation=conversation_with_learner,
            )
            teacher_message = _generate(
                teacher=teacher,
                scenario=scenario,
                authorization=authorization,
                learner_message=learner_message,
                conversation=conversation_with_learner,
                prompt_registry=prompt_registry,
            )
            state_after = authorization.next_state
            trace_record = _turn_trace(
                authorization,
                scenario=scenario,
                plan=plan,
                plan_path=plans_path,
                state_before=state_before,
                state_after=state_after,
            )
            transcript_record = _transcript_record(
                authorization,
                scenario=scenario,
                learner_message=learner_message,
                learner_signal=learner_signal,
                teacher_message=teacher_message,
                plan=plan,
                plan_path=plans_path,
                state_before=state_before,
                state_after=state_after,
            )

            # The generated response and trace have passed all deterministic checks.
            # Only now does the controller advance and the accepted exchange enter
            # either durable snapshot.
            controller.commit(authorization)
            transcript.append(transcript_record)
            trace.append(trace_record)
            conversation.extend(
                [
                    {"role": "learner", "content": learner_message},
                    {"role": "teacher", "content": teacher_message},
                ]
            )
            _checkpoint(
                transcript,
                trace,
                plans,
                transcript_path=transcript_path,
                markdown_path=markdown_path,
                trace_path=trace_path,
                plans_path=plans_path,
            )
            print(
                f"captured {scenario_id} exchange {turn_index + 1}; "
                f"concept={authorization.contract.active_concept_id}; "
                f"outcome={authorization.assessment.learner_outcome}"
            )

    if not allow_short_run:
        counts = {
            scenario_id: len(_scenario_rows(transcript, scenario_id))
            for scenario_id in (str(item["id"]) for item in selected)
        }
        if counts != {str(item["id"]): TURNS_PER_SCENARIO for item in selected}:
            raise RuntimeError(f"all-DSA run is incomplete: {counts}")
    return transcript, trace, plans


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run generic model tutoring for all DSA replay scenarios"
    )
    parser.add_argument("--corpus", type=Path, default=raw.DEFAULT_CORPUS)
    parser.add_argument("--fresh", action="store_true", help="discard selected persisted prefixes")
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--mcp-name", default=DEFAULT_MCP_NAME)
    parser.add_argument("--turn-timeout-seconds", type=int, default=DEFAULT_TURN_TIMEOUT_SECONDS)
    parser.add_argument(
        "--skip-local-setup",
        action="store_true",
        help="skip local Codex/runtime checks and MCP registration",
    )
    parser.add_argument(
        "--allow-short-run",
        action="store_true",
        help="development only: allow selected or incomplete corpus runs",
    )
    parser.add_argument("--transcript", type=Path, default=DEFAULT_TRANSCRIPT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--plans", type=Path, default=DEFAULT_PLANS)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    corpus = raw.load_corpus(args.corpus)
    scenario_ids = set(args.scenario) or None

    if not args.skip_local_setup:
        version = local.ensure_codex_available(args.codex_bin)
        print(f"local Codex: {version}")
        local.ensure_local_runtime(args.python_bin)
        local.configure_local_study_os_mcp(
            args.codex_bin,
            args.python_bin,
            args.mcp_name,
        )
        print(f"Study OS MCP ready: {args.mcp_name}")

    student = local.CodexCliActor(
        role="student",
        codex_bin=args.codex_bin,
        model=args.model,
        mcp_name=args.mcp_name,
        timeout_seconds=args.turn_timeout_seconds,
    )
    teacher = AllDSATeacherActor(
        role="teacher",
        codex_bin=args.codex_bin,
        model=args.model,
        mcp_name=args.mcp_name,
        timeout_seconds=args.turn_timeout_seconds,
    )
    try:
        transcript, trace, plans = run_all_dsa(
            corpus,
            student,
            teacher,
            scenario_ids=scenario_ids,
            model_identifier=args.model,
            transcript_path=args.transcript,
            markdown_path=args.markdown,
            trace_path=args.trace,
            plans_path=args.plans,
            fresh=args.fresh,
            allow_short_run=args.allow_short_run,
        )
    finally:
        student.close()
        teacher.close()

    print(
        f"captured generic all-DSA tutoring: {len(plans)} plans / "
        f"{len(transcript)} exchanges / {len(transcript) * 2} visible messages"
    )
    print(f"transcript: {args.transcript}")
    print(f"trace: {args.trace}")
    print(f"plans: {args.plans}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
