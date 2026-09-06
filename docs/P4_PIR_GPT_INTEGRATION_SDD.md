# P4/PIR System Design — Study OS GPT Canonical PIR Integration

Date: 2026-09-05
Status: proposed implementation design
Tracker: #66
Companion: `docs/P4_PIR_GPT_INTEGRATION_PDD.md`

## Design objective

Add a production-facing known-problem PIR teaching path to the existing Study OS application/MCP architecture while preserving the current semantic-tool boundary and evidence durability model.

The MCP server must remain a transport projection. PIR teaching semantics belong below MCP, behind typed application contracts and deterministic domain/controller code.

## Layering

```text
Study OS GPT
    ↓
MCP / GPT Actions transport
    ↓
application contracts + ApplicationService
    ↓
PIR teaching service/controller
    ├── canonical asset registry
    ├── deterministic assessment
    ├── traversal authorization
    ├── representation renderer
    └── problem-run repository
    ↓
existing Study OS runtime/evidence persistence
```

No PIR tool may perform ad-hoc SQL or embed hidden evaluator/oracle data in the MCP layer.

## Pinned module boundary

The portable PIR repository remains the research/schema authority. Production Study OS consumes a reviewed, pinned subset/asset revision.

A problem run stores at least:

```text
canonical_problem_id
canonical_pir_revision
controller_revision
renderer_revision
assessment_revision
```

The revision tuple is immutable for the lifetime of a run. Updating installed assets affects only newly started runs unless an explicit migration contract is designed later.

## Canonical known-problem registry

First registry entry:

```text
canonical_problem_id: sliding-window.max-sum-k.sep4.v1
source: September-4 calibrated sliding-window trajectory
status: reviewed_known_problem
```

Resolution for the first slice is deliberately conservative. `resolve_problem` may recognize only explicit aliases/problem fingerprints registered for this asset. Unknown problems return `needs_compilation`; they are not automatically compiled in this slice.

The live runtime must not import benchmarker oracles. Production assets may contain controller-only assessment expectations required to execute the reviewed lesson, but independent evaluation expectations remain outside runtime context.

## Core production models

All public/application-boundary models are strict, frozen and `extra="forbid"`.

### ProblemResolution

```text
status: known | needs_compilation
canonical_problem_id: str | null
canonical_pir_revision: str | null
reason: str
```

### ProblemRun

```text
problem_run_id: str
subject_id: str
session_id: str
canonical_problem_id: str
canonical_pir_revision: str
controller_revision: str
renderer_revision: str
assessment_revision: str
current_step_id: str
status: active | assembled_mastery_unproven | completed_validated | blocked
transition_seq: int
created_at: UTC datetime
updated_at: UTC datetime
```

`assembled_mastery_unproven` is a terminal status for the September-4 final-code frontier. It must not be aliased to `completed_validated`.

### TeachingTurn

Renderer-safe only:

```text
problem_run_id
turn_id
canonical_step_id
turn_kind: instruction | assessment | correction | expansion | status
representation_id
learner_visible_markdown
response_kind: none | integer | integer_sequence | text | code
allowed_actions
run_status
```

Forbidden from TeachingTurn:

- expected answer;
- grading predicate;
- hidden correction oracle;
- future canonical nodes not authorized for display;
- benchmark oracle fields;
- mastery inference not established by the controller.

### ControllerAssessment

Controller-only:

```text
assessment_id
canonical_step_id
response_kind
expected_value / expected_predicate
normalization_policy
outcome_map
```

It is never projected directly to MCP.

### LearnerOutcome

```text
correct
partial
incorrect
meta
hint_request
unresolved
```

The production integration must preserve PARTIAL distinctly.

### ExpansionRequest

```text
problem_run_id
turn_id
request_kind: why | easier_example | more_detail | repeat_representation | clarify_term
learner_request
```

An expansion request does not itself advance canonical state.

## MCP/application operations

### `resolve_problem`

Mutating: no.

Required input:

```text
problem_text
domain
```

Required output:

```text
status
canonical_problem_id
canonical_pir_revision
reason
```

For unknown input in this slice: `status=needs_compilation`.

### `start_problem`

Mutating/idempotent: yes.

Required input:

```text
idempotency_key
session_id
subject_id
canonical_problem_id
```

Required output:

```text
problem_run_id
canonical_problem_id
canonical_pir_revision
run_status
turn
created
```

A retry with the same idempotency key returns the original run/result.

### `get_problem_turn`

Mutating: no.

Required input:

```text
problem_run_id
subject_id
```

Required output:

```text
problem_run_id
run_status
turn
```

The subject must own the run.

### `submit_problem_response`

Mutating/idempotent: yes.

Required input:

```text
idempotency_key
problem_run_id
subject_id
turn_id
response
```

Required output:

```text
problem_run_id
outcome
run_status
turn
created
```

Algorithm:

```text
load run
→ verify subject/run/turn identity
→ verify turn is current and expects a response
→ normalize according to controller-only assessment policy
→ classify outcome
→ append durable attempt/evidence
→ authorize exactly one next transition
→ persist new problem-run state atomically
→ render next TeachingTurn
→ return renderer-safe result
```

