# Agent Handoff

Last updated: 2026-08-24

## Current phase

**Research Gate R0 — P1 ChatGPT-to-WSL transport and cross-session acceptance.**

Study OS is not yet a production learning application. P0 is merged and the
 target WSL validation is green: the P0 suite passed 35 tests, and the P1
 transport suite adds 4 tests; repository validation passes,
and `doctor` is healthy. The active gate is now connecting the unchanged local
semantic runtime to ChatGPT through a secure tunnel and proving fresh-chat
checkpoint/resume continuity.

## Current experiment

- Subject: `subject-001`
- Domain: DSA
- Language: Python
- Concept family: Sliding Window
- Goal: observe a representation-transition failure and test whether an intervention survives fading, transfer, and delayed retrieval.
- Bootstrap cross-session state: `subjects/subject-001/CURRENT.json`
- Current learner checkpoint status: **not started**; no DSA learning episode has been run yet.
- Target live-state architecture: local WSL Study OS service + SQLite + private evidence store.
- Current implementation tracker: Issue #5; P0 implementation PR #6 is merged; P1 transport branch `codex/p1-http-mcp-transport`.
- P0 local runtime implementation is present under `src/study_os/` with migration `0001` and CLI `cli/study_os.py`.
- P0 validation passed on WSL after merge: 35 tests, repository validator,
  compile checks, CLI `migrate`, `doctor`, and `list-tools`; the P1 branch adds
  4 HTTP transport tests. The runtime reports
  schema version `1` and all 13 approved semantic MCP tools.
- P1 adds only `src/study_os/mcp/http_server.py`, the `mcp-http` CLI command,
  transport tests, and the integration handoff; the database, service layer,
  migration version, and MCP contract remain unchanged.

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
21. Evidence used to derive learner state is subject-scoped; evidence from another learner cannot support the current learner's derived state.
22. Representation outcomes require behavioral assessment evidence, not merely any resolvable source ID.
23. A passing checkpoint capability must cite a same-subject passing assessment; `pass_unaided` additionally requires `assistance_level="none"`.
24. Restore must recover the previous DB/evidence pair if the replacement swap fails before acceptance.

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
- Added a loopback-only Streamable HTTP adapter around the existing MCP server,
  with optional bearer authentication and exact Origin allowlisting.
- Added `docs/P1_CHATGPT_MCP_INTEGRATION.md` with tunnel/app setup and the
  two-fresh-chat acceptance sequence.
- Reviewed PR #6 against the database, validation, handoff, error/idempotency, and failure-mode contracts.
- Changed PR #6 linkage from `Fixes #5` to `Refs #5` so merging P0 does not auto-close the tracker before P1/P2.
- Remediated subject provenance, representation-outcome evidence, checkpoint source-session doctor checks, restore rollback, and failed-export cleanup in `a2b77ec`.
- Added adversarial P0 review tests in `5fde05f`.
- Added commit-time evidence-backed capability-promotion enforcement and aligned checkpoint tests; latest head `ffeaa24` passes GitHub Actions CI #44.

## Next recommended tasks

### Local Luna / WSL — P1 transport

1. Start `cli/study_os.py mcp-http` on `127.0.0.1` using the private runtime root.
2. Configure Secure MCP Tunnel to forward its HTTPS endpoint to `/mcp`.
3. Register/rescan the custom Study OS MCP app in a workspace with MCP write permission.
4. Verify the exact 13-tool list and record the P1 Chat A/Chat B evidence.

### Cloud/repo — P1 review

1. Keep contract `0.1.0` and schema version `1` unchanged during transport integration.
2. Review the P1 adapter and exact-tool-list tests, then merge the P1 branch if accepted.
3. Complete the external tunnel/app setup and fresh-chat continuity test; do not claim P1 acceptance from local HTTP tests alone.

### After P1

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
- cross-subject evidence cannot support another learner's derived state;
- raw evidence mutation is detected;
- representation outcomes require a real intervention plus behavioral assessment evidence;
- passing checkpoint capability state is backed by cited assessment evidence;
- unaided pass state is backed by an unaided assessment;
- checkpoint + current pointer update is atomic;
- resume survives process restart;
- broken pointer/evidence/source-session references are detected by `doctor`;
- backup -> destroy/move -> restore reproduces checkpoint + evidence hashes;
- interrupted restore replacement recovers the previous working runtime;
- failed export transactions do not leave orphan semantic artifacts;
- MCP tool surface conforms to the repo contract;
- SQL/shell/generic file-write/code-exec tools are absent;
- updated validation passes on the target WSL machine.

## Unresolved decisions

- Exact SQLite migration/tooling library is now Python stdlib SQLite with ordered SQL files; future Postgres migration remains open.
- Exact DB backup cadence and whether private evidence backups are encrypted off-device.
- Whether hidden transfer fixtures live in a separate access-controlled local store/repo.
- Exact ChatGPT plan/workspace capabilities available for the custom MCP app, especially write/modify actions.
- Exact Secure MCP Tunnel setup/auth model for the WSL runtime.
- The Secure MCP Tunnel client/credentials are not present in this WSL checkout;
  external tunnel provisioning and ChatGPT app registration remain operational
  setup, not repository implementation.
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
- Do not let one subject's evidence support another subject's learner state.
- Do not promote capability to passed without cited behavioral assessment evidence.
- Do not trust backups until a restore test passes.
- Do not let an LLM-derived label overwrite learner self-report or observed events.
- Do not let AI generate authoritative algorithm state without deterministic validation.
- Do not expand scope into a full DSA curriculum yet.
- Do not describe Subject 001 results as universal evidence.
- Do not optimize solely for “felt clearer” or immediate completion speed.
- Do not resume from ChatGPT memory when a Study OS checkpoint exists; read the canonical checkpoint.

## Completion definition for the next agent

A task is not complete until relevant local/repository checks pass and this handoff + manifest are updated if the task changed project state, gates, paths, schemas, contracts, runtime ownership, or open decisions.
