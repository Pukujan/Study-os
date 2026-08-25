# Application Contract Architecture — E11a-0

Status: architecture decision / pre-implementation contract. This document does not introduce HTTP, frontend, generated clients, or a new runtime authority.

## Decision

Study OS will introduce a transport-independent application boundary between semantic use cases and transport adapters.

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

E11a-0 is inventory-only. The machine-readable inventory is `contracts/application-operation-inventory.v0.1.json`; it records the migration target and is mechanically reconciled with the current MCP contract and runtime method surface.

Beginning with E11a-1, the single canonical authoring source for application DTOs/results/errors will be typed Python models in `study_os.application.contracts`, using Pydantic v2. JSON Schema will be generated from those models. OpenAPI and a framework-neutral TypeScript client are later projections from the canonical contract artifacts, not separately hand-authored equivalents.

Until those models exist, the inventory must not be mistaken for an implemented DTO library or used to claim HTTP/frontend readiness.

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
2. Requests reject unknown fields unless an explicit extension point declares otherwise. This keeps command semantics fail-closed.
3. Generated/compatible response decoders may ignore additive same-major fields when that behavior is part of the declared compatibility promise.
4. Removing a field, changing requiredness incompatibly, changing type incompatibly, or changing a field's semantic meaning requires an explicit breaking/major contract change.
5. A field name is never silently reused for a different meaning.
6. Deprecation requires a documented removal/version plan; ad-hoc deletion is not permitted.
7. Compatibility fixtures must cover every application-contract version still claimed as supported.
8. Generated artifacts must be reproducible and mechanically freshness-checked once generation exists.

## Serialization rules

Canonical application JSON projections will use UTF-8 JSON with deterministic field semantics.

- Timestamps cross the application boundary as RFC 3339 UTC timestamps using `Z`.
- Identifiers are opaque strings. Clients must not infer ordering, type, authorization, or learner semantics from identifier formatting.
- Non-finite numeric values are forbidden.
- Missing and explicit `null` are different states; optionality/nullability must be declared per field.
- When a canonical request fingerprint is needed for idempotency, semantic content is serialized deterministically using sorted keys and compact JSON after transport noise is removed.
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

E11a-1 will introduce a transport-independent error envelope with machine-readable category/code, safe public message/detail, and retryability metadata. HTTP status codes and MCP error formatting are adapter mappings, not semantic error authority.

Every durable application command corresponding to a mutating MCP tool remains idempotent by required idempotency key. Exact retry returns the same logical durable result; same key with materially different semantic content returns `conflict`; failed transactions must not create successful idempotency records.

## Operation inventory

`contracts/application-operation-inventory.v0.1.json` is the E11a-0 executable migration inventory. For each of the 13 current MCP tools it records:

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

E11a-0 requires a stdlib-only inventory validator and negative-control tests that fail when:

- any canonical MCP tool is missing, duplicated, or invented;
- command/query or idempotency classification drifts from the MCP contract;
- required request/result migration fields drift from the MCP contract;
- a mapped runtime method no longer exists;
- HTTP exposure is enabled early;
- semantic authority moves away from the application boundary;
- error categories drift from the existing durable error vocabulary.

Later E11a slices add DTO/schema serialization tests, generated-artifact freshness, compatibility fixtures, and direct-application-versus-MCP differential conformance before runtime behavior is moved.

## Non-goals for E11a-0

This slice does not add Pydantic, DTO implementation code, JSON Schema generation, OpenAPI, HTTP routes, authentication, TypeScript, React, Svelte, browser tests, deployment changes, persistence changes, schema migrations, semantic runtime changes, or adaptive live authority.
