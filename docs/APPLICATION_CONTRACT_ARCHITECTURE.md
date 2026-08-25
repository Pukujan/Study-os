# Application Contract Architecture — E11a

Status: E11a-0 architecture/inventory is canonical; E11a-1 implements a representative contract core only. HTTP, frontend, generated clients, MCP migration, and new runtime authority remain deferred.

## Decision

Study OS uses a transport-independent application boundary between semantic use cases and transport adapters.

```text
domain/state
    -> application use cases
        -> canonical application contracts
            -> MCP adapter
            -> HTTP adapter (later)
            -> CLI adapter where useful
                 -> generated framework-neutral client (later)
                      -> one frontend framework (later)
```

The application contract is the semantic integration boundary. MCP tool schemas, future HTTP/OpenAPI routes, generated TypeScript, React state, and Svelte stores are projections or consumers; none is allowed to become the source of learner-state semantics.

The existing public MCP surface remains exactly 13 semantic tools until a separate reviewed contract/version change explicitly changes it.

## Canonical source of truth

The single canonical authoring source for implemented application DTOs/results/errors is typed Python in `src/study_os/application/contracts.py`, using Pydantic v2. The E11a-0 migration inventory remains `contracts/application-operation-inventory.v0.1.json` and is mechanically reconciled with the current MCP contract and runtime method surface.

E11a-1 intentionally implements only this representative subset:

- shared application contract version metadata;
- stable application error category/code/message/retryability/public-detail envelope;
- `inspect_runtime_health` request/result models corresponding to current MCP `doctor`;
- `start_study_session` request/result models corresponding to current MCP `start_session`.

JSON Schema is generated deterministically on demand from the canonical Python models and is checked in CI on Python 3.11 and 3.12. No equivalent hand-authored JSON Schema is committed as a competing source of truth. OpenAPI and a framework-neutral TypeScript client remain later projections.

The existence of representative models does not claim MCP conformance migration, HTTP readiness, or frontend readiness. MCP continues using the existing runtime path until a later bounded E11a adapter slice proves semantic equivalence.

## Authority boundaries

Domain/application code owns evidence admissibility, provenance, attempts and assessments, checkpoint advancement, capability state, prerequisite eligibility, assistance constraints, retention state, representation validity, and adaptive promotion/authority.

Transport and frontend code may validate transport shape and improve UX, but it may not decide whether a semantic learner-state transition is valid. A directly crafted request must be accepted or rejected by the same backend semantic rules as an equivalent UI or MCP request.

Persistence internals are adapters. Future transport/frontend packages must not import SQLite repositories, migrations, adaptive implementations, or curriculum implementations to perform semantic decisions.

## Version namespaces

Application contract versioning is independent from all other version axes:

- application contract version — request/result/error boundary consumed by adapters;
- MCP contract version — public MCP tool surface and transport shape;
- runtime package version — distributable implementation version;
- database schema/migration version — persisted operational state layout;
- curriculum version — authored learning-content graph/version;
- adaptive-policy/model version — shadow/advisory algorithm identity;
- evidence/schema versions — persisted evidence and public-safe data artifacts.

A change in one namespace does not silently imply a change in another. Any compatibility coupling must be explicit and tested.

## Compatibility and deprecation policy

Before a stable 1.x application contract is claimed:

1. Additive response fields are the default compatible same-major evolution.
2. Requests reject unknown fields unless an explicit extension point declares otherwise. Current representative Pydantic models enforce `extra="forbid"`.
3. Generated/compatible response decoders may ignore additive same-major fields only when that behavior is part of the declared compatibility promise.
4. Removing a field, changing requiredness incompatibly, changing type incompatibly, or changing a field's semantic meaning requires an explicit breaking/major contract change.
5. A field name is never silently reused for a different meaning.
6. Deprecation requires a documented removal/version plan; ad-hoc deletion is not permitted.
7. Compatibility fixtures must cover every application-contract version still claimed as supported once more than one supported version exists.
8. Generated artifacts must be reproducible and mechanically freshness-checked.

