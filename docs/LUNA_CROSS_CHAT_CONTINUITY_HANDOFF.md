# Luna Handoff — Cross-Chat Continuity + Real GPT Capture

Date: 2026-09-03  
Issues: #56, #59

## Read first

1. `docs/P3_DURABLE_EVIDENCE_CAPTURE_PDD.md`
2. `docs/P3_DURABLE_EVIDENCE_CAPTURE_SDD.md`
3. `docs/P3_SOURCE_TURN_DURABILITY_PDD_DELTA.md`
4. `docs/P3_SOURCE_TURN_DURABILITY_SDD_DELTA.md`
5. `docs/P3_SOURCE_TURN_DURABILITY_TDD_DELTA.md`
6. `docs/P3_CROSS_CHAT_CONTINUITY_PDD.md`
7. `docs/P3_CROSS_CHAT_CONTINUITY_SDD.md`
8. `docs/P3_CROSS_CHAT_CONTINUITY_TDD.md`
9. `docs/ADR-0015-source-turn-capture.md`

## Audit is accepted as the current diagnosis

Do not repeat destructive investigation or reset learner data.

Current audited live runtime:

```text
runtime root: /root/.study-os
DB: /root/.study-os/db/study-os.sqlite3
evidence root: /root/.study-os/evidence
service source: /mnt/d/Study-os-main
listener: 127.0.0.1:18765
schema: 1
doctor: healthy
```

Incident classification: **B + C**.

- B: the actual GPT subject/runtime identity has not yet been proven by durable source-turn records.
- C: historical `default` and `subject-001` sessions contain no source-turn `messages/raw_artifacts` and therefore require reconciliation where a private source transcript exists.

The only current message-backed session is synthetic smoke evidence and must not be mistaken for learner history.

## First implementation goal

Do not start by backfilling history.

First make the *current* real GPT path trustworthy:

```text
real GPT user turn
→ intended /root/.study-os runtime
→ stable learner subject_id
→ append exact user turn

real GPT assistant response
→ append exact planned response
→ emit same response
```

Then prove fresh-chat continuity.

## Stable subject identity

Before code changes that assume a learner identity, identify the actual GPT configuration/policy that chooses `subject_id`.

Do not create a new subject merely to obtain passing tests.

The owner should end up with one explicit learner identity policy for the current Study OS GPT.

If `default` vs `subject-001` is ambiguous, report the evidence and propose the smallest canonical choice/mapping. Do not merge histories silently.

## Continuity implementation

Preferred new bounded semantic operation:

```text
resume_learning_context(subject_id)
```

Keep historical `resume(subject_id)` checkpoint semantics intact unless a separately approved contract change says otherwise.

The continuity operation should return:

- accepted checkpoint if present;
- recent post-checkpoint evidence separately;
- recent evidence-only fallback if no checkpoint exists;
- explicit no-context / identity/runtime diagnostic when appropriate.

It must not convert transcript discussion into mastery/capability state.

## No migration first

Schema v1 already represents the necessary evidence classes.

Implement CT1–CT9 without a migration if possible.

If a migration appears necessary, stop and report the failing test and missing semantic before modifying the live DB.

## `/actions` cleanup

Narrow error handling so semantic `StudyOSError` categories remain explicit and unexpected exceptions alone become `internal_error`.

Add regression coverage.

## Real GPT acceptance

CT10–CT12 are mandatory before closure.

Synthetic `/mcp`, `/actions`, curl, or direct service calls do not satisfy them.

Need proof for:

- real GPT fresh-chat continuity;
- real GPT user source-turn capture;
- exact displayed assistant response capture.

Public receipt should contain IDs/hashes/timestamps and pass/fail only, not raw learner content.

## Historical repair

After current live capture/continuity is proven:

1. backup live DB + evidence;
2. identify private/lossless transcript sources for missed historical periods;
3. run reviewed reconciliation;
4. verify attempts/events/checkpoints remain intact;
5. verify only missing source turns are appended;
6. preserve reconciliation provenance;
7. leave unrecoverable gaps explicit if no source exists.

Do not generate missing turns from summaries or memory and call them raw transcript.

## Required completion report

Return:

```text
exact implementation SHA
runtime root used
stable subject_id policy
MCP contract version if changed
schema migration yes/no
CT1–CT12 results
ST1–ST22 results
/actions semantic-error tests
full suite result
doctor result
backup/restore result
real GPT user message_id/artifact_id/hash
real GPT assistant message_id/artifact_id/hash
fresh-chat continuity result
historical reconciliation status
limitations
```

Do not close #56/#59 while any of CT10–CT12 is blocked.
