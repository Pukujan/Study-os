# P3 Cross-Chat Continuity SDD

Status: proposed implementation contract  
Date: 2026-09-03  
Parent: #52  
Related: #56, #59

## Design objective

Provide bounded, evidence-backed cross-chat continuity without making accepted checkpoints optional or turning transcript history into mastery state.

## Existing facts to preserve

The live runtime already provides:

- SQLite schema v1;
- `sessions`;
- `messages` linked to immutable `raw_artifacts`;
- `learning_events`;
- `attempts`;
- `checkpoints` and `subject_current_checkpoint`;
- `append_conversation_turn`;
- reviewed transcript reconciliation;
- `doctor` integrity checks;
- backup/restore.

The preferred implementation is therefore schema-v1-first. Add no migration unless a failing acceptance test proves that the existing structures cannot represent the required semantics.

## Current failure mode

Current resume behavior is effectively:

```text
resume(subject_id)
→ subject_current_checkpoint
→ checkpoint exists? return checkpoint
→ otherwise not_found
```

That is correct for the narrow meaning “resume accepted checkpoint state,” but insufficient for product continuity.

## New semantic operation

Preferred bounded operation:

```text
resume_learning_context(subject_id)
```

This should be additive rather than silently changing the meaning of the historical `resume` operation in v0.2.

### Why additive

`resume` currently has a strong contract around accepted checkpoint state. Reinterpreting it to return transcript-derived fallback state risks mixing two semantic classes.

A separate continuity operation can return a structured union of:

- checkpoint context;
- post-checkpoint evidence;
- evidence-only fallback context;
- no-evidence/identity diagnostic.

## Logical response model

Conceptual shape:

```json
{
  "subject_id": "subject-001",
  "continuity_status": "checkpoint_plus_recent_evidence",
  "checkpoint": {
    "checkpoint_id": "...",
    "current_focus": "...",
    "next_action": "...",
    "created_at": "..."
  },
  "recent_evidence": {
    "sessions": [],
    "messages": [],
    "learning_events": [],
    "attempts": []
  },
  "evidence_boundary": {
    "checkpoint_is_accepted_state": true,
    "recent_evidence_is_not_mastery": true
  }
}
```

Exact public schema may be narrower; the semantic distinction is mandatory.

## Continuity status values

Recommended bounded statuses:

```text
checkpoint_only
checkpoint_plus_recent_evidence
evidence_only
no_durable_context
identity_or_runtime_unverified
```

Do not overload HTTP success/failure with learner-state meaning.

## Evidence selection

Use bounded recent evidence, not an unbounded transcript dump.

Initial policy may select, per subject:

- latest N sessions by `started_at`;
- latest N message occurrences by local capture/source chronology;
- latest N learning events;
- latest N attempts;
- items newer than the accepted checkpoint when a checkpoint exists.

The selection limit must be deterministic/configured and tested.

## Checkpoint boundary

When a current checkpoint exists, locate its `created_at` and preserve its accepted state exactly.

Evidence newer than that checkpoint is returned as **post-checkpoint evidence** rather than being merged into `capability_state` or `next_action` automatically.

Conceptually:

```text
checkpoint.created_at = T

messages/events/attempts with created/source occurrence after T
→ post_checkpoint_evidence
```

If source timestamps and local capture timestamps differ due to reconciliation, preserve both. Selection/order must not rewrite original source chronology.

## No-checkpoint fallback

When no accepted checkpoint exists:

1. verify the subject exists;
2. query recent sessions/messages/events/attempts owned by that subject;
3. if evidence exists, return `evidence_only`;
4. if nothing exists, return `no_durable_context`;
5. do not synthesize a checkpoint.

## Stable identity and runtime verification

The real GPT integration must be configured with an explicit stable subject identity.

Recommended integration metadata:

```text
subject_id
source_client
integration_instance/ref where available
runtime fingerprint/diagnostic metadata where safe
```

The local runtime may expose a bounded diagnostic field such as runtime instance/root fingerprint via `doctor`/status, but must not expose secrets or arbitrary filesystem paths to the GPT unless explicitly approved.

For CT6, it is enough that the integration can distinguish:

- expected subject exists with evidence;
- requested subject does not exist;
- live runtime instance does not match expected deployment/configuration metadata.

A mismatch should not be phrased as authoritative learner amnesia.

## Real GPT source-turn sequence

The intended learner-facing sequence remains:

```text
receive user turn
→ append exact user turn
→ perform tutoring/semantic operations
→ prepare exact assistant response
→ append exact planned assistant response
→ emit the same assistant response
```

If the assistant append fails but a response is nevertheless displayed, that turn becomes reconciliation-required and must not be claimed as durably captured.

## Read surface and privacy

Do not expose generic raw transcript browsing to the GPT merely to implement continuity.

`resume_learning_context` should return only the bounded data required for continuity.

If source content is included, apply explicit limits and preserve privacy. Prefer structured summaries/metadata produced deterministically from stored evidence where possible, but do not fabricate semantic summaries that obscure source provenance.

A future richer `read_conversation_turns` operation can be considered separately.

## Historical reconciliation

Existing `reconcile_conversation` remains the authority for reviewed private transcript backfill.

Rules:

- do not backfill from memory or paraphrase when a lossless source is required;
- preserve source artifact hash;
- append missing occurrences only;
- preserve live vs reconciliation origin;
- rerun idempotently;
- ambiguous matches remain review-required;
- never rewrite existing checkpoint/attempt/event rows merely to make chronology look cleaner.

## `/actions` error handling

Narrow transport handling so `StudyOSError` categories remain explicit even if internal MCP behavior changes.

Desired pattern:

```text
StudyOSError
→ preserve category/details

unexpected Exception
→ internal_error
```

This is transport hygiene, not a new learning semantic.

## MCP surface

Do not add generic read/write primitives.

If `resume_learning_context` is exposed to the GPT, version the bounded semantic contract accordingly. Historical v0.1/v0.2 contracts remain immutable records.

Whether this becomes v0.3 is an implementation decision to make with the contract diff; do not silently mutate v0.2.

## Doctor/integrity

Existing message/artifact integrity remains mandatory.

Continuity-specific health should verify where feasible:

- message→artifact links resolve;
- content hashes agree;
- checkpoint pointers resolve;
- no cross-subject evidence leakage;
- runtime schema is supported.

Do not mark `doctor` unhealthy merely because a learner has no checkpoint or no history; that is a valid data state, not database corruption.

## Backup/restore

No new durable state should exist outside the existing DB + evidence backup boundary unless explicitly specified.

After restore:

- checkpoint continuity must match pre-backup state;
- evidence-only continuity must match pre-backup state;
- source artifact hashes must verify;
- exact append retry remains idempotent.

## Migration policy

Default: **no migration**.

A migration is justified only if a failing CT test proves schema v1 cannot represent required stable semantics. If migration becomes necessary, stop and write a migration-specific delta before touching live learner data.
