# Current State

Date: 2026-09-03
Status: operational dogfooding + durable evidence + structured curriculum acquisition

## Current product reality

Study OS is already being used by Subject 001 through the GPT app for real learning. That dogfooding is producing direct product-development evidence about where learning breaks and what kinds of representation changes help or hurt.

The current learner-facing surface remains GPT. A dedicated frontend is important later, but it is not the present critical path.

The local Study OS runtime remains the intended canonical operational store: SQLite plus a private evidence store. GitHub remains source/spec/research/issue history and curated public evidence, not the live learner database.

## What has become clearer from real use

The active product hypothesis is no longer limited to one DSA representation experiment.

Real episodes have exposed subject-level failure modes including:

- representation translation overhead when authored code form competes with algorithmic reasoning;
- variable-name semantic interference when an arbitrary identifier carries an unrelated learned meaning;
- information overload and under-information as distinct tutoring failures;
- over-help/under-help as distinct from learner capability;
- dynamic decomposition/recomposition as a way to zoom into one blocked operation without turning the entire curriculum into micro-lessons.

These are operational findings/hypotheses, not universal efficacy claims.

## Current architectural priority

The highest-priority engineering problem is reliable learner-data capture from the real GPT learning surface into the local runtime.

Reported HTTP 502 failures mean the current end-to-end path is not dependable enough for longitudinal evidence acquisition.

The required invariant is:

> No silent learner-evidence loss.

A learner interaction must be durably acknowledged locally or explicitly known to be missing/uncertain and recoverable through reconciliation/backfill.

The evidence architecture should preserve:

```text
raw/private evidence
 -> normalized operational records
 -> derived learner/system state
```

with provenance from derived claims back to lower-level evidence.

## Current curriculum direction

Structured curriculum/data work proceeds in parallel with dogfooding.

Approved public/open sources may be sampled, normalized, mapped to competencies/prerequisites, and expanded into structured learning material without waiting for a complete Sliding Window-only research gate.

Source provenance, source class, rights/license boundaries, authored representation, and learner outcomes remain distinct.

External/public content is candidate learning material; Study OS is responsible for observing when the source representation itself creates avoidable difficulty.

## Current operational loop

```text
source task
 -> learner attempt
 -> observed/self-reported friction
 -> diagnosis hypothesis
 -> representation / information / assistance / granularity operation
 -> learner response
 -> fade / restore source difficulty
 -> original-format check / transfer / retention when warranted
 -> update learner + system evidence
```

The learner and the tutoring system must be evaluated separately.

## Durable assets

The project currently values as durable:

- architecture and ownership boundaries;
- persistent data semantics/migrations;
- raw evidence integrity and provenance;
- learner-state contracts;
- curriculum/task provenance and competency structure;
- representation/intervention semantics;
- PDD/SDD/decision invariants;
- recovery/reconciliation guarantees.

Implementation code is replaceable when needed. Engineering assurance should protect these assets and the real learning path rather than become an independent product objective.

## Immediate execution priorities

1. Diagnose and restore the GPT -> local Study OS write path.
2. Define/implement durable-or-recoverable capture and reconciliation.
3. Continue Subject 001 learning through GPT while the system is being repaired and evolved.
4. Continue approved public-source curriculum sampling/normalization in parallel.
5. Record and refine representation, information, assistance, and decomposition operations from real trajectories.
6. Develop learner and system evaluation from those trajectories.
7. Apply broader hardening when a concrete failure model or product surface justifies it.
8. Activate dedicated frontend/multimodal work later when it has higher value than continued GPT dogfooding.

## Current planning authority

See `docs/ROADMAP.md` and the latest accepted entries in `docs/DECISIONS.md`.

Historical GitHub issues remain valuable lineage, but old unchecked items are not automatically current execution priorities when superseded by later accepted planning decisions.
