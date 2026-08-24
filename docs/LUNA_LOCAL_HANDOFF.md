# Luna Local Implementation Handoff — Study OS v0.1

This file is intended to be handed directly to the learner's local coding agent ("Luna") running in WSL.

## Mission

Implement the local-first Study OS runtime defined by Issue #4 and `docs/LOCAL_RUNTIME_ARCHITECTURE.md` without changing the learning/research contracts silently.

The local runtime is the canonical operational store for learner state. GitHub remains source/spec/test/research control.

## Read first

1. `AGENTS.md`
2. `PROJECT_MANIFEST.yaml`
3. `docs/LOCAL_RUNTIME_ARCHITECTURE.md`
4. `docs/PARALLEL_EXECUTION_PLAN.md`
5. `docs/VALIDATION_STRATEGY.md`
6. `docs/CHECKPOINTING.md`
7. `docs/FOSSIL_INTEGRATION.md`
8. `contracts/study-os-mcp-tools.v0.1.json`
9. Issue #4
10. Issue #3

## Do not build yet

Do not spend the first implementation cycle on:

- production UI;
- generated video/image pipeline;
- Postgres;
- graph database;
- FOSSIL runtime integration;
- public hosting;
- arbitrary remote shell/file tools;
- full DSA curriculum.

## Local runtime target

Use a project-agnostic layout similar to:

```text
src/study_os/
  db/
    migrations/
    connection.py
    repositories/
  domain/
    models.py
    errors.py
  services/
    sessions.py
    evidence.py
    assessments.py
    checkpoints.py
    representations.py
    health.py
    backups.py
  mcp/
    server.py
    tools.py
  evidence/
    store.py
  config.py

cli/
  study_os.py

tests/
  unit/
  integration/
  contract/
```

Exact structure may differ, but keep MCP -> service -> repository -> SQLite separation.

## Storage location

Default outside the Git working tree:

```text
~/.study-os/
  db/study-os.sqlite3
  evidence/
  backups/
  config/
```

Allow a configurable root for tests so every test can use a temporary directory.

## Database requirements

Project-agnostic minimum entities:

- subjects
- projects
- domains
- concepts
- sessions
- messages/raw_artifacts
- learning_events
- episodes
- attempts
- assessments
- representations
- interventions
- representation_outcomes
- checkpoints
- retention_probes

Use migrations from day one. Enable SQLite foreign keys. Prefer stable text/UUID-style IDs over row numbers as external identifiers.

### Required semantic invariants

- raw evidence is immutable after capture;
- durable write APIs accept an idempotency key/request ID;
- repeated same request must not duplicate a learning event/checkpoint;
- derived learner state requires evidence IDs;
- current checkpoint update is atomic with accepted checkpoint creation;
- checkpoint must not claim untested capability as passed;
- representation outcome references real intervention + behavioral evidence;
- FOSSIL is not involved in normal writes/resume;
- GitHub is not involved in normal writes/resume.

## Private evidence store

Implement content hashing (SHA-256) and metadata records. Prefer copy-on-ingest into an immutable session artifact directory. A mismatch between stored hash and current bytes must be detected by `doctor`/verification.

## Initial service methods

Implement at minimum:

- `doctor()`
- `status(subject_id)`
- `start_session(...)`
- `record_learning_event(...)`
- `record_attempt(...)`
- `record_assessment(...)`
- `record_representation_intervention(...)`
- `record_representation_outcome(...)`
- `checkpoint(...)`
- `resume(subject_id)`
- `backup(...)`
- `restore(...)`

Retention scheduling can be stubbed only if the contract clearly reports `not_implemented`; do not silently fake scheduling.

## MCP surface

Implement the approved tool names and request/response shapes from `contracts/study-os-mcp-tools.v0.1.json`.

Rules:

- semantic tools only;
- no SQL tool;
- no shell tool;
- no unrestricted write-file tool;
- no arbitrary code execution;
- validate tool arguments;
- stable machine-readable errors;
- MCP wrapper calls service methods, not ad-hoc SQL.

## `doctor` checks

Must fail non-zero / unhealthy when any of these are detected:

- migration/schema version incompatible;
- required tables missing;
- foreign keys disabled or broken;
- current checkpoint points to missing checkpoint;
- checkpoint references missing evidence;
- private evidence hash mismatch;
- configured evidence root unavailable;
- unsupported contract/runtime version.

## Backup/restore

Implement before real learning data is trusted.

Acceptance:

1. create fixture DB + evidence;
2. backup;
3. destroy/move working data;
4. restore;
5. hashes/checkpoints/record counts match;
6. `doctor` passes.

## Testing requirements

Follow `docs/VALIDATION_STRATEGY.md`.

Minimum PR evidence:

- migration test from empty DB;
- migration repeat/idempotency test;
- idempotent event-write test;
- invalid derived claim without evidence rejection test;
- checkpoint atomic/current-pointer test;
- resume-after-process-restart integration test;
- evidence mutation/hash failure test;
- backup/restore test;
- MCP contract conformance test;
- prohibited generic tool test.

## First deterministic fixture

Use a synthetic/non-private Subject 001-style fixture, not the learner's actual transcript.

Example sequence:

1. start session;
2. record `confusion_reported` self-report;
3. record `state_trace + predict` intervention;
4. record supported correct attempt;
5. record faded correct assessment;
6. record representation outcome evidence level 3;
7. create checkpoint with state tracing passed and implementation not tested;
8. restart service;
9. resume and verify next action.

## Branch/PR handoff back to cloud reviewer

When P0 implementation is ready:

1. run all local tests;
2. run repository tests;
3. push a branch;
4. open a PR referencing Issue #4;
5. in PR body include:
   - architecture summary;
   - migration version;
   - test commands + result summary;
   - known limitations;
   - backup/restore result;
   - MCP tool list;
   - changes to contracts, if any;
   - whether manifest/handoff need update.

Do not merge merely because the happy path works. The cloud/repo reviewer will inspect the diff and compare the implementation to the versioned contracts/failure tests.

## Definition of done for Luna P0

P0 is complete only when the runtime can be deleted/restarted/restored and still reproduce a valid learner checkpoint from durable evidence, with no GitHub/FOSSIL dependency in the operational path.
