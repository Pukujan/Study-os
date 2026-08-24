# Agent Handoff

Last updated: 2026-08-23

## Current phase

**Research Gate R0 — pre-build experiment design.**

Study OS is not yet a production learning application. Current work is allowed only when it improves the evidence loop, experiment reproducibility, transcript/data integrity, deterministic representation testing, or agent handoff.

## Current experiment

- Subject: `subject-001`
- Domain: DSA
- Language: Python
- Concept family: Sliding Window
- Goal: observe a representation-transition failure and test whether an intervention survives fading, transfer, and delayed retrieval.

## Canonical state

Read `PROJECT_MANIFEST.yaml` first.

Key contracts:

- `docs/PROJECT_BOUNDARY.md`
- `docs/RESEARCH_FOUNDATIONS.md`
- `docs/FAILURE_MODES.md`
- `docs/RESEARCH_PLAN.md`
- `docs/FOSSIL_INTEGRATION.md`
- `plugins/study-os-ingest/skill.md`
- `schemas/*.schema.json`

## Important decisions

1. Study OS canonical learning data uses a dedicated schema.
2. FOSSIL is optional for promoted durable knowledge; it is not required for every learning event.
3. Full raw transcripts remain local/private by default because this repository is public.
4. Subject 001 is the first longitudinal design participant, not a population proxy.
5. No fixed learning-style model. Representation choice must be based on task/state/outcome.
6. CI is appropriate now; CD/deployment is deferred until Research Gate R0 passes.
7. Multimodal video/image pipelines are deferred until the evidence loop works end-to-end.

## Recent changes

- Established repository/folder boundaries.
- Added versioned schemas for sessions, events, episodes, representations, and lesson IR.
- Added minimal deterministic transcript preservation CLI.
- Added `@study-os-ingest` skill contract (not yet packaged/installed as an actual ChatGPT plugin).
- Added research foundations with academic sources.
- Added adversarial failure-mode catalog and mitigations.
- Added research plan and explicit R0/R1/R2 gates.
- Added root `AGENTS.md` and `PROJECT_MANIFEST.yaml`.

## Next recommended tasks

1. Finish CI/repository-validation checks.
2. Add `docs/DECISIONS.md` or ADRs for major decisions.
3. Create a redacted example session fixture and validate it against schemas.
4. Implement transcript normalization with stable message/span provenance.
5. Implement learning-event extraction as proposals, not ground truth.
6. Define first Sliding Window Lesson IR and deterministic state model.
7. Define matched baseline/intervention/transfer/retention problem fixtures.
8. Run first instrumented learning session with Subject 001.
9. After delay, run retention probe and assemble first Golden Learning Trajectory.
10. Only then decide whether an application UI is justified.

## Unresolved decisions

- Exact private raw-evidence storage location and backup policy.
- Whether hidden transfer fixtures live in a private sibling repo or encrypted/local store.
- How the actually invokable `@study-os-ingest` plugin/skill will be packaged and connected.
- Whether FOSSIL export uses direct package generation or a separate adapter/service.
- Exact experimental design for first alternating-representation comparison.
- Which representation renderer should be authoritative for state animations after Mermaid/static traces.

## Hazards

- Do not commit full personal transcripts to public Git history.
- Do not let an LLM-derived label overwrite learner self-report or observed events.
- Do not let AI generate authoritative algorithm state without deterministic validation.
- Do not expand scope into a full DSA curriculum yet.
- Do not describe Subject 001 results as universal evidence.
- Do not optimize solely for “felt clearer” or immediate completion speed.

## Completion definition for the next agent

A task is not complete until relevant tests/checks pass and this handoff + manifest are updated if the task changed project state, gates, paths, schemas, or open decisions.
