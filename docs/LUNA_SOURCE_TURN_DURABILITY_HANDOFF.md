# Luna Local Handoff — P3.0 Source-Turn Durability

Date: 2026-09-03

Focused issue: #56

Parent tracker: #52

## Mission

Implement the missing append-only learner-facing source-turn capability in the local Study OS runtime so GPT learning can continue without silently losing the conversation evidence needed for later reconstruction.

Primary invariant:

> Every learner-facing turn is either durably captured as Study OS source evidence or explicitly remains reconciliation-required.

This is not a generic transcript feature and not a FOSSIL runtime task. It is a repair of an existing Study OS architecture gap.

## Read first

Read in this order:

1. `AGENTS.md`
2. `docs/HANDOFF.md`
3. `docs/P3_DURABLE_EVIDENCE_CAPTURE_PDD.md`
4. `docs/P3_DURABLE_EVIDENCE_CAPTURE_SDD.md`
5. `docs/P3_DURABLE_EVIDENCE_CAPTURE_TDD.md`
6. `docs/P3_SOURCE_TURN_DURABILITY_PDD_DELTA.md`
7. `docs/P3_SOURCE_TURN_DURABILITY_SDD_DELTA.md`
8. `docs/P3_SOURCE_TURN_DURABILITY_TDD_DELTA.md`
9. `docs/ADR-0015-source-turn-capture.md`
10. `docs/FOSSIL_INTEGRATION.md`
11. `docs/DATABASE_CONTRACT.md`
12. `docs/LOCAL_RUNTIME_ARCHITECTURE.md`
13. `src/study_os/db/migrations/0001_initial.sql`
14. `src/study_os/evidence/store.py`
15. `src/study_os/services/runtime_base.py`
16. current MCP/application contracts and tests
17. Issue #56 and its latest comments

## Important repository finding

Do **not** begin by designing a new transcript database.

Schema v1 already has:

```text
raw_artifacts
messages
idempotency_records
```

and the runtime already has `EvidenceStore` plus `capture_evidence`.

The gap is that these pieces are not wired into a retry-safe semantic message/source-turn operation accessible to the GPT.

Preferred MVP:

```text
append_conversation_turn
  -> EvidenceStore exact bytes
  -> raw_artifacts
  -> messages
  -> idempotency_records
```

Default migration decision: **none**.

If you believe a migration is required, first write a failing test proving which invariant schema v1 cannot represent and explain that in the PR.

## Required semantic operation

Preferred name:

`append_conversation_turn`

Required semantics are in the SDD delta.

At minimum it must accept:

```text
idempotency_key
session_id
subject_id
role
content
```

and optional source provenance.

It must return stable message/artifact/hash identity after commit.

## MCP contract change is authorized narrowly

The current exact-13-tool v0.1 surface is not sufficient for canonical source-turn capture.

For this issue only, ADR-0015 authorizes one bounded semantic addition.

Expected direction:

```text
MCP v0.1 = historical exact 13 tools
MCP v0.2 = current exact 14 tools
              + append_conversation_turn
```

Preserve the existing 13 semantics exactly.

Do not add generic file, SQL, shell, arbitrary transcript read/write, or admin tools.

If repository contract conventions require a different version-file strategy, preserve the semantic versioning intent and document it.

## Test-first sequence

Implement against `docs/P3_SOURCE_TURN_DURABILITY_TDD_DELTA.md`.

Start with ST1-ST10 before touching GPT integration.

Minimum early red tests should prove:

1. user turn creates one `messages` + `raw_artifacts` occurrence;
2. assistant turn does the same;
3. exact retry creates no duplicate;
4. conflicting retry fails;
5. identical text with different logical turn identities remains two occurrences;
6. source metadata is preserved but never invented;
7. source time != local capture time;
8. source evidence survives semantic-processing failure;
9. pre-commit failure does not false-ack;
10. post-commit response loss resolves original result.

Then implement application/MCP conformance, reconciliation, doctor, backup/restore, and end-to-end smoke.

