# Luna Historical Transcript Recovery Handoff

Date: 2026-09-03  
Parent: #52  
Related: #56, #59

## Current accepted state

Live source-turn capture and cross-chat continuity are accepted. The remaining P3.0 durability gap is historical recovery: older learner conversations occurred before reliable source-turn capture, so historical structured attempts/events/checkpoints may exist without canonical transcript `messages + raw_artifacts`.

Live authority remains:

```text
runtime root: /root/.study-os
SQLite: /root/.study-os/db/study-os.sqlite3
private evidence: /root/.study-os/evidence
stable learner subject: subject-001
```

Do not reset, recreate, or destructively migrate learner storage as part of recovery.

## Recovery source is now available directly in GitHub

The learner explicitly authorized public publication of the supplied ChatGPT Markdown export so Luna can pull it directly.

Source directory:

```text
sessions/2026-09-03/mcp-recovery-transcript-gap/raw/public-export/
  chatgpt-6a8ca3b3-6434-83ea-a807-98080d8bcada/
```

Read that directory's `README.md` and reconstruct the exact Markdown from:

```text
transcript.md.gz.b64.part01
transcript.md.gz.b64.part02
transcript.md.gz.b64.part03
transcript.md.gz.b64.part04
```

Required source identity:

```text
conversation_id: 6a8ca3b3-6434-83ea-a807-98080d8bcada
original_filename: Study OS Tutor - Check Study OS health.md
exported_at: 2026-09-04T01:22:07.725Z
reported_turns_captured: 40
reported_completeness: PARTIAL / NOT ESTABLISHED
original_size_bytes: 30104
original_sha256: 07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d
```

The public transport archive is lossless only if reconstruction produces that exact SHA-256. Stop if it does not.

## Critical source-quality boundary

The export is **not proven to be the complete original ChatGPT conversation**. Its own exporter reports `PARTIAL / NOT ESTABLISHED` and warns that scroll sweeps did not establish a stable turn set.

It also contains assistant messages that themselves embed prior raw-conversation Markdown. Therefore:

> Do not parse every `## User` / `## Assistant` heading as a source turn.

Nested headings inside assistant-authored transcript/code blocks are content of that assistant response, not additional outer turns.

Use two separate completion states:

```text
source_exhausted
= all uniquely recoverable outer evidence from this exact export was reviewed

conversation_complete
= the full original ChatGPT conversation is independently proven complete and ordered
```

`source_exhausted=yes` is possible while `conversation_complete=NOT_ESTABLISHED`.

## Required recovery ordering

```text
published lossless transport archive
        ↓
reconstructed exact Markdown bytes
        ↓
local Study OS immutable raw source artifact
        ↓
reviewed outer-turn reconstruction
        ↓
reviewed/session-mapped reconciliation input
        ↓
missing messages + raw_artifacts only
        ↓
reviewed source-linked learning events/episodes
        ↓
derived learner/system state only where separately justified
```

Raw/source recovery comes before learner-state interpretation.

## Phase 0 — audit and backup before mutation

1. Pull latest `main`.
2. Reconstruct the Markdown exactly using the source-directory `README.md`.
3. Verify original SHA-256 `07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d`.
4. Confirm live root `/root/.study-os` and learner `subject-001`.
5. Run `doctor` and record pre-import counts by subject/session.
6. Create a complete Study OS backup.
7. Record existing attempts/events/checkpoints/current-pointer so preservation can be verified afterward.

No live import before these pass.

## Phase 1 — preserve the source itself in Study OS

Store the reconstructed exact Markdown bytes in the local private Study OS evidence store before normalizing turns.

Required provenance includes at minimum:

```text
source_client: chatgpt
source_conversation_ref: 6a8ca3b3-6434-83ea-a807-98080d8bcada
source_filename: Study OS Tutor - Check Study OS health.md
source_sha256: 07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d
exported_at: 2026-09-04T01:22:07.725Z
source_completeness_claim: partial_not_established
capture_origin: historical_recovery_source
publication_origin: user_authorized_github_recovery_archive
```

Original source bytes are immutable. Parser outputs are rebuildable.

## Phase 2 — review outer turns without double-counting

Produce a reviewed extraction table before reconciliation:

```text
candidate_outer_turns
accepted_outer_turns
nested_copy_blocks_ignored
exact_duplicate_candidates
ordering_ambiguities
missing_or_uncertain_regions
rejected_invalid_regions
```

Requirements:

