# Agent Handoff

Last updated: 2026-08-23

## Current phase

**Research Gate R0 — local-runtime foundation + research harness readying.**

Study OS is not yet a production learning application. Broad product/UI work is gated on one complete auditable Sliding Window learning trajectory.

## Current experiment

- Subject: `subject-001`
- Domain: DSA
- Language: Python
- Concept family: Sliding Window
- Goal: observe a representation-transition failure and test whether an intervention survives fading, transfer, and delayed retrieval.
- Bootstrap cross-session state: `subjects/subject-001/CURRENT.json`
- Current learner checkpoint status: **not started**; no DSA learning episode has been run yet.
- Target live-state architecture: local WSL Study OS service + SQLite + private evidence store.

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
- `docs/CHECKPOINTING.md`
- `docs/LOCAL_RUNTIME_ARCHITECTURE.md`
- `docs/FOSSIL_INTEGRATION.md`
- `docs/CI_CD.md`
- `docs/DECISIONS.md`
- `docs/AGENT_RESEARCH_PROTOCOL.md`
- `docs/SOURCE_INDEX.md`
- `plugins/study-os-ingest/skill.md`
- `plugins/study-os-checkpoint/skill.md`
- `schemas/*.schema.json`
- Issue #4 — local-first runtime / `@StudyOS` orchestration

## Important decisions

1. Study OS canonical learning data uses a dedicated schema.
2. FOSSIL is optional for promoted durable knowledge; it is not required for every learning event or learner resume.
3. Full raw transcripts remain local/private by default because this repository is public.
4. Subject 001 is the first longitudinal design participant, not a population proxy.
5. No fixed learning-style model. Representation choice must be based on task/state/outcome.
6. Representation family and learning operation are distinct experimental variables.
7. Deterministic algorithm state is authoritative; generated media is illustrative until validated.
8. Broad deployment remains deferred until Research Gate R0 passes.
9. Multimodal video/image pipelines are deferred until the evidence loop works end-to-end.
10. Agents must keep manifest/handoff/decisions synchronized when project state changes.
11. Cross-session continuity uses derived, provenance-backed checkpoints; ChatGPT memory is never canonical state.
12. The repo defines Study OS ingest/checkpoint skill contracts, but there is not yet an installed @-mentionable Study OS ChatGPT app/plugin.
13. **Live learner state is moving off GitHub into a local Study OS runtime**. WSL + SQLite + a private evidence store is the v0.1 target.
14. GitHub owns code/schemas/research/plugin architecture/curated artifacts, not high-frequency live learning telemetry.
15. GitHub Actions is repository CI only and must never be required to study, score, checkpoint, or resume. Local runtime validation is mandatory regardless of Actions.
16. The intended ChatGPT integration is one semantic `@StudyOS` MCP-backed app surface. Do not expose arbitrary SQL/shell/file mutation tools.
17. ChatGPT cannot directly reach a WSL-only localhost service; use a supported secure/private MCP tunnel or equivalent authenticated remote path. Verify current plan/workspace write capabilities during integration.

## Recent changes

- Established repository/folder boundaries and public/private data boundary.
- Added versioned schemas for sessions, events, episodes, representations, lesson IR, learner checkpoints, and current-checkpoint pointers.
- Added minimal deterministic transcript preservation CLI and unit tests.
- Added `@study-os-ingest` and `@study-os-checkpoint` skill contracts (not yet packaged/installed as actual ChatGPT plugins).
- Added `docs/CHECKPOINTING.md` and initialized `subjects/subject-001/CURRENT.json` as a bootstrap resume entry point.
- Added academic research foundations, failure-mode catalog, measurement model, and R0/R1/R2 gates.
- Added root `AGENTS.md`, `PROJECT_MANIFEST.yaml`, decision log, and agent research protocol.
- Added repository/research-integrity validator and GitHub Actions CI; Actions is now explicitly non-runtime/optional during R0.
- Added `docs/LOCAL_RUNTIME_ARCHITECTURE.md` and Issue #4 defining WSL/SQLite/private evidence storage and the unified `@StudyOS` semantic tool boundary.
- Updated manifest/decision log to make the local DB the future canonical live checkpoint/state store.

