---
name: study-os-ingest
description: Ingest a learning conversation into Study OS as immutable transcript evidence, normalized session metadata, append-only learning events, and proposed learning episodes. Use when the user invokes @study-os-ingest or asks to preserve/analyze a Study OS learning session.
---

# Study OS Ingest

## Purpose

Turn a learning conversation into durable Study OS evidence without treating model interpretation as ground truth.

The skill should be callable conceptually as:

`@study-os-ingest ingest this learning session`

or:

`@study-os-ingest ingest transcript <provided transcript/export>`

This repository file defines the skill contract. Registering it as an installed ChatGPT/plugin skill is a separate packaging/deployment step.

## Canonical destination

Study OS is the source of truth.

Logical session layout:

```text
sessions/YYYY-MM-DD/<session-id>/
  manifest.json
  raw/
    transcript.md
    transcript.original.*
    SHA256SUMS
  normalized/
    transcript.jsonl
  events/
    learning-events.jsonl
  episodes/
    <episode-id>.json
  derived/
    learner-state-before.json
    learner-state-after.json
    session-summary.md
  knowledge/
    README.md
```

Do not write directly to a global FOSSIL pack as the only persistence path.

### Public repository rule

If the target repository is public, **do not upload full raw transcript content by default**. Preserve raw evidence in a local/private evidence root or private artifact store, then commit only its hash/reference plus reviewed/redacted derivatives. See `docs/DATA_POLICY.md`.

A public manifest may refer to raw evidence with a logical URI such as `private://sessions/.../transcript.original.json` plus SHA-256.

Uploading a full raw transcript to a public repository requires explicit user intent for that specific artifact.

## Ingest workflow

1. **Capture raw evidence**
   - Preserve the provided transcript/export exactly when bytes or structured source are available.
   - If only visible conversation text is available, preserve a verbatim Markdown capture and mark `capture_method=copy`.
   - Compute and store SHA-256 for every raw artifact.
   - Never edit a raw artifact after ingest. Corrections create a new artifact/version.
   - For public repositories, put this evidence in private/local storage unless the user explicitly chooses public publication.

2. **Create session manifest**
   - Validate against `schemas/session-manifest.schema.json`.
   - Record provider/model/conversation ID only when actually known.
   - Use pseudonymous subject IDs such as `subject-001`.
   - In public repositories, reference private raw artifacts by logical URI/hash rather than embedding their contents.

3. **Normalize transcript**
   - Produce JSONL with stable message IDs, role, timestamp when available, content, tool/media references, and source offsets.
   - Normalization is derived and rebuildable from raw evidence.
   - Redact public derivatives when needed; never overwrite the raw artifact.

4. **Extract learning events**
   - Validate every event against `schemas/learning-event.schema.json`.
   - Separate `observed`, `self_reported`, and `derived` evidence classes.
   - Every event extracted from a transcript must include transcript provenance.
   - Never convert “I understand” directly into mastery.

5. **Propose learning episodes**
   - Group related events into `learner state -> task -> attempt -> failure/uncertainty -> intervention -> re-attempt -> assessment` episodes.
   - Validate against `schemas/learning-episode.schema.json`.
   - Mark ambiguous episode boundaries `needs_review`.

6. **Preserve representation details**
   - Record representation family, operation, and version when known.
   - Distinguish modality from operation: e.g. `structural + trace`, `textual + expand`, `procedural + reconstruct`.

7. **Record learner feedback precisely**
   - Preserve explicit statements about what was confusing/helpful and why as `self_reported` evidence.
   - A model may propose a causal interpretation as `derived`, with confidence, but it must not rewrite the learner’s explanation.

8. **Assess rather than infer mastery**
   - Prefer prediction, explanation, reconstruction, implementation, hidden transfer, and delayed retention evidence.
   - If no behavioral test occurred, record `not_tested` rather than assuming success.

9. **Generate session summary**
   - Summarize important failures, interventions, breakthroughs, unresolved transitions, and follow-up assessments.
   - Every derived conclusion should point back to event IDs.

10. **Optional FOSSIL promotion/export**
    - Do not automatically ingest every learning event into FOSSIL.
    - Export only selected durable artifacts: curated trajectory summaries, lesson hypotheses, validated domain knowledge, research conclusions, or promoted findings.
    - FOSSIL output is derived/rebuildable from Study OS canonical data.

## Folder routing

Route knowledge by scope:

- session-specific observation -> `sessions/.../knowledge/`
- lesson instructional hypothesis -> `domains/<domain>/<concept>/lessons/<lesson>/knowledge/`
- concept knowledge -> `domains/<domain>/<concept>/knowledge/`
- domain knowledge -> `domains/<domain>/knowledge/`

Never promote a subject-specific observation into lesson/domain knowledge without an explicit promotion event/review.

## Versioning rules

Version independently:

- schema version;
- lesson version;
- representation version;
- assessment version;
- learner-model derivation version.

Git history is provenance, but it is not the semantic version model.

## Output requirements

After ingest, report:

- session ID and destination path/reference;
- raw artifact hashes;
- whether raw evidence is private or public;
- number of normalized messages;
- counts by evidence class;
- proposed learning episodes;
- unresolved/needs-review items;
- whether any FOSSIL export was produced.

## Safety / integrity

- Never fabricate missing transcript content, timestamps, scores, or learner feedback.
- Never silently rewrite raw transcripts.
- Never treat derived labels as observed facts.
- Never expose private transcript data outside the target chosen by the user.
- Never rely on `.gitignore` to protect data when writing through a GitHub API; enforce the public/private boundary explicitly.
