# P3.0 Durable Evidence Capture — Test-Driven Development Document

Status: accepted implementation specification once merged

Parent tracker: #52 — P3 Operational learning, durable evidence, and structured curriculum

Companion documents:

- `docs/P3_DURABLE_EVIDENCE_CAPTURE_PDD.md`
- `docs/P3_DURABLE_EVIDENCE_CAPTURE_SDD.md`

Primary implementer: local Luna / WSL coding agent

Date: 2026-09-03

## 1. Purpose

This document tells the local implementation agent how to repair the real GPT -> Study OS -> local persistence failure path using tests that protect the durable evidence architecture.

The objective is not to maximize test count or harden unrelated code. The objective is to make the following invariant executable:

> No silent learner-evidence loss.

A learner interaction must be either:

1. durably committed and safely retryable; or
2. explicitly known to be missing/uncertain and recoverable through reconciliation/backfill.

Implementation code is replaceable. The tests should protect persistent evidence identity, provenance, idempotency, acknowledgement semantics, restart durability, and reconciliation behavior.

## 2. Required workflow for Luna

Use this order.

```text
OBSERVE REAL FAILURE
    ↓
LOCALIZE 502 BOUNDARY
    ↓
ADD/SELECT FAILING TEST FOR THAT FAILURE CLASS
    ↓
MAKE SMALLEST IMPLEMENTATION CHANGE
    ↓
RUN FOCUSED TESTS
    ↓
RUN EXISTING RUNTIME/CONTRACT REGRESSION
    ↓
VERIFY ON DISPOSABLE LOCAL RUNTIME
    ↓
VERIFY REAL GPT PATH
```

Do not begin with a broad refactor.

Do not introduce a schema migration unless the PDD/SDD semantics genuinely cannot be represented with the current schema.

Do not change MCP/public semantics merely to make a local implementation easier.

## 3. Existing tests that already protect useful invariants

The repository already contains valuable coverage in `tests/test_local_runtime.py` and related application/MCP tests.

Luna must preserve and reuse these rather than duplicate them superficially.

Existing behavior includes tests for:

- empty database migration and repeat-safe migration;
- exact idempotent learning-event retry;
- conflicting idempotency-key reuse rejection;
- derived claims requiring resolvable evidence;
- evidence hash mutation detected by `doctor`;
- checkpoint/current-pointer durability;
- checkpoint stale-pointer conflict;
- durable semantic operation results;
- backup/restore of checkpoint + evidence;
- exact MCP tool contract / no generic SQL-shell tools;
- stable validation errors;
- stale schema/missing evidence-root health failure;
- checkpoint transaction rollback on interruption;
- invalid partial backup rejection;
- SQLite busy/locked returned as retryable unavailable.

These remain regression requirements.

## 4. First deliverable: failure-localization evidence

Before writing production code, Luna must determine which boundary produces the current 502.

Use sanitized correlation data only; do not put private learner content in logs or public fixtures.

For one reproducible failed GPT write, establish as many of these facts as possible:

```text
A. Did request reach tunnel/edge?
B. Did MCP/transport process receive it?
C. Did Study OS semantic/application handler receive it?
D. Did idempotency lookup occur?
E. Did a SQLite transaction begin?
F. Did required evidence/semantic record commit?
G. Was a success result constructed?
H. Did result serialization/transport fail after commit?
```

Record the observed classification in the implementation PR:

- `pre_local_receipt`
- `transport_or_handler_before_commit`
- `persistence_before_commit`
- `post_commit_response_failure`
- `multiple_or_unresolved`

If the failure cannot be reproduced, do not invent a root cause. Implement only generic requirements justified by a testable failure model and document the unresolved boundary.

## 5. Test layers

Use the cheapest test that can prove each invariant.

### Layer A — service/runtime tests

Primary home when possible:

`tests/test_local_runtime.py`

or a focused new file such as:

`tests/test_p3_durable_evidence_capture.py`

These tests own durability, transactions, idempotency, reconciliation, and restart behavior.

### Layer B — application contract/conformance tests

Use existing `tests/test_application_*_conformance.py` suites when application request/result/error behavior changes.

Do not add transport-specific semantics to the application model merely for testing convenience.

### Layer C — MCP adapter tests

Use existing MCP conformance tests when the actual failure is at MCP mapping/serialization/exception handling.

The MCP adapter must remain a transport projection of application/runtime semantics.

### Layer D — disposable end-to-end local path

Add the smallest local test/harness that exercises the actual process boundary involved in the 502 if unit/integration tests cannot reproduce it.

This may include the local MCP server/tunnel-facing process, but must use disposable/synthetic learner data.

### Layer E — real GPT verification

Only after lower layers pass, exercise one real Study OS learning write through the GPT integration.

Do not use the user's valuable session as the first failure-injection environment.

## 6. Required P3.0 tests

The following are the canonical acceptance tests. Exact names may differ, but the semantics must be present.

### T1 — exact retry remains one durable record

**Given** one retryable durable operation with idempotency key `K` and payload fingerprint `F`.

**When** the same logical operation is executed twice.

**Then**:

