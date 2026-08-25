# Agent Handoff

Last updated: 2026-08-25

## Current phase

**P2 adaptive-learning integration with engineering-verification hardening.**

P0 local runtime is complete and merged. The repository contains the P2 adaptive foundation: structured telemetry, versioned adapter contracts, atomic curriculum fixtures, BKT/CAT/IRT/FSRS shadow mechanisms, scaffold control, representation policy, learner-relative complexity, tutor-policy regression, proposal-to-outcome linkage, atomic retention-probe closure, and richer resume projection.

The deployed/local P1 ChatGPT transport remains a separate lineage with private WSL/Cloudflare/GPT Action configuration intentionally absent from this public repository. Do not modify or invent those local secrets/configurations from cloud-only work.

## Canonical trackers

- Issue #10 — P2 learner model, curriculum, adaptive control, shadow/canary/live-promotion gates.
- Issue #21 — production-grade agentic verification and SWE foundations.
- Issue #5 — historical P0/P1 runtime and continuity parent tracker.

Before any P2 component reaches G5 advisory/canary or later, apply the relevant Issue #21 verification gates.

## Current runtime/contracts

- Runtime/package version: `0.1.0`.
- MCP semantic contract: `0.1.0`.
- SQLite schema version: `1` / migration `0001`.
- Public semantic tool surface remains exactly 13 tools.
- Canonical live learner state remains local SQLite + private evidence store.
- GitHub is source/spec/research/CI, not the live learner database.

## Current engineering structure

Study OS remains a modular monolith in progress:

- `src/study_os/adaptive/` — pure/adaptive decision mechanisms and shadow policy logic.
- `src/study_os/curriculum/` — versioned competency/item loading and validation.
- `src/study_os/db/` — SQLite connection/migrations.
- `src/study_os/evidence/` — private evidence/hash handling.
- `src/study_os/services/` — semantic application/runtime facade; transitional and still contains the large preserved `runtime_base.py`.
- `src/study_os/mcp/` — MCP transport wrappers.

Do not aggressively refactor the semantic runtime until property/state-machine/reference-model verification freezes its behavior.

## Verification state

The first Issue #21 SWE baseline is now mandatory in CI:

1. Python compile;
2. repository/schema/privacy/contract validator;
3. runtime-package/MCP-version consistency and exact 13-tool count;
4. architecture check preventing `adaptive/` and `curriculum/` pure logic from importing DB/evidence/service/MCP layers;
5. Ruff lint for critical Python errors;
6. Pyright basic type checking over `src/study_os`;
7. branch-aware coverage with a 70% floor;
8. full unittest suite.

The baseline is configured in `pyproject.toml`, `.github/workflows/ci.yml`, and `tools/check_engineering_baseline.py`. Coverage is a regression floor, not proof of correctness.

Remaining Issue #21 verification order:

1. Ruff format + reproducible dependency lock/project-state convergence;
2. Hypothesis property/state-machine/metamorphic tests;
3. independent executable reference model + differential tests;
4. mutation/negative controls;
5. protected engineering holdout tests;
6. seeded >=100x learner-policy simulation;
7. load/failure/chaos tests;
8. targeted Alloy/TLA+/SMT/formal verification where state-space risk justifies it.

Do not use theorem proving, mutation score, coverage, an LLM grader, or synthetic learners as a single sufficient correctness oracle.

## Learner/adaptive state

Issue #10 remains the behavioral authority. Implemented foundations include versioned `LearnerSnapshot` / `DecisionProposal`, structured attempt/hint/representation telemetry, the first atomic running-extrema/second-largest curriculum slice, baseline/BKT/CAT/IRT/FSRS shadow mechanisms, an evidence-gated scaffold controller, contextual representation policy, learner-relative complexity, tutor-behavior regression, proposal-to-outcome linkage, retention-probe closure, and richer resume context.

These components remain non-authoritative/shadow unless explicitly promoted through the documented G0-G7 ladder.

## Immediate next work

1. Add property/state-machine testing around session/attempt/assessment/checkpoint/resume/probe/retry/restart semantics.
2. Build a small independent in-memory reference model and differential harness.
3. Add mutation/negative-control verification.
4. Establish a coding-agent-hidden engineering holdout boundary.
5. Run deterministic >=100-trajectory synthetic learner-policy regression before G5.
6. Only then resume live-shadow -> advisory/canary promotion work.

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

Keep this file concise and current. Git and issues are history. Update it when operational phase, current trackers, runtime ownership, versions/contracts, deployment boundary, mandatory verification, or next execution priorities materially change.
