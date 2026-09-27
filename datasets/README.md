# Datasets

Datasets are curated derivatives of canonical session evidence.

Planned boundaries:

```text
datasets/
  learner-episodes/
  golden-trajectories/
  hidden-transfer/
  delayed-retention/
```

## Reviewed learner episodes

`learner-episodes/` contains reviewed, public-safe derivatives of canonical Study OS learning sessions that are useful research evidence but do not yet satisfy the full Golden Learning Trajectory criteria.

These records must keep observed, self-reported, and derived claims separate. They must also state which follow-up measurements are still missing. A canonical Study OS session may still have a failed or unverified structured runtime write; when that happens, the derivative must distinguish **canonical session origin** from **durable runtime persistence status** rather than silently treating the episode as noncanonical or pretending the write succeeded.

Raw transcripts and unnecessary third-party source content remain private by default.

## Golden Learning Trajectories

A golden trajectory is not a transcript and not a question/answer pair. It is a reviewed sequence linking:

`initial learner state -> task -> attempts -> failure evidence -> interventions -> self-report -> behavioral assessments -> assistance removal -> transfer -> retention`

Every trajectory must preserve source session/event/episode IDs.

A reviewed learner episode must not be promoted to `golden-trajectories/` until the required provenance and behavioral follow-up are present.

## Hidden transfer

Problems used to evaluate transfer must be kept distinct from teaching examples. The learner should not be shown their labels/solutions before the transfer attempt.

## Delayed retention

Retention assessments should record elapsed delay, assistance level, representation availability, and whether the task was reconstructed or merely recognized.