- exactly one underlying durable evidence/semantic record exists;
- both calls resolve to the same durable identity;
- the second call is identifiable as an idempotent replay where the API exposes this distinction.

Existing event-retry coverage may satisfy part of this; extend it to the operation(s) involved in the real 502.

### T2 — idempotency conflict fails closed

**Given** a committed operation for key `K` / fingerprint `F1`.

**When** `K` is reused with materially different payload `F2`.

**Then**:

- explicit `conflict` or the canonical equivalent is returned;
- original durable record remains unchanged;
- no second learner-evidence record is created.

Existing runtime coverage is regression authority.

### T3 — commit then response loss

This is the most important new unknown-result test.

**Given** a durable operation.

**When** failure is injected *after* the DB/durability commit but *before* the caller receives the success result.

**Then**:

- the first caller may observe timeout/transport failure/unknown result;
- the durable record exists exactly once;
- retry with the same idempotency identity/fingerprint returns/resolves the original committed result;
- no duplicate evidence is created.

The failure injection point must be genuinely post-commit. Do not simulate this by raising before the transaction commits.

### T4 — crash/failure before commit

**When** failure occurs after request receipt but before the required transaction commits.

**Then**:

- no successful durable receipt exists;
- partial records governed by the transaction are absent/rolled back;
- a clean exact retry can commit once.

Existing checkpoint rollback coverage is useful but does not automatically prove every write path involved in the 502.

### T5 — committed evidence survives process restart

**Given** a confirmed committed learner-evidence operation.

**When** the Study OS process/service is closed and recreated from the same runtime root.

**Then**:

- the evidence is queryable/referencable;
- idempotent retry still resolves correctly;
- any durable receipt/capture state required by the P3 contract survives.

### T6 — source/raw capture survives semantic processing failure

If the implementation introduces/uses a source-turn capture stage:

**Given** a captured learner-facing source turn.

**When** normalization/classification/derived processing is forced to fail.

**Then**:

- source evidence remains durable;
- processing status is failed/pending rather than pretending the turn never existed;
- the same source evidence can be reprocessed later;
- derived records are not fabricated.

This test must prove the PDD hierarchy:

```text
raw/source evidence
    survives independently of
normalized/derived processing
```

### T7 — pre-local-receipt transcript backfill

**Given** a reviewed synthetic transcript containing a turn that does not exist locally.

**When** reconciliation is run.

**Then**:

- exactly one backfilled source record is added;
- provenance records that capture origin is reconciliation/backfill;
- original/source chronology is preserved only where supported;
- local recovery/commit time is not falsified as original live receipt time.

### T8 — reconciliation rerun is idempotent

Run T7's same transcript/source again.

Expected:

- no duplicate source turn;
- outcome identifies already-present/exact match or equivalent.

### T9 — ambiguous reconciliation refuses to guess

**Given** two plausible local candidates with insufficient identity to choose safely.

**When** reconciliation is attempted.

**Then**:

- automatic merge does not occur;
- state becomes explicit review/ambiguity;
- both existing provenance histories remain intact.

Text similarity alone must never silently decide learner-history identity.

### T10 — `doctor` exposes unresolved evidence states

Create fixture state containing one or more of:

- unresolved unknown-result operation;
- reconciliation-required missing turn;
- ambiguous reconciliation item;
- referenced raw artifact/hash failure.

Expected:

- `doctor` reports the actionable condition;
- `doctor` does not silently mutate history to repair it.

`healthy` semantics may distinguish fatal integrity failure from attention-required state if the SDD implementation chooses that model, but the distinction must be explicit and tested.

### T11 — backup/restore preserves P3 evidence semantics

Extend existing backup/restore verification so the restored system preserves, where implemented:

- source/capture identities;
- content hashes/artifact references;
- idempotency identities/fingerprints;
- reconciliation provenance;
- unknown/reconciled status;
- semantic/derived evidence references.

After restore:

- `doctor` passes or reports the same known attention states as before backup;
- exact retry behavior remains coherent.

### T12 — database/storage failure never false-acks

Use realistic disposable failure cases for the touched path, such as:

- SQLite busy/locked;
- unwritable evidence directory;
- forced storage exception before commit.

Expected:

- stable failure category;
- no durable-success acknowledgement;
- no silent evidence disappearance.

Existing DB-busy tests remain part of this acceptance evidence.

### T13 — no regression of checkpoint/evidence provenance

Run existing tests proving:

- derived state requires evidence;
- checkpoint/current pointer integrity;
- evidence hash integrity;
- representation/assessment provenance;
- resume continuity.

P3.0 must not trade existing semantic integrity for transport reliability.

### T14 — no public/private boundary regression

If new logging, capture metadata, reconciliation fixtures, or diagnostics are added:

- test/public fixtures contain synthetic/redacted content only;
- raw private transcript text is not written to repository logs/fixtures;
- secrets/tunnel credentials are absent;
- logs prefer stable IDs/hashes/categories over content.

## 7. Failure-injection hooks

Prefer small explicit test seams over broad monkey-patching of unrelated internals.

Useful seams may include callbacks/fault points conceptually equivalent to:

```text
before_transaction
before_commit
after_commit_before_result
after_source_capture_before_semantic_processing
before_reconciliation_append
```

These do not need to become public production APIs.

If an existing transaction/service boundary already provides a clean injection point, reuse it.

The test must state exactly which side of the durability boundary the failure occurs on.

## 8. Reconciliation test fixture

Use a synthetic private-safe fixture, for example:

```text
conversation: synthetic-p3-reconciliation

turn-001 user:
"What does box[7] return?"

turn-002 assistant:
"1"

turn-003 user:
"I still don't understand the variable name."
```

Fixture requirements:

- stable source conversation/message IDs when testing strong identity;
- a variant without source IDs for hash/chronology matching;
- a deliberately ambiguous variant;
- no real private learner transcript.

Do not encode a real learner's raw conversation into public test fixtures.

## 9. Diagnostic acceptance receipt

The implementation PR must include a concise diagnostic table:

| Boundary | Observed? | Evidence |
|---|---|---|
| request reached local transport | yes/no/unknown | sanitized log/test ref |
| application handler entered | yes/no/unknown | ref |
| transaction began | yes/no/unknown | ref |
| commit occurred | yes/no/unknown | ref |
| caller received result | yes/no/unknown | ref |

And classify the reproduced failure.

Do not include secrets or private learner content.

## 10. Implementation acceptance matrix

Before Luna asks for merge, all applicable rows must be green.

| Requirement | Required evidence |
|---|---|
| no false durable ACK | T3/T4/T12 |
| exact retry safety | T1/T3 |
| conflict rejection | T2 |
| restart durability | T5 |
| raw/source survives semantic failure | T6 |
| pre-receipt recovery | T7 |
| reconciliation idempotency | T8 |
| ambiguity fail-closed | T9 |
| operational diagnostics | T10 |
| backup/restore | T11 |
| existing semantic integrity | T13 |
| privacy boundary | T14 |

A requirement may be marked not applicable only with a written architectural reason consistent with the PDD/SDD.

## 11. Commands / execution expectations

Use the repository's actual environment/tooling. At minimum run the focused test file(s), then the existing repository validation/regression suite used by the project.

Expected focused pattern:

```bash
python -m unittest tests.test_p3_durable_evidence_capture -v
python -m unittest tests.test_local_runtime -v
```

If Luna extends existing files rather than creating `test_p3_durable_evidence_capture.py`, adjust the focused command accordingly.

Then run the repository's canonical validation/tests from the current checkout. Do not invent a new mandatory toolchain merely for this repair.

Record exact commands and pass/fail counts in the PR.

## 12. Schema/migration test requirements

If no persistent schema change is required, explicitly say so in the PR.

If a migration is required, add tests for:

1. migration from the current real schema version;
2. repeat-safe migration invocation;
3. preservation of existing learner records;
4. new uniqueness/foreign-key constraints;
5. failed migration not partially claiming success;
6. backup before applying migration to valuable local learner data;
7. restore/read compatibility after migration.

Do not repurpose an old column with new semantics silently.

## 13. Rollout verification

After tests pass on disposable data:

### R1 — local disposable runtime

- start service;
- perform durable write;
- retry;
- restart;
- query/resume;
- run `doctor`.

### R2 — local transport/MCP path

Exercise the same operation through the actual adapter/process used by GPT.

### R3 — controlled unknown-result test

Where safely possible, reproduce post-commit response loss against disposable data and prove retry recovery.

### R4 — real GPT smoke

Use the actual GPT app for one small non-sensitive Study OS write.

Verify local durable evidence directly after the call.

### R5 — normal learning resumes

Only after the path is green should the learner rely on it again as routine canonical capture.

Known unreconciled historical 502 sessions remain explicitly incomplete until backfilled/reconciled.

## 14. Stop conditions

Luna should stop and report rather than improvise if:

- fixing the 502 appears to require changing the public 13-tool MCP contract;
- a destructive migration of valuable learner data is required without a tested backup;
- the local code does not match current `main` architecture/contracts;
- a secret/tunnel/config change would need to be committed publicly;
- reconciliation cannot identify a record safely;
- a proposed change would make derived state authoritative over raw evidence;
- the failure is actually outside the local Study OS boundary and cannot be corrected locally.

In those cases, preserve diagnostics and propose the smallest architecture/contract decision needed.

## 15. Definition of done

P3.0 local repair is ready for review when:

1. the real 502 boundary is reproduced/localized or explicitly remains unresolved with evidence;
2. all applicable T1–T14 tests are green;
3. no acknowledged durable write is lost in the test suite;
4. exact retry cannot duplicate the affected learner evidence;
5. post-commit unknown result can be resolved safely;
6. pre-receipt missing evidence has one tested reconciliation/backfill path;
7. restart and backup/restore preserve the new durability semantics;
8. existing learner/checkpoint/provenance tests remain green;
9. real GPT smoke succeeds against the local runtime;
10. the PR records exact tested SHA, commands, results, migration status, known limitations, and any unreconciled historical gaps.

The desired outcome is not "the 502 disappeared once." It is:

> The system can prove what was committed, safely recover from uncertain results, and identify what still needs reconciliation.
