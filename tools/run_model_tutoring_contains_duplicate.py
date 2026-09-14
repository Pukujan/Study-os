#!/usr/bin/env python3
"""Run the bounded model-tutoring pilot for Contains Duplicate.

This is a pilot runner, not a replacement replay harness.  It reuses the existing
local Codex actors and local Study OS MCP wiring, but inserts the model/schema seam:
Luna diagnoses, the deterministic kernel authorizes, and Luna generates a bounded
learner-visible response that is validated before persistence.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import run_dual_luna_local_codex as local  # noqa: E402
import run_dual_luna_transcript as raw  # noqa: E402
from study_os.model_tutoring import (  # noqa: E402
    ASSISTANCE_LEVELS,
    DIAGNOSIS_FAMILIES,
    ModelDiagnosis,
    ModelTutoringController,
    ModelTutoringError,
    OPERATIONS,
    SCENARIO_ID,
    build_generation_prompt,
    parse_generation_response,
    parse_model_diagnosis,
    validate_generated_response,
)


DEFAULT_TRANSCRIPT = ROOT / "artifacts" / "model-tutoring-contains-duplicate.jsonl"
DEFAULT_TRACE = ROOT / "artifacts" / "model-tutoring-contains-duplicate-trace.jsonl"
DEFAULT_MARKDOWN = ROOT / "artifacts" / "model-tutoring-contains-duplicate.md"
DEFAULT_MODEL = "gpt-5.6-luna"


class PilotTeacherActor(local.CodexCliActor):
    """Teacher actor whose only product-facing path is local Study OS + model output."""

    def _role_contract(self) -> str:
        return (
            "You are Luna, the adaptive teacher in a Study OS model-tutoring pilot. "
            f"For EVERY request call the local MCP server {self.mcp_name!r} using its "
            "resolve_problem tool with the supplied problem text and domain dsa. The "
            "tool may report that no reviewed asset exists; that is internal routing "
            "evidence and must never appear in learner-visible output. Continue through "
            "the supplied bounded generation contract. Do not edit files or use any "
            "other tools.\n\n"
            "In diagnosis phase, return JSON only with a diagnosis object containing "
            "diagnosis_family, operation, assistance_level, and a short decomposition; "
            f"diagnosis_family MUST be one of {sorted(DIAGNOSIS_FAMILIES)}, operation "
            f"MUST be one of {sorted(OPERATIONS)}, and assistance_level MUST be one of "
            f"{sorted(ASSISTANCE_LEVELS)}; do not invent labels. Do not include a response. "
            "In generation phase, return JSON only with a "
            "response string; do not include commentary outside JSON. The deterministic "
            "controller owns stage, progression, variables, assistance ceiling, and "
            "mastery. Never claim mastery or change the current concept."
        )

    def _parse_events(self, stdout: str) -> tuple[str | None, str, bool, list[str]]:
        thread_id, message, _mcp_completed, errors = super()._parse_events(stdout)
        resolved = False
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            item = event.get("item") if isinstance(event, dict) else None
            if not isinstance(item, dict) or item.get("type") != "mcp_tool_call":
                continue
            if (
                item.get("server") == self.mcp_name
                and item.get("tool") == "resolve_problem"
                and item.get("status") == "completed"
            ):
                resolved = True
        if not resolved:
            raise RuntimeError(
                "teacher did not complete the required Study OS resolve_problem MCP call"
            )
        return thread_id, message, True, errors


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} must contain an object")
        rows.append(value)
    return rows


def _matching_prefix(
    transcript: list[dict[str, Any]], trace: list[dict[str, Any]], scenario_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Resume only a contiguous common prefix; discard an incomplete final turn."""

    transcript = sorted(
        [row for row in transcript if str(row.get("scenario_id")) == scenario_id],
        key=lambda row: int(row.get("turn_index", -1)),
    )
    trace = sorted(
        [row for row in trace if str(row.get("scenario_id")) == scenario_id],
        key=lambda row: int(row.get("turn_index", -1)),
    )
    common: list[dict[str, Any]] = []
    common_trace: list[dict[str, Any]] = []
    for index in range(min(len(transcript), len(trace))):
        if int(transcript[index].get("turn_index", -1)) != index:
            break
        if int(trace[index].get("turn_index", -1)) != index:
            break
        common.append(transcript[index])
        common_trace.append(trace[index])
    return common, common_trace


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    temp.replace(path)


