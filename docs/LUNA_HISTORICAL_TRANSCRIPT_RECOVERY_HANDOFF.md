# Luna Historical Transcript Recovery Handoff

Date: 2026-09-03  
Parent: #52  
Related: #56, #59

## Current state

Live GPT capture and cross-chat continuity are accepted on `main` through final receipt SHA `90fe4733a621ff7286fc88b26ba8d48e1ee73ed6`.

The remaining P3.0 evidence gap is historical: older Study OS learning occurred while source-turn capture was unavailable/502ing. Structured attempts/events/checkpoints exist, but the historical transcript/source turns are missing from canonical `messages + raw_artifacts`.

## New private recovery source supplied by the learner

The learner supplied a Markdown export in ChatGPT named:

```text
Study OS Tutor - Check Study OS health.md
```

Public-safe fingerprint/metadata only:

```text
conversation_id: 6a8ca3b3-6434-83ea-a807-98080d8bcada
exported_at: 2026-09-04T01:22:07.725Z
reported_turns_captured: 40
exporter_completeness: PARTIAL / NOT ESTABLISHED
sha256: 07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d
```

The raw Markdown is private learner evidence. **Do not commit it to GitHub, issues, logs, fixtures, or public CI artifacts.**

Luna must receive the exact local file from the learner and verify the SHA-256 above before using it.

## Critical parsing warning

Do **not** parse every Markdown `## User` / `## Assistant` heading as a source turn.

The export contains assistant messages that themselves embed earlier raw-conversation Markdown. Therefore headings occur inside quoted/fenced assistant content and would create duplicate fake turns under a naive parser.

The exporter also explicitly reports that repeated scroll sweeps did not establish a stable turn set. Treat the file as a **candidate recovery source**, not proof that the underlying ChatGPT conversation is complete or perfectly ordered.

Terminology:

- `source_exhausted`: every uniquely recoverable outer turn from this exact file has been reviewed/imported;
- `conversation_complete`: the full original ChatGPT conversation is proven complete and ordered.

Do not set or claim `conversation_complete=true` from this source alone unless an independent/lossless source establishes it.

## Objective

Recover as much historical learner evidence as this private source actually supports while preserving uncertainty and all existing live Study OS data.

Required hierarchy:

```text
original private Markdown bytes
        ↓
reviewed outer-turn reconstruction
        ↓
Study OS reconciliation source artifact
        ↓
missing messages + raw_artifacts
        ↓
reviewed learning events/episodes
        ↓
derived learner/system state only where separately justified
```

## Phase 0 — preserve and audit before mutation

1. Pull latest `main`.
2. Confirm live root remains `/root/.study-os` and stable learner identity remains `subject-001`.
3. Run `doctor` and record counts by subject/session.
4. Create a full Study OS backup before historical import.
5. Copy the supplied Markdown into a private local staging location outside the public repository.
6. Verify SHA-256 exactly:

```text
07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d
```

If the hash differs, stop and report the new artifact as a separate source version rather than silently substituting it.

## Phase 1 — preserve the original source bytes privately

The original Markdown bytes are themselves evidence and must survive normalization failure.

Before deriving normalized turns, store the exact source privately in Study OS evidence with provenance including at minimum:

```text
source_client: chatgpt
source_conversation_ref: 6a8ca3b3-6434-83ea-a807-98080d8bcada
source_filename: Study OS Tutor - Check Study OS health.md
source_sha256: 07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d
exported_at: 2026-09-04T01:22:07.725Z
source_completeness_claim: partial_not_established
capture_origin: historical_recovery_source
```

Do not rewrite this artifact when parser logic changes. Normalized/reviewed outputs are rebuildable; original bytes are not.

If the current runtime has no clean semantic operation for preserving this Markdown as a raw recovery source before JSON reconciliation, use the smallest architecture-compatible local service path. Do not add generic file/SQL MCP access.

## Phase 2 — reconstruct only the real outer conversation turns

Build the reviewed reconciliation input from the outer ChatGPT conversation, not from headings embedded inside assistant-authored Markdown/code fences.

Requirements:

1. Markdown-aware/fence-aware extraction or manual review; no heading-regex-only parser.
2. Preserve exact outer user/assistant content bytes as represented by the source.
3. Detect and mark repeated/nested historical transcript copies as assistant content, not new turns.
4. Do not invent missing turns.
5. Do not invent timestamps/message IDs unavailable from the source.
6. Do not assert sequence/order where exporter instability leaves it unresolved.
7. Where chronology can be established, give each reviewed outer turn a deterministic recovery identity tied to this source artifact and reviewed ordinal.
8. Produce an explicit review table:

```text
candidate_outer_turns
accepted_outer_turns
nested_copy_blocks_ignored
exact_duplicate_candidates
ordering_ambiguities
missing/uncertain_regions
rejected_invalid_regions
```

No live DB import until `ordering_ambiguities` that affect target ordering/session assignment are either resolved or explicitly kept out of the import.

## Phase 3 — map to historical Study OS sessions conservatively

The transcript appears to cover learning around Python/DSA, LeetCode Two Sum, dictionaries, `enumerate`, and representation/naming interventions.

Use existing checkpoint/event/attempt timestamps and content provenance to map reviewed turn ranges to existing historical `subject-001` sessions where supported.

Rules:

- never move/rewrite existing attempts/events/checkpoints;
- never create a false historical session boundary merely to force completeness;
- if one turn/range cannot be assigned to an existing session with sufficient confidence, keep it source-only/unresolved and report it;
- if a dedicated recovery session is needed for truly unassignable source evidence, propose that explicitly before creating it and preserve `capture_origin=reconciliation`.

## Phase 4 — reconcile missing source turns

Convert each reviewed/session-mapped segment to the existing private UTF-8 JSON reconciliation shape and run the existing `reconcile` path.

Expected turn semantics:

```text
role: user | assistant
content: exact reviewed outer-turn content
source_conversation_ref: 6a8ca3b3-6434-83ea-a807-98080d8bcada
capture_origin: reconciliation
```

Use source message IDs/timestamps only when actually supported.

For each target segment report:

```text
already_present_exact
backfilled_missing
ambiguous_review_required
rejected_invalid_source
```

Ambiguity must fail closed.

Then rerun the exact same reconciliation. Second run must create zero additional turns.

## Phase 5 — prove no existing learner data was damaged

After reconciliation verify:

- historical attempts unchanged;
- historical learning events unchanged;
- historical checkpoints/current-pointer unchanged unless a separately approved derived-state operation intentionally updates them;
- live post-fix messages remain unchanged;
- new historical messages are backed by private raw artifacts;
- message hashes == artifact hashes == on-disk bytes;
- reconciliation provenance is preserved;
- `doctor` is healthy;
- backup/restore preserves the recovered evidence;
- repeated reconciliation is idempotent.

## Phase 6 — save the recovered material as live-learning data

Only after raw/source recovery is stable, create reviewed operational learning evidence from the recovered turns.

Candidate high-value episodes already visible in the source include:

- source/author representation caused translation overhead during LeetCode Two Sum decoding;
- `seen` created semantic interference because the learner associated that name with sets;
- `index_by_num` remained confusing;
- neutral `box` representation was clearer;
- after the representation change, the learner correctly retrieved the value stored under key `7`;
- the learner explicitly identified variable naming/author language as unnecessary concept difficulty;
- the learner identified append-only transcript durability as a system requirement after 502 losses.

Treat these as **candidate observed/self-reported episodes**, not mastery claims.

For every new event/episode:

```text
evidence_class: observed | self_reported | derived
source_ids: recovered message/raw-artifact IDs
capture_origin: historical_reconciliation
```

Do not turn transcript content into capability/mastery without separate assessment evidence.

## Completion criteria

Luna returns a private/public-safe receipt containing:

```text
source SHA verified: yes/no
backup before import: path/id + PASS
source bytes preserved privately: artifact id + hash
candidate outer turns: N
accepted reviewed outer turns: N
nested/embedded duplicate blocks ignored: N
ordering ambiguities unresolved: N
session mapping unresolved: N

per historical session:
  messages before -> after
  raw_artifacts before -> after
  already_present_exact
  backfilled_missing
  ambiguous_review_required
  rejected_invalid_source

second reconciliation added: 0
existing attempts unchanged: PASS/FAIL
existing events unchanged before reviewed Phase 6: PASS/FAIL
existing checkpoints unchanged: PASS/FAIL
doctor: PASS/FAIL
hash/link integrity: PASS/FAIL
backup/restore: PASS/FAIL

reviewed live-learning episodes created: N
all new derived/operational records cite recovered source IDs: PASS/FAIL

source_exhausted: yes/no
conversation_complete: yes/no/NOT_ESTABLISHED
remaining known gaps
final code SHA if code changed
```

## Do not

- do not commit the raw Markdown publicly;
- do not call this source complete because the filename/export looks complete;
- do not parse nested transcript copies as separate turns;
- do not infer missing user/assistant text from summaries;
- do not overwrite structured historical evidence;
- do not force ambiguous turns into arbitrary sessions;
- do not promote transcript text to mastery;
- do not make FOSSIL or GitHub the live learner-data store.
