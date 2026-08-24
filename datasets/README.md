# Datasets

Datasets are curated derivatives of canonical session evidence.

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

## Hidden transfer

Problems used to evaluate transfer must be kept distinct from teaching examples. The learner should not be shown their labels/solutions before the transfer attempt.

## Delayed retention

Retention assessments should record elapsed delay, assistance level, representation availability, and whether the task was reconstructed or merely recognized.