- Markdown/fence-aware extraction plus human review;
- preserve exact recoverable user/assistant content;
- nested transcript copies remain inside the containing assistant turn;
- do not invent missing text, timestamps, message IDs, or ordering;
- deterministic recovery identity may be generated from source hash + reviewed ordinal;
- ambiguities that affect ordering or target-session assignment stay unresolved.

## Phase 3 — map to historical Study OS records conservatively

Use existing session/checkpoint/event/attempt evidence to map reviewed turn ranges where supported.

Never:

- overwrite/move existing attempts, events, checkpoints, or current pointers;
- force uncertain turns into arbitrary historical sessions;
- fabricate a session boundary to make the transcript look complete.

If an unassignable source range requires a dedicated recovery session, report/propose it explicitly and preserve reconciliation provenance.

## Phase 4 — reconcile only genuinely missing turns

Use the existing reviewed `reconcile_conversation` path against `subject-001` and appropriate historical session(s).

For every segment report:

```text
already_present_exact
backfilled_missing
ambiguous_review_required
rejected_invalid_source
```

Ambiguity fails closed.

Run the same reconciliation a second time. The second run must add **zero** turns.

Every backfilled message must have a backing raw artifact and `capture_origin=reconciliation` (or equivalent explicit historical-recovery provenance).

## Phase 5 — preservation/integrity proof

After import verify:

```text
existing attempts unchanged: PASS/FAIL
existing pre-review learning events unchanged: PASS/FAIL
existing checkpoints/current pointer unchanged: PASS/FAIL
live post-fix messages unchanged: PASS/FAIL
new messages backed by raw artifacts: PASS/FAIL
message hash == artifact hash == bytes: PASS/FAIL
second reconciliation added 0: PASS/FAIL
doctor healthy: PASS/FAIL
backup/restore preserves recovered evidence: PASS/FAIL
```

Do not proceed to derived learning records if raw reconciliation/integrity is unresolved.

## Phase 6 — save the recovered interaction as durable live-learning data

After raw recovery is stable, create reviewed source-linked operational evidence for useful historical learning moments.

High-value candidate episodes visible in this source include:

- LeetCode Two Sum author representation created decoding/translation overhead;
- `enumerate` reduced unnecessary representation translation relative to index-first code during acquisition;
- `seen` caused semantic interference because the learner associated the term with sets;
- `index_by_num` remained confusing;
- neutral `box` terminology produced clearer immediate understanding;
- learner correctly retrieved the value under key `7` after the representation change;
- learner explicitly identified variable naming/author language as avoidable concept difficulty;
- learner identified append-only transcript durability as a product requirement after MCP 502 losses.

For each reviewed record preserve:

```text
evidence_class: observed | self_reported | derived
source_ids: recovered message/raw-artifact IDs
capture_origin: historical_reconciliation
```

Do not promote transcript text to mastery, transfer, or retention without separate evidence.

## Completion receipt

Return a public-safe receipt with:

```text
source SHA verified: yes/no
source bytes preserved in local Study OS: artifact id + hash
backup before import: PASS/FAIL
candidate outer turns: N
accepted reviewed outer turns: N
nested/embedded transcript blocks ignored: N
ordering ambiguities unresolved: N
session mappings unresolved: N

per target session:
  messages before -> after
  raw_artifacts before -> after
  already_present_exact
  backfilled_missing
  ambiguous_review_required
  rejected_invalid_source

second reconciliation added: 0/nonzero
existing attempts unchanged: PASS/FAIL
existing events unchanged before reviewed Phase 6: PASS/FAIL
existing checkpoints unchanged: PASS/FAIL
doctor: PASS/FAIL
hash/link integrity: PASS/FAIL
backup/restore: PASS/FAIL

reviewed source-linked learning episodes created: N
source_exhausted: yes/no
conversation_complete: yes/no/NOT_ESTABLISHED
remaining known gaps
final code SHA if code changed
```

## Non-negotiable boundaries

- The learner explicitly authorized this source's public GitHub publication; do not generalize that authorization to other private learner evidence.
- Study OS local SQLite + evidence store remains canonical learner storage; GitHub is only the recovery-source transport/archive here.
- Do not claim this export is complete when its own metadata says otherwise.
- Do not double-count nested transcript copies.
- Do not infer missing conversation text.
- Do not overwrite structured historical data.
- Reconciliation ambiguity fails closed.
- Transcript evidence is not mastery.
- FOSSIL remains optional downstream lineage, not the live recovery target.
