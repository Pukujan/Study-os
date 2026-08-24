# Study OS

Study OS is an experimental learning system for observing, modeling, and improving how a learner translates technical concepts between representations.

The first vertical slice is **DSA in Python**, with Subject 001 as the initial longitudinal test subject.

## Core hypothesis

A learner often fails at a representation transition rather than at the underlying concept itself. Study OS records those transitions and adapts instruction across multiple representations: prose, figures, flowcharts, state traces, invariants, pseudocode, code scaffolds, executable code, audio, and later video.

The system should not treat “I understand” as mastery. It should preserve self-report, observed behavior, intervention history, delayed retention, and transfer as separate evidence.

## Atomic unit

The atomic unit is a **learning episode**:

`learner state -> task -> attempt -> failure/uncertainty -> intervention -> re-attempt -> assessment -> delayed/transfer evidence`

A chat session can contain many learning episodes. A lesson can span many sessions.

## Project boundary

Study OS owns:

- raw learning-session evidence and immutable transcript captures;
- learning events and episodes;
- learner-state snapshots;
- representation definitions and versions;
- lesson intermediate representations;
- assessment, retention, and transfer evidence;
- experimental comparison of learning interventions.

Study OS does **not** initially own:

- a general-purpose knowledge graph platform;
- general RAG infrastructure;
- universal claims about how all humans learn;
- a full DSA curriculum;
- production multimodal generation infrastructure.

## First slice

Start deliberately small:

- one learner: Subject 001;
- one language: Python;
- one DSA family: Sliding Window;
- a small problem set;
- a limited set of representations;
- instrumented sessions that record what helped, what failed, and whether improvement survives removal of assistance.

## Repository layout

- `docs/` — project boundary, current state, architecture, FOSSIL integration decisions.
- `schemas/` — versioned canonical Study OS data contracts.
- `domains/` — domain and concept knowledge organized by domain/concept/lesson.
- `sessions/` — immutable/raw session evidence plus derived learning events and episodes.
- `subjects/` — learner-model snapshots and subject-specific state.
- `datasets/` — curated golden trajectories, transfer sets, and retention sets.
- `plugins/` — small assistant/agent skills, beginning with transcript ingestion.
- `fossil/` — optional generated/exported FOSSIL-compatible artifacts; never the Study OS source of truth.

## Data principle

Keep three evidence classes separate:

1. **Observed** — what happened: answer, score, hint count, transcript span, elapsed time.
2. **Self-reported** — what the learner says was confusing/helpful and why.
3. **Derived** — model/system interpretations such as “likely invariant-to-state-transition failure.”

Derived labels are proposals, not ground truth.

## FOSSIL boundary

Study OS uses a dedicated learning schema. FOSSIL is a good fit for durable provenance, promoted research knowledge, lesson claims, and long-lived knowledge packs, but should not be required for every learning micro-event.

Canonical flow:

`raw transcript -> Study OS events/episodes -> learner/lesson state -> optional FOSSIL export`

See `docs/FOSSIL_INTEGRATION.md`.

## Status

**v0.1 / experiment design.** No claim is made yet that the learning procedure generalizes beyond Subject 001.