A stale/previous `turn_id` must not advance the run. Exact idempotent retry returns the original result; conflicting reuse of an idempotency key returns conflict.

### `request_problem_expansion`

Mutating/idempotent: yes because the request/result becomes evidence and may select an expansion state.

Required input:

```text
idempotency_key
problem_run_id
subject_id
turn_id
request_kind
learner_request
```

Required output:

```text
problem_run_id
run_status
turn
created
```

Expansion may change the learner-visible turn while preserving the same canonical advancement gate. It may not skip forward.

## Controller transition semantics

Every executable canonical step declares allowed outcomes and target steps.

Example:

```text
SUM_I
  correct   → NEXT_SUM
  partial   → SUM_I_ARITHMETIC_REPAIR
  incorrect → SUM_I_VALUE_LOOKUP_REPAIR
  hint      → SUM_I_HINT
```

Transitions not explicitly declared are forbidden.

Terminal final exposure for the historical slice:

```text
FINAL_COMBINED_LOOP_EXPOSURE
  → ASSEMBLED_MASTERy_UNPROVEN
```

No implicit transition to mastery exists.

## Representation continuity

Each step declares required representation state. The renderer validates that a TeachingTurn contains the required learner-visible elements before release.

For example, recurrence introduction may require:

```text
array
indexes
active_window
sum labels
preserved variable roles
```

A renderer that drops a required element fails closed with an internal/integrity error rather than returning degraded prose.

## Correction mutation budget

Correction states declare preserved elements and allowed changes.

Example:

```text
preserve:
- array
- index row
- learner-correct box contents
allow_change:
- arithmetic prompt
```

This prevents a correction from replacing the entire representation or changing unrelated correct work.

## Persistence

The first implementation should persist problem-run control state in the canonical local Study OS database, not in GitHub and not in GPT conversation memory.

Minimum new durable entities:

### `problem_runs`

- problem_run_id primary key;
- idempotency/start identity;
- subject_id;
- session_id;
- canonical_problem_id;
- pinned revision tuple;
- current_step_id;
- status;
- transition_seq;
- timestamps.

### `problem_run_operations`

Durable idempotency/result ledger for mutating PIR operations:

- operation_id / idempotency_key unique in operation scope;
- problem_run_id;
- operation kind;
- input hash;
- outcome/result payload or result reference;
- created_at.

Existing attempts/learning events/conversation turns remain the evidence authority. Do not create a parallel transcript store.

## Transaction boundary

For `submit_problem_response`, learner attempt/evidence, problem-run transition, and idempotency result must commit atomically where the existing storage architecture permits.

The system must not acknowledge an advanced turn if the durable transition/evidence commit failed.

## Resume/restart

After restart, `get_problem_turn` reconstructs the current TeachingTurn from:

```text
persisted run
+ pinned canonical asset
+ current_step_id
+ renderer revision
```

It must not ask GPT to infer where the lesson was.

If the pinned canonical asset/revision is unavailable after restart, the run becomes blocked/unavailable; it must not silently migrate to another asset revision.

## Existing evidence integration

PIR operations should call/reuse existing evidence semantics rather than duplicating them.

At minimum, production integration records:

- learner attempt response;
- learner outcome classification;
- canonical step/run/revision context;
- representation/operation identity where meaningful;
- source conversation/message references when supplied by the live GPT path.

Transcript language remains evidence, not mastery.

## Error behavior

Use existing application error categories.

Examples:

- invalid problem/run/turn shape → `validation_error`;
- unknown run/problem → `not_found`;
- stale turn or conflicting idempotency reuse → `conflict`;
- missing pinned asset / failed renderer invariant → `integrity_error` or `unavailable` as appropriate;
- unsupported contract/revision → `unsupported_version`;
- unexpected failure → `internal_error` with safe public details only.

No successful-looking TeachingTurn is returned after an unexpected controller/storage failure.

## GPT execution contract

The GPT should be instructed:

1. use PIR semantic tools when a problem run is active;
2. display `learner_visible_markdown` without changing represented roles or leaking answers;
3. do not independently decide the next lesson step;
4. submit learner responses to the active run;
5. route clarification requests through `request_problem_expansion` rather than answering with an unauthorized new abstraction;
6. treat `assembled_mastery_unproven` as exactly that status.

This prompt/instruction contract is versioned independently from controller logic.

## Local Luna boundary

Luna is deployment/integration operator only for this slice.

Allowed local work:

- inspect installed runtime/configuration;
- back up local state;
- apply reviewed migration;
- install exact reviewed commit;
- restart MCP/tunnel;
- execute local integration/live GPT checks;
- fix environment-specific wiring without changing design semantics;
- report sanitized receipts.

Not allowed without returning to review:

- changing canonical graph;
- altering assessment expectations;
- weakening tests;
- editing PDD/SDD/TDD to match local behavior;
- importing benchmark oracle material into runtime;
- changing progression/mastery rules.

## Versioning

The MCP contract must receive a new semantic version when the five operations are exposed. Generated GPT Actions/OpenAPI and application-operation inventories must remain mechanically synchronized with that contract.

Existing MCP v0.3 consumers must either remain supported under the current deployment compatibility policy or the local upgrade must explicitly update the GPT action schema/configuration in the same validated deployment change.
