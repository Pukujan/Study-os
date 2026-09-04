# Agent Handoff

Last updated: 2026-09-03

## Current phase

**P3 operational dogfooding + historical evidence recovery + structured curriculum acquisition.**

Live capture and cross-chat continuity are now accepted through final verification receipt SHA:

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

The remaining immediate P3.0 task is **historical transcript/source recovery** for learning that occurred before reliable source-turn capture.

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

Cross-chat implementation history remains in Issue #59 and the continuity PDD/SDD/TDD.

## New private recovery source

The learner supplied a ChatGPT Markdown export for historical recovery.

Public-safe source identity:

```text
filename: Study OS Tutor - Check Study OS health.md
conversation_id: 6a8ca3b3-6434-83ea-a807-98080d8bcada
exported_at: 2026-09-04T01:22:07.725Z
reported_turns_captured: 40
reported_completeness: PARTIAL / NOT ESTABLISHED
sha256: 07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d
```

The raw file is private learner evidence and must **not** be committed publicly.

Public-safe manifest:

`sessions/2026-09-03/mcp-recovery-transcript-gap/knowledge/recovery-source-manifest.md`

Exact recovery procedure:

`docs/LUNA_HISTORICAL_TRANSCRIPT_RECOVERY_HANDOFF.md`

## Critical source limitation

Do not call this source a complete transcript yet.

The exporter itself says completeness is `PARTIAL / NOT ESTABLISHED` and that scrolling did not establish a stable turn set.

The Markdown also contains assistant responses that embed prior raw-conversation Markdown. Therefore a naive parser that treats every `## User` / `## Assistant` heading as a source turn will create duplicate/fake historical turns.

Use these distinct statuses:

```text
source_exhausted
= all uniquely recoverable outer turns from this exact source reviewed/imported

conversation_complete
= full original ChatGPT conversation independently proven complete and ordered
```

The second status remains `NOT_ESTABLISHED` unless stronger source evidence proves it.

## Immediate Luna task

1. Receive the exact private Markdown locally from the learner.
2. Verify its SHA-256.
3. Audit the current live DB/evidence counts and run `doctor`.
4. Backup `/root/.study-os` before import.
5. Preserve the original Markdown bytes as immutable private Study OS source evidence.
6. Reconstruct only real outer ChatGPT turns; ignore nested transcript copies inside assistant content.
7. Resolve chronology/session assignment conservatively; ambiguity stays unresolved rather than guessed.
8. Convert reviewed segments to the existing reconciliation JSON shape.
9. Reconcile only genuinely missing turns into `subject-001` historical sessions.
10. Rerun reconciliation and prove zero additional writes.
11. Verify attempts/events/checkpoints were not overwritten.
12. Verify message/artifact hashes, provenance, doctor, restart, and backup/restore.
13. After raw recovery is stable, create reviewed source-linked live-learning events/episodes for high-value historical learning observations.
14. Report `source_exhausted` separately from `conversation_complete`.

## Candidate high-value live-learning episodes

The supplied source contains evidence around:

- LeetCode Two Sum representation translation overhead;
- `enumerate` vs index-first authored code during acquisition;
- semantic interference from the variable name `seen`;
- continued confusion with `index_by_num`;
- improved immediate clarity using neutral `box` terminology;
- correct immediate dictionary lookup after the representation change;
- learner recognition that variable naming/author language can create extraneous difficulty;
- learner recognition that append-only transcript capture is needed for outage resilience.

Treat these as candidate observed/self-reported findings, not mastery/transfer/retention claims.

All reviewed operational records must link back to recovered source IDs.

## Architecture to protect

```text
RAW / SOURCE EVIDENCE
        ↓
NORMALIZED OPERATIONAL RECORDS
        ↓
DERIVED LEARNER + SYSTEM STATE
```

Original private source bytes survive parser/normalization failure.

Transcript/source evidence never silently becomes mastery or capability.

## Runtime ownership

- Canonical live learner state/evidence: local SQLite + private evidence store.
- GPT app: current learner-facing surface.
- GitHub: architecture/spec/contracts/tests/issue lineage and public-safe recovery manifests only.
- FOSSIL: optional downstream lineage/research promotion; not live learner persistence.

## Non-negotiable invariants

- No destructive DB/evidence reset.
- No public raw learner transcript.
- No invented missing turns.
- No naive nested-heading parsing.
- Reconciliation ambiguity fails closed.
- Exact retry/reconciliation rerun does not duplicate evidence.
- Existing structured historical evidence is not overwritten.
- Stable learner identity remains explicit.
- Raw/private evidence retains immutable provenance and hashes.
- Derived learner/system state cites source evidence.
- Generic SQL/shell/file MCP access remains prohibited.
