# P3.0 Source-Turn Durability — TDD Delta

Status: accepted implementation specification once merged

Parent tracker: #52

Focused issue: #56

Extends: `docs/P3_DURABLE_EVIDENCE_CAPTURE_TDD.md`

Companion deltas:

- `docs/P3_SOURCE_TURN_DURABILITY_PDD_DELTA.md`
- `docs/P3_SOURCE_TURN_DURABILITY_SDD_DELTA.md`

Primary implementer: local Luna / WSL coding agent

Date: 2026-09-03

## 1. Purpose

This delta turns the newly discovered append-only transcript/source-turn gap into executable acceptance tests.

The original P3 T1-T14 tests remain required where applicable. This document adds the source-turn-specific tests Luna must make green before Issue #56 is considered fixed.

The implementation target is the existing architecture:

```text
EvidenceStore
+ raw_artifacts
+ messages
+ idempotency_records
```

Do not start by creating a new transcript database.

## 2. Test-first implementation order

Use this order:

```text
inspect current local schema/data
    ↓
write source-turn tests against current repository architecture
    ↓
prove existing schema is sufficient or demonstrate why it is not
    ↓
implement append_conversation_turn
    ↓
application contract
    ↓
MCP projection/versioned contract
    ↓
reconciliation
    ↓
doctor + backup/restore
    ↓
synthetic MCP smoke
    ↓
real GPT two-turn smoke
```

A migration is not the default. If a migration is introduced, first add a failing test that proves a required invariant cannot be safely represented with schema v1.

## 3. Required source-turn tests

### ST1 — append user turn creates one canonical message occurrence

**Given** an active synthetic session.

**When** `append_conversation_turn` is called for a user turn.

**Then**:

- one `messages` row exists;
- one referenced `raw_artifacts` row exists;
- the private evidence file exists;
- `messages.content_sha256` equals the raw artifact SHA-256;
- the artifact bytes equal UTF-8 encoding of the exact supplied content;
- result returns stable `message_id`, `artifact_id`, hash, and capture origin;
- no learning event/attempt/mastery state is required for the append to succeed.

### ST2 — append assistant turn is equivalent source evidence

Repeat ST1 with `role = assistant`.

The assistant turn must not be treated as derived state merely because the tutor generated it.

### ST3 — exact retry does not create another occurrence

**Given** a committed append for idempotency key `K`.

**When** the exact same request is repeated with `K`.

**Then**:

- the same `message_id` and `artifact_id` are returned;
- exactly one canonical `messages` row exists for that request;
- exactly one canonical `raw_artifacts` row is referenced by that message;
- no second message occurrence is created.

This is the source-turn specialization of parent T1.

### ST4 — conflicting idempotency reuse fails closed

**Given** key `K` committed for content/hash `A`.

**When** `K` is reused with changed content, role, session, or other fingerprinted identity field.

**Then**:

- canonical conflict is returned;
- original message/artifact remain unchanged;
- no second canonical message is created.

### ST5 — repeated identical text with a new logical identity is allowed

**Given** two genuine separate user occurrences whose text is identical.

**When** they use distinct idempotency keys.

**Then**:

- two message occurrences exist;
- they have distinct local `message_id` values;
- implementation may reuse identical immutable bytes internally only if occurrence identity/provenance remains separate.

This prevents accidental content-hash deduplication from deleting real conversation chronology.

### ST6 — source metadata remains provenance, not invented identity

Test both:

1. a turn with source conversation/message/timestamp/sequence metadata;
2. a turn where those fields are absent.

Expected:

- supplied metadata round-trips through message metadata;
- absent values remain absent/null;
- no synthetic ChatGPT message ID or source timestamp is invented.

### ST7 — source time and local capture time remain distinct

Append a turn with an old synthetic `source_timestamp`.

Expected:

- source timestamp remains in metadata;
- message `created_at`/local capture time reflects actual local capture;
- they are not overwritten to equal one another.

### ST8 — raw source survives downstream semantic failure

**Given** ST1 source capture succeeds.

**When** a deliberately injected normalization/learning-event/derived-processing step fails afterward.

**Then**:

- `messages` row remains;
- `raw_artifacts` row/file remain;
- hash still verifies;
- no fabricated downstream record is created;
- later reprocessing can reference the same source message/artifact.

