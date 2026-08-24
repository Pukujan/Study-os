# Versioning

Study OS versions semantic artifacts independently so experiments can compare changes without treating a Git commit as the only version identifier.

## Versioned artifacts

### Schema version

Changes to canonical JSON contracts.

Example: `learning-event.schema.json` version `0.1.0`.

- PATCH: clarifications or compatible optional fields.
- MINOR: backward-compatible new semantics/fields.
- MAJOR: incompatible event meaning or required-field changes.

### Lesson version

Version the Lesson IR independently.

Example: `dsa.sliding-window.window-as-region@0.3.0`.

Increment when the lesson’s semantic structure, sequence, goals, or assessments change.

### Representation version

Every representation receives its own version.

Examples:

- `sliding-window.pointer-trace@2`
- `sliding-window.flowchart@4`
- `sliding-window.invariant-plain-language@3`

A representation version should change when its content or behavior changes enough that learning outcomes may differ.

### Assessment version

Hidden-transfer, immediate, and retention assessments are versioned independently from lessons. This prevents a lesson change from silently changing the measuring instrument.

### Learner-model derivation version

Observed events are immutable. Learner-state snapshots are derived and may be recomputed by newer models/rules.

Store the derivation version with every snapshot.

## Artifact identity

Prefer stable IDs plus explicit versions:

```text
lesson_id: dsa.sliding-window.maintaining-validity
lesson_version: 0.1.0
representation_id: dsa.sliding-window.pointer-trace
representation_version: 1
assessment_id: dsa.sliding-window.transfer-001
assessment_version: 1
learner_model_version: 0.1.0
```

## Raw evidence

Raw transcript/export evidence is **not semantically versioned**. It is content-addressed with SHA-256.

If a better export is captured later, add a new raw artifact and record its hash; never replace the previous artifact.

## Promotion versions

When a session observation is promoted into a lesson hypothesis or research finding, create a new stable promoted artifact that cites its source event/episode IDs. Do not mutate the original session evidence.

## Git

Git provides repository history and review provenance, but semantic versions remain inside Study OS artifacts so experiments can reason about them directly.