def _write_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(raw.render_markdown(rows), encoding="utf-8")
    temp.replace(path)


def _scenario(corpus: dict[str, Any]) -> dict[str, Any]:
    matches = [item for item in corpus.get("scenarios", []) if item.get("id") == SCENARIO_ID]
    if len(matches) != 1:
        raise ValueError("corpus must contain exactly one contains-duplicate-set scenario")
    return matches[0]


def _signal(scenario: dict[str, Any], index: int) -> str:
    return str(scenario["turns"][index]["learner_signal"])


def _replay_state(
    controller: ModelTutoringController,
    scenario: dict[str, Any],
    rows: list[dict[str, Any]],
) -> None:
    diagnosis = ModelDiagnosis("uncertain_mixed", "probe", "A1")
    for row in rows:
        index = int(row["turn_index"])
        authorization = controller.authorize(
            diagnosis,
            turn_index=index,
            learner_signal=_signal(scenario, index),
        )
        controller.commit(authorization)


def _teacher_payload(
    *,
    scenario: dict[str, Any],
    turn_index: int,
    learner_message: str,
    conversation: list[dict[str, str]],
    phase: str,
    contract: Any | None = None,
    previous_error: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": "model_tutoring_teacher_turn",
        "role": "teacher",
        "phase": phase,
        "scenario_id": scenario["id"],
        "title": scenario["title"],
        "problem": scenario["problem"],
        "domain": "dsa",
        "turn_index": turn_index,
        "learner_message": learner_message,
        "conversation": list(conversation),
    }
    if contract is not None:
        payload["generation_contract"] = asdict(contract)
        payload["generation_prompt"] = build_generation_prompt(
            contract,
            learner_message=learner_message,
            history=conversation,
        )
    elif phase == "diagnosis":
        payload["diagnosis_schema"] = {
            "diagnosis_family": sorted(DIAGNOSIS_FAMILIES),
            "operation": sorted(OPERATIONS),
            "assistance_level": sorted(ASSISTANCE_LEVELS),
        }
    if previous_error:
        payload["repair_feedback"] = previous_error
    return payload


