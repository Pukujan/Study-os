# Agent Handoff

Last updated: 2026-09-07
Primary tracker: #63
PIR integration tracker: #66

## Current phase

**P4 — deterministic learning controller + versioned representation engine + operational improvement loop.**

Study OS is being used for real learning. The product center is deterministic control of curriculum/progression plus versioned, bounded AI diagnosis and representation generation.

## Accepted foundation

The durable P3 evidence/continuity substrate remains operational and supporting:

- learner-facing surface: Study OS GPT;
- stable learner identity: `subject-001`;
- canonical local learner state: SQLite + private evidence store;
- durable learner/assistant source turns;
- cross-chat continuity;
- source evidence distinct from capability/mastery;
- backup/restore and doctor/integrity protections.

GitHub contains public-safe architecture, contracts, tests, schemas and curated regression evidence, not the live learner database.

## PIR / PAM state

The known sliding-window PIR integration has completed PAM Checkpoint A assurance.

Accepted evidence:

```text
PR #71: merged
verified PR head: 0ccfc9245cc86acdd68587f4bf72158d18ac2070
normal CI: PASS on same SHA
PIR Mutation Gate: PASS on same SHA
mutants: 1268 total / 1064 killed / 204 classified survivors
timeouts: 0
other failures: 0
unresolved non-equivalent semantic survivors: 0
```

Do not reopen mutation assurance merely because raw survivors remain. Equivalent and diagnostic/non-authority survivors were explicitly classified by the gate.

The existing #66 sequence remains:

```text
PAM A — complete
→ PAM B — pinned local MCP deployment + restart/resume validation
→ PAM C — first real Study OS GPT PIR dogfood receipt
```

PAM B is the next persistent-local/Luna deployment lane. Do not mix that deployment work with the P4 teaching-controller design branch.

## New operational teaching regression

A mutation-testing dogfood lesson exposed a controller/representation failure before any canonical learner answer was submitted.

Public-safe interpretation:

- code-first presentation was not sufficiently understandable to attempt the task;
- repeated same-target explanation did not resolve the barrier;
- the learner explicitly requested a visual/chart representation;
- a later concrete capacity/ticket framing was more intuitive;
- canonical attempts correctly remained zero because no valid parent-task response was submitted.

Treat this as **system/pedagogical routing evidence**, not a learner task failure and not proof that one particular analogy is universally superior.

## Current focused P4 delta

Branch under development:

`codex/p4-prerequisite-sensitive-remediation`

Focused specs:

- `docs/P4_PREREQUISITE_REMEDIATION_PDD.md`
- `docs/P4_PREREQUISITE_REMEDIATION_SDD.md`
- `docs/P4_PREREQUISITE_REMEDIATION_TDD.md`

The delta implements/shapes:

```text
source learner difficulty evidence
→ versioned schema-constrained DiagnosisProposal
→ deterministic prerequisite-sensitive remediation router
→ parent progression blocked
→ canonical missing prerequisite selected only when justified
→ bounded operation set
→ structured representation constraints
→ behavioral micro-probe
→ later controller-authorized parent re-entry
```

New versioned diagnosis artifacts:

- `prompts/p4/diagnosis-proposal.v0.1.md`
- `schemas/p4-diagnosis-proposal.schema.json`
- `src/study_os/adaptive/diagnosis.py`

New deterministic router:

- `src/study_os/adaptive/prerequisite_remediation.py`

The existing representation policy remains downstream of task/competency selection and now carries richer structural rendering constraints.

Public-safe regression fixture:

- `tests/fixtures/p4_mutation_lab_representation_failure.v0.1.json`

Focused tests:

- `tests/test_p4_prerequisite_remediation.py`

## Authority boundary

Study OS code/state controls:

- active course node/competency;
- canonical prerequisite graph;
- prerequisite satisfaction;
- progression blocking/advancement;
- allowed remediation target;
- assistance ceiling;
- legal pedagogical operations;
- evidence semantics;
- parent re-entry.

AI may:

- propose diagnosis hypotheses through a pinned prompt/schema;
- propose representation signals;
- realize an authorized representation.

AI may not:

- invent prerequisite IDs;
- grade representation confusion as a parent-task failure;
- advance course/mastery state;
- exceed assistance limits;
- silently alter prompt/schema/module versions.

## Unfamiliar problems / no-dataset boundary

Versioned prompt engineering + schema-constrained outputs are part of the intended solution for unfamiliar problems, but arbitrary raw-problem compilation is still deferred from the live learner product.

Long-horizon path:

```text
raw unfamiliar problem
→ versioned semantic/decomposition compiler prompt
→ schema-constrained candidate concept/prerequisite graph
→ deterministic validation
→ accepted graph version
→ normal deterministic learning controller
```

Until that compiler is separately validated, the remediation router may traverse only an already-canonical prerequisite graph.

When learner state is uncertain, prefer an explicit diagnostic probe over fabricated prerequisite/mastery claims.

## Planning authority

Read current material in this order:

1. Issue #63
2. Issue #66 for the PIR/PAM deployment sequence
3. `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`
4. `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`
5. `docs/ADR-0016-deterministic-learning-control.md`
6. focused prerequisite-remediation PDD/SDD/TDD
7. `docs/ROADMAP.md`
8. `docs/CURRENT_STATE.md`
9. `PROJECT_MANIFEST.yaml`
10. latest accepted `docs/DECISIONS.md`

Historical checklists do not override later accepted implementation/evidence.

## Immediate next work

For the focused prerequisite-remediation branch:

1. run the focused regression suite;
2. run compile/lint/type/repository validation;
3. use normal PR CI as clean independent attestation;
4. fix only implementation/spec-conforming failures;
5. do not promote the new adaptive path beyond shadow authority in this slice;
6. merge only after review/green evidence.

In parallel, a separate persistent local session may execute PAM B from #66 against the merged known PIR revision. It must not redesign this teaching architecture merely to obtain deployment green.

## Non-negotiable invariants

1. No silent learner-evidence loss.
2. Course progression is code/state controlled.
3. AI diagnosis is a hypothesis, not truth.
4. AI behavior is bounded by explicit authorized operations.
5. Representation difficulty must not be silently graded as concept failure.
6. Ambiguous prerequisite diagnosis fails closed.
7. Raw/source evidence survives module/model changes.
8. Prompt/schema/module evolution is explicit and versioned.
9. Same canonical controller inputs + controller version produce the same authorization.
10. Historical/replay evidence never masquerades as learner-experienced outcome.
11. Source/authentic representations remain restorable where claimed.
12. Arbitrary raw-problem compilation remains deferred until separately validated.

## Known hazards

- prerequisite misdiagnosis may route to the wrong remediation target;
- a representation that looks clearer may still fail to improve behavior;
- one learner trajectory is not population evidence;
- model-generated decomposition must not become canonical without validation;
- local deployment state can drift from public contracts;
- a tutor/model must not reinterpret controller output as permission to advance.
