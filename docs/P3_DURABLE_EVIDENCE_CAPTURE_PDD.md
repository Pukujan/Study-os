# P3.0 Durable Evidence Capture — Product Design Document

Status: proposed

Parent tracker: #52 — P3 Operational learning, durable evidence, and structured curriculum

Date: 2026-09-03

## 1. Product decision

Study OS is already being used as a real learner-facing GPT application. That usage is producing the highest-value product evidence in the project: actual attempts, confusion, representation failures, tutor interventions, learner feedback, retries, and later outcomes.

The immediate product risk is therefore not lack of a dedicated frontend. It is loss or uncertainty of this operational learning evidence when the GPT -> Study OS -> local runtime path fails.

P3.0 makes durable-or-recoverable evidence capture the highest-priority runtime objective.

## 2. Product objective

The learner should be able to keep using Study OS for real learning while the system preserves enough evidence to reconstruct what happened and continue longitudinally.

The required product guarantee is:

> No silent learner-evidence loss.

A learner interaction must end in one of two states:

1. **durably captured** — Study OS can prove the local evidence was committed; or
2. **known uncertain/missing** — the system does not claim success and the interaction can later be reconciled/backfilled from an available conversation/transcript source.

The goal is not to promise that networks, tunnels, GPT integrations, or local processes can never fail. The goal is to make failure explicit, non-destructive, retry-safe, and recoverable.

## 3. Why this is product work

Study OS currently learns about its own teaching behavior from real sessions.

Examples already observed include:

- representation translation overhead;
- variable-name semantic interference;
- learner-reported information overload/under-information as candidate failure classes;
- task decomposition into smaller operations;
- assistance/hint amount;
- source-representation restoration and future transfer/retention checks.

If the underlying interaction history is missing or ambiguous, Study OS cannot reliably:

- reconstruct learner state;
- grade the learner;
- grade the tutoring system;
- compare interventions;
- distinguish self-report from observed behavior;
- know which representation was actually shown;
- know whether a later answer was assisted;
- perform trustworthy longitudinal analysis.

Durable capture is therefore part of the learning-product architecture, not merely an infrastructure convenience.

## 4. Current learner-facing surface

The GPT application remains the primary learner-facing surface during P3.

A dedicated frontend is deferred because the GPT currently provides a coherent and flexible learning interaction for Subject 001 and is exposing novel failure modes through free-form conversation.

The current loop remains:

```text
structured/source learning material
        -> GPT learning interaction
        -> learner attempt / question / confusion
        -> Study OS teaching operation
        -> learner response
        -> operational evidence
        -> learner/system evaluation
        -> next learning action
```

P3.0 protects this loop. It does not replace it.

## 5. Durable asset hierarchy

The project explicitly values durable architecture and data above implementation code.

The evidence hierarchy is:

```text
RAW / SOURCE EVIDENCE
        ↓
NORMALIZED OPERATIONAL RECORDS
        ↓
DERIVED LEARNER + SYSTEM STATE
```

### 5.1 Raw/source evidence

Examples:

- user message/attempt;
- assistant response;
- tool result relevant to the learning interaction;
- imported/reconciled transcript turn;
- source task reference;
- source conversation/message identifiers when available;
- immutable content hash/provenance.

Raw evidence is never silently rewritten to match a later interpretation.

### 5.2 Normalized operational records

Examples:

- attempt;
- assessment;
- intervention;
- representation exposure;
- assistance exposure;
- information-dose operation;
- task decomposition/recomposition;
- learner feedback;
- original/source representation restoration;
- transfer/retention result.

### 5.3 Derived state

Examples:

- candidate failure signature;
- learner capability estimate;
- intervention effectiveness estimate;
- over-help/under-help hypothesis;
- representation-effectiveness hypothesis;
- next-action proposal.

Derived state must remain reproducible from linked evidence and may be replaced without destroying the underlying history.

## 6. Core product requirements

### R1 — No false durability acknowledgement

Study OS must not report a durable write as successful until the local durability boundary has committed the record required by the operation.

### R2 — Retry safety

If the caller receives a timeout/502/unknown result and retries the same durable operation, Study OS must not duplicate the underlying evidence.

Exact retry must resolve to the same durable result.

Conflicting reuse of an idempotency identity must fail explicitly.

### R3 — Raw capture survives semantic-processing failure

Where the architecture captures a learner/assistant turn before deriving structured learning semantics, a failure to classify/normalize/derive that turn must not erase the raw evidence.

Capture status and semantic-processing status are separate concerns.

### R4 — Explicit uncertainty

Unknown write state must be representable.

The system must distinguish at minimum:

- confirmed committed;
- confirmed rejected/not committed;
- caller-visible unknown result;
- reconciliation required;
- reconciled/backfilled.

### R5 — Restart continuity

A confirmed committed record must remain queryable after Study OS service/process restart.

### R6 — Reconciliation/backfill

If a turn fails before the local service receives it, local persistence cannot preserve data it never saw.

Study OS must therefore support a reconciliation path from an available source such as a conversation export/transcript or other reviewed capture.

Reconciliation must:

- preserve the backfill source provenance;
- avoid overwriting an existing raw record;
- deduplicate exact matches;
- surface ambiguous matches for review rather than guessing;
- link reconciled records into the original session/episode chronology where evidence supports the linkage.

FOSSIL may be one downstream/source reference when available, but reconciliation must not require FOSSIL as a runtime dependency.

### R7 — Capture every learner-facing turn when feasible

