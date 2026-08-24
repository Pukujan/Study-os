# Agent Handoff

Last updated: 2026-08-23

## Current phase

**Research Gate R0 — research harness readying.**

Study OS is not yet a production learning application. Broad product/UI work is gated on one complete auditable Sliding Window learning trajectory.

## Current experiment

- Subject: `subject-001`
- Domain: DSA
- Language: Python
- Concept family: Sliding Window
- Goal: observe a representation-transition failure and test whether an intervention survives fading, transfer, and delayed retrieval.

## Canonical state

Read `PROJECT_MANIFEST.yaml` first.

Key contracts:

- `docs/PROJECT_CHARTER.md`
- `docs/PROJECT_BOUNDARY.md`
- `docs/PRODUCT_VISION.md`
- `docs/RESEARCH_FOUNDATIONS.md`
- `docs/RESEARCH_STATUS.md`
- `docs/RESEARCH_QUESTIONS.md`
- `docs/FAILURE_MODES.md`
- `docs/RESEARCH_PLAN.md`
- `docs/MEASUREMENT_MODEL.md`
- `docs/BUILD_GATES.md`
- `docs/FOSSIL_INTEGRATION.md`
- `docs/CI_CD.md`
- `docs/DECISIONS.md`
- `docs/AGENT_RESEARCH_PROTOCOL.md`
- `docs/SOURCE_INDEX.md`
- `plugins/study-os-ingest/skill.md`
- `schemas/*.schema.json`

## Important decisions

1. Study OS canonical learning data uses a dedicated schema.
2. FOSSIL is optional for promoted durable knowledge; it is not required for every learning event.
3. Full raw transcripts remain local/private by default because this repository is public.
4. Subject 001 is the first longitudinal design participant, not a population proxy.
5. No fixed learning-style model. Representation choice must be based on task/state/outcome.
6. Representation family and learning operation are distinct experimental variables.
7. Deterministic algorithm state is authoritative; generated media is illustrative until validated.
8. CI is active now; CD/deployment is deferred until Research Gate R0 passes.
9. Multimodal video/image pipelines are deferred until the evidence loop works end-to-end.
10. Agents must keep manifest/handoff/decisions synchronized when project state changes.

## Recent changes

- Established repository/folder boundaries and public/private data boundary.
- Added versioned schemas for sessions, events, episodes, representations, and lesson IR.
- Added minimal deterministic transcript preservation CLI and unit tests.
- Added `@study-os-ingest` skill contract (not yet packaged/installed as an actual ChatGPT plugin).
- Added academic research foundations and durable source index.
- Added adversarial failure-mode catalog with mitigations.
- Added falsifiable research questions, measurement model, and R0/R1/R2 gates.
- Added project charter, product vision, roadmap, and research-status docs.
- Added root `AGENTS.md`, `PROJECT_MANIFEST.yaml`, decision log, and agent research protocol.
- Added repository/research-integrity validator.
- Added GitHub Actions CI for compile, schema/data validation, privacy-boundary check, and unit tests.
- CD is intentionally not configured yet.

## Next recommended tasks

1. Verify the GitHub Actions CI run on `main` and fix any failures.
2. Create a redacted example session fixture and validate it against schemas.
3. Decide private raw-evidence storage/backup location.
4. Implement transcript normalization with stable message/span provenance.
5. Implement learning-event extraction as proposals, not ground truth.
6. Define first Sliding Window Lesson IR and deterministic state model.
7. Define matched baseline/intervention/transfer/retention problem fixtures.
8. Decide hidden-eval storage boundary so tutor cannot leak answers.
9. Run first instrumented learning session with Subject 001.
10. After delay, run retention probe and assemble first Golden Learning Trajectory.
11. Only then decide whether an application UI is justified.

## Unresolved decisions

- Exact private raw-evidence storage location and backup policy.
- Whether hidden transfer fixtures live in a private sibling repo, local store, or another access-controlled artifact store.
- How the actually invokable `@study-os-ingest` plugin/skill will be packaged and connected.
- Whether FOSSIL export uses direct package generation or a separate adapter/service.
- Exact experimental design for first alternating-representation comparison.
- Which deterministic renderer/state format becomes authoritative after Mermaid/static traces.
- Whether the first delayed-retention schedule should be fixed (for example 24h/72h) or adapt from performance.

## Hazards

- Do not commit full personal transcripts to public Git history.
- Do not let an LLM-derived label overwrite learner self-report or observed events.
- Do not let AI generate authoritative algorithm state without deterministic validation.
- Do not expand scope into a full DSA curriculum yet.
- Do not describe Subject 001 results as universal evidence.
- Do not optimize solely for “felt clearer” or immediate completion speed.
- Do not interpret representation preference as a fixed sensory learning style.

## Completion definition for the next agent

A task is not complete until relevant tests/checks pass and this handoff + manifest are updated if the task changed project state, gates, paths, schemas, or open decisions.
