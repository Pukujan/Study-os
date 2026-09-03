# P3.0 Source-Turn Durability — Product Design Delta

Status: accepted implementation specification once merged

Parent tracker: #52

Focused issue: #56 — Add append-only learner transcript/source capture and outage reconciliation

Extends: `docs/P3_DURABLE_EVIDENCE_CAPTURE_PDD.md`

Date: 2026-09-03

## 1. Why this delta exists

The 2026-09-03 MCP recovery session exposed a specific gap in the existing P3 durability design:

- learning continued while the Study OS MCP path was returning 502s;
- after recovery, canonical structured learner state was materially stale relative to the conversation;
- the learner-facing semantic surface exposed structured events/attempts/assessments but no append-only source-turn primitive;
- restoring structured writes did not reconstruct the missing verbatim interaction sequence.

This conflicts with an existing Study OS ownership decision in `docs/FOSSIL_INTEGRATION.md`: Study OS, not FOSSIL, canonically owns exact raw transcript/export evidence, normalized transcript, and the append-only learning event history.

The problem-discovery record is preserved at:

`sessions/2026-09-03/mcp-recovery-transcript-gap/knowledge/problem-discovery.md`

The private verbatim source remains local/private.

## 2. Product decision

Source-turn capture is no longer a long-term aspiration inside P3.0. It is a current durability requirement.

For the supported GPT integration, Study OS must be capable of preserving the learner-facing conversation sequence independently of whether any turn is immediately classified as an attempt, assessment, representation intervention, or other semantic learning event.

The required hierarchy is:

```text
learner-facing source turn
        ↓
append-only durable source evidence
        ↓
normalized/semantic learning records
        ↓
derived learner + system state
```

Semantic processing is downstream of source capture and may fail without erasing the source turn.

## 3. Product invariant

> Every learner-facing turn must either be durably captured as append-only Study OS source evidence or remain explicitly known as uncaptured/reconciliation-required. Structured semantic writes are not a substitute for transcript/source evidence.

This extends the existing invariant:

> No silent learner-evidence loss.

## 4. Supported turn scope for the first implementation

The first implementation must support at least:

- learner/user turns;
- assistant/tutor turns.

Tool results may be added later when they materially affect learner-facing reconstruction, but are not required to block the initial repair unless Luna finds they are necessary to reproduce the actual interaction faithfully.

A turn is an occurrence, not merely a unique text blob. Repeated identical text remains two distinct message occurrences even if the underlying immutable content bytes are deduplicated internally.

## 5. Learner-facing behavior

Normal studying must remain the priority.

The intended GPT behavior after the new capability is deployed is:

```text
receive learner turn
    ↓
append learner turn to Study OS
    ↓
reason/respond normally
    ↓
append planned assistant response
    ↓
emit that response to learner
```

If live append fails because the local/MCP path is unavailable:

- the tutor should still be allowed to answer rather than blocking learning indefinitely;
- the failed live append must not be represented as durable success;
- the conversation becomes reconciliation-required until recovered from an actual transcript/export/source;
- later backfill preserves that it was recovered after the fact rather than captured live.

The learner should not have to manually administer routine successful capture.

## 6. Exactness requirement

For live GPT capture, Study OS preserves the exact source-turn content supplied to the append operation.

For an assistant turn, the GPT integration should treat the persisted assistant content as the planned final response and emit that same content after successful capture. If the append call fails and the response is still shown, later reconciliation is the authority for what was actually displayed.

For platform exports, the original export bytes remain a separate stronger raw source artifact when available.

Do not claim that a per-turn string received over MCP is identical to an unavailable platform-internal export format.

## 7. Current product requirements

### ST-R1 — Capture before interpretation

A learner-facing turn must be appendable without first assigning it a learning-event type, mastery meaning, failure signature, or intervention label.

### ST-R2 — Append-only occurrence identity

Each turn occurrence has a stable local message identity and cannot be silently overwritten.

### ST-R3 — Retry-safe append

An exact retry of the same append request resolves to the original durable message result and does not create another message occurrence.

Conflicting reuse of the same idempotency identity fails explicitly.

### ST-R4 — Private immutable content