## Serialization rules

Canonical application JSON projections use UTF-8 JSON with deterministic field semantics.

- Timestamps cross the application boundary as RFC 3339 UTC timestamps using `Z`; the representative session result requires an aware UTC value and emits fixed microsecond precision.
- Identifiers are opaque non-empty strings. Clients must not infer ordering, type, authorization, or learner semantics from identifier formatting.
- Non-finite numeric values are forbidden in public contract JSON.
- Missing and explicit `null` are different states; optionality/nullability is declared per field.
- Canonical model JSON uses sorted keys and compact separators. This is compatible with later semantic request fingerprinting but does not replace the existing runtime idempotency implementation in E11a-1.
- Serialization must never add private transcript bodies, secrets, credentials, hidden holdout answers, or backend-only authority flags to public/client DTOs.

## Errors and retries

The application boundary reuses the existing stable error categories:

- `validation_error`
- `not_found`
- `conflict`
- `integrity_error`
- `unsupported_version`
- `unavailable`
- `internal_error`

E11a-1 implements a transport-independent error envelope with machine-readable category and lowercase code, safe public message/detail, and retryability metadata. Nested public detail rejects known private/secret field classes and non-finite numbers. HTTP status codes and MCP error formatting remain adapter mappings, not semantic error authority.

Every durable application command corresponding to a mutating MCP tool remains idempotent by required idempotency key. Exact retry returns the same logical durable result; same key with materially different semantic content returns `conflict`; failed transactions must not create successful idempotency records. E11a-1 models this request metadata but does not replace the proven runtime implementation.

## Operation inventory

`contracts/application-operation-inventory.v0.1.json` is the executable migration inventory. For each of the 13 current MCP tools it records:

- current runtime service method;
- target application operation;
- command/query classification;
- idempotency expectation;
- required transport-independent request/result fields inherited from the current public contract for migration accounting;
- persistence effect;
- evidence/provenance requirement;
- externally observable state transition;
- error-envelope policy;
- deferred HTTP exposure.

The inventory does not require one permanent application use case per MCP tool. Later E11a slices may consolidate internal application composition where semantics remain equivalent, but all 13 MCP mappings must stay explicit and mechanically conformant.

## Privacy and configuration boundary

Application contracts expose the minimum identifiers, state projections, and provenance references required by a client. They do not expose raw private evidence by default.

Local-only Cloudflare, WSL, GPT Action, tunnel, token, cookie, deployment, and credential configuration is outside E11a repository work. No generated schema/client/example may contain those values. Future remote HTTP exposure requires a separate authenticated transport/security decision and tests before use.

## Adaptive authority

E11a is an architecture seam only. It does not promote any adaptive component. Current adaptive components remain shadow-only until the Issue #21 verification and Issue #10 promotion gates explicitly permit later authority.

## Verification ratchet

E11a-0 retains its stdlib-only inventory validator and negative controls. E11a-1 adds contract tests and deterministic generation checks that fail when:

- error categories drift from the durable runtime/MCP vocabulary;
- unsupported application versions or extra request fields are accepted;
- strict request field types are silently coerced;
- representative request/result migration fields drift from the operation inventory;
- timestamps are naive or non-UTC;
- public error/health detail contains known private fields or non-finite values;
- generated JSON Schema is invalid or rendering is nondeterministic;
- representative serialized instances fail their generated schemas.

E11a-2 must prove direct application-versus-MCP differential conformance for a bounded representative adapter migration before any broader runtime behavior is moved.

## Current non-goals

The E11a-1 representative core does not add HTTP routes, authentication, TypeScript, React, Svelte, browser tests, deployment changes, persistence changes, schema migrations, semantic runtime changes, MCP tool-count changes, or adaptive live authority. It also does not yet route MCP calls through the canonical models.