def run_pilot(
    *,
    scenario: dict[str, Any],
    student: local.CodexCliActor,
    teacher: PilotTeacherActor,
    transcript_rows: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
    transcript_path: Path,
    trace_path: Path,
    markdown_path: Path,
    turns: int = 15,
    model_identifier: str = DEFAULT_MODEL,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    controller = ModelTutoringController(model_identifier=model_identifier)
    _replay_state(controller, scenario, transcript_rows)
    conversation = raw._conversation_from_records(transcript_rows)

    for turn_index in range(len(transcript_rows), turns):
        learner_result = student.ask(
            raw.build_student_payload(
                scenario,
                turn_index=turn_index,
                conversation=conversation,
            )
        )
        learner_message = raw._extract_message(learner_result, role="student")
        conversation_with_learner = conversation + [
            {"role": "learner", "content": learner_message}
        ]
        learner_signal = _signal(scenario, turn_index)

        diagnosis: ModelDiagnosis | None = None
        diagnosis_error: str | None = None
        diagnosis_raw: str = ""
        for _attempt in range(3):
            diagnosis_result = teacher.ask(
                _teacher_payload(
                    scenario=scenario,
                    turn_index=turn_index,
                    learner_message=learner_message,
                    conversation=conversation_with_learner,
                    phase="diagnosis",
                    previous_error=diagnosis_error,
                )
            )
            try:
                diagnosis_raw = raw._extract_message(diagnosis_result, role="teacher")
                diagnosis = parse_model_diagnosis(diagnosis_raw)
                break
            except ModelTutoringError as exc:
                diagnosis_error = str(exc)
        if diagnosis is None:
            raise RuntimeError(
                f"teacher diagnosis failed at turn {turn_index}: {diagnosis_error}; "
                f"last response={diagnosis_raw[:800]!r}"
            )

        authorization = controller.authorize(
            diagnosis,
            scenario_id=SCENARIO_ID,
            turn_index=turn_index,
            learner_signal=learner_signal,
        )
        generation_error: str | None = None
        generated: str | None = None
        for _attempt in range(4):
            generation_result = teacher.ask(
                _teacher_payload(
                    scenario=scenario,
                    turn_index=turn_index,
                    learner_message=learner_message,
                    conversation=conversation_with_learner,
                    phase="generation",
                    contract=authorization.contract,
                    previous_error=generation_error,
                )
            )
            try:
                generated = parse_generation_response(
                    raw._extract_message(generation_result, role="teacher")
                )
                validate_generated_response(generated, authorization.contract)
                break
            except ModelTutoringError as exc:
                generated = None
                generation_error = str(exc)
        if generated is None:
            raise RuntimeError(f"teacher generation failed at turn {turn_index}: {generation_error}")

        record = {
            "schema_version": "study-os.model-tutoring-exchange.v0.1",
            "scenario_id": scenario["id"],
            "title": scenario["title"],
            "problem": scenario["problem"],
            "turn_index": turn_index,
            "learner_signal": learner_signal,
            "learner_message": learner_message,
            "teacher_message": generated,
            "model_diagnosis": asdict(diagnosis),
            "controller_stage": authorization.contract.stage,
        }
        transcript_rows.append(record)
        trace_rows.append(authorization.trace)
        controller.commit(authorization)
        conversation.extend(
            [
                {"role": "learner", "content": learner_message},
                {"role": "teacher", "content": generated},
            ]
        )
        _write_jsonl(transcript_rows, transcript_path)
        _write_jsonl(trace_rows, trace_path)
        _write_markdown(transcript_rows, markdown_path)
        print(f"captured contains-duplicate exchange {turn_index + 1}; total={len(transcript_rows)}")

    return transcript_rows, trace_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the bounded Contains Duplicate model tutoring pilot")
    parser.add_argument("--corpus", type=Path, default=raw.DEFAULT_CORPUS)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--mcp-name", default=local.DEFAULT_MCP_NAME)
    parser.add_argument("--transcript", type=Path, default=DEFAULT_TRANSCRIPT)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--turn-timeout-seconds", type=int, default=local.DEFAULT_TURN_TIMEOUT_SECONDS)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--keep-codex-sandbox", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    corpus = raw.load_corpus(args.corpus)
    scenario = _scenario(corpus)
    if not args.fresh:
        transcript = _load_rows(args.transcript)
        trace = _load_rows(args.trace)
    else:
        transcript, trace = [], []
    transcript, trace = _matching_prefix(transcript, trace, SCENARIO_ID)
    if transcript or trace:
        _write_jsonl(transcript, args.transcript)
        _write_jsonl(trace, args.trace)

    version = local.ensure_codex_available(args.codex_bin)
    print(f"local Codex: {version}")
    local.ensure_local_runtime(args.python_bin)
    local.configure_local_study_os_mcp(args.codex_bin, args.python_bin, args.mcp_name)
    print(f"Study OS MCP ready: {args.mcp_name}")

    full_access = not args.keep_codex_sandbox
    student = local.CodexCliActor(
        role="student",
        codex_bin=args.codex_bin,
        model=args.model,
        mcp_name=args.mcp_name,
        full_access=full_access,
        timeout_seconds=args.turn_timeout_seconds,
    )
    teacher = PilotTeacherActor(
        role="teacher",
        codex_bin=args.codex_bin,
        model=args.model,
        mcp_name=args.mcp_name,
        full_access=full_access,
        timeout_seconds=args.turn_timeout_seconds,
    )
    try:
        transcript, trace = run_pilot(
            scenario=scenario,
            student=student,
            teacher=teacher,
            transcript_rows=transcript,
            trace_rows=trace,
            transcript_path=args.transcript,
            trace_path=args.trace,
            markdown_path=args.markdown,
            model_identifier=args.model,
        )
    finally:
        student.close()
        teacher.close()

    if len(transcript) != 15 or len(trace) != 15:
        raise RuntimeError("pilot must finish exactly 15 transcript and trace turns")
    print(f"captured model tutoring pilot: {len(transcript)} exchanges / {len(transcript) * 2} visible messages")
    print(f"transcript: {args.transcript}")
    print(f"trace: {args.trace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
