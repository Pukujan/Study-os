# Historical transcript recovery source manifest

Date recorded: 2026-09-03  
Related issues: #52, #56, #59

## Purpose

Record the identity, publication status, limitations, and intended canonical use of the ChatGPT transcript export supplied for Study OS historical learner-evidence recovery.

The learner explicitly authorized public publication of **this specific source** so local Luna can pull it directly. This does not change the default privacy policy for other learner evidence.

## Source identity

```text
source_type: ChatGPT Markdown export
source_filename: Study OS Tutor - Check Study OS health.md
conversation_id: 6a8ca3b3-6434-83ea-a807-98080d8bcada
exported_at: 2026-09-04T01:22:07.725Z
reported_turns_captured: 40
reported_completeness: PARTIAL / NOT ESTABLISHED
original_size_bytes: 30104
original_sha256: 07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d
publication: user_authorized_public_recovery_source
```

## Public archive location

```text
sessions/2026-09-03/mcp-recovery-transcript-gap/raw/public-export/
  chatgpt-6a8ca3b3-6434-83ea-a807-98080d8bcada/
```

The exact Markdown bytes are represented losslessly as a deterministic gzip archive split across four base64 transport files. See that directory's `README.md` for reconstruction and hash verification.

Archive identity:

```text
gzip_size_bytes: 6977
gzip_sha256: 7395fc7a9af7d4cff4c283017927da7bbe2c7e3fcc128d3977d2bac734052592
```

## Source-quality warning

The export itself states that repeated scroll sweeps did not establish a stable turn set. Publication does not make the source complete.

The Markdown also contains assistant messages that embed earlier raw-conversation Markdown. Therefore repeated `## User` / `## Assistant` headings inside the source must not be naively interpreted as additional outer turns.

Use distinct completion statuses:

```text
source_exhausted = all uniquely recoverable outer turns from this exact export were reviewed
conversation_complete = full original conversation independently proven complete and ordered
```

`conversation_complete` is currently **NOT ESTABLISHED**.

## Canonical destination

```text
published recovery source
  -> reconstruct + hash verify
  -> local Study OS immutable raw evidence
  -> reviewed outer-turn reconstruction
  -> historical messages + raw_artifacts via reconciliation
  -> reviewed source-linked learning events/episodes
  -> derived state only where separately justified
```

Study OS remains the canonical owner of learner evidence. GitHub is serving as an explicitly authorized recovery-source transport/archive for this source, not as the live learner database.

## Candidate reviewed live-learning findings

The source contains evidence relevant to at least these subject-level episodes:

- representation translation overhead while reading a LeetCode Two Sum solution;
- `enumerate` as a lower-translation acquisition representation than index-first authored code;
- semantic interference from the variable name `seen` because of prior set association;
- continued confusion with `index_by_num`;
- improved immediate clarity after changing the representation to neutral `box` terminology;
- a correct immediate dictionary lookup after that representation change;
- learner identification of variable naming/author language as avoidable concept difficulty;
- learner identification of append-only transcript capture as a resilience requirement after MCP 502 failures.

These are candidate observed/self-reported/derived findings only. They are not mastery, transfer, or retention claims.

## Recovery authority

See `docs/LUNA_HISTORICAL_TRANSCRIPT_RECOVERY_HANDOFF.md` and Issue #56.

The required process is: exact source reconstruction and hashing, backup-before-import, immutable local source preservation, reviewed outer-turn extraction, conservative session mapping, idempotent reconciliation, integrity verification, and only then source-linked operational episode creation.
