# Local-First Study OS Runtime Architecture

## Decision

Study OS v0.1 will be **local-first**.

The live learning system of record runs locally (initially in WSL). GitHub is the versioned project/code/research repository, not the operational learner database.

## Ownership boundaries

### Local Study OS runtime owns

- subjects and project-agnostic learner identities;
- study sessions;
- normalized messages/events;
- attempts and assessments;
- representation interventions and outcomes;
- assistance/fading state;
- learner-state derivations;
- checkpoints and current pointers;
- retention/transfer schedules;
- private raw transcript/evidence metadata;
- local raw/private artifacts.

### GitHub owns

- application/plugin source code;
- MCP/app tool contracts;
- schemas and migrations;
- Lesson IR and deterministic representation specifications;
- tests and fixtures;
- project requirements and research methodology;
- issue logs/decisions/handoffs;
- curated/redacted research artifacts and released datasets;
- optional FOSSIL export code/mappings.

GitHub must not be required to record an answer, create a checkpoint, resume a learner, or run a study session.

## Initial local stack

```text
WSL
├── Study OS service
│   ├── MCP server / semantic tool boundary
│   └── optional local HTTP/FastAPI administration API
├── SQLite
│   └── operational learning state
├── private evidence store
│   ├── immutable transcript exports
│   ├── hashes
│   └── media/attachments
└── local clone of Study-os
    ├── schemas
    ├── migrations
    ├── lesson definitions
    └── tests
```

SQLite is appropriate for Subject 001 and early single-user research. The schema should remain relational and migration-friendly so SQLite can later move to Postgres without changing semantic tool contracts.

## Project-agnostic database requirement

The local runtime must not hard-code DSA or Study OS project structure into generic storage primitives.

At minimum model:

- `subjects`
- `projects`
- `domains`
- `concepts`
- `sessions`
- `messages` / `raw_artifacts`
- `learning_events`
- `episodes`
- `attempts`
- `assessments`
- `representations`
- `interventions`
- `representation_outcomes`
- `checkpoints`
- `retention_probes`

Domain-specific payloads may use versioned JSON fields or extension tables, but canonical provenance/session/checkpoint semantics should be reusable across future learning domains.

## One @StudyOS orchestration surface

The intended user-facing app is one `@StudyOS` surface. It should expose semantic tools rather than generic database/file operations.

Examples:

- `start_session`
- `resume`
- `get_current_state`
- `record_learning_event`
- `record_attempt`
- `record_assessment`
- `record_representation_intervention`
- `record_representation_outcome`
- `checkpoint`
- `schedule_retention_probe`
- `get_next_probe`
- `status`
- `export_fossil`

The LLM/tutor chooses teaching actions; Study OS validates and persists learning evidence.

Do not expose unrestricted `run_sql`, `write_file`, or arbitrary shell/database mutation tools to the conversational model.

## How ChatGPT reaches WSL

ChatGPT cannot treat `localhost` inside the learner's WSL environment as directly reachable from the cloud product.

The preferred integration is:

```text
ChatGPT
   ↓
@StudyOS custom app
   ↓
remote/private MCP connection
   ↓
secure tunnel
   ↓
WSL Study OS MCP server
   ↓
SQLite + private evidence
```

Use an authenticated private MCP tunnel or another deliberately configured secure remote HTTPS path. Do not publicly expose an unauthenticated WSL port.

The exact ChatGPT custom-app/write capability is plan-dependent and must be verified at integration time. The local runtime must still work standalone if ChatGPT app integration is unavailable.

## GitHub Actions decision

GitHub Actions is **not part of the Study OS runtime**.

Study sessions, checkpointing, scoring, and resume must never depend on GitHub Actions.

Actions may remain as optional repository CI for:

- schema checks;
- migrations/tests;
- plugin/app contract tests;
- static validation;
- public-data/privacy checks.

The local Study OS service must also run its own startup/runtime validation because production correctness cannot depend on CI having run previously.

If maintaining Actions becomes distracting during R0, it may be reduced or disabled without changing Study OS runtime behavior.

