# Agent Handoff

Last updated: 2026-08-25

## Current phase

**P2 adaptive-learning integration with engineering-verification hardening.**

P0 local runtime is complete and merged. The repository now contains the P2 adaptive foundation: structured telemetry, versioned adapter contracts, atomic curriculum fixtures, BKT/CAT/IRT/FSRS shadow mechanisms, scaffold control, representation policy, learner-relative complexity, tutor-policy regression, proposal-to-outcome linkage, atomic retention-probe closure, and richer resume projection.

The deployed/local P1 ChatGPT transport remains a separate lineage with private WSL/Cloudflare/GPT Action configuration that is intentionally not stored in this public repository. Do not modify or invent those local secrets/configurations from cloud-only work.

## Canonical trackers

- Issue #10 — P2 learner model, curriculum, adaptive control, shadow/canary/live-promotion gates.
- Issue #21 — production-grade agentic verification and SWE foundations.
- Issue #5 — historical P0/P1 runtime and continuity parent tracker.

Before any P2 component reaches G5 advisory/canary or later, apply the relevant Issue #21 verification gates.

## Current runtime/contracts

- Runtime/package version: `0.1.0`.
- MCP semantic contract: `0.1.0`.
- SQLite schema version: `1` / migration `0001`.
- Public semantic tool surface remains 13 tools.
- Canonical live learner state remains local SQLite + private evidence store.
- GitHub is source/spec/research/CI, not the live learner database.

## Current engineering structure

Study OS is a modular-monolith-in-progress:

- `src/study_os/adaptive/` — pure/adaptive decision mechanisms and shadow policy logic.
- `src/study_os/curriculum/` — versioned competency/item loading and validation.
- `src/study_os/db/` — SQLite connection/migrations.
- `src/study_os/evidence/` — private evidence/hash handling.
- `src/study_os/services/` — semantic application/runtime facade; currently transitional and still contains a large preserved `runtime_base.py`.
- `src/study_os/mcp/` — MCP transport wrappers.

Do not refactor the large semantic runtime aggressively until property/state-machine/reference-model verification exists. Freeze semantics first, then decompose use cases.

## Verification state

Current mandatory repository CI is still only:

1. Python compile;
2. repository/schema/contract validator;
3. unittest suite.

Issue #21 is the canonical plan to add, in order:

1. project-state/doc convergence;
2. Ruff + Pyright + coverage + reproducible dependency/version checks;
3. architecture/import-boundary tests;
4. Hypothesis property/state-machine/metamorphic tests;
5. executable reference model + differential tests;
6. mutation/negative controls;
7. private engineering holdout tests;
8. seeded 100x learner-policy simulation;
9. load/failure/chaos tests;
10. targeted Alloy/TLA+/SMT/formal verification where the state-space risk justifies it.

Do not use theorem proving, mutation score, coverage, an LLM grader, or synthetic learners as a single sufficient correctness oracle.

## Learner/adaptive state

Issue #10 remains the behavioral authority. Implemented foundations include:

- versioned `LearnerSnapshot` / `DecisionProposal` contracts;
- standardized attempt/hint/representation telemetry;
- first atomic running-extrema/second-largest curriculum slice;
- baseline and BKT diagnostic selectors;
- CAT/IRT diagnostic/instruction ranking;
- FSRS retention adapter;
- evidence-gated scaffold controller;
- contextual representation policy;
- learner-relative complexity/load estimator;
- tutor-behavior policy regression;
- shadow recommendation -> later assessment outcome linkage;
- retention-probe closure through assessment;
- richer resume context including do-not-reteach, retention, and recent representation history.

These components remain non-authoritative/shadow unless explicitly promoted through the documented G0-G7 ladder.

## Immediate next work

Engineering verification now precedes further live adaptive promotion:

1. repair manifest/tracker state drift;
2. add static/type/coverage/version/architecture gates;
3. add property/state-machine testing around the semantic runtime;
4. build a small independent executable reference model and differential harness;
5. add mutation/negative-control verification;
6. establish a coding-agent-hidden engineering holdout boundary;
7. run deterministic >=100-trajectory synthetic learner-policy regression before G5;
8. only then resume live-shadow -> advisory/canary promotion work.

In parallel, Issue #10 should be updated to distinguish already-implemented foundations from remaining live-shadow/outcome-validation work.

## Non-negotiable invariants

- Raw/private learning evidence is not committed to this public repository.
- Observed, self-reported, and derived evidence remain distinct.
- Self-report or conversational fluency cannot promote capability.
- Passing checkpoint capability states require same-subject behavioral assessment evidence.
- Exact retries must not duplicate durable evidence.
- Checkpoint creation/current-pointer updates remain atomic.
- Hidden learning/evaluation answers must not be exposed to the tutor.
- Hidden engineering holdout answers/tests must not be exposed to coding agents before implementation.
- Adaptive/donor components do not own canonical SQLite/checkpoint state.
- Representation policies are contextual experiments, not fixed learning-style labels.
- Do not grant live adaptive authority without the documented promotion gates and verification prerequisites.

## Handoff rule

Keep this file concise and current. Git and issues are the history. Update this handoff when the operational phase, current trackers, runtime ownership, versions/contracts, deployment boundary, or next execution priorities materially change.
