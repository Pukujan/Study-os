# Local Database Contract — Study OS v0.1

This document specifies semantic database requirements for the local Study OS runtime. Luna may choose reasonable SQLite column names/ORM details, but the behaviors and relationships below are required unless changed explicitly in the repo contract.

## General rules

- SQLite initially; migration-friendly for later Postgres.
- `PRAGMA foreign_keys = ON` for every connection.
- UTC timestamps where timestamps are known.
- Stable externally visible text/UUID-style IDs.
- Raw evidence bytes live in the private evidence store; DB stores metadata/hash/path.
- High-frequency operational data never requires GitHub/FOSSIL.
- JSON payloads must include a payload/schema version when semantics can evolve.

## Required logical entities

### subjects

Required semantics:
- stable subject ID;
- created timestamp;
- active/inactive state optional;
- never store unnecessary identifying data for v0.1.

### projects

A reusable learning/research project boundary, e.g. `dsa-python`.

### domains

Domain within a project, e.g. `dsa`.

### concepts

Concept/pattern, e.g. `sliding-window`.

### sessions

Must reference subject + project + domain. Track start/end/status and source/client metadata when known.

### raw_artifacts

Must include:
- artifact ID;
- session ID;
- content SHA-256;
- local path/storage locator;
- media/content type when known;
- immutable capture timestamp;
- capture method/source metadata.

Changing bytes after capture must be detectable.

### learning_events

Must include:
- event ID;
- session ID;
- subject ID;
- evidence class: `observed | self_reported | derived`;
- event type;
- versioned payload;
- source/provenance IDs when applicable;
- idempotency key/request ID;
- created timestamp.

For `derived`, evidence/source references are mandatory.

### episodes

Derived grouping of events around a learning episode. Must not overwrite underlying events. Episode boundary confidence/review status may be versioned metadata.

### attempts

Represents a learner response/action to a task/probe. Preserve assistance/context separately from correctness.

### assessments

Must represent a capability dimension, result, assistance level, and evidence IDs. Do not encode a single universal mastery score as the only learner state.

### representations

Versioned representation definition/reference. At minimum family + semantic version/identifier.

### interventions

Must record:
- representation family/reference;
- operation (`predict`, `trace`, `restate`, etc.);
- target bottleneck/hypothesis;
- subject/session;
- version;
- creation time.

### representation_outcomes

Must reference a real intervention and evidence. Evidence score 0–5 is contextual, not universal.

Suggested uniqueness scope should prevent accidental duplicate outcome creation for the same idempotent request.

### checkpoints

Immutable derived learner-state snapshot.

Must include:
- checkpoint ID;
- subject ID;
- source session IDs;
- evidence IDs;
- capability state;
- assistance/fading state;
- current focus;
- do-not-reteach state;
- next action/probe;
- retention due metadata if any;
- checkpoint schema/derivation version;
- created timestamp.

Checkpoint creation and current-pointer advancement must occur atomically.

### subject_current_checkpoint

One current accepted pointer per subject. This may be represented as a table or subject field, but must:
- point to an existing checkpoint;
- update atomically with checkpoint acceptance;
- be detected as invalid by `doctor` if corrupted.

### retention_probes

Must reference subject + concept/source checkpoint, due time, status, and completion/result when available.

## Idempotency storage

Every durable mutating semantic operation must support retry safety.

Implementation options include:

- unique `(operation_name, idempotency_key)` table;
- unique idempotency key column scoped appropriately;
- dedicated request ledger.

Required behavior:

- first request commits response/result;
- exact retry returns/reconstructs same logical result without a duplicate write;
- reuse of an idempotency key with materially different request content returns `conflict`/integrity error;
- failed transaction must not reserve a success result incorrectly.

## Transaction boundaries

At minimum use transactions for:

- durable event + idempotency result;
- assessment/outcome creation;
- checkpoint creation + current pointer update;
- restore/import operations affecting multiple related records.

## Deletion policy

For R0 prefer append-only/soft lifecycle for evidence-bearing records. Do not hard-delete raw evidence or canonical learning events through the ChatGPT/MCP semantic surface.

Administrative local tooling may support explicit destructive reset for test/dev databases only.

## Index expectations

At minimum queries should remain efficient for:

- sessions by subject/time;
- events by session/order;
- evidence IDs;
- current checkpoint by subject;
- checkpoint history by subject/time;
- interventions/outcomes by subject/concept;
- due retention probes.

## Doctor/integrity checks

`doctor` must verify at minimum:

- expected migration/schema version;
- foreign keys enabled;
- foreign-key violations absent;
- current checkpoint pointer resolvable;
- checkpoint evidence/source IDs resolvable;
- raw artifact files available where required;
- raw hashes match bytes;
- contract/runtime version compatible.

## Migration contract

- migration 0001 creates all P0-required primitives or a clearly documented subset with subsequent ordered migrations;
- applying latest migrations to empty DB succeeds;
- rerunning migration command is safe;
- every schema change gets a migration;
- no manual ad-hoc production schema edits;
- migration compatibility is included in backup/restore testing.
