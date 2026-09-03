# Agent Handoff

Last updated: 2026-09-03

## Current phase

**P3 operational dogfooding + durable evidence + structured curriculum acquisition.**

The current highest-priority incident is now **cross-chat continuity + real GPT capture verification**, not the original 502 localization.

Source-turn persistence exists in the local runtime, but the 2026-09-03 live audit established:

- the real Study OS GPT user/assistant turn path is still not proven end-to-end;
- historical `default` and `subject-001` sessions contain no durable source-turn `messages/raw_artifacts`;
- `resume(subject_id)` remains checkpoint-only and cannot recover evidence-backed context when no accepted checkpoint exists.

## Planning authority

Read in this order:

1. `docs/ROADMAP.md`
2. `docs/CURRENT_STATE.md`
3. latest accepted `docs/DECISIONS.md`
4. Issue #52
5. Issue #56
6. Issue #59
7. task-specific PDD/SDD/TDD below.

Historical issue checklists do not override the current roadmap.

## Current Luna implementation package

Read all of these before changing runtime behavior:

1. `docs/P3_DURABLE_EVIDENCE_CAPTURE_PDD.md`
2. `docs/P3_DURABLE_EVIDENCE_CAPTURE_SDD.md`
3. `docs/P3_SOURCE_TURN_DURABILITY_PDD_DELTA.md`
4. `docs/P3_SOURCE_TURN_DURABILITY_SDD_DELTA.md`
5. `docs/P3_SOURCE_TURN_DURABILITY_TDD_DELTA.md`
6. `docs/P3_CROSS_CHAT_CONTINUITY_PDD.md`
7. `docs/P3_CROSS_CHAT_CONTINUITY_SDD.md`
8. `docs/P3_CROSS_CHAT_CONTINUITY_TDD.md`
9. `docs/LUNA_CROSS_CHAT_CONTINUITY_HANDOFF.md`
10. `docs/ADR-0015-source-turn-capture.md`

## Accepted local audit

Do not reset or recreate learner storage to investigate this incident.

Audited live runtime:

```text
runtime root: /root/.study-os
SQLite: /root/.study-os/db/study-os.sqlite3
private evidence: /root/.study-os/evidence
service source: /mnt/d/Study-os-main
listener: 127.0.0.1:18765
schema: 1
doctor: healthy
```

Incident classification: **B + C**.

### B — real GPT identity/capture not evidenced

No durable source-turn record can currently be attributed to the reported real fresh GPT chat. The actual GPT `subject_id` and runtime binding must be proven.

### C — historical source capture missing

Historical `default` and `subject-001` sessions contain structured events/attempts/checkpoints but zero `messages` and zero transcript `raw_artifacts`.

The only message-backed session is the synthetic source-turn smoke subject. It is verification data, not learner history.

## Current invariant

> A fresh learner-facing Study OS conversation must recover the latest trustworthy learning context available for the same stable learner identity, while transcript/source evidence remains distinct from assessed learner capability.

This extends the existing P3 invariant:

> No silent learner-evidence loss.

## Architecture to protect

```text
RAW / SOURCE EVIDENCE
        ↓
NORMALIZED OPERATIONAL RECORDS
        ↓
DERIVED LEARNER + SYSTEM STATE
```

For continuity:

```text
accepted checkpoint
+
post-checkpoint evidence
        ↓
bounded continuity context
```

or, when no checkpoint exists:

```text
recent durable sessions/messages/events/attempts
        ↓
evidence-only continuity
```

Do not synthesize a checkpoint or mastery claim from transcript text.

## Current implementation direction

Preferred additive semantic operation:

```text
resume_learning_context(subject_id)
```

Keep historical `resume(subject_id)` semantics checkpoint-specific unless a separately approved contract change says otherwise.

Schema v1 should be reused first. No migration unless a failing CT acceptance test proves it insufficient.

## Immediate next work

1. Prove which stable `subject_id` the actual Study OS GPT uses.
2. Prove the actual GPT reaches `/root/.study-os`.
3. Implement CT1–CT9 test-first on disposable data.
4. Add bounded checkpoint-independent continuity.
5. Preserve checkpoint + post-checkpoint evidence as separate semantic classes.
6. Narrow `/actions` exception handling to preserve `StudyOSError` categories.
7. Run full regressions including source-turn ST tests.
8. Run CT10–CT12 with the **actual Study OS GPT**:
   - fresh-chat continuity;
   - real user-turn durable capture;
   - exact displayed assistant-response durable capture.
9. Only after current capture is proven, reconcile historical private transcripts where lossless sources exist.

## CT acceptance

CT1–CT12 are defined in `docs/P3_CROSS_CHAT_CONTINUITY_TDD.md`.

CT10–CT12 cannot be replaced by local curl, synthetic `/actions`, synthetic MCP, or direct service calls.

Do not close #56 or #59 while CT10–CT12 remain blocked.

## Historical reconciliation

Where a private/lossless transcript exists:

```text
private transcript
→ reviewed reconcile_conversation
→ append only genuinely missing source turns
→ preserve reconciliation provenance
```

Do not overwrite existing attempts/events/checkpoints.

Where no source exists, leave the historical source-turn gap explicit. Never invent raw transcript from summaries or memory.

## Runtime ownership

- Canonical live learner state/evidence: local SQLite + private evidence store.
- GPT app: current learner-facing surface.
- GitHub: architecture/spec/contracts/tests/issue lineage and curated public evidence.
- FOSSIL: optional downstream lineage/research promotion; not live per-turn persistence.

## Engineering stance

Protect architecture, data semantics, provenance, persistent contracts, recovery guarantees, and learner/system evidence boundaries.

Implementation code is replaceable. Avoid broad refactors and general hardening unless the current failure model requires them.

## Non-negotiable invariants

- No destructive learner DB/evidence reset as an incident shortcut.
- Stable learner identity must be explicit.
- Raw/private transcript is not committed publicly by default.
- Exact retry must not duplicate durable evidence.
- No acknowledged durable write may disappear after restart.
- Reconciliation ambiguity fails closed.
- Missing turns are recovered only from actual source evidence.
- Transcript/source evidence does not silently become mastery/capability.
- Subject evidence is isolated by subject ownership.
- GitHub/FOSSIL do not become live runtime dependencies.
- Generic SQL/shell/file MCP access remains prohibited.