This is the source-turn specialization of parent T6.

### ST9 — failure before DB commit does not false-ack

Inject failure after request receipt and, where practical, after evidence-file creation but before SQLite commit.

Expected:

- no durable-success result;
- no canonical `messages` row;
- no canonical `raw_artifacts` row from the failed transaction;
- exact retry can create one canonical message successfully;
- any filesystem orphan caused by process-crash simulation is not treated as committed evidence.

If ordinary exception compensation removes the uncommitted file, assert that behavior.

### ST10 — post-commit response loss resolves original append

Inject failure after transaction commit but before the caller receives the result.

Expected:

- canonical message/artifact/idempotency result exist exactly once;
- caller may observe unknown/transport failure;
- retry same key/fingerprint returns original message/artifact result;
- no duplicate occurrence.

This is the critical append-turn form of parent T3.

### ST11 — process restart preserves appended turns

Append at least one user and one assistant turn.

Restart/recreate the Study OS runtime against the same root.

Expected:

- message/artifact links survive;
- hashes verify;
- exact append retry still resolves original result;
- session chronology remains queryable by supported internal/local diagnostics.

### ST12 — application contract is strict

Add canonical `AppendConversationTurnRequest` / `AppendConversationTurnResult` or equivalent.

Test:

- required fields;
- role validation;
- non-empty content;
- optional source metadata;
- unknown/application-version fields rejected according to existing conventions;
- runtime result malformed -> application boundary fails closed;
- no raw private content appears in error strings unless explicitly required for a local-only diagnostic.

### ST13 — MCP contract is versioned and exactly bounded

If the operation is GPT-facing as specified:

- preserve the old v0.1 contract as historical compatibility evidence where repository conventions allow;
- publish/update the current contract as v0.2.0 or equivalent minor-version addition;
- current semantic tool count becomes exactly 14;
- the only added semantic tool is the bounded source-turn append operation;
- all previous 13 tool names/required semantics remain unchanged;
- generic SQL/shell/file-write tools remain absent.

Existing exact-13 tests must be updated intentionally, not bypassed.

### ST14 — MCP append projection matches direct application/runtime behavior

Using synthetic content, compare:

```text
direct runtime append
application service append
MCP append
```

for equivalent request semantics.

Expected:

- same validation/error categories;
- same durable result fields/projection where contract requires;
- equivalent idempotency behavior;
- no transport-specific mutation semantics.

### ST15 — reviewed backfill adds one genuinely missing turn

Create a synthetic private-safe transcript/source artifact containing a turn absent from local message history.

Run the reviewed reconciliation path.

Expected:

- source artifact is hash-preserved;
- one missing message is appended;
- `capture_origin = reconciliation`;
- source conversation/message/timestamp/order metadata are retained only when supported by the source;
- local recovery time is current local time;
- no existing live message is rewritten.

### ST16 — reconciliation rerun is idempotent

Run ST15 again with the same source.

Expected:

- zero additional message occurrences;
- outcome is `already_present_exact` or canonical equivalent.

### ST17 — ambiguous reconciliation refuses automatic merge

Create a fixture with insufficient metadata and multiple plausible local matches.

Expected:

- no automatic merge/backfill linkage decision is made;
- result is explicit ambiguity/review-required;
- all source and local evidence remain intact.

### ST18 — backfill chronology preserves two clocks

Backfill a turn whose source timestamp predates the local recovery time.

Expected:

- source chronology metadata remains source chronology;
- `messages.created_at` remains actual local recovery/commit time;
- ordering/reporting code can distinguish the two facts.

### ST19 — `doctor` verifies message/artifact integrity

Create valid and invalid synthetic states.

At minimum test detection of:

- message referencing missing artifact row/file;
- content hash mismatch;
- invalid/conflicting append idempotency state where observable;
- ambiguous/unresolved reconciliation status where implemented;
- orphan evidence file if Luna implements reliable orphan detection.

`doctor` must not mutate the history to make the check pass.

### ST20 — backup/restore preserves transcript substrate

Append user + assistant turns, plus one reconciled turn.

Backup, restore into disposable state, and verify:

- message IDs preserved;
- artifact IDs/paths/hashes preserved;
- evidence bytes verify;
- live vs reconciliation origin preserved;
- source metadata preserved;
- exact append retry remains idempotent;
- `doctor` produces equivalent health/attention state.

