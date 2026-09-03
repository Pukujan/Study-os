# Problem discovery — append-only transcript durability gap

Date: 2026-09-03
Scope: Study OS runtime / evidence architecture
Evidence status: reviewed session-scoped problem discovery
Promotion status: not promoted

## Source boundary

This public repository does **not** contain the verbatim learner conversation.

The reviewed source was a user-provided conversation excerpt from the active Study OS learning session. The private source fingerprint used for this review is:

```text
sha256: 0525d4824b239a3f6b7d3535f5ce9f4ccd72c899adb7e9a6ececaaeb27361ea5
bytes: 3557
```

The fingerprint identifies the reviewed source used to derive this note; it does not mean the private transcript has already been durably captured by the Study OS local runtime.

## Observed / user-provided evidence

The reviewed conversation reports this sequence:

1. Study OS MCP had previously been returning HTTP 502 failures during real learning.
2. After recovery, the MCP health check was reported healthy.
3. The canonical learner state returned after recovery was materially stale relative to the learning that had occurred during the outage window.
4. The available Study OS semantic actions exposed structured learner-state/evidence operations, but no explicit append-only raw-transcript operation such as `append_transcript`, `store_message`, or `get_full_transcript` was available through the learner-facing integration.
5. A structured system-design/learning event could be written again after MCP recovery, but this did not recover the missing verbatim interaction history.

These are session-level observations from the reviewed conversation. They are not population claims and do not by themselves establish the exact local root cause of every missing turn.

## Existing architecture already requires more

`docs/FOSSIL_INTEGRATION.md` already assigns these assets to **Study OS canonical evidence**:

- exact raw transcript/export bytes;
- normalized transcript;
- append-only learning event log;
- learning episodes;
- assessment attempts;
- representation versions;
- learner-state derivations.

It also explicitly says transcript ingest should first:

1. save immutable/raw transcript;
2. create normalized transcript and manifest;
3. append observed/self-reported events;
4. propose derived learning episodes;
5. optionally export promoted knowledge to FOSSIL.

Therefore the newly observed problem is not merely a request for a new convenience feature. It is an **implementation/capability gap against an existing Study OS ownership decision**.

## Derived problem statement

Study OS currently has a resilience gap between:

```text
learner-facing conversation
        ↓
structured Study OS semantic writes
        ↓
local SQLite / evidence state
```

When the semantic/MCP write path is unavailable, the learner can continue learning in ChatGPT, but Study OS may have no canonical append-only source record from which the structured learner state can later be rebuilt.

That means:

```text
transport outage
+ continued learning
+ no independent raw-turn capture
= possible unrecoverable evidence gap
```

This directly weakens the P3 invariant:

> No silent learner-evidence loss.

A healthy structured database after recovery is insufficient if the source conversation required to reconstruct the missing learning sequence was never captured by Study OS.

## Required architectural property

The immediate design target should be:

> **Every learner-facing turn should be durably captured as append-only source evidence, or remain explicitly known as uncaptured/reconciliation-required. Structured semantic processing must not be the only persistence path.**

Logical ordering:

```text
SOURCE TURN
    ↓
append-only durable transcript/source record
    ↓
normalized turn
    ↓
learning events / attempts / operations
    ↓
derived learner + system state
```

If downstream semantic processing fails, the source turn must remain available for later replay/reconciliation.

## Candidate capability — proposed, not yet accepted design

A future runtime primitive may need semantics equivalent to:

```text
append_conversation_turn
read_conversation_turns
reconcile_conversation
```

The exact public/MCP shape is **not decided by this evidence record**.

Whatever implementation is selected should preserve:

- append-only source identity;
- conversation/session identity;
- role and source ordering where supported;
- original timestamp separately from local capture/backfill timestamp;
- content hash / immutable private artifact reference;
- idempotent re-append/reconciliation;
- no duplicate turn on retry;
- explicit provenance for live capture vs later backfill;
- raw/source survival when normalization or learner-state derivation fails;
- privacy: verbatim private transcript remains local/private by default.

## Reconciliation requirement

For turns created while Study OS is unreachable:

```text
later reviewed transcript/export
        ↓
compare stable IDs/hashes/order
        ↓
append only genuinely missing source turns
        ↓
mark provenance = backfill/reconciliation
        ↓
re-run normalization / structured learner-event extraction
```

Ambiguous matches must fail closed rather than silently merging learner history.

## Why this is urgent

Real learning continued while the Study OS MCP path was failing. The system recovered operationally, but canonical state was reported stale.

Until source-turn durability exists, another outage can reproduce the same evidence-loss window even if the structured database, retries, and checkpoint logic are otherwise healthy.

## Immediate engineering question

Before implementation, determine the smallest architecture-compatible way to satisfy the existing transcript ownership decision:

1. whether the local runtime already has an unused raw/source artifact model that can be extended;
2. whether transcript turn identity belongs in SQLite, the private immutable evidence store, or both;
3. whether a new semantic MCP operation is required or whether the current transport can automatically capture source turns before semantic dispatch;
4. how ChatGPT outage-window turns can be backfilled without fabricating chronology or identity;
5. how this integrates with the existing P3 durable-evidence PDD/SDD/TDD and backup/restore contract.

## Relationship to FOSSIL

This knowledge item belongs to **Study OS**.

FOSSIL semantics are useful for the provenance discipline—source evidence remains separate from proposed claims—but FOSSIL is not the canonical learner transcript database and should not be made a runtime dependency for every turn.

The canonical direction remains:

```text
raw conversation evidence
    → Study OS canonical schema
    → normalized/derived learning evidence
    → optional FOSSIL export/promotion
```

## Status

- observed problem: **supported by reviewed session evidence**;
- existing architecture conflict: **verified in repository documentation**;
- exact runtime root cause: **not yet established**;
- exact transcript API/schema: **proposed / undecided**;
- implementation priority: **immediate P3.0 durability follow-up**.