The long-term capture model should be capable of storing the learner-facing conversation sequence, not only selected events that a tutor happened to classify as important.

Operational/derived records may then reference those captured turns.

This requirement exists because unanticipated learner statements can later become important product evidence.

### R8 — Minimal learner burden

Durability instrumentation must not turn studying into manual data administration.

The learner should not have to repeatedly confirm routine writes during normal successful operation.

Manual reconciliation is acceptable only when a failure actually occurred or provenance is ambiguous.

### R9 — Privacy boundary

Canonical private/raw learner evidence remains local/private by default.

Public GitHub artifacts may contain reviewed/redacted derivatives, hashes, schemas, fixtures, and research conclusions according to existing data policy.

### R10 — Architecture independence

The evidence model must survive replacement of implementation code.

Persistent identities, schemas/migrations, provenance, idempotency semantics, capture states, and reconciliation rules are durable contracts. Particular Python classes/functions are not.

## 7. Product failure model

P3.0 must design for these distinct cases.

### F1 — Failure before local receipt

```text
GPT/client -> X -> Study OS local runtime
```

Local Study OS has no copy of the turn.

Required behavior: do not claim local durability; later reconciliation/backfill is the recovery path.

### F2 — Local receipt, failure before durable commit

Required behavior: no success acknowledgement; retry must be safe.

### F3 — Durable commit, response lost before caller receives success

Required behavior: caller may believe result is unknown; exact retry resolves to the already committed record rather than duplicating it.

### F4 — Raw capture succeeds, semantic derivation fails

Required behavior: preserve raw capture; mark processing failure/pending state; allow later reprocessing.

### F5 — Service crash/restart

Required behavior: committed records survive; incomplete/uncommitted work is not reported as durable.

### F6 — Database unavailable/busy/disk-full/corrupt boundary

Required behavior: explicit failure/health state; never silently discard the evidence while reporting success.

### F7 — Reconciliation source conflicts with local data

Required behavior: preserve both provenance records, fail closed on ambiguous automatic merge, and require reviewed resolution.

## 8. Product success criteria

Before P3.0 is considered complete, demonstrate on the real local architecture or a faithful disposable copy:

1. **0 acknowledged-lost writes** across the acceptance suite.
2. **0 duplicate durable evidence records** for exact retries.
3. Conflicting idempotency reuse is explicitly rejected.
4. Commit-then-response-loss can be reconciled by retry/query without duplication.
5. Confirmed committed evidence survives service restart.
6. Raw captured evidence remains available when downstream semantic processing fails.
7. At least one simulated pre-receipt missing turn can be backfilled from a reviewed transcript source with provenance.
8. Re-running reconciliation does not duplicate the same backfilled turn.
9. `doctor`/diagnostics can identify capture/reconciliation states that require attention.
10. Backup -> restore reproduces the tested learner evidence identities, hashes, and durable capture status.
11. Derived learner/system records retain evidence references after restore.
12. Normal successful studying does not require manual persistence administration by the learner.

## 9. Success metrics during real dogfooding

Track operationally, without turning them into learner-truth metrics:

- confirmed durable write count;
- rejected write count by stable failure category;
- caller-unknown write count;
- reconciliation-required count;
- reconciliation success/ambiguous count;
- duplicate prevented count;
- write/reconciliation latency where useful;
- sessions with unresolved evidence gaps;
- backup/restore verification status.

Do not infer learner capability from these system-reliability metrics.

## 10. Non-goals for P3.0

P3.0 does **not** require:

- a dedicated web/mobile frontend;
- React/Svelte/TypeScript client generation;
- Postgres migration;
- microservices;
- generalized multi-user architecture;
- live adaptive-policy promotion;
- a new mastery model;
- complete automated FOSSIL synchronization;
- multimodal video/audio generation;
- broad mutation/formal/chaos programs unrelated to the actual durability failure;
- rewriting the structured curriculum plan;
- proving that Study OS improves learning generally.

Those may be valuable later, but they are not prerequisites for restoring trustworthy operational evidence capture.

## 11. Relationship to current curriculum and learning work

P3.0 must not block Subject 001 from continuing to learn unnecessarily.

In parallel:

- approved public-source curriculum work may continue;
- real GPT dogfooding may continue;
- reviewed public derivatives of learner episodes may continue;
- representation/information/assistance/decomposition hypotheses may continue to evolve.

If a session is affected by a known capture failure, its evidence scope must say so until reconciliation is complete.

## 12. Delivery sequence

### P3.0-A — Diagnose

Reproduce/localize the current 502 path and determine whether failures occur:

- before the local service;
- at transport/auth/tunnel boundary;
- during request handling;
- during persistence;
- after persistence while returning the result.

Do not redesign the system before identifying which failure classes are real.

### P3.0-B — Protect the durability boundary

Implement only the smallest architectural changes required to satisfy R1–R5 and preserve existing persistent semantics where possible.

### P3.0-C — Reconciliation

Add explicit missing/unknown/backfill semantics and one reviewed transcript reconciliation workflow.

### P3.0-D — Recovery verification

Verify restart, retry, unknown-result, backup/restore, and integrity diagnostics.

### P3.0-E — Resume normal dogfooding

Return the GPT learning loop to routine use with visible evidence status and a documented recovery procedure.

## 13. Product acceptance principle

P3.0 is accepted when the learner can focus on learning and Study OS can later answer, with evidence:

> What interaction happened, what did the system actually preserve, what is still uncertain, and how can any missing evidence be recovered?

That is the foundation required before operational learner/system evaluation can be trusted.