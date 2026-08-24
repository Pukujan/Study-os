# Parallel Execution Plan — Cloud/Repo + Local Luna

## Goal

Develop Study OS v0.1 in two parallel tracks that meet at versioned contracts and acceptance tests.

The learner should not wait for the full hosted product before starting implementation work. The cloud/repo track defines what must be true; the local Luna/WSL track implements the runtime that satisfies those contracts.

## Track A — cloud/repository work

Owned through this repository and reviewable by any agent.

Responsibilities:

1. versioned semantic tool contracts;
2. database/storage invariants and migration requirements;
3. JSON schemas for learning evidence/checkpoints;
4. deterministic fixtures and reference trajectories;
5. contract/conformance tests;
6. validation/failure-injection requirements;
7. research integrity rules;
8. plugin/app orchestration contract;
9. public-safe documentation, handoff, decisions, issues;
10. review of Luna-pushed implementation against acceptance tests.

Track A must not depend on access to the learner's WSL database.

## Track B — local Luna / WSL runtime

Runs on the learner's machine and owns private operational state.

Responsibilities:

1. project-agnostic SQLite schema + migrations;
2. private immutable evidence store;
3. service/repository layer;
4. health/doctor command;
5. backup/export/restore;
6. semantic Study OS operations;
7. MCP server exposing only approved semantic tools;
8. local integration tests;
9. canonical local checkpoint/resume;
10. later secure tunnel integration.

Track B must implement against repository contracts instead of inventing incompatible local APIs.

## Synchronization boundary

The two tracks synchronize through Git:

```text
cloud/repo defines contract + tests
          ↓
Luna pulls contract
          ↓
Luna implements locally
          ↓
Luna runs local validation
          ↓
Luna pushes branch/PR
          ↓
cloud review runs contract tests + inspects implementation
          ↓
accept / revise
```

Do not synchronize live learner data through Git.

## First parallel milestone — P0

### Track A deliverables

- `contracts/study-os-mcp-tools.v0.1.json`
- `docs/VALIDATION_STRATEGY.md`
- `docs/LUNA_LOCAL_HANDOFF.md`
- contract tests under `tests/`
- deterministic reference fixture(s)
- Issue tracking P0 acceptance

### Track B deliverables

- local package layout;
- migration 0001;
- SQLite database creation;
- evidence directory initialization;
- `doctor`/health;
- `start_session`, `record_learning_event`, `checkpoint`, `resume`, `status` service methods;
- MCP wrappers for the initial approved subset;
- unit/integration tests;
- backup/restore smoke test.

## P0 merge gate

Do not call the local runtime ready until all of the following are true:

- fresh DB migrates from empty state;
- repeated migration invocation is safe/idempotent;
- invalid schema version fails loudly;
- raw evidence hashing detects mutation;
- derived learner-state writes without evidence are rejected;
- repeated event submission with the same idempotency key does not duplicate evidence;
- checkpoint references existing evidence and becomes current atomically;
- resume returns the last accepted checkpoint and next action;
- broken checkpoint pointer is detected by `doctor`;
- backup -> destroy working copy -> restore reproduces the same checkpoint/evidence hashes;
- MCP surface matches the versioned contract exactly;
- arbitrary SQL/shell/file mutation is not exposed through MCP;
- all repo-side contract tests pass;
- all local Luna tests pass.

## P1 cross-session acceptance

After P0:

1. fresh Chat/session A starts Subject 001;
2. Study OS records baseline evidence;
3. at least one representation intervention is recorded;
4. behavioral retest is recorded;
5. checkpoint is created;
6. session A closes;
7. fresh Chat/session B resumes using local checkpoint only;
8. session B does not require full transcript replay;
9. source evidence remains reconstructable;
10. no GitHub commit is required for the resume path.

## P2 learning-validity acceptance

After technical continuity works:

- assistance fading;
- changed-surface transfer;
- delayed retention;
- representation-effectiveness evidence score;
- candidate DSA tier updates;
- first Golden Learning Trajectory.

## Review rule

Implementation convenience never overrides a contract silently. If Luna discovers a contract is wrong, change the repository contract/decision explicitly first or in the same PR with rationale and migration impact.
