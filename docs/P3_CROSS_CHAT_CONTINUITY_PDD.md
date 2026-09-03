# P3 Cross-Chat Continuity PDD

Status: proposed implementation contract  
Date: 2026-09-03  
Parent: #52  
Related: #56, #59

## Problem

Study OS can now durably store source turns through `append_conversation_turn`, but a fresh real Study OS GPT chat still failed to recover prior learning context.

The local audit found two distinct causes:

1. historical `default` and `subject-001` sessions contain no durable `messages` or `raw_artifacts`, so older source turns were never captured and require reconciliation/backfill where a private source exists;
2. `resume(subject_id)` still depends on `subject_current_checkpoint` and cannot recover bounded continuity from durable evidence when a current checkpoint is absent.

The audit also did not prove that the real GPT surface is currently writing either the actual learner turn or the exact assistant response into the live runtime.

## Product guarantee

> A fresh Study OS conversation must recover the latest trustworthy learning context available for the same learner identity, even when no current checkpoint exists, without silently converting transcript evidence into mastery or capability claims.

This guarantee has two independent prerequisites:

- **identity continuity:** the GPT must use a stable learner identity and the intended live Study OS runtime;
- **evidence continuity:** Study OS must be able to return bounded recent evidence independently of checkpoint existence.

## User-visible success

When the learner asks a fresh Study OS chat what they were studying, Study OS should be able to answer from the strongest available durable evidence.

Examples of acceptable continuity:

- “Your last accepted checkpoint says you were working on Python/DSA foundations.”
- “After that checkpoint, your durable session evidence shows work on dictionaries and Two Sum representation.”
- “There is no accepted checkpoint, but the most recent durable session shows you were working on X.”

Study OS must identify the evidence class/source where it matters.

## Non-goals

This phase does not:

- infer mastery from transcript text;
- replace checkpoints;
- auto-create a new learner identity because an old one is inconvenient;
- make GitHub or FOSSIL the live runtime;
- add generic SQL/file access to the GPT;
- reconstruct missing historical turns without a real source artifact;
- guarantee that remote ChatGPT turns exist locally if the GPT integration never called Study OS.

## Required continuity hierarchy

Use the strongest available evidence in this order while preserving provenance:

```text
accepted checkpoint
        +
post-checkpoint durable evidence
        ↓
bounded continuity context
```

If no checkpoint exists:

```text
recent durable sessions/messages/events/attempts
        ↓
bounded continuity context
```

If no durable evidence exists:

```text
explicit no-evidence result
```

Do not fabricate or infer history from absence.

## Evidence semantics

The continuity response may include:

- accepted checkpoint state;
- recent session identifiers/timestamps;
- recent source-turn summaries or bounded excerpts where privacy policy permits;
- recent learning event types;
- recent attempts/task identifiers;
- explicit post-checkpoint evidence.

The continuity response must not silently upgrade these into capability/mastery.

Example:

```text
observed durable source evidence:
  learner discussed dictionary lookup

accepted capability state:
  unknown_baseline
```

Both can coexist.

## Stable identity requirement

The actual learner-facing GPT integration must have one explicit stable `subject_id` policy.

A fresh chat must not silently switch between `default`, `subject-001`, a generated subject, or another runtime root.

If runtime/identity cannot be verified, the system should surface that as an integration/identity problem rather than reporting “no history” as though it were authoritative.

## Historical gap recovery

Historical sessions with structured attempts/events but no raw turns remain valid structured evidence.

Where a private/lossless transcript export exists:

```text
private source transcript
→ reviewed reconciliation
→ append missing raw turns
→ preserve reconciliation provenance
```

Reconciliation must not overwrite existing structured evidence or accepted checkpoints.

Where no source transcript exists, the missing source turns remain explicitly missing.

## Real GPT acceptance requirement

Synthetic local HTTP tests are necessary but insufficient.

Completion requires actual Study OS GPT proof that:

1. one learner/user turn is written to the intended runtime;
2. the exact assistant response displayed to the learner is written to the intended runtime;
3. a new GPT conversation using the same stable learner identity can recover useful prior context from Study OS.

## Privacy

Raw learner transcript remains local/private by default.

Public evidence may contain:

- IDs;
- counts;
- hashes;
- synthetic fixtures;
- reviewed/redacted findings;
- test outcomes.

Do not commit real raw learner text to the public repository.

## Success metrics

P3 cross-chat continuity is accepted when:

- CT1–CT9 are green in deterministic/synthetic tests;
- CT10–CT12 are demonstrated through the real Study OS GPT surface;
- no learner-data reset or destructive migration was required;
- checkpoint semantics remain unchanged for existing accepted checkpoints;
- transcript/source evidence remains distinct from derived capability state;
- runtime/subject mismatch cannot silently masquerade as an authoritative empty history.