## Runtime validation inside Study OS

The local service should validate at startup and before durable writes:

- database schema/migration version;
- required tables/indexes;
- semantic event/checkpoint schemas;
- evidence provenance requirements;
- immutable raw-artifact hashes;
- no derived learner-state claims without evidence links;
- checkpoint pointer integrity;
- representation/lesson version references.

A `study-os doctor` / `health` operation should report whether the local runtime is safe to use.

## Checkpoint model

The canonical checkpoint belongs in the local database.

GitHub `subjects/subject-001/CURRENT.json` is currently a research/bootstrap artifact, not the long-term live source of truth.

When the local runtime is active:

```text
local DB checkpoint = canonical live state
GitHub checkpoint snapshots = optional curated/reproducibility exports
```

A checkpoint remains a derived, provenance-backed snapshot. Raw evidence and append-only events remain independently recoverable.

## Manual and automated checkpointing

### Manual v0.1

The learner may invoke:

- `@StudyOS checkpoint`
- `@StudyOS resume`

The tool creates/loads the local canonical checkpoint.

### Automatic later

When Study OS receives events throughout a tutoring session, it may propose or create checkpoints at deterministic boundaries:

- session close;
- confirmed breakthrough after behavioral retest;
- material assistance/fading transition;
- lesson boundary;
- transfer assessment;
- retention assessment;
- persistent failure changing the next-session plan.

Do not automate checkpointing by assuming a vanilla ChatGPT conversation can silently observe conversation termination. Automatic persistence must occur through Study OS tool calls/runtime events.

## Raw transcript/evidence storage

Keep private raw evidence outside the public Git repository, for example:

```text
~/.study-os/
├── db/study-os.sqlite3
├── evidence/<subject>/<session>/...
├── backups/
└── config/
```

Raw artifacts are immutable after capture and content-addressed/hashed.

Database rows point to artifact IDs/paths and hashes rather than storing all media/blobs inline.

## Backup/recovery invariant

- Deleting FOSSIL must not destroy Study OS.
- Deleting a graph/search projection must not destroy Study OS.
- Losing derived checkpoints must not destroy raw evidence/events.
- A database backup + evidence-store backup must be sufficient to restore local learner continuity.

Add explicit backup/export commands before accumulating valuable longitudinal data.

## FOSSIL boundary

FOSSIL remains downstream and optional.

Study OS may promote:

- curated Golden Learning Trajectories;
- repeated representation findings;
- lesson hypotheses;
- validated domain knowledge;
- research conclusions.

Do not dual-write every learner event into FOSSIL and do not make checkpoint/resume depend on the FOSSIL API.

## Suggested build sequence

### L0 — local storage foundation

1. create project-agnostic SQLite schema + migrations;
2. implement local private evidence store;
3. implement health/doctor + backup/export;
4. implement semantic repository/service layer;
5. implement checkpoint/resume in local DB.

### L1 — Study OS MCP boundary

1. implement semantic MCP tools;
2. validate tool inputs/outputs against versioned schemas;
3. add authentication/authorization assumptions;
4. test locally with deterministic fixtures.

### L2 — ChatGPT integration

1. package the custom Study OS app/plugin surface;
2. connect the WSL MCP server through a secure/private tunnel;
3. verify read/write tool support for the active ChatGPT plan/workspace;
4. test `@StudyOS status`, `resume`, `record_*`, and `checkpoint` from a fresh chat;
5. verify a second fresh chat resumes from the same local checkpoint.

### L3 — automatic instrumentation

After R0 proves the learning loop:

- automatic meaningful event capture;
- boundary-triggered checkpoint proposals;
- retention reminders/probes;
- richer mobile UI;
- Postgres/object-store migration only when justified.

## R0 architecture principle

The learner should be able to focus on learning while agents/tutors call a small number of semantic Study OS tools. The persistence layer, versioning, provenance, scoring, checkpointing, and validation rules belong in Study OS—not in conversational memory and not in GitHub commits.
