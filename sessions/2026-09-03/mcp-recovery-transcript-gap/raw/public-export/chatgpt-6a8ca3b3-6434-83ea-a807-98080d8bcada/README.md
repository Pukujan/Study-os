# User-authorized historical ChatGPT transcript source

The learner explicitly authorized publication of this transcript source so local Luna can recover missing historical Study OS evidence without a separate file transfer.

## Source identity

```text
conversation_id: 6a8ca3b3-6434-83ea-a807-98080d8bcada
original_filename: Study OS Tutor - Check Study OS health.md
exported_at: 2026-09-04T01:22:07.725Z
reported_turns_captured: 40
reported_completeness: PARTIAL / NOT ESTABLISHED
original_size_bytes: 30104
original_sha256: 07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d
```

The export itself warns that repeated scroll sweeps did not establish a stable turn set. Publication does **not** upgrade that source-quality claim.

## Why the file is stored as four chunks

The exact Markdown bytes were deterministically gzip-compressed (`mtime=0`) and base64-encoded for lossless transport through the GitHub connector. This is transport encoding only; it is not normalization or semantic parsing.

```text
gzip_size_bytes: 6977
gzip_sha256: 7395fc7a9af7d4cff4c283017927da7bbe2c7e3fcc128d3977d2bac734052592
base64_chars: 9304
```

Published chunk Git blob SHA-1 values:

```text
part01  a976db52975e78275d9b164daebb6bfe7e536ff1
part02  649c6c3458ca0b18a833d317724430b07f7d4f92
part03  df5bb2ac32ed5e3e808c3edec223d030f094fde0
part04  8211bcd23cb2014e6950f68a70106cf5fc0bee99
```

## Reconstruct the exact Markdown

From this directory:

```bash
cat transcript.md.gz.b64.part01 \
    transcript.md.gz.b64.part02 \
    transcript.md.gz.b64.part03 \
    transcript.md.gz.b64.part04 \
  | tr -d '\n' \
  | base64 -d > transcript.md.gz

sha256sum transcript.md.gz
# expected: 7395fc7a9af7d4cff4c283017927da7bbe2c7e3fcc128d3977d2bac734052592

gzip -dc transcript.md.gz > 'Study OS Tutor - Check Study OS health.md'

wc -c 'Study OS Tutor - Check Study OS health.md'
# expected: 30104

sha256sum 'Study OS Tutor - Check Study OS health.md'
# expected: 07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d
```

Do not use the source if either hash differs.

## Recovery warning

Do **not** treat every Markdown `## User` / `## Assistant` heading as a separate source turn. Some assistant messages embed earlier transcript Markdown inside their own response, which would create duplicate fake turns under naive heading parsing.

Recover reviewed outer turns only. Preserve unresolved ordering/session mapping rather than guessing. Distinguish:

```text
source_exhausted
= all uniquely recoverable evidence from this published export has been reviewed

conversation_complete
= the underlying original ChatGPT conversation is independently proven complete and ordered
```

`conversation_complete` remains `NOT_ESTABLISHED` from this source alone.

## Canonical destination

The published archive is a recovery source, not the live learner database. Luna must reconstruct it, preserve the exact source bytes in the local Study OS evidence store, reconcile only genuinely missing turns into canonical `messages + raw_artifacts`, and then create reviewed source-linked learning events/episodes where justified.

See `docs/LUNA_HISTORICAL_TRANSCRIPT_RECOVERY_HANDOFF.md` and Issue #56.
