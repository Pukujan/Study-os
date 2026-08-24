# Agent Handoff

Last updated: 2026-08-24

## Current phase

**Research Gate R0 — P0 parallel cloud-contract + local-runtime implementation.**

Study OS is not yet a production learning application. The immediate goal is to make the local runtime implementation satisfy versioned repository contracts and extensive validation before attempting real cross-chat learning continuity.

## Current experiment

- Subject: `subject-001`
- Domain: DSA
- Language: Python
- Concept family: Sliding Window
- Goal: observe a representation-transition failure and test whether an intervention survives fading, transfer, and delayed retrieval.
- Bootstrap cross-session state: `subjects/subject-001/CURRENT.json`
- Current learner checkpoint status: **not started**; no DSA learning episode has been run yet.
- Target live-state architecture: local WSL Study OS service + SQLite + private evidence store.
- Current implementation tracker: Issue #5, branch `codex/issue-5-p0-runtime`.
- P0 local runtime implementation is present under `src/study_os/` with migration `0001` and CLI `cli/study_os.py`.
- Local validation currently passes: 28 WSL tests, repository validator, and compile checks.

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
- `docs/PARALLEL_EXECUTION_PLAN.md`
- `docs/VALIDATION_STRATEGY.md`
- `docs/LUNA_LOCAL_HANDOFF.md`
- `docs/DATABASE_CONTRACT.md`
- `docs/ERROR_IDEMPOTENCY_CONTRACT.md`
- `contracts/study-os-mcp-tools.v0.1.json`
- `docs/FOSSIL_INTEGRATION.md`
- `docs/CI_CD.md`
- `docs/DECISIONS.md`
- `docs/AGENT_RESEARCH_PROTOCOL.md`
- `docs/SOURCE_INDEX.md`
- `plugins/study-os-ingest/skill.md`
- `plugins/study-os-checkpoint/skill.md`
- `schemas/*.schema.json`
- Issue #3 — v0.1 mobile adaptive learning loop
- Issue #4 — local-first runtime / `@StudyOS` orchestration
- Issue #5 — P0 parallel implementation + validation

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
13. Live learner state belongs in the local Study OS runtime; GitHub owns source/spec/research, not live telemetry.
14. GitHub Actions is repository CI only and must never be required to study, score, checkpoint, or resume.
15. The intended ChatGPT integration is one semantic `@StudyOS` MCP-backed app surface. Do not expose arbitrary SQL/shell/file mutation tools.
16. ChatGPT cannot directly reach a WSL-only localhost service; use a supported secure/private MCP tunnel or equivalent authenticated path.
17. P0 is contract-first and parallel: cloud/repo defines versioned contracts/tests while Luna implements locally against them.
18. Durable mutating semantic tools require idempotency keys; retry duplication is treated as evidence corruption risk.
19. Checkpoint creation + current pointer update is atomic.
20. Backup/restore and failure-injection tests are required before trusting longitudinal learner data.

## Recent changes

- Added local-first runtime architecture and Issue #4.
- Added `docs/PARALLEL_EXECUTION_PLAN.md` defining cloud/repo and local Luna tracks.
- Added `docs/VALIDATION_STRATEGY.md` with V0–V10 validation layers: contracts, migrations, evidence integrity, services, MCP, checkpoint/resume, backup/restore, failure injection, privacy, cross-session, and learning validity.
- Added `docs/LUNA_LOCAL_HANDOFF.md` as the exact local WSL implementation handoff.
- Added `docs/DATABASE_CONTRACT.md` for project-agnostic SQLite semantics and invariants.
- Added `docs/ERROR_IDEMPOTENCY_CONTRACT.md` for stable error categories, retries, idempotency, checkpoint atomicity, and concurrency behavior.
- Added `contracts/study-os-mcp-tools.v0.1.json` defining the semantic MCP surface.
- Added a synthetic reference learning trajectory under `tests/fixtures/`.
- Added `tests/test_runtime_contracts.py` so the repo checks required semantic tools, idempotency, prohibited generic machine access, evidence-backed representation scoring, and checkpoint semantics.
- Created Issue #5 as the P0 shared cloud/local implementation tracker.
- Updated `PROJECT_MANIFEST.yaml` to make P0 parallel implementation the current milestone.
- Implemented the project-agnostic SQLite/evidence/service/MCP runtime for Issue #5.
- Added migration `0001`, configurable private runtime root, SHA-256 evidence verification, doctor, backup/restore, idempotent semantic operations, atomic checkpoints, and MCP stdio wrappers.
- Added repository-level MCP/runtime layout validation and local integration/failure tests.

## Next recommended tasks

### Local Luna / WSL — P0 implementation complete; review next

1. Review the pushed Issue #5 PR against the versioned contracts and failure modes.
2. Confirm the local WSL runtime on the target machine with `cli/study_os.py doctor`.
3. Connect the MCP stdio/server boundary through a supported authenticated private path when integration work begins.

### Cloud/repo — continue in parallel

1. Review Luna's pushed implementation against the machine-readable contract and P0 failure modes.
2. Extend cloud-side conformance tests as implementation details reveal ambiguous contracts.
3. Add contract version migration tests once Luna introduces runtime/migration versions.
4. Add a generated-vs-expected MCP tool-list comparison test once the server implementation exists.
5. Add fixture-driven checkpoint/resume integration test callable against a local test service implementation in CI if practical.
6. Keep contracts authoritative; if a contract is wrong, update it explicitly with rationale rather than silently accepting drift.

### After P0

1. Connect WSL MCP through a secure/private path supported by the active ChatGPT plan/workspace.
2. Run P1: fresh Chat A -> checkpoint -> fresh Chat B resume without transcript replay or GitHub runtime writes.
3. Implement first deterministic Sliding Window Lesson IR/state model and hidden transfer boundary.
4. Run the first instrumented learning trajectory.
5. Complete fading, transfer, delayed retention, representation scoring, and first Golden Learning Trajectory.

## P0 technical acceptance highlights

Do not accept the local runtime until:

- empty DB migration works;
- migration command is repeat-safe;
- foreign keys are enforced;
- exact write retries do not duplicate events;
- idempotency key reuse with changed content conflicts;
- derived learner claims without evidence are rejected;
- raw evidence mutation is detected;
- checkpoint + current pointer update is atomic;
- resume survives process restart;
- broken pointer/evidence is detected by `doctor`;
- backup -> destroy/move -> restore reproduces checkpoint + evidence hashes;
- MCP tool surface conforms to the repo contract;
- SQL/shell/generic file-write/code-exec tools are absent.

## Unresolved decisions

- Exact SQLite migration/tooling library is now Python stdlib SQLite with ordered SQL files; future Postgres migration remains open.
- Exact DB backup cadence and whether private evidence backups are encrypted off-device.
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
- Do not expose arbitrary SQL/shell/file-write/code-execution tools through `@StudyOS`.
- Do not allow retry behavior to duplicate learner evidence.
- Do not allow checkpoint/current-pointer partial commits.
- Do not trust backups until a restore test passes.
- Do not let an LLM-derived label overwrite learner self-report or observed events.
- Do not let AI generate authoritative algorithm state without deterministic validation.
- Do not expand scope into a full DSA curriculum yet.
- Do not describe Subject 001 results as universal evidence.
- Do not optimize solely for “felt clearer” or immediate completion speed.
- Do not resume from ChatGPT memory when a Study OS checkpoint exists; read the canonical checkpoint.

## Completion definition for the next agent

A task is not complete until relevant local/repository checks pass and this handoff + manifest are updated if the task changed project state, gates, paths, schemas, contracts, runtime ownership, or open decisions.
