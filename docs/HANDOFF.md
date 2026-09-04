# Agent Handoff

Last updated: 2026-09-03

## Current phase

**P3 operational dogfooding + historical evidence recovery + structured curriculum acquisition.**

Live source-turn capture and cross-chat continuity are accepted through final verification receipt SHA:

```text
90fe4733a621ff7286fc88b26ba8d48e1ee73ed6
```

Accepted live state:

- stable learner identity: `subject-001`;
- live runtime root: `/root/.study-os`;
- real GPT user turns durably captured;
- exact displayed assistant turns durably captured;
- `resume_learning_context(subject_id)` returns checkpoint + recent evidence;
- CT1–CT12 passed;
- full suite passed at 265 tests;
- doctor/hash integrity and backup/restore passed;
- no schema migration.

The immediate P3.0 task is now **historical transcript/source recovery** for learning that occurred before reliable source-turn capture.

## Planning authority

Read in this order:

1. `docs/ROADMAP.md`
2. `docs/CURRENT_STATE.md`
3. latest accepted `docs/DECISIONS.md`
4. Issue #52
5. Issue #56
6. `docs/P3_DURABLE_EVIDENCE_CAPTURE_PDD.md`
7. `docs/P3_DURABLE_EVIDENCE_CAPTURE_SDD.md`
8. `docs/P3_SOURCE_TURN_DURABILITY_PDD_DELTA.md`
9. `docs/P3_SOURCE_TURN_DURABILITY_SDD_DELTA.md`
10. `docs/LUNA_HISTORICAL_TRANSCRIPT_RECOVERY_HANDOFF.md`

## User-authorized historical recovery source

The learner explicitly authorized public GitHub publication of one specific ChatGPT Markdown export so local Luna can pull it without a separate file transfer.

Source directory:

```text
sessions/2026-09-03/mcp-recovery-transcript-gap/raw/public-export/
  chatgpt-6a8ca3b3-6434-83ea-a807-98080d8bcada/
```

Read its `README.md` before use.

Source identity:

```text
filename: Study OS Tutor - Check Study OS health.md
conversation_id: 6a8ca3b3-6434-83ea-a807-98080d8bcada
exported_at: 2026-09-04T01:22:07.725Z
reported_turns_captured: 40
reported_completeness: PARTIAL / NOT ESTABLISHED
original_size_bytes: 30104
original_sha256: 07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d
```

The exact source is losslessly represented as a four-part deterministic gzip/base64 transport archive. Luna must reconstruct it and verify the original SHA-256 before importing anything.

This publication authorization applies only to this source. Other raw learner evidence remains private by default.

## Critical source limitation

Do **not** call this export a complete original conversation.

Its own metadata says `PARTIAL / NOT ESTABLISHED` and warns that scrolling did not establish a stable turn set.

It also contains assistant responses that embed earlier raw-conversation Markdown. A parser that treats every `## User` / `## Assistant` heading as an outer turn will double-count/fabricate history.

Use separate statuses:

```text
source_exhausted
= all uniquely recoverable outer evidence from this exact export reviewed/imported

conversation_complete
= full original ChatGPT conversation independently proven complete and ordered
```

## Immediate Luna task

1. Pull latest `main`.
2. Reconstruct the exact Markdown from the published archive and verify SHA-256.
3. Confirm `/root/.study-os` and `subject-001`.
4. Run `doctor`, capture pre-import counts, and create a full backup.
5. Preserve the reconstructed exact Markdown bytes in the local Study OS immutable evidence store.
6. Reconstruct only reviewed real outer ChatGPT turns; nested transcript copies stay inside their containing assistant messages.
7. Map reviewed ranges to historical Study OS sessions only where supported; ambiguity remains unresolved.
8. Reconcile only genuinely missing turns.
9. Rerun identical reconciliation and prove zero additional writes.
10. Verify existing attempts/events/checkpoints/current-pointer and live post-fix messages were not overwritten.
11. Verify message/artifact hashes, `doctor`, restart, and backup/restore.
12. Only after raw recovery is stable, create reviewed source-linked operational learning events/episodes.
13. Report `source_exhausted` separately from `conversation_complete`.

The exact procedure and completion receipt are in `docs/LUNA_HISTORICAL_TRANSCRIPT_RECOVERY_HANDOFF.md`.

## High-value historical learning evidence

The source contains candidate evidence around:

- LeetCode Two Sum representation translation overhead;
- `enumerate` vs index-first authored code during acquisition;
- semantic interference from the variable name `seen`;
- continued confusion with `index_by_num`;
- improved immediate clarity using neutral `box` terminology;
- correct immediate dictionary lookup after that representation change;
- learner identification of variable naming/author language as avoidable concept difficulty;
- learner identification of append-only transcript capture as an outage-resilience requirement.

These are candidate observed/self-reported/derived findings, not mastery, transfer, or retention claims. Every reviewed operational record must cite recovered source IDs.

## Architecture to protect

```text
RAW / SOURCE EVIDENCE
        ↓
NORMALIZED OPERATIONAL RECORDS
        ↓
DERIVED LEARNER + SYSTEM STATE
```

The published archive is recovery transport, not the canonical live learner store. After reconstruction, canonical learner evidence remains local SQLite + private Study OS evidence.

## Runtime ownership

- Canonical live learner state/evidence: local SQLite + private evidence store.
- GPT app: current learner-facing surface.
- GitHub: source/spec/history plus this explicitly user-authorized recovery archive.
- FOSSIL: optional downstream lineage/research promotion; not live learner persistence.

## Non-negotiable invariants

- No destructive DB/evidence reset.
- No invented missing turns.
- No naive nested-heading parsing.
- Reconciliation ambiguity fails closed.
- Repeated reconciliation does not duplicate evidence.
- Existing structured historical evidence is not overwritten.
- Stable learner identity remains explicit.
- Raw/source evidence retains immutable provenance and hashes.
- Transcript evidence never silently becomes mastery/capability.
- Generic SQL/shell/file MCP access remains prohibited.
