# Checkpointing and Cross-Session Resume

## Purpose

Study OS must not depend on ChatGPT conversation memory for longitudinal learning state.

A checkpoint is a **derived, provenance-backed snapshot** of the learner state at a useful boundary. It is not raw evidence and does not replace session events/episodes.

## Canonical model

```text
raw/private transcript
  -> normalized transcript
  -> append-only learning events
  -> learning episodes
  -> learner-state derivation
  -> immutable checkpoint snapshot
  -> mutable CURRENT pointer
```

If checkpoint logic changes, old checkpoints remain historical artifacts and a new checkpoint can be derived from canonical events.

## Storage

For Subject 001:

```text
subjects/subject-001/
  checkpoints/
    <checkpoint-id>.json
  CURRENT.json
```

- `checkpoints/<id>.json` is immutable after commit.
- `CURRENT.json` is a small public-safe pointer/summary that identifies the latest accepted checkpoint and how to resume.
- Do not put raw transcript text in checkpoints.
- Every learner claim must point to source event/episode/session IDs.

## What a checkpoint contains

A checkpoint answers:

1. What concept are we working on?
2. Which capabilities have actually been tested?
3. At what assistance level did the learner last succeed?
4. Which representations helped, failed, or remain ambiguous?
5. Which learner-state diagnoses are hypotheses rather than observations?
6. What should the next tutor avoid reteaching?
7. What is the next high-information probe/action?
8. Is a delayed retention probe due?

Checkpoint schema: `schemas/learner-checkpoint.schema.json`.

## When to checkpoint

### Required checkpoints

- session end;
- lesson boundary;
- before ending after a major breakthrough;
- after a persistent failure that changes the next-session plan;
- before and after a transfer test;
- before and after delayed-retention assessment.

### Optional/manual checkpoint

The learner may request one at any time, especially before switching chats/models or taking a break.

## Resume protocol in a fresh ChatGPT session

A fresh agent/tutor should read, in this order:

1. `PROJECT_MANIFEST.yaml`
2. `AGENTS.md`
3. `subjects/subject-001/CURRENT.json`
4. the checkpoint referenced by `CURRENT.json`
5. only the source episode/event summaries needed to verify uncertain state
6. the active Lesson IR/problem fixture

The tutor should **not** re-read the full transcript by default.

Resume behavior:

- briefly confirm the current focus;
- do not reteach items listed in `resume.do_not_reteach` unless a new assessment shows regression;
- start with `resume.next_action` or `resume.next_probe`;
- preserve the current assistance/fading level;
- if the checkpoint is stale or contradicted by behavior, append new evidence and derive a new checkpoint rather than rewriting the old one.

## Manual checkpoint command

Intended assistant surface:

```text
@study-os-checkpoint checkpoint this session
```

or later through a unified Study OS app:

```text
@StudyOS checkpoint
@StudyOS resume
```

The repository currently contains the skill contract, but this does **not** itself register an @-mentionable ChatGPT app/plugin.

Until that packaging exists, a connected GitHub-capable agent can perform the same operation when explicitly asked to read the checkpoint skill contract and write the resulting public-safe checkpoint files.

## Automated checkpointing

There are two meanings of automation.

### 1. Tutor/application automation — desired later

When Study OS owns the tutoring runtime, it can checkpoint automatically at deterministic boundaries such as:

- episode closed;
- lesson boundary reached;
- assistance level changed materially;
- breakthrough + behavioral confirmation;
- session ending;
- retention/transfer assessment completed.

This is the preferred long-term design because the tutoring runtime has direct access to session events and can create checkpoint proposals without relying on conversational memory.

### 2. Vanilla ChatGPT background automation — not assumed

The project must not assume that an ordinary ChatGPT conversation can silently monitor itself and push GitHub checkpoints in the background. A tool/app invocation or a Study OS-owned runtime is required for persistence.

Therefore v0.1 uses **explicit checkpoint calls**. Automated boundary-triggered checkpointing becomes a build target after the core evidence loop works.

## FOSSIL relationship

FOSSIL is not needed to resume the learner.

The checkpoint is Study OS state and belongs in the Study OS schema.

FOSSIL may later receive promoted durable knowledge such as:

- a curated trajectory summary;
- a repeated instructional finding;
- a lesson hypothesis;
- research conclusions.

Do not make resume depend on the FOSSIL API or graph availability.

## Why this matters for N=1

Checkpointing is especially important for a longitudinal single-subject design because it prevents:

- each new tutor session from resetting the learner model;
- accidental reteaching that contaminates assessment;
- forgotten assistance/hint history;
- model/provider changes from erasing context;
- subjective chat memory from becoming the experiment record.

A checkpoint makes each session reproducible and lets different models/tutors continue from the same evidence state.
