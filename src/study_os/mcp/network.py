"""Secure loopback Streamable HTTP transport for Study OS.

This module is intentionally optional. The P0 runtime remains dependency-free and
usable over stdio; P1 installs ``mcp==2.0.0`` to expose the same semantic service
over a loopback-only HTTP endpoint suitable for OpenAI Secure MCP Tunnel.
"""

from __future__ import annotations

import hmac
import os
from contextlib import asynccontextmanager
from typing import Any

from mcp.server import MCPServer as SDKMCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

from ..services.runtime import StudyOSService
from .server import MCPServer as SemanticMCPServer


MCP_BEARER_TOKEN_ENV = "STUDY_OS_MCP_BEARER_TOKEN"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


class BearerAuthMiddleware:
    """Authenticate every HTTP request before MCP parsing or tool dispatch."""

    def __init__(self, app: Any, token: str):
        if not token or any(character.isspace() for character in token):
            raise ValueError("Study OS MCP bearer token must be non-empty and whitespace-free")
        self.app = app
        self.token = token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        authorization_values = [
            value.decode("latin-1")
            for name, value in scope.get("headers", [])
            if name.lower() == b"authorization"
        ]
        valid = False
        if len(authorization_values) == 1:
            scheme, separator, presented = authorization_values[0].partition(" ")
            valid = (
                separator == " "
                and scheme.lower() == "bearer"
                and bool(presented)
                and not any(character.isspace() for character in presented)
                and hmac.compare_digest(presented, self.token)
            )

        if not valid:
            response = JSONResponse(
                {
                    "error": {
                        "code": "authentication_required",
                        "detail": "Bearer authentication required",
                    }
                },
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def build_network_mcp_server(service: StudyOSService) -> SDKMCPServer:
    """Expose the frozen Study OS semantic surface through the MCP 2 server.

    Every network tool delegates to the existing P0 ``SemanticMCPServer`` so
    validation, idempotency, evidence provenance, checkpoint gating, and stable
    error payloads remain single-sourced in the already accepted runtime.

    The MCP handlers are deliberately ``async`` even though the underlying
    service calls are synchronous. MCP 2 runs synchronous tool handlers in a
    worker thread; Study OS intentionally owns a thread-affine SQLite connection.
    Async handlers therefore keep dispatch on the server event-loop/owner thread
    instead of weakening SQLite safety with cross-thread connection access.
    """

    semantic = SemanticMCPServer(service)
    server = SDKMCPServer(
        name="study-os",
        version="0.1.0",
        instructions=(
            "Study OS durable learner-state tools. In a fresh chat, call resume for "
            "an existing subject before teaching. Record behavioral evidence before "
            "claiming capability, and checkpoint only evidence-backed learner state."
        ),
    )

    @server.tool(name="doctor")
    async def doctor() -> dict[str, Any]:
        """Check Study OS database, evidence, checkpoint, and contract health."""

        return semantic.call_tool("doctor")

    @server.tool(name="status")
    async def status(subject_id: str) -> dict[str, Any]:
        """Read lightweight current learner/session/checkpoint status."""

        return semantic.call_tool("status", {"subject_id": subject_id})

    @server.tool(name="start_session")
    async def start_session(
        idempotency_key: str,
        subject_id: str,
        project_id: str,
        domain_id: str,
        source_client: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Start one durable learner session; retries must reuse the same key and payload."""

        arguments: dict[str, Any] = {
            "idempotency_key": idempotency_key,
            "subject_id": subject_id,
            "project_id": project_id,
            "domain_id": domain_id,
        }
        if source_client is not None:
            arguments["source_client"] = source_client
        if metadata is not None:
            arguments["metadata"] = metadata
        return semantic.call_tool("start_session", arguments)

    @server.tool(name="record_learning_event")
    async def record_learning_event(
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        evidence_class: str,
        event_type: str,
        payload: dict[str, Any],
        source_ids: list[str] | None = None,
        payload_version: str = "0.1.0",
    ) -> dict[str, Any]:
        """Record an observed, self-reported, or evidence-backed derived learning event."""

        arguments: dict[str, Any] = {
            "idempotency_key": idempotency_key,
            "session_id": session_id,
            "subject_id": subject_id,
            "evidence_class": evidence_class,
            "event_type": event_type,
            "payload": payload,
            "payload_version": payload_version,
        }
        if source_ids is not None:
            arguments["source_ids"] = source_ids
        return semantic.call_tool("record_learning_event", arguments)

    @server.tool(name="record_attempt")
    async def record_attempt(
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        task_id: str,
        response: Any,
        assistance_level: str = "none",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record a learner response and the actual assistance level used for that attempt."""

        arguments: dict[str, Any] = {
            "idempotency_key": idempotency_key,
            "session_id": session_id,
            "subject_id": subject_id,
            "task_id": task_id,
            "response": response,
            "assistance_level": assistance_level,
        }
        if context is not None:
            arguments["context"] = context
        return semantic.call_tool("record_attempt", arguments)

    @server.tool(name="record_assessment")
    async def record_assessment(
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        capability: str,
        result: str,
        assistance_level: str,
        evidence_ids: list[str],
    ) -> dict[str, Any]:
        """Record an assessment backed by same-subject behavioral evidence."""

        return semantic.call_tool(
            "record_assessment",
            {
                "idempotency_key": idempotency_key,
                "session_id": session_id,
                "subject_id": subject_id,
                "capability": capability,
                "result": result,
                "assistance_level": assistance_level,
                "evidence_ids": evidence_ids,
            },
        )

    @server.tool(name="record_representation_intervention")
    async def record_representation_intervention(
        idempotency_key: str,
        session_id: str,
        subject_id: str,
        representation_family: str,
        operation: str,
        representation_version: str,
        target_bottleneck: str,
    ) -> dict[str, Any]:
        """Record a deliberate representation change used to address a learner bottleneck."""

        return semantic.call_tool(
            "record_representation_intervention",
            {
                "idempotency_key": idempotency_key,
                "session_id": session_id,
                "subject_id": subject_id,
                "representation_family": representation_family,
                "operation": operation,
                "representation_version": representation_version,
                "target_bottleneck": target_bottleneck,
            },
        )

    @server.tool(name="record_representation_outcome")
    async def record_representation_outcome(
        idempotency_key: str,
        intervention_id: str,
        subject_id: str,
        evidence_score: int,
        evidence_ids: list[str],
    ) -> dict[str, Any]:
        """Record an intervention outcome only when same-subject assessment evidence exists."""

        return semantic.call_tool(
            "record_representation_outcome",
            {
                "idempotency_key": idempotency_key,
                "intervention_id": intervention_id,
                "subject_id": subject_id,
                "evidence_score": evidence_score,
                "evidence_ids": evidence_ids,
            },
        )

    @server.tool(name="checkpoint")
    async def checkpoint(
        idempotency_key: str,
        subject_id: str,
        source_session_ids: list[str],
        evidence_ids: list[str],
        capability_state: dict[str, Any],
        assistance_state: dict[str, Any],
        resume: dict[str, Any],
    ) -> dict[str, Any]:
        """Persist an evidence-backed learner checkpoint and next action atomically."""

        return semantic.call_tool(
            "checkpoint",
            {
                "idempotency_key": idempotency_key,
                "subject_id": subject_id,
                "source_session_ids": source_session_ids,
                "evidence_ids": evidence_ids,
                "capability_state": capability_state,
                "assistance_state": assistance_state,
                "resume": resume,
            },
        )

    @server.tool(name="resume")
    async def resume(subject_id: str) -> dict[str, Any]:
        """Recover the accepted checkpoint and next action for an existing learner."""

        return semantic.call_tool("resume", {"subject_id": subject_id})

    @server.tool(name="schedule_retention_probe")
    async def schedule_retention_probe(
        idempotency_key: str,
        subject_id: str,
        concept_id: str,
        due_at: str,
        source_checkpoint_id: str,
    ) -> dict[str, Any]:
        """Schedule a durable delayed-retention probe tied to a checkpoint."""

        return semantic.call_tool(
            "schedule_retention_probe",
            {
                "idempotency_key": idempotency_key,
                "subject_id": subject_id,
                "concept_id": concept_id,
                "due_at": due_at,
                "source_checkpoint_id": source_checkpoint_id,
            },
        )

    @server.tool(name="get_next_probe")
    async def get_next_probe(subject_id: str) -> dict[str, Any]:
        """Read the learner's next due retention probe, if any."""

        return semantic.call_tool("get_next_probe", {"subject_id": subject_id})

    @server.tool(name="export_fossil")
    async def export_fossil(
        idempotency_key: str,
        subject_id: str,
        artifact_type: str,
        source_ids: list[str],
    ) -> dict[str, Any]:
        """Create a local semantic FOSSIL export artifact; not required in the live learning path."""

        return semantic.call_tool(
            "export_fossil",
            {
                "idempotency_key": idempotency_key,
                "subject_id": subject_id,
                "artifact_type": artifact_type,
                "source_ids": source_ids,
            },
        )

    registered = tuple(tool.name for tool in server._tool_manager.list_tools())
    expected = tuple(semantic.list_tool_names())
    if registered != expected:
        raise RuntimeError(
            "network MCP tool surface drifted from the frozen Study OS contract: "
            f"registered={registered!r}, expected={expected!r}"
        )
    return server


def create_network_app(
    service: StudyOSService,
    *,
    bearer_token: str | None = None,
    host: str = "127.0.0.1",
    max_request_body_size: int = 1024 * 1024,
    transport_security: TransportSecuritySettings | None = None,
) -> Starlette:
    """Create the loopback-only authenticated Streamable HTTP MCP app."""

    if host not in LOOPBACK_HOSTS:
        raise ValueError("Study OS MCP HTTP transport must bind to a loopback host")
    if max_request_body_size < 1:
        raise ValueError("max_request_body_size must be positive")

    resolved_bearer_token = (
        bearer_token if bearer_token is not None else os.environ.get(MCP_BEARER_TOKEN_ENV)
    )
    if not resolved_bearer_token:
        raise ValueError(
            "Study OS MCP bearer token is required; set " f"{MCP_BEARER_TOKEN_ENV}"
        )

    mcp = build_network_mcp_server(service)
    mcp_app = mcp.streamable_http_app(
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        max_request_body_size=max_request_body_size,
        transport_security=transport_security,
        host=host,
    )

    @asynccontextmanager
    async def lifespan(app: Starlette):
        async with mcp.session_manager.run():
            yield

    app = Starlette(routes=[Mount("/", app=mcp_app)], lifespan=lifespan)
    app.add_middleware(BearerAuthMiddleware, token=resolved_bearer_token)
    app.state.study_os_service = service
    app.state.mcp_server = mcp
    return app


__all__ = [
    "BearerAuthMiddleware",
    "MCP_BEARER_TOKEN_ENV",
    "build_network_mcp_server",
    "create_network_app",
]
