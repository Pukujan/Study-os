# Historical transcript recovery source manifest

Date recorded: 2026-09-03  
Related issues: #52, #56, #59

## Purpose

Record the existence, identity, limitations, and intended use of a private ChatGPT transcript export supplied for Study OS historical learner-evidence recovery.

The raw transcript is **not** stored in this public repository.

## Source identity

```text
source_type: private ChatGPT Markdown export
source_filename: Study OS Tutor - Check Study OS health.md
conversation_id: 6a8ca3b3-6434-83ea-a807-98080d8bcada
exported_at: 2026-09-04T01:22:07.725Z
reported_turns_captured: 40
reported_completeness: PARTIAL / NOT ESTABLISHED
sha256: 07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d
privacy: local/private learner evidence
```

## Source-quality warning

The export itself states that repeated scroll sweeps did not establish a stable turn set.

It also contains assistant messages that embed earlier raw-conversation Markdown. Therefore repeated `## User` / `## Assistant` headings inside the file are not evidence of additional source turns and must not be parsed naively.

This source may be sufficient to recover substantial missing learning evidence, but it does not by itself establish full original-conversation completeness or ordering.

Use these distinct statuses:

```text
source_exhausted = all uniquely recoverable outer turns from this exact file were reviewed
conversation_complete = full original conversation independently proven complete and ordered
```

The second status is currently **NOT ESTABLISHED**.

## Intended canonical destination

```text
private original source bytes
  -> Study OS private raw evidence
  -> reviewed normalized/reconciliation input
  -> historical messages + raw_artifacts
  -> reviewed learning events/episodes
  -> derived state only with evidence provenance
```

Study OS remains the canonical owner of learner evidence. GitHub stores only this public-safe manifest and implementation/evidence-recovery lineage.

## Candidate live-learning findings for reviewed recovery

The private source contains evidence relevant to at least these subject-level learning episodes:

- representation translation overhead while reading a LeetCode Two Sum solution;
- preference for `enumerate` over an index-first authored representation during acquisition;
- semantic interference from the variable name `seen` because of prior set association;
- continued confusion with `index_by_num`;
- improved immediate clarity after changing the representation to neutral `box` terminology;
- a correct immediate dictionary lookup response after the representation change;
- learner identification of variable naming/author language as an avoidable source of conceptual difficulty;
- learner identification of append-only transcript capture as a required resilience mechanism after MCP 502 failures.

These are candidate observed/self-reported findings only. They are not mastery, transfer, or retention claims.

## Recovery authority

See:

`docs/LUNA_HISTORICAL_TRANSCRIPT_RECOVERY_HANDOFF.md`

The handoff requires source hashing, backup-before-import, original-byte preservation, reviewed outer-turn reconstruction, conservative session mapping, idempotent reconciliation, integrity verification, and source-linked operational episode creation.
