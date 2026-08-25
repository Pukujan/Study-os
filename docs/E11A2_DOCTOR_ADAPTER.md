# E11a-2a — Doctor application/MCP conformance

This slice migrates only the MCP `doctor` operation through the canonical application boundary.

## Why only doctor

Inspection before implementation found that the legacy `start_session` runtime method accepts optional `source_client` and `metadata` kwargs while the MCP v0.1 contract records only its required fields and the MCP input schema currently permits additional properties. The strict E11a-1 `StartStudySessionRequest` forbids undeclared fields. Routing `start_session` through that strict model without first making optional-field compatibility explicit would narrow existing accepted behavior.

Therefore this slice deliberately leaves `start_session` on the preserved legacy dispatch path and adds a regression test proving those optional arguments remain accepted.

## Doctor path

```text
MCP doctor
  -> ApplicationService.inspect_runtime_health
      -> preserved StudyOSService.doctor semantic runtime
      -> RuntimeHealthResult canonical contract
  -> explicit MCP v0.1 projection
```

The projection restores the legacy flattened health-check metadata so valid MCP `doctor` output remains semantically identical to direct runtime output. Application-contract version metadata does not leak into the MCP v0.1 result.

Malformed legacy runtime results fail closed as `internal_error`; adapter/schema mismatches must never produce successful-looking MCP responses.

## Architecture ratchet

Because `study_os.application` is now a real package, the engineering baseline includes it in top-level dependency-cycle detection and rejects application imports of MCP, concrete DB/evidence packages, or the legacy service package. MCP may depend inward on the application boundary.

## Non-goals

No MCP tool is added or removed. No database/schema, HTTP/frontend, deployment/private credential, Cloudflare/WSL/GPT Action, curriculum/adaptive behavior, or adaptive authority change is part of this slice.

The next `start_session` adapter slice must first resolve the optional-field compatibility contract explicitly, then prove direct-runtime/application/MCP idempotency and payload equivalence before production dispatch changes.
