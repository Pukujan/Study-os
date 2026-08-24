# Agent Handoff

Last updated: 2026-08-24

## Current phase

**Research Gate R0 — P0 implementation under final target-machine validation.**

Study OS is not yet a production learning application. The local runtime has now been implemented and cloud/repo review findings have been remediated. The remaining P0 gate is to rerun the updated validation suite and `doctor` on the target WSL machine before merging PR #6 and attempting real cross-chat learning continuity.

## Current experiment

- Subject: `subject-001`
- Domain: DSA
- Language: Python
- Concept family: Sliding Window
- Goal: observe a representation-transition failure and test whether an intervention survives fading, transfer, and delayed retrieval.
- Bootstrap cross-session state: `subjects/subject-001/CURRENT.json`
- Current learner checkpoint status: **not started**; no DSA learning episode has been run yet.
- Target live-state architecture: local WSL Study OS service + SQLite + private evidence store.
- Current implementation tracker: Issue #5; implementation PR #6; branch `codex/issue-5-p0-runtime`.
- P0 local runtime implementation is present under `src/study_os/` with migration `0001` and CLI `cli/study_os.py`.
- Original WSL validation at `a280eb4` passed 28 tests, repository validator, compile checks, CLI migrate/doctor, and backup/restore.
- Cloud review remediation head is `ffeaa24`; GitHub Actions CI run #44 passes with the added adversarial regression tests.
- **Pending P0 merge gate:** rerun the updated suite, repository validator, and CLI `doctor` on the target WSL machine.

## Planned learner-development architecture

The active research study remains only DSA/Python/Sliding Window. Broader curriculum planning is now explicitly separated from research scope.

Planned competency tracks:

1. algorithmic foundations;
2. software and systems foundations;
3. system design and reliability;
4. AI systems, evaluation, and reliability;
5. technical problem framing and diagnosis.

Canonical conceptual loop:

`goal -> plan -> task/episode -> attempt -> test/assessment -> evidence -> capability state -> diagnosis/next action -> plan update -> transfer/delayed test`

Study OS currently has strong evidence/assessment/capability-state machinery, a partial plan mechanism, and no first-class canonical goal or learner study-plan schema. Do not create those schemas until the live learning loop demonstrates a concrete need for durable multi-goal planning.

See `docs/LEARNING_CONTROL_MODEL.md` and Decision D013.

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
- `docs/LEARNING_CONTROL_MODEL.md`
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
25. Planned competency tracks are curriculum architecture, not automatic expansion of the active research scope; goal/plan/test/evidence/state concepts are explicitly separated and scoring remains multidimensional.

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
- Reviewed PR #6 against the database, validation, handoff, error/idempotency, and failure-mode contracts.
- Changed PR #6 linkage from `Fixes #5` to `Refs #5` so merging P0 does not auto-close the tracker before P1/P2.
- Remediated subject provenance, representation-outcome evidence, checkpoint source-session doctor checks, restore rollback, and failed-export cleanup in `a2b77ec`.
- Added adversarial P0 review tests in `5fde05f`.
- Added commit-time evidence-backed capability-promotion enforcement and aligned checkpoint tests; latest head `ffeaa24` passes GitHub Actions CI #44.
- Added `docs/LEARNING_CONTROL_MODEL.md` defining the goal/plan/task/test/evidence/state loop and five planned competency tracks while preserving DSA/Sliding Window as the sole active R0 research slice.
- Added Decision D013 and manifest v0.1.6 to distinguish curriculum architecture from validated research scope.

## Next recommended tasks

### Local Luna / WSL — final P0 target validation

1. Pull branch `codex/issue-5-p0-runtime` at `ffeaa24` or later.
2. Run `python3 -m compileall tools tests`.
3. Run `python3 tools/validate_repo.py`.
4. Run `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
5. Run the CLI against a temporary/private runtime root: `migrate`, `doctor`, and `list-tools`.
6. Confirm `doctor` is healthy and report the updated test count/results on PR #6.
7. If all target-machine checks pass, merge PR #6 without closing Issue #5, then begin P1.

### Cloud/repo — P0 review complete pending WSL gate

1. Keep contract `0.1.0` and schema version `1` unchanged unless a new explicit contract decision is required.
2. Do not merge solely from GitHub CI; wait for the post-remediation WSL validation result because local runtime behavior is the P0 target.
3. If WSL exposes a platform-specific failure, add a deterministic regression test before accepting P0.
4. After P0 merges, update manifest/handoff to make P1 cross-session continuity the active milestone.

### Learner-control design — deferred until evidence loop needs it

1. Do not implement first-class goal or study-plan schemas during P0 merely because the conceptual model now exists.
2. Use the current checkpoint `current_focus`, `next_action`, `next_probe`, capability state, and retention scheduling for the first real trajectory.
3. After the first instrumented trajectory, review whether durable multi-goal planning would reduce learner/tutor ambiguity.
4. If T5 technical problem framing is activated, build scenario/eval fixtures that score evidence-gathering and diagnosis behavior rather than hidden-root-cause guessing.

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
- Whether the first Study OS MCP service also exposes a local FastAPI/admin API or MCP only.
- Whether FOSSIL export is direct package generation or a separate adapter/service.
- Exact first alternating-representation experimental design.
- Which deterministic renderer/state format becomes authoritative after Mermaid/static traces.
- Whether delayed-retention scheduling is fixed or performance-adaptive.
- Whether/when first-class goal and learner study-plan schemas are justified by actual learning-loop complexity.
- What rubric/fixture format should represent T5 open-ended technical diagnosis when that track is activated.

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
- Do not confuse planned competency tracks with active/validated research domains.
- Do not describe Subject 001 results as universal evidence.
- Do not optimize solely for “felt clearer” or immediate completion speed.
- Do not resume from ChatGPT memory when a Study OS checkpoint exists; read the canonical checkpoint.

## Completion definition for the next agent

A task is not complete until relevant local/repository checks pass and this handoff + manifest are updated if the task changed project state, gates, paths, schemas, contracts, runtime ownership, or open decisions.