## Filesystem/SQLite crash boundary

`EvidenceStore.capture` writes the file before the surrounding SQLite transaction commits.

For ordinary exceptions, preserve/use the existing compensation behavior so uncommitted files are removed where safe.

A hard process crash can leave an orphan evidence file before SQLite commit. That orphan is **not canonical message evidence**.

Required behavior:

- no success ACK without DB commit;
- retry may create the one canonical message;
- do not adopt an orphan silently unless you implement and test a deterministic verified recovery rule;
- report orphan files through `doctor` if reliable detection is implemented.

Do not complicate the MVP solely to eliminate harmless unacknowledged orphan bytes unless the tests or real runtime show they create a material risk.

## Reconciliation

Use a local/reviewed path first.

Do not add a second GPT-facing reconciliation MCP tool unless a new reviewed decision authorizes it.

The reconciliation path must:

- preserve/hash its source transcript/export artifact;
- enumerate existing local messages;
- match strongest identity first;
- append only genuinely missing turns using the same source-turn data model;
- set live vs reconciliation origin distinctly;
- retain source time separately from recovery time;
- be idempotent on rerun;
- fail closed on ambiguity.

Use synthetic fixtures in committed tests.

## GPT integration behavior

Once the new MCP capability is deployed and lower layers pass:

```text
user turn arrives
  -> append user turn
  -> tutor reasons
  -> compose response
  -> append assistant response
  -> emit same response
```

If append is unavailable:

- do not claim the turn was persisted;
- do not block the learner indefinitely;
- allow response to continue;
- treat the conversation window as reconciliation-required.

If the ChatGPT integration cannot call the new tool at all, stop and report that exact integration blocker after proving the local/application/MCP operation itself.

## Required real smoke

After synthetic tests and backup/restore pass:

1. verify real Study OS service + transport health;
2. make one small non-sensitive learner message in the GPT;
3. verify a canonical user `messages` row + raw artifact locally;
4. let GPT answer;
5. verify a canonical assistant `messages` row + raw artifact locally;
6. verify hashes;
7. run `doctor`;
8. report sanitized IDs/status only.

This is the first end-to-end proof that the transcript substrate actually works.

## Historical outage recovery

Do not automatically rewrite old sessions after live capture works.

Use actual preserved transcript/export evidence for each known gap.

The 2026-09-03 MCP recovery discovery is evidence of the gap, not itself a complete private transcript artifact in GitHub.

## Implementation PR requirements

Open one focused PR referencing #56 and #52.

Include:

### Architecture receipt

```text
schema migration: none | <version + reason>
application operation: <name>
MCP contract: <version>
semantic tool count: <count>
reconciliation surface: <local command/service>
raw content storage: <existing EvidenceStore path semantics>
```

### ST1-ST22 receipt

For every source-turn TDD test:

```text
PASS
NOT APPLICABLE + exact reason
BLOCKED + evidence
```

### Original P3 receipt

Report applicable parent T1-T14 status.

### Verification

- exact head SHA;
- exact commands;
- pass/fail totals;
- migration status;
- restart proof;
- backup/restore proof;
- MCP conformance result;
- real GPT two-turn smoke result;
- known unresolved reconciliation gaps.

## Stop conditions

Stop and report instead of improvising if:

- valuable local data needs destructive migration without verified backup;
- current local schema differs from repository main materially;
- the GPT platform cannot invoke the new semantic tool;
- safe private raw storage cannot be maintained;
- reconciliation is ambiguous;
- a proposed implementation stores summaries instead of raw source turns;
- fixing capture would require FOSSIL as a live dependency;
- a generic file/SQL/admin surface seems necessary.

## Definition of done

Issue #56 is fixed only when the actual Study OS GPT path proves that one user turn and one assistant turn are durably represented by canonical local `messages` + `raw_artifacts`, exact retry is safe, failure/reconciliation behavior is tested, and backup/restore preserves the resulting transcript substrate.
