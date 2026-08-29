# Datasets

Datasets are curated derivatives of canonical session evidence.

The methodology capture at
[`learner-methodology/2026-08-29-study-os-methodology-capture.json`](learner-methodology/2026-08-29-study-os-methodology-capture.json)
is a public-safe, draft derivative of one reconstructed shared conversation.
It keeps self-reported, observed, and derived records separate and points to
the complete source preserved in FOSSIL. It is not a live learner checkpoint,
mastery record, or universal learning rule.

Planned boundaries:

```text
datasets/
  golden-trajectories/
  hidden-transfer/
  delayed-retention/
```

## Golden Learning Trajectories

A golden trajectory is not a transcript and not a question/answer pair. It is a reviewed sequence linking:

`initial learner state -> task -> attempts -> failure evidence -> interventions -> self-report -> behavioral assessments -> assistance removal -> transfer -> retention`

Every trajectory must preserve source session/event/episode IDs.

Public derivatives must not contain full private transcripts, raw capture
payloads, secrets, or account identifiers. Use hashes, stable provenance
references, and concise reviewed findings instead.

## Hidden transfer

Problems used to evaluate transfer must be kept distinct from teaching examples. The learner should not be shown their labels/solutions before the transfer attempt.

## Delayed retention

Retention assessments should record elapsed delay, assistance level, representation availability, and whether the task was reconstructed or merely recognized.