### ST21 — privacy/public-boundary regression

Repository fixtures and test output must use synthetic content only.

Assert/document that:

- no real learner transcript is committed;
- no tunnel credentials are logged;
- no raw turn content appears in normal public CI logs unless the synthetic fixture intentionally tests it;
- hashes/IDs/status categories are preferred in diagnostics.

### ST22 — real GPT two-turn smoke

Only after all lower-layer tests pass:

1. start the real local Study OS service/transport;
2. use the GPT app for one small non-sensitive learner turn;
3. verify that user turn is appended durably;
4. verify that the assistant reply is appended durably;
5. verify both raw artifacts/hash links locally;
6. run `doctor`;
7. retry one append identity only in a controlled way if needed to confirm idempotency.

The PR must record sanitized evidence that two distinct learner-facing turns became two canonical message occurrences.

If the ChatGPT/app platform cannot invoke the new tool, record that as an integration blocker rather than pretending the end-to-end requirement passed.

## 4. Reconciliation fixture guidance

Do not use real private conversation text in committed tests.

A safe fixture can look like:

```json
{
  "conversation_id": "synthetic-source-turns-001",
  "turns": [
    {
      "source_message_id": "m1",
      "role": "user",
      "content": "What does cache[7] return?",
      "source_timestamp": "2026-09-03T12:00:00Z"
    },
    {
      "source_message_id": "m2",
      "role": "assistant",
      "content": "It returns the value stored under key 7.",
      "source_timestamp": "2026-09-03T12:00:02Z"
    }
  ]
}
```

Also include:

- a no-source-ID fixture for hash/chronology matching;
- a deliberately ambiguous fixture;
- a repeated-identical-text fixture to protect occurrence identity.

## 5. Preferred test locations

Use existing conventions.

Likely focused homes:

```text
tests/test_p3_source_turn_durability.py
tests/test_application_*append_conversation_turn*_conformance.py
existing MCP contract/runtime tests
```

If Luna finds a cleaner existing test module, reuse it rather than multiplying files.

## 6. Required regression suite

In addition to ST1-ST22, run all applicable original P3 T1-T14 coverage and the repository's existing tests protecting:

- schema migration;
- raw evidence immutability/hash verification;
- idempotency conflicts;
- learning-event evidence resolution;
- checkpoint atomicity/current pointer;
- backup/restore;
- MCP application-boundary conformance;
- representation/assessment provenance;
- resume;
- DB busy/unavailable errors;
- public semantic tool restrictions.

## 7. Migration gate

The default PR declaration should be:

`migration: none`

unless Luna has a red test proving schema v1 cannot safely represent a required source-turn invariant.

If a migration is required, add tests for:

- migration from actual current local schema;
- existing sessions/raw_artifacts/messages preservation;
- repeat-safe migration;
- rollback/failure behavior;
- backup before valuable-local-data migration;
- restore compatibility.

## 8. Implementation PR receipt

The Luna implementation PR must reference #56 and report:

### Architecture

- existing tables reused;
- migration: none/version;
- current MCP contract version/tool count;
- application operation name;
- reconciliation surface;
- any intentionally deferred source metadata.

### Test matrix

Report ST1-ST22 as:

- PASS;
- NOT APPLICABLE + architecture reason;
- BLOCKED + evidence.

Also report applicable original T1-T14.

### Exact verification

- tested head SHA;
- exact commands;
- pass/fail counts;
- disposable restart result;
- backup/restore result;
- synthetic MCP smoke;
- real GPT two-turn smoke;
- any historical outage gaps still unreconciled.

## 9. Definition of done

Issue #56 is ready for review only when:

- source turns are durable independently of semantic events;
- exact retry cannot duplicate them;
- conflicting retry cannot mutate them;
- post-commit response loss resolves correctly;
- source evidence survives semantic-processing failure;
- user and assistant turns survive restart;
- one reviewed missing turn can be backfilled idempotently;
- ambiguous backfill refuses to guess;
- backup/restore preserves the transcript substrate;
- the MCP/application surface is narrowly versioned rather than generically expanded;
- one actual GPT exchange is proven in local canonical `messages` + `raw_artifacts` evidence.
