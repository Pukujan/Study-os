# E11a-0 Verification Scope

This note records the bounded acceptance surface for Issue #26 E11a-0.

The slice is complete only when the exact PR head demonstrates all of the following:

- the application operation inventory maps exactly the existing 13 MCP semantic tools;
- request/result migration fields, command/query classification, and idempotency match the canonical MCP contract;
- every mapped current service method exists in the runtime source;
- canonical application-contract source-of-truth, versioning, compatibility, serialization, error, privacy, and authority decisions are documented;
- HTTP and frontend implementation remain deferred;
- transport/frontend semantic authority remains false;
- repository validation, dependency-lock verification, architecture boundaries, Ruff, Pyright, wheel build/install smoke, Python 3.11 compatibility, full tests, and branch coverage remain green;
- no local deployment, Cloudflare/WSL/GPT Action configuration, credentials, database schema, runtime semantics, MCP tool count, or adaptive authority changes occur.

E11a-1 may begin only from the merged canonical E11a-0 baseline. It should introduce a very small representative transport-independent DTO/result/error subset and protect behavior with the existing stateful/reference-model verification before any MCP migration is attempted.
