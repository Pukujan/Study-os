# P3.0 Durable Evidence Capture — System Design Document

Status: proposed

Parent tracker: #52 — P3 Operational learning, durable evidence, and structured curriculum

Companion product document: `docs/P3_DURABLE_EVIDENCE_CAPTURE_PDD.md`

Date: 2026-09-03

## 1. Design objective

Design the GPT -> Study OS -> local persistence path so real learning evidence is either durably committed or explicitly recoverable, without making the learner manually administer routine writes.

Primary invariant:

> No silent learner-evidence loss.

Secondary invariant:

> Raw/source evidence must survive independently of later normalization, learner-model derivation, or system grading.

## 2. Existing architecture to preserve

Accepted local-first architecture remains:

```text
GPT learner-facing application
        ↓
secure/private Study OS transport
        ↓
Study OS semantic/runtime boundary
        ↓
local SQLite + private evidence store
```

GitHub remains source/spec/research/curated-data infrastructure, not the live learner database.

FOSSIL remains optional/downstream and must not be required for live capture, resume, or recovery.

The current implementation may be replaced or refactored. Persistent evidence identities, provenance, idempotency semantics, migration rules, and recovery behavior are the durable system contracts.

## 3. Required separation of concerns

The durability design must separate four concerns that are easy to collapse accidentally.

### 3.1 Source-turn capture

Stores what was actually observed from the learner-facing interaction when available.

Examples:

- learner/user message;
- assistant message/response;
- relevant Study OS/tool result;
- imported transcript turn used for reconciliation.

### 3.2 Semantic operation processing

Turns source evidence into operational records such as:

- attempts;
- assessments;
- interventions;
- representation exposures;
- assistance exposures;
- task decomposition/recomposition;
- learner feedback;
- transfer/retention results.

### 3.3 Derived state

Produces replaceable interpretations such as:

- failure hypotheses;
- learner capability state;
- intervention effectiveness;
- system grading;
- next-action proposals.

### 3.4 Durability/reconciliation control

Tracks whether evidence is confirmed local, caller-unknown, missing, backfilled, duplicated, or ambiguous.

No layer may silently promote uncertainty from a lower layer into certainty at a higher layer.

## 4. Logical architecture

The target logical flow is:

```text
                 REMOTE / GPT SIDE

 learner turn / assistant turn / semantic command
                         │
                         ▼
                transport request
              correlation + idempotency
                         │
                         ▼
──────────────── LOCAL DURABILITY BOUNDARY ────────────────
                         │
                         ▼
                 ingress validation
                         │
                         ▼
              durable source/capture record
                         │
              ┌──────────┴───────────┐
              │                      │
              ▼                      ▼
       semantic processing      capture receipt
              │                      │
              ▼                      ▼
       operational records      caller response
              │
              ▼
         derived state

──────────────── RECONCILIATION PATH ──────────────────────
 conversation/transcript source
              │
              ▼
       reviewed normalization
              │
              ▼
    identity/hash/order matching
              │
       ┌──────┴────────┐
       ▼               ▼
 exact match       missing record
 deduplicate       append backfill
                       │
                       ▼
              semantic reprocessing
```

This is a logical architecture. It does not require a specific class/package split.

## 5. Durability boundary

The system must define one explicit point at which a write is considered durably accepted.

A successful acknowledgement means:

- the required local durable record has committed;
- the operation has a stable identity;
- exact retry can resolve to that identity/result;
- restart will not erase the committed record.

A response generated before that boundary must never be described as a durable success.

## 6. Two-stage evidence model

Because Study OS wants to preserve every learner-facing interaction when feasible, semantic validation must not be allowed to destroy source evidence.

### Stage A — source capture

Capture the smallest trustworthy source envelope first.

Candidate durable fields:

```text
capture_id
subject_id
session_id
source_system
source_conversation_ref? 
source_message_ref?
source_parent_ref?
role
content_or_private_artifact_ref
content_hash
source_timestamp?
local_received_at
correlation_id
idempotency_key?
capture_origin = live | reconciliation
provenance_ref?
```

Exact field names/versioning are implementation decisions, but the semantics above must be representable.