## Next recommended tasks

### Local runtime foundation (next local coding session)

1. Create a project-agnostic SQLite schema + migrations for subjects/projects/domains/concepts/sessions/events/episodes/attempts/assessments/representations/interventions/outcomes/checkpoints/retention probes.
2. Create the private evidence store under a non-Git path such as `~/.study-os/evidence/`; raw artifacts immutable + hashed.
3. Implement repository/service layer so domain logic does not issue ad-hoc SQL everywhere.
4. Implement canonical local checkpoint/resume and a single current checkpoint pointer per subject/project context.
5. Implement `doctor`/health validation and enforce schema/provenance/checkpoint invariants at startup/write time.
6. Implement DB/evidence backup + restore test before valuable longitudinal data accumulates.

### MCP/app boundary

7. Expose semantic MCP operations only: status/start/resume/record event/attempt/assessment/intervention/outcome/checkpoint/next probe/retention/export-fossil.
8. Add deterministic integration fixtures and strict schemas for tool inputs/outputs.
9. Package one unified `@StudyOS` custom app/plugin surface.
10. Connect the local WSL MCP server using Secure MCP Tunnel or an equivalent authenticated private path supported by the active ChatGPT plan/workspace.
11. Verify `@StudyOS status`, write operations, `checkpoint`, and fresh-chat `resume` against the same local DB.

### Learning experiment

12. Implement transcript normalization/event extraction needed by the first Study OS session.
13. Define first Sliding Window Lesson IR + deterministic state model.
14. Define matched baseline/intervention/transfer/retention problem fixtures and hidden-eval boundary.
15. Run first instrumented learning session with Subject 001.
16. Produce first canonical local checkpoint; start a fresh tutor/chat and resume from it.
17. Run delayed retention and assemble first Golden Learning Trajectory.
18. Only then expand the product/UI/modalities.

## Unresolved decisions

- Exact SQLite migration/tooling library and repository-layer implementation.
- Exact DB backup cadence and whether private evidence backups are local-only or encrypted off-device.
- Whether hidden transfer fixtures live in a separate access-controlled local store/repo.
- Exact ChatGPT plan/workspace capabilities available for the custom MCP app, especially write/modify actions.
- Exact Secure MCP Tunnel setup/auth model for the WSL runtime.
- Whether the first Study OS MCP service also exposes a local FastAPI/admin API or MCP only.
- Whether FOSSIL export is direct package generation or a separate adapter/service.
- Exact first alternating-representation experimental design.
- Which deterministic renderer/state format becomes authoritative after Mermaid/static traces.
- Whether delayed-retention scheduling is fixed or performance-adaptive.

## Hazards

- Do not commit full personal transcripts to public Git history.
- Do not use GitHub as the live operational learner database after the local runtime exists.
- Do not make GitHub Actions part of the study/checkpoint/resume path.
- Do not publicly expose an unauthenticated local/WSL service.
- Do not expose arbitrary SQL/shell/file-write tools through `@StudyOS`.
- Do not let an LLM-derived label overwrite learner self-report or observed events.
- Do not let AI generate authoritative algorithm state without deterministic validation.
- Do not expand scope into a full DSA curriculum yet.
- Do not describe Subject 001 results as universal evidence.
- Do not optimize solely for “felt clearer” or immediate completion speed.
- Do not interpret representation preference as a fixed sensory learning style.
- Do not resume from ChatGPT memory when a Study OS checkpoint exists; read the canonical checkpoint.

## Completion definition for the next agent

A task is not complete until relevant local/repository checks pass and this handoff + manifest are updated if the task changed project state, gates, paths, schemas, runtime ownership, or open decisions.
