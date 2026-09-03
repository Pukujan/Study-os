# ADR-0015 — Study OS owns append-only learner source-turn capture

Status: accepted once merged

Date: 2026-09-03

Related: #52, #56

## Context

Study OS already assigns canonical raw transcript/export evidence and append-only learner-event history to the local Study OS runtime/private evidence store.

A real MCP outage/recovery episode demonstrated that structured learning operations can be unavailable or stale while the actual GPT conversation continues. After recovery, the runtime had no dependable append-only learner-facing transcript substrate to reconstruct what occurred.

The initial schema already contains `raw_artifacts`, `messages`, and `idempotency_records`, but there is no canonical runtime/application/MCP operation that appends a learner-facing source turn into those structures.

## Decision

1. **Study OS remains the canonical owner of raw learner transcript/source-turn evidence.** FOSSIL remains optional downstream export/promotion.
2. **Source-turn capture occurs before semantic learning interpretation.** A turn does not need to be classified as an attempt/event/intervention before it is durably preserved.
3. **Reuse the existing schema first.** The preferred implementation uses `EvidenceStore` + `raw_artifacts` + `messages` + `idempotency_records`; schema migration is not authorized by default.
4. **Add one bounded semantic append-turn operation if required by the GPT integration.** Preferred name: `append_conversation_turn`.
5. **Version the MCP contract rather than silently changing v0.1.** Adding this capability may supersede the exact-13-tool current-surface invariant with an exact-14-tool v0.2 surface while preserving all prior 13 tool semantics.
6. **Do not expose generic file, SQL, shell, or arbitrary transcript mutation.** The new capability is semantic and narrow.
7. **Reconciliation/backfill is local/reviewed first.** It may reuse the same internal append semantics with `capture_origin = reconciliation` without requiring a second GPT-facing MCP tool.
8. **Live and recovered evidence remain distinguishable.** Source timestamp and local capture/recovery time are separate facts.
9. **Learning should continue during capture outages.** Failure to append must not be mislabeled as durability success; the conversation becomes reconciliation-required rather than blocking the learner indefinitely.

## Consequences

The durable chain becomes:

```text
learner/user or assistant turn
  -> immutable private evidence bytes
  -> raw_artifacts
  -> messages
  -> optional semantic learning records
  -> derived learner/system state
```

A semantic-processing failure can no longer erase the only evidence of the turn.

Post-commit response loss is resolved by idempotent retry against the stored append result.

Historical outage windows remain incomplete until reconciled from actual source evidence.

## Compatibility

This ADR does not change the semantics of existing events, attempts, assessments, interventions, checkpoints, retention probes, or FOSSIL exports.

`record_learning_event` is not redefined as transcript storage.

The previous exact-13-tool MCP surface remains historical v0.1 compatibility evidence; any new current surface must be explicitly versioned and mechanically tested.

## Verification

Implementation is governed by:

- `docs/P3_SOURCE_TURN_DURABILITY_PDD_DELTA.md`
- `docs/P3_SOURCE_TURN_DURABILITY_SDD_DELTA.md`
- `docs/P3_SOURCE_TURN_DURABILITY_TDD_DELTA.md`