Raw/private content may live in the private evidence store with SQLite holding a stable reference/hash if that is the accepted privacy/storage pattern.

### Stage B — semantic processing

Semantic records reference `capture_id` or equivalent evidence identity.

Candidate processing state:

```text
not_required
pending
processed
failed_retryable
failed_review
superseded_by_version
```

A Stage B failure does not mutate/delete Stage A evidence.

## 7. Capture state model

Server/local durability state and caller knowledge must not be conflated.

### 7.1 Local record state

A source record is either:

```text
committed
rejected_before_commit
```

Do not persist fake intermediate states that imply durability unless they themselves are durably stored and meaningful.

### 7.2 Caller/reconciliation state

The surrounding operation may be classified as:

```text
confirmed_committed
confirmed_not_committed
unknown_to_caller
reconciliation_required
reconciled_existing
reconciled_backfill
ambiguous_review_required
```

The exact persisted representation may be a receipt/reconciliation table or equivalent append-only events.

## 8. Identity and idempotency

### 8.1 Durable command identity

Every retryable durable operation must have an identity that allows Study OS to distinguish:

- exact retry of the same logical request;
- a new request with coincidentally similar content;
- conflicting reuse of an existing idempotency identity.

### 8.2 Payload fingerprint

Where idempotency is used, store or deterministically derive a request/payload fingerprint.

Rules:

```text
same idempotency identity + same fingerprint
    -> return original durable result

same idempotency identity + different fingerprint
    -> explicit conflict
```

### 8.3 Source message identities

If the GPT/source platform exposes stable conversation/message identifiers, preserve them as provenance, not as the sole local primary key.

If source IDs are unavailable, local identities and hashes/order metadata remain authoritative locally.

## 9. Write protocol

For a live durable operation:

```text
1. receive request
2. assign/validate correlation + idempotency identity
3. perform minimal envelope validation
4. enter local transaction/durability boundary
5. detect exact retry/conflict
6. durably persist source evidence required for this operation
7. persist semantic operation records atomically when they are part of the same declared invariant
8. commit
9. only after commit, construct success receipt
10. return result
```

Important: not every semantic derivation must be in the Stage A capture transaction. Expensive/model-derived interpretation should remain separately retryable when possible.

## 10. Transaction boundaries

The system must document which records require atomicity together.

Examples likely requiring atomicity:

- durable request identity + its committed source record;
- checkpoint + current pointer, where existing architecture already requires it;
- any receipt that claims a specific semantic write was committed + that semantic write.

Examples that should generally remain independently recoverable:

- raw/source evidence and later model-derived failure classification;
- raw/source evidence and later system grading;
- raw/source evidence and later representation-effectiveness estimate.

Do not widen transactions merely for implementation convenience if doing so makes raw capture depend on optional derived processing.

## 11. Failure semantics

### 11.1 Failure before local service receipt

The local runtime cannot prove the message existed.

Recovery:

- later conversation/transcript reconciliation;
- preserve imported-source provenance;
- no invented timestamp/message identity beyond what source evidence supports.

### 11.2 Failure after receipt but before commit

No durable-success response.

Retry is safe because no committed idempotency record exists, or because any durably persisted receipt correctly reflects incomplete/rejected semantics.

### 11.3 Failure after commit but before caller receives response

This is the key unknown-result case.

On retry:

- same idempotency identity/fingerprint resolves to original committed result;
- no duplicate source/semantic record is created.

### 11.4 Semantic-processing failure

Raw/source record remains.

Processing failure records enough diagnostic information to retry/review without embedding secrets/private learner content into public logs.

### 11.5 SQLite busy/locked

Use bounded, explicit retry according to the runtime's single-user concurrency model.

If the operation cannot commit, return a stable failure category. Never acknowledge success on an uncommitted write.

### 11.6 Disk full / permission / evidence-store write failure

Fail closed at the durability boundary if the operation requires that storage.

`doctor` must surface the unhealthy storage state.

### 11.7 Integrity/hash mismatch

Do not silently repair source evidence in place.

Quarantine/surface the mismatch and preserve enough metadata to diagnose which artifact is inconsistent.

## 12. Reconciliation design