Raw turn content remains local/private by default and is hash-verifiable.

Public GitHub may contain only synthetic fixtures, hashes, schema/contract metadata, and reviewed/redacted derivatives.

### ST-R5 — Source provenance

Preserve when available:

- source client/provider;
- source conversation identifier;
- source message/turn identifier;
- parent/reference identifier;
- source-reported timestamp;
- source order/sequence evidence;
- local capture timestamp;
- capture origin: live or reconciliation.

Missing source metadata must remain missing rather than invented.

### ST-R6 — Chronology honesty

Original/source time and local recovery/commit time are separate facts.

Backfilled turns must never be rewritten to look as if Study OS captured them live at the original source timestamp.

### ST-R7 — Structured semantics reference source evidence

New or reprocessed learning events/attempts/interventions derived from a captured turn should reference the source message/artifact evidence where the existing domain contract allows it.

Derived state must not become the only remaining record of what occurred.

### ST-R8 — Outage reconciliation

Study OS must support one reviewed path that can append genuinely missing turns from actual transcript/export evidence after an outage.

Reconciliation must be idempotent and fail closed on ambiguous identity.

### ST-R9 — Backup/restart durability

Captured turn identity, raw evidence reference/hash, provenance, and reconciliation origin survive service restart and backup/restore.

### ST-R10 — Minimal semantic surface

Do not expose generic file writes, SQL, shell, or arbitrary mutation merely to capture a transcript.

A narrowly scoped semantic turn-append operation is permitted because source-turn durability is now a canonical Study OS requirement.

## 8. MCP/application-surface decision

The previous exact-13-tool MCP surface was valuable as an anti-sprawl constraint, but it did not include the canonical transcript/source-turn capability required by the architecture.

This delta authorizes one bounded semantic addition for source-turn append if the GPT integration cannot satisfy live capture through an already-existing semantic operation without abusing its meaning.

Preferred semantic operation name:

`append_conversation_turn`

The name may change only if the application-contract design finds a materially clearer equivalent.

This does **not** authorize generic raw file mutation or arbitrary transcript database access.

A versioned MCP contract change is expected if this operation becomes GPT-facing. Existing v0.1 semantics remain historical compatibility evidence rather than being silently reinterpreted.

## 9. Reconciliation surface decision

Reconciliation is initially a local/reviewed recovery operation, not a learner-facing GPT requirement.

The first implementation may expose reconciliation through a local CLI/tooling path rather than adding another MCP tool.

This keeps the live conversational surface small while still satisfying outage recovery.

## 10. Success criteria for Issue #56

Issue #56 is product-complete when all applicable conditions are demonstrated:

1. one learner/user turn can be appended durably before semantic classification;
2. one assistant/tutor turn can be appended durably;
3. exact append retry produces one canonical message occurrence;
4. conflicting idempotency reuse fails explicitly;
5. raw turn evidence survives downstream semantic-processing failure;
6. post-commit response loss can be retried without duplication;
7. captured turns survive process restart;
8. one synthetic/reviewed outage transcript can backfill a missing turn;
9. rerunning that reconciliation adds nothing duplicate;
10. ambiguous reconciliation refuses automatic merge;
11. source time and local recovery time remain distinguishable;
12. backup/restore preserves source-turn identity, hashes and provenance;
13. public tests/logs contain no real private learner transcript;
14. one controlled GPT smoke demonstrates the new append operation on actual learner/assistant turns;
15. normal course learning can continue even if live capture temporarily fails, with the gap explicitly recoverable rather than silently forgotten.

## 11. Non-goals

This delta does not require:

- building the dedicated frontend;
- making FOSSIL the runtime transcript database;
- adding transcript search/RAG;
- storing chain-of-thought or hidden system messages;
- capturing platform-internal metadata that the integration does not actually receive;
- audio/video generation;
- multi-user transcript sharing;
- automatic promotion of session observations into lesson/domain knowledge;
- broad database redesign.

## 12. Acceptance principle

The learner should be able to finish the course through the GPT while Study OS can later answer, from its own canonical local evidence:

> What did the learner and tutor actually exchange, which turns were captured live, which were recovered later, and which gaps remain unresolved?
