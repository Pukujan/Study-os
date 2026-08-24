# Validation Strategy — Study OS v0.1

Study OS handles longitudinal learner evidence. A silent correctness failure is a research-data failure, not merely a software bug. Validation therefore covers software behavior, evidence integrity, privacy, checkpoint continuity, and learning-experiment semantics.

## Validation levels

### V0 — static contract validation

Validate without a running local service:

- JSON/YAML/schema syntax;
- semantic MCP tool contract shape;
- required tools present;
- prohibited generic tools absent;
- version identifiers present;
- public/private path rules;
- project manifest invariants.

### V1 — database and migration validation

Local Luna must test:

- empty DB -> latest schema;
- migration ordering;
- migration repeat safety;
- foreign-key enforcement;
- uniqueness/idempotency constraints;
- invalid schema version detection;
- downgrade/unsupported-version behavior defined explicitly;
- indexes required for session/current-checkpoint queries.

### V2 — evidence integrity validation

Required invariants:

- raw artifacts have stable content hashes;
- raw artifacts are immutable after capture;
- observed/self_reported/derived remain distinct;
- derived state requires evidence references;
- source IDs must resolve;
- deleted/missing evidence invalidates dependent derived snapshots rather than silently passing;
- representation outcomes reference a real intervention + assessment;
- timestamps are recorded but never fabricated when unavailable.

### V3 — semantic service validation

Test service methods independently of MCP:

- start/resume session;
- record event;
- record attempt/assessment;
- record intervention/outcome;
- create checkpoint;
- get current state;
- retention scheduling/status;
- health/doctor.

Test success and rejection paths.

### V4 — MCP contract/conformance validation

The MCP server must:

- expose only versioned approved semantic tools;
- validate input and output payloads;
- return stable error categories;
- not expose SQL, shell, generic file writes, or arbitrary code execution;
- preserve idempotency keys on durable write operations;
- map each tool to the service layer rather than direct ad-hoc SQL.

### V5 — checkpoint/resume validation

Critical sequence:

1. create evidence;
2. create checkpoint;
3. verify checkpoint references evidence;
4. atomically advance current pointer;
5. start a separate service/session process;
6. resume;
7. verify exact accepted checkpoint + next action returned;
8. corrupt pointer and ensure `doctor` fails;
9. restore pointer and ensure continuity returns.

Checkpoint creation must never mark untested capability as passed.

### V6 — backup/restore validation

Before real longitudinal learning data accumulates:

- create DB + evidence fixture;
- backup both;
- hash backup artifacts;
- delete/replace working DB/evidence copy;
- restore;
- verify logical record counts;
- verify checkpoint IDs/current pointer;
- verify raw evidence hashes;
- verify `doctor` passes.

A backup that has never been restored is not considered validated.

### V7 — failure-injection validation

Test at minimum:

- process interruption during checkpoint creation;
- repeated request/retry with same idempotency key;
- malformed MCP payload;
- missing source evidence;
- evidence hash mismatch;
- stale schema/migration version;
- DB locked/busy condition;
- missing private evidence directory;
- invalid representation version;
- invalid checkpoint current pointer;
- partial backup;
- service restart between record and resume.

The system must fail visibly without inventing or silently dropping learning state.

### V8 — privacy/security validation

- raw/private transcript artifacts never enter public Git by default;
- local evidence permissions are restrictive where supported;
- secrets/tunnel credentials stay outside repository;
- MCP does not expose arbitrary machine access;
- logs avoid raw sensitive transcript bodies by default;
- export commands are explicit and scoped;
- FOSSIL export does not automatically include all micro-events.

### V9 — cross-client / cross-session acceptance

Manual end-to-end acceptance once the MCP bridge exists:

- Chat A invokes Study OS and records a short fixture/real session;
- checkpoint is created;
- Chat B has no access to Chat A conversation text;
- Chat B calls `resume`;
- returned learner state matches DB checkpoint;
- Chat B begins at `next_action` rather than reteaching completed material;
- a new event can be written and checkpointed;
- DB continuity survives service restart.

### V10 — learning-validity validation

Software success is insufficient. For R0 we also require:

- confusion/self-report is not counted as mastery loss;
- intervention family + operation + version recorded;
- behavioral probe after representation change;
- assistance level recorded;
- faded/unaided retest;
- changed-surface transfer;
- delayed retention;
- representation effectiveness score based on evidence, not preference alone;
- learner capability dimensions remain separate;
- tier promotion cannot be caused by one lucky problem.

## Test evidence hierarchy

Prefer, in order:

1. deterministic unit tests;
2. property/invariant tests;
3. integration tests against temporary SQLite/evidence directories;
4. contract tests against MCP schemas;
5. failure-injection tests;
6. backup/restore test;
7. manual secure-tunnel ChatGPT acceptance;
8. longitudinal learner experiment.

## Required test artifacts from Luna

A Luna implementation PR should include:

- migration files;
- unit tests;
- integration tests using a temporary DB;
- one deterministic end-to-end fixture;
- one backup/restore test;
- one idempotency/retry test;
- one corruption/doctor failure test;
- generated/declared MCP tool list for conformance comparison;
- local test command(s) and captured summary in PR description.

## Release rule

No `v0.1-ready` claim until P0 technical acceptance and P1 cross-session continuity both pass. No learning-method efficacy claim until P2 learning-validity evidence exists.