Reconciliation exists because failures can occur before local receipt and because caller-visible 502/timeout can leave uncertain commit state.

### 12.1 Reconciliation inputs

Allowed reviewed inputs may include:

- exported conversation transcript;
- user-supplied lossless Markdown transcript;
- platform export with message IDs;
- existing private evidence capture;
- FOSSIL reconstruction/reference when deliberately selected as evidence source.

No one source is globally required.

### 12.2 Matching order

Prefer strongest available identity:

```text
1. exact source conversation + message ID
2. exact known local/source correlation identity
3. content hash + role + adjacent stable source identities
4. content hash + chronology/source metadata
5. manual review when ambiguity remains
```

Never automatically merge two plausible records merely because their text is similar.

### 12.3 Reconciliation outcomes

For each imported source turn:

```text
already_present_exact
backfilled_missing
linked_to_unknown_committed_operation
ambiguous_review_required
rejected_invalid_source
```

### 12.4 Append-only correction

A backfill adds evidence with reconciliation provenance.

It does not rewrite the historical local record to pretend live capture succeeded.

The history should remain capable of answering:

> Was this captured live, or recovered later?

### 12.5 Idempotent reconciliation

Reprocessing the same transcript/source must not create duplicate evidence.

## 13. Ordering and chronology

Canonical local receipt time and source-reported time are different facts.

Store them separately when source time exists.

For live capture:

- local receipt/commit ordering is authoritative for local durability;
- source chronology may help reconstruct learner interaction order.

For reconciliation:

- source ordering/provenance may place a backfilled turn into the interaction chronology;
- the backfill's local commit time remains the actual time Study OS recovered it.

Never rewrite recovery time into fake original local receipt time.

## 14. Diagnostics and `doctor`

`doctor` should become capable of checking the evidence-capture invariants that matter operationally.

Candidate checks:

### Storage

- DB opens and required migrations are compatible;
- foreign keys/integrity checks pass;
- private evidence root is readable/writable according to configured mode;
- referenced raw artifacts exist and hash correctly where required.

### Durability/idempotency

- no conflicting durable request fingerprints under one idempotency identity;
- no duplicate source identity where uniqueness is declared;
- committed receipts reference existing durable records.

### Evidence lineage

- semantic records reference existing evidence/capture records where required;
- derived learner/system records do not point to missing evidence;
- reconciliation records point to valid source/backfill evidence.

### Operational attention

- count/list caller-unknown/reconciliation-required items;
- count ambiguous reconciliation items;
- expose last successful backup/restore verification metadata when available.

`doctor` reports state; it must not silently rewrite historical evidence to make checks pass.

## 15. Logging and observability

Use correlation identifiers that can connect:

```text
transport request
-> local operation
-> capture record
-> semantic write/result
```

Logs must avoid raw private learner content by default.

Useful stable categories include:

```text
capture_received
capture_committed
capture_rejected
idempotent_retry_resolved
idempotency_conflict
semantic_processing_failed
caller_result_unknown
reconciliation_backfill
reconciliation_ambiguous
storage_unhealthy
```

Logs are diagnostic observations, not canonical learner evidence unless deliberately ingested as such.

## 16. Backup and restore

The backup unit must cover all data required to reconstruct longitudinal state.

At minimum:

- SQLite operational database;
- private evidence artifacts referenced by the DB;
- integrity/hash manifest or equivalent verification data.

Acceptance sequence:

```text
capture known evidence
-> backup
-> move/destroy disposable working state
-> restore
-> run doctor
-> verify identities/hashes
-> verify current learner state references existing evidence
-> verify exact retry semantics remain coherent
```

A backup that restores a checkpoint but loses the underlying evidence is not sufficient.

## 17. Schema/migration principles

If P3.0 requires persistent schema changes:

1. write the data/invariant change before implementation;
2. use versioned forward migration;
3. preserve existing historical records;
4. do not reinterpret an existing field silently;
5. add compatibility/read tests for existing local data;
6. backup before destructive/irreversible migration on valuable learner data;
7. migration failure must not partially claim success.

Do not migrate merely to make code aesthetically cleaner.

## 18. Security/privacy boundary

