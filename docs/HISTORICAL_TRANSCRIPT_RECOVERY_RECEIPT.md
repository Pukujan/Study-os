# Historical Transcript Recovery Receipt

Date: 2026-09-04  
Issue: #56  
Source conversation: `6a8ca3b3-6434-83ea-a807-98080d8bcada`

## Source verification

- Published archive reconstructed from all four GitHub chunks: PASS.
- Gzip SHA-256: `7395fc7a9af7d4cff4c283017927da7bbe2c7e3fcc128d3977d2bac734052592`.
- Reconstructed Markdown: 30,104 bytes.
- Markdown SHA-256: `07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d`.
- Source bytes preserved in local Study OS as artifact
  `historical-recovery-source-07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d`.
- Source completeness: `PARTIAL / NOT ESTABLISHED`.

## Recovery result

- Runtime: `/root/.study-os`.
- Target subject: `subject-001`.
- Target session: `0446d18d-046b-4b8b-a00f-f2f629787bda`.
- Session mapping was supported by the existing checkpoint source-session IDs
  and matching historical learning events.
- Candidate reviewed outer turns: 34 (19 user, 15 assistant).
- Accepted reviewed outer turns: 34.
- Embedded/nested headings ignored: 50 across the generated raw-Markdown
  copies contained inside the final assistant response.
- Exact duplicate candidates: 0.
- Ordering ambiguity: retained as an explicit source limitation; no timestamps
  were invented.
- Conversation complete: `NOT_ESTABLISHED`.

Target session counts:

| Asset | Before | After |
|---|---:|---:|
| messages | 4 | 38 |
| raw_artifacts | 4 | 40 |

- Already present exact: 0.
- Backfilled missing: 34.
- Ambiguous review required: 0.
- Rejected invalid source: 0.
- Second reconciliation added: 0; all 34 resolved as `already_present_exact`.

## Preservation and integrity

- Backup before import: PASS — `/root/.study-os/backups/recovery-preimport-20260904`.
- Existing structured tables unchanged: PASS, including attempts, learning
  events, assessments, checkpoints, and current checkpoint pointers.
- New messages backed by raw artifacts: PASS.
- Message hash equals artifact hash equals on-disk bytes: PASS.
- Post-import backup/restore into disposable runtime: PASS.
- Restored doctor: PASS.
- Live doctor: PASS.
- Reviewed source-linked learning episodes created: 0. Interpretation remains
  deferred because this source is incomplete and transcript evidence alone is
  not mastery/capability evidence.

## Remaining limitations

The source is now preserved and its uniquely reviewed outer evidence is
reconciled, but the original ChatGPT conversation is not proven complete or
fully ordered. The recovery deliberately did not infer missing turns, promote
transcript text into mastery, or alter existing structured learner state.
