# Agent Handoff

Last updated: 2026-09-03

## Current phase

**Operational dogfooding + durable evidence + structured curriculum acquisition.**

Study OS is already being used by Subject 001 through the GPT app for real learning. That usage is now a primary product-development and evidence-generation loop.

The immediate execution priority is not broad code hardening or frontend implementation. It is to make the GPT -> local Study OS evidence path dependable enough that ongoing learning does not silently lose data, while curriculum/data work continues in parallel.

## Planning authority

Read in this order:

1. `docs/ROADMAP.md`
2. `docs/CURRENT_STATE.md`
3. latest accepted entries in `docs/DECISIONS.md`
4. active issue/PR specifics

Git/issues preserve history. Old unchecked issue items do not override later accepted roadmap/decision changes.

## Runtime ownership

- Canonical live learner state remains local SQLite + private evidence store.
- GitHub remains source/spec/research/issue history/CI and curated public evidence.
- FOSSIL remains optional/downstream for durable lineage, promoted findings, and research artifacts; it is not the live learner database.
- The GPT app remains the current learner-facing surface.

## Current reliability incident

Real learning sessions have reported HTTP 502 failures while attempting Study OS writes.

Treat this as a learner-data integrity/reliability problem, not merely a transient UX defect.

### Required invariant

> No silent learner-evidence loss.

A write must be either durably acknowledged locally or explicitly identifiable as missing/uncertain and recoverable through reconciliation/backfill.

Protect:

- commit-before-success acknowledgement;
- idempotent exact retries;
- no duplicate durable evidence;
- correlation/operation identifiers;
- visible unknown/failed write state;
- service-restart continuity;
- integrity/doctor checks;
- backup/restore;
- transcript reconciliation for turns that failed before local receipt;
- raw/private evidence provenance.

## Learning/evidence direction

Current operational evidence supports testing, at subject level:

- `representation_translation_overhead`;
- `variable_name_semantic_interference`;
- information overload/under-information;
- over-help/under-help;
- dynamic task decomposition/recomposition;
- assistance fade and source/original representation restoration.

Do not convert these into universal learner traits or population claims.

Preserve the event chain where available:

```text
source task
 -> learner attempt
 -> failure/confusion evidence
 -> intervention/operation
 -> representation + assistance + information/granularity conditions
 -> learner response
 -> fade/original-format check
 -> transfer
 -> delayed retention
```

Learner evaluation and system/intervention evaluation remain separate.

## Curriculum/data direction

Approved public/open curriculum sources may be sampled and structured in parallel with operational learning.

Do not reinstate the old global rule that all curriculum expansion must wait for one complete Sliding Window trajectory.

Preserve source provenance, source class, rights/license boundary, competency/prerequisite mapping, task version, authored representation, and learner outcome separately.

PR #50 is the current draft source-registry/planning work. PR #51 is the current draft canonical operational learning evidence around Two Sum representation failures. PR #49 is retrospective methodology evidence. Review each on its own evidence/privacy boundary.

## Existing trackers: current interpretation

- #4 local-first runtime: preserve as accepted architectural lineage.
- #10 learner/curriculum/adaptive work: keep/reframe around learner model, representation operations, assistance, and real outcome evidence; OSS mechanisms are implementation options, not the product identity.
- #21 engineering assurance: keep as a risk-driven toolbox/backlog; architecture/data integrity work that protects current operations remains valuable, but the old full hardening order is no longer the near-term roadmap.
- #26 application/frontend boundary: defer/park until a dedicated frontend becomes active product work.
- #42 curriculum: keep/reframe so structured public curriculum may expand in parallel with dogfooding.
- #1/#2/#3/#5/#27: candidates for historical/superseded closure after a separate issue-cleanup review.

Do not close/rewrite historical issues merely because this handoff says they are candidates. Issue cleanup is a separate deliberate action.

## Current engineering stance

Preserve PDD/SDD, invariants, data contracts/migrations, architecture boundaries, provenance, idempotency, recovery, and compatibility when they protect durable project assets.

Implementation code is replaceable. Do not prioritize mutation score, broad synthetic simulation, formal methods, exhaustive platform hardening, or frontend tooling merely because an old checklist contains them. Activate those methods when a concrete current failure model justifies them.

## Immediate next work

1. Inspect the actual local GPT/MCP/transport/SQLite failure path that is producing 502s.
2. Write a focused persistence/reconciliation PDD/SDD with the no-silent-loss invariant.
3. Repair and verify the real local capture path under restart/retry/unknown-result conditions.
4. Continue real Subject 001 learning through GPT and reconcile any missed sessions.
5. Continue small-sample structured curriculum ingestion from approved sources.
6. Extend operational event semantics only when real trajectories require them, especially representation/information/assistance/decomposition operations.
7. Build learner and system grading/evaluation from real downstream outcomes.
8. Defer dedicated frontend and rich multimodal product work until the owner promotes it in priority.

## Non-negotiable invariants

- Raw/private learning evidence is not committed publicly by default.
- Observed, self-reported, and derived evidence remain distinct.
- Derived learner/system state retains evidence provenance.
- Exact retry must not duplicate durable evidence.
- No acknowledged local durable write may disappear after restart.
- Remote failure before local receipt must be detectable/recoverable through reconciliation rather than silently treated as captured.
- Hidden learning/evaluation answers remain protected.
- Adaptive components do not own canonical SQLite/checkpoint state directly.
- Representation policies are contextual interventions, not fixed learning-style labels.
- Public/source curriculum provenance remains distinct from learner outcomes.

## Handoff rule

Keep this file concise and current. Update it when the operational phase, current reliability incident, runtime ownership, planning authority, or immediate execution priorities materially change.