P3.0 must not weaken the accepted private-evidence boundary.

- no raw private transcripts committed to public GitHub by default;
- no local tunnel/auth secrets committed to repository fixtures/docs;
- reconciliation tooling treats imported transcripts as private evidence unless explicitly reviewed/redacted;
- diagnostic logs should use IDs/hashes/categories rather than raw content where possible;
- arbitrary SQL/shell/file mutation is not exposed to the GPT merely to repair capture.

## 19. Focused verification strategy

Verification is risk-driven and directly tied to the durability invariant.

Required tests/experiments include:

### V1 — exact retry

Send same durable operation twice with same idempotency identity and fingerprint.

Expected: one durable evidence record, same result identity.

### V2 — idempotency conflict

Reuse identity with changed payload.

Expected: explicit conflict, no mutation of original record.

### V3 — commit then lose response

Inject failure after DB commit before caller receives success.

Expected: retry resolves original result, no duplicate.

### V4 — crash before commit

Inject failure before transaction commit.

Expected: no success receipt; retry can perform one clean commit.

### V5 — service restart

Commit evidence, restart process, query/retry.

Expected: evidence/result survives.

### V6 — semantic processing failure

Capture source turn, deliberately fail downstream normalization/derivation.

Expected: source evidence remains and processing can be retried.

### V7 — pre-receipt missing turn reconciliation

Create transcript containing a turn never sent to local runtime.

Expected: reviewed reconciliation adds one backfilled record with provenance.

### V8 — reconciliation rerun

Run same source again.

Expected: no duplicate.

### V9 — ambiguous reconciliation

Create two plausible local matches.

Expected: automatic reconciliation refuses to guess.

### V10 — backup/restore

Verify DB + private evidence + hashes + lineage after restore.

### V11 — DB/storage failure

Exercise locked/busy/unwritable/disposable disk-failure paths that are realistic for the current local deployment.

Expected: explicit failure, no false acknowledgement.

Do not require unrelated mutation/formal/browser/multi-user testing to accept this narrow slice unless implementation changes create a new material risk.

## 20. Rollout plan

### S0 — Observe current failure before modification

Collect sanitized diagnostics sufficient to localize the real 502 boundary.

Questions:

- Did the request reach the tunnel/transport?
- Did Study OS receive it?
- Did request validation run?
- Did a DB transaction begin?
- Did it commit?
- Did result serialization/transport return fail after commit?

### S1 — Lock the durability contract

Implement the smallest changes required for:

- commit-before-ack;
- retry resolution;
- unknown-result diagnosis;
- restart-safe capture.

### S2 — Source-turn preservation

Ensure source evidence can survive semantic-processing failure and can be linked by later operational records.

### S3 — Reconciliation/backfill

Implement one narrow reviewed transcript reconciliation path.

### S4 — Recovery acceptance

Pass focused V1–V11 tests on disposable state, then validate the real local deployment with sanitized evidence.

### S5 — Return to routine learning

Resume normal GPT dogfooding with capture/reconciliation status observable enough to diagnose future failures without interrupting learning.

## 21. Explicitly deferred work

Do not use P3.0 as justification to implement:

- dedicated frontend;
- generic application-contract rewrite;
- HTTP API expansion unrelated to current transport;
- multi-user auth/product hosting;
- Postgres;
- multimodal rendering;
- adaptive-policy promotion;
- wholesale runtime refactor;
- broad platform/SWE cleanup.

If a narrow refactor is necessary to establish the durability boundary, document the invariant it protects and keep the change replaceable.

## 22. Acceptance condition

P3.0 is technically complete when, for the current GPT/local Study OS architecture:

```text
received evidence
    -> cannot be acknowledged before durable commit

exact retry
    -> cannot duplicate evidence

committed-but-response-lost
    -> can be resolved without duplication

semantic derivation failure
    -> cannot destroy raw evidence

service restart
    -> cannot erase committed evidence

pre-receipt missing turn
    -> can be reconciled later with provenance

ambiguous recovery
    -> cannot silently guess

backup/restore
    -> preserves evidence identities, hashes, and lineage
```

Only after these invariants hold should implementation-level optimization or broader hardening take priority over continued learner use.