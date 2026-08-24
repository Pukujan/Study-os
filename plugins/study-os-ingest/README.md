# `@study-os-ingest`

This directory defines the Study OS transcript-ingest assistant skill.

## Intended user experience

```text
@study-os-ingest ingest this learning session
```

or:

```text
@study-os-ingest ingest this transcript as DSA / sliding-window
```

The assistant should preserve the transcript, create a session manifest, normalize messages when possible, extract provenance-linked learning events, propose learning episodes, and report unresolved labels for review.

## Current status

`skill.md` is the behavioral contract. It is **not automatically installed as a ChatGPT @-mentionable plugin merely because it exists in GitHub**.

A later packaging step should register this skill with a runtime that can:

1. access the current conversation/export;
2. write to this repository or a local checkout;
3. optionally call a provider-aware transcript normalizer;
4. optionally call the Study OS -> FOSSIL export adapter.

## Minimal fallback

Until the @ plugin is wired, raw transcript files can be ingested locally with:

```bash
python tools/ingest_transcript.py transcript.md \
  --provider chatgpt \
  --subject subject-001 \
  --domain dsa \
  --concept sliding-window
```

This deterministic stage preserves immutable evidence and creates a manifest without attempting to hallucinate semantic labels.

## Dependency boundary

The future plugin should depend on Study OS schemas and a storage writer (GitHub or local filesystem). FOSSIL must remain optional.
