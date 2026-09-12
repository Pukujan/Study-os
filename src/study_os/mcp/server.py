"""Small dependency-free MCP stdio boundary for the semantic service."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from ..application.contracts import (
    AppendConversationTurnRequest,
    NextRetentionProbeRequest,
    RecordAssessmentRequest,
    RecordAttemptRequest,
    RecordLearningEventRequest,
    RecordRepresentationInterventionRequest,
    RecordRepresentationOutcomeRequest,
    ResumeLearningContextRequest,
    ResumeSubjectRequest,
    ScheduleRetentionProbeRequest,
    StartStudySessionRequest,
    SubjectStatusRequest,
)
from ..application.pir_contracts import (
    GetProblemTurnRequest,
    RequestProblemExpansionRequest,
    ResolveProblemRequest,
    StartProblemRequest,
    SubmitProblemResponseRequest,
)
from ..application.pir_service import (
    PIRApplicationService,
    project_get_problem_turn_to_mcp,
    project_request_problem_expansion_to_mcp,
    project_resolve_problem_to_mcp,
    project_start_problem_to_mcp,
    project_submit_problem_response_to_mcp,
)
from ..application.service import (
    project_append_conversation_turn_to_mcp,
    project_next_retention_probe_to_mcp,
    project_record_assessment_to_mcp,
    project_record_attempt_to_mcp,
    project_record_learning_event_to_mcp,
    project_record_representation_intervention_to_mcp,
    project_record_representation_outcome_to_mcp,
    project_resume_learning_context_to_mcp,
    project_resume_subject_to_mcp,
    project_runtime_health_to_mcp,
    project_schedule_retention_probe_to_mcp,
    project_start_study_session_to_mcp,
    project_subject_status_to_mcp,
)
from ..errors import StudyOSError, validation
from ..services.runtime import StudyOSService
from .tools import CONTRACT_PATH, load_contract


class MCPServer:
    def __init__(
        self,
        service: StudyOSService | None = None,
        contract_path: str | Path | None = None,
    ) -> None:
        self.service = service or StudyOSService()
        self.application = PIRApplicationService(self.service)
        path = Path(contract_path) if contract_path else CONTRACT_PATH
        self.contract = load_contract(path)
        self.tool_specs = {tool["name"]: tool for tool in self.contract["tools"]}

    def list_tool_names(self) -> list[str]:
        return [tool["name"] for tool in self.contract["tools"]]

    def list_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for spec in self.contract["tools"]:
            required = list(spec["required_input"])
            properties = {name: {} for name in required}
            if spec["name"] == "request_problem_expansion":
                properties["request_kind"] = {
                    "type": "string",
                    "enum": [
                        "why",
                        "easier_example",
                        "more_detail",
                        "repeat_representation",
                        "clarify_term",
                    ],
                    "description": "Choose one supported expansion kind exactly.",
                }
            description = spec.get(
                "description", f"Study OS semantic operation: {spec['name']}"
            )
            tools.append(
                {
                    "name": spec["name"],
                    "description": description,
                    "inputSchema": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                        "additionalProperties": True,
                    },
                }
            )
        return tools

    def _validate_arguments(self, name: str, arguments: dict[str, Any]) -> None:
        if not isinstance(arguments, dict):
            raise validation("Tool arguments must be an object")
        spec = self.tool_specs.get(name)
        if spec is None:
            raise validation("Unknown MCP tool", tool=name)
        missing = [field for field in spec["required_input"] if field not in arguments]
        if missing:
            raise validation(
                "Required MCP tool arguments are missing",
                tool=name,
                missing=missing,
            )

    @staticmethod
    def _reject_unexpected(
        name: str,
        arguments: dict[str, Any],
        allowed: set[str],
    ) -> None:
        unexpected = sorted(set(arguments) - allowed)
        if unexpected:
            raise validation(
                f"{name} received unexpected arguments",
                unexpected=unexpected,
            )

    def _dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "doctor":
            if arguments:
                raise validation(
                    "doctor does not accept arguments",
                    unexpected=sorted(arguments),
                )
            result = project_runtime_health_to_mcp(
                self.application.inspect_runtime_health()
            )
        elif name == "status":
            self._reject_unexpected(name, arguments, {"subject_id"})
            request = SubjectStatusRequest(**arguments)
            result = project_subject_status_to_mcp(
                self.application.get_subject_status(request)
            )
        elif name == "resume":
            self._reject_unexpected(name, arguments, {"subject_id"})
            request = ResumeSubjectRequest(**arguments)
            result = project_resume_subject_to_mcp(
                self.application.resume_subject(request)
            )
        elif name == "resume_learning_context":
            self._reject_unexpected(name, arguments, {"subject_id"})
            request = ResumeLearningContextRequest(**arguments)
            result = project_resume_learning_context_to_mcp(
                self.application.resume_learning_context(request)
            )
        elif name == "get_next_probe":
            self._reject_unexpected(name, arguments, {"subject_id"})
            request = NextRetentionProbeRequest(**arguments)
            result = project_next_retention_probe_to_mcp(
                self.application.get_next_retention_probe(request)
            )
        elif name == "resolve_problem":
            self._reject_unexpected(name, arguments, {"problem_text", "domain"})
            request = ResolveProblemRequest(**arguments)
            result = project_resolve_problem_to_mcp(
                self.application.resolve_problem(request)
            )
        elif name == "start_problem":
            self._reject_unexpected(
                name,
                arguments,
                {
                    "idempotency_key",
                    "session_id",
                    "subject_id",
                    "canonical_problem_id",
                },
            )
            request = StartProblemRequest(**arguments)
            result = project_start_problem_to_mcp(
                self.application.start_problem(request)
            )
        elif name == "get_problem_turn":
            self._reject_unexpected(
                name,
                arguments,
                {"problem_run_id", "subject_id"},
            )
            request = GetProblemTurnRequest(**arguments)
            result = project_get_problem_turn_to_mcp(
                self.application.get_problem_turn(request)
            )
        elif name == "submit_problem_response":
            self._reject_unexpected(
                name,
                arguments,
                {
                    "idempotency_key",
                    "problem_run_id",
                    "subject_id",
                    "turn_id",
                    "response",
                },
            )
            request = SubmitProblemResponseRequest(**arguments)
            result = project_submit_problem_response_to_mcp(
                self.application.submit_problem_response(request)
            )
        elif name == "request_problem_expansion":
            self._reject_unexpected(
                name,
                arguments,
                {
                    "idempotency_key",
                    "problem_run_id",
                    "subject_id",
                    "turn_id",
                    "request_kind",
                    "learner_request",
                },
            )
            request = RequestProblemExpansionRequest(**arguments)
            result = project_request_problem_expansion_to_mcp(
                self.application.request_problem_expansion(request)
            )
        elif name == "start_session":
            self._reject_unexpected(
                name,
                arguments,
                {
                    "idempotency_key",
                    "subject_id",
                    "project_id",
                    "domain_id",
                    "source_client",
                    "metadata",
                },
            )
            request = StartStudySessionRequest(**arguments)
            result = project_start_study_session_to_mcp(
                self.application.start_study_session(request)
            )
        elif name == "append_conversation_turn":
            self._reject_unexpected(
                name,
                arguments,
                {
                    "idempotency_key",
                    "session_id",
                    "subject_id",
                    "role",
                    "content",
                    "source_conversation_ref",
                    "source_message_ref",
                    "source_parent_ref",
                    "source_timestamp",
                    "source_sequence",
                    "source_client",
                },
            )
            request = AppendConversationTurnRequest(**arguments)
            result = project_append_conversation_turn_to_mcp(
                self.application.append_conversation_turn(request)
            )
        elif name == "record_attempt":
            self._reject_unexpected(
                name,
                arguments,
                {
                    "idempotency_key",
                    "session_id",
                    "subject_id",
                    "task_id",
                    "response",
                    "assistance_level",
                    "context",
                },
            )
            request = RecordAttemptRequest(**arguments)
            result = project_record_attempt_to_mcp(
                self.application.record_attempt(request)
            )
        elif name == "record_learning_event":
            self._reject_unexpected(
                name,
                arguments,
                {
                    "idempotency_key",
                    "session_id",
                    "subject_id",
                    "evidence_class",
                    "event_type",
                    "payload",
                    "source_ids",
                    "payload_version",
                },
            )
            request = RecordLearningEventRequest(**arguments)
            result = project_record_learning_event_to_mcp(
                self.application.record_learning_event(request)
            )
        elif name == "record_assessment":
            self._reject_unexpected(
                name,
                arguments,
                {
                    "idempotency_key",
                    "session_id",
                    "subject_id",
                    "capability",
                    "result",
                    "assistance_level",
                    "evidence_ids",
                    "retention_probe_id",
                },
            )
            request = RecordAssessmentRequest(**arguments)
            result = project_record_assessment_to_mcp(
                self.application.record_assessment(request)
            )
        elif name == "record_representation_intervention":
            self._reject_unexpected(
                name,
                arguments,
                {
                    "idempotency_key",
                    "session_id",
                    "subject_id",
                    "representation_family",
                    "operation",
                    "representation_version",
                    "target_bottleneck",
                },
            )
            request = RecordRepresentationInterventionRequest(**arguments)
            result = project_record_representation_intervention_to_mcp(
                self.application.record_representation_intervention(request)
            )
        elif name == "record_representation_outcome":
            self._reject_unexpected(
                name,
                arguments,
                {
                    "idempotency_key",
                    "intervention_id",
                    "subject_id",
                    "evidence_score",
                    "evidence_ids",
                },
            )
            request = RecordRepresentationOutcomeRequest(**arguments)
            result = project_record_representation_outcome_to_mcp(
                self.application.record_representation_outcome(request)
            )
        elif name == "schedule_retention_probe":
            self._reject_unexpected(
                name,
                arguments,
                {
                    "idempotency_key",
                    "subject_id",
                    "concept_id",
                    "due_at",
                    "source_checkpoint_id",
                },
            )
            request = ScheduleRetentionProbeRequest(**arguments)
            result = project_schedule_retention_probe_to_mcp(
                self.application.schedule_retention_probe(request)
            )
        else:
            method = getattr(self.service, name, None)
            if method is None or not callable(method):
                raise StudyOSError(
                    "internal_error",
                    f"No service implementation for MCP tool: {name}",
                    False,
                )
            result = method(**arguments)
        if not isinstance(result, dict):
            raise StudyOSError(
                "internal_error",
                "Service response must be an object",
                False,
                {"tool": name, "result_type": type(result).__name__},
            )
        spec = self.tool_specs[name]
        missing = [field for field in spec["required_output"] if field not in result]
        if missing:
            raise StudyOSError(
                "internal_error",
                "Service response does not satisfy MCP output contract",
                False,
                {"tool": name, "missing": missing},
            )
        return result

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            args = arguments or {}
            self._validate_arguments(name, args)
            return self._dispatch(name, args)
        except StudyOSError as exc:
            return exc.as_dict()
        except (TypeError, ValueError, KeyError) as exc:
            return StudyOSError("validation_error", str(exc), False).as_dict()
        except Exception as exc:
            return StudyOSError(
                "internal_error",
                "Unexpected Study OS service failure",
                False,
                {"exception": type(exc).__name__},
            ).as_dict()

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        request_id = message.get("id")
        method = message.get("method")
        params = message.get("params") or {}
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "study-os", "version": "0.1.0"},
            }
        elif method == "notifications/initialized":
            return None
        elif method == "tools/list":
            result = {"tools": self.list_tools()}
        elif method == "tools/call":
            if not isinstance(params, dict) or not isinstance(params.get("name"), str):
                error = validation("tools/call requires a tool name")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": error.as_dict()["error"],
                }
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            self.call_tool(
                                params["name"],
                                params.get("arguments") or {},
                            ),
                            sort_keys=True,
                        ),
                    }
                ]
            }
        else:
            error = validation("Unsupported MCP method", method=method)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": error.as_dict()["error"],
            }
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def run_stdio(
        self,
        input_stream: TextIO = sys.stdin,
        output_stream: TextIO = sys.stdout,
    ) -> None:
        for line in input_stream:
            if not line.strip():
                continue
            try:
                response = self.handle_message(json.loads(line))
                if response is not None:
                    output_stream.write(
                        json.dumps(response, separators=(",", ":")) + "\n"
                    )
                    output_stream.flush()
            except Exception as exc:
                error = StudyOSError(
                    "internal_error",
                    "Invalid MCP message",
                    False,
                    {"exception": type(exc).__name__},
                )
                output_stream.write(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": error.as_dict()["error"],
                        }
                    )
                    + "\n"
                )
                output_stream.flush()
