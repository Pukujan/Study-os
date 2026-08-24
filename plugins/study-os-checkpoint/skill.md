---
name: study-os-checkpoint
description: Create or resume a provenance-backed learner checkpoint for Study OS. Use when the learner asks to checkpoint, save learning state, switch chats/models, end a study session, or resume from the latest accepted checkpoint.
---

# Study OS Checkpoint

## Purpose

Persist enough **derived learner state** that a new tutor/session can continue from the same evidence without using hidden conversational memory as the source of truth.

Intended invocation:

`@study-os-checkpoint checkpoint this session`

or:

`@study-os-checkpoint resume subject-001`

This repository file defines the skill contract. It is not, by itself, an installed @-mentionable ChatGPT app/plugin.

## Checkpoint workflow

1. Read `PROJECT_MANIFEST.yaml`, `AGENTS.md`, and `docs/CHECKPOINTING.md`.
2. Identify the current subject/session/domain/concept.
3. Read the current session's public-safe events/episodes and the previous checkpoint when one exists.
4. Do not infer unrecorded mastery from conversation tone or self-report.
5. Create a checkpoint that validates against `schemas/learner-checkpoint.schema.json`.
6. Preserve provenance through source session/episode/event IDs.
7. Record skill status by tested capability, not one global mastery score.
8. Record representation outcomes separately from learner-state hypotheses.
9. Preserve assistance/fading state.
10. Populate `resume.current_focus`, `resume.do_not_reteach`, and exactly one highest-information next action/probe.
11. Write immutable checkpoint to `subjects/<subject>/checkpoints/<checkpoint-id>.json`.
12. Update `subjects/<subject>/CURRENT.json` to point to the new accepted checkpoint.
13. Update `docs/HANDOFF.md` only if project/research state changed; ordinary learner-state checkpoints should not turn HANDOFF into a learner log.

## Resume workflow

1. Read `subjects/<subject>/CURRENT.json`.
2. Load the referenced checkpoint.
3. Load only the minimum source events/episodes needed to verify ambiguous hypotheses.
4. Resume at `resume.next_action` / `resume.next_probe`.
5. Do not reteach `resume.do_not_reteach` unless new behavioral evidence shows regression.
6. Continue the previous assistance/fading policy.
7. Append new learning evidence; never rewrite the old checkpoint.

## Evidence rules

Checkpoint state is derived.

- Observed behavior must reference observed event IDs.
- Learner explanations/preferences must reference self-reported event IDs.
- Diagnoses such as `invariant_to_control_flow confusion` remain hypotheses with confidence + evidence.
- If no behavioral assessment occurred, use `not_tested`.

## Privacy

This repository is public.

Do not include raw transcript passages, account identifiers, secrets, or private conversation data in a checkpoint. Use stable event/session IDs and concise public-safe summaries.

## FOSSIL

Do not require FOSSIL for checkpoint/resume. Checkpointing is Study OS learner-state infrastructure.

A later optional FOSSIL export may promote curated learning/research findings, but must not be the only copy of the checkpoint or its evidence.

## Output after checkpoint

Report:

- checkpoint ID;
- subject;
- source session(s);
- current focus;
- tested skill statuses;
- unresolved hypotheses;
- assistance level;
- next action/probe;
- retention due time if applicable;
- files written/updated.
