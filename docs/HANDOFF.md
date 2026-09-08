# Agent Handoff

Last updated: 2026-09-08
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

The known sliding-window PIR integration has completed PAM Checkpoints A and B.

Accepted PAM-A evidence:

```text
PR #71: merged
verified PR head: 0ccfc9245cc86acdd68587f4bf72158d18ac2070
merge/deployment baseline: 151c819e3457ae41fa1810b5060d0101f91bc12a
normal CI: PASS on verified head
PIR Mutation Gate: PASS on verified head
mutants: 1268 total / 1064 killed / 204 classified survivors
timeouts: 0
other failures: 0
unresolved non-equivalent semantic survivors: 0
```

Accepted PAM-B evidence from Issue #66:

```text
deployed revision: 151c819e3457ae41fa1810b5060d0101f91bc12a
schema: 2 via reviewed 0002_pir_problem_runs.sql
local tests: 342 / 342 PASS
MCP/private transport: healthy
semantic tools: 20 total, including 5 PIR tools
generic capabilities: none
known sliding-window resolution: PASS
restart/resume: PASS on same ProblemRun + pinned revisions
retry/idempotency: PASS
local_only_changes: []
```

The initial Windows CRLF mismatch during PAM B was accepted as repository-byte/environment normalization, not a semantic local repair.

Do not reopen PAM A or B unless new evidence invalidates their accepted claims.

Current checkpoint state:

```text
PAM A — PASSED
PAM B — PASSED
PAM C — NEXT / NOT YET CLAIMED
```

A later Issue #66 planning comment accidentally regressed PAM B to “not yet passed”; the 2026-09-08 ledger correction supersedes that stale status.

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

Canonical review PR:

`#75 — Add prerequisite-sensitive remediation control`

Branch:

`codex/p4-prerequisite-sensitive-remediation`

Superseded planning PRs #73 and #74 are closed. Useful broader #73 concepts were retained as candidate Issue #63 backlog; #74's unique deferred live-authority requirements were preserved in:

- `docs/P4_PREREQUISITE_REMEDIATION_DEFERRED_LIVE_REQUIREMENTS.md`

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

This path remains **shadow authority** in this slice and is not part of the accepted PAM-B deployment receipt.

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
2. Issue #66 for PIR/PAM checkpoint evidence
3. `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`
4. `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`
5. `docs/ADR-0016-deterministic-learning-control.md`
6. focused prerequisite-remediation PDD/SDD/TDD
7. `docs/P4_PREREQUISITE_REMEDIATION_DEFERRED_LIVE_REQUIREMENTS.md`
8. `docs/ROADMAP.md`
9. `docs/CURRENT_STATE.md`
10. `PROJECT_MANIFEST.yaml`
11. latest accepted `docs/DECISIONS.md`

Historical checklists and superseded PRs do not override later accepted evidence.

## Immediate next work

1. Keep PR #75 green/reviewable and do not reinterpret its shadow code as part of the PAM-B deployment receipt.
2. Run **PAM C** through the real Study OS GPT against the exact PAM-B deployment baseline `151c819e3457ae41fa1810b5060d0101f91bc12a`.
3. During PAM C, verify backend-authorized renderer-safe state, free-language requests without unauthorized advancement, durable learner/assistant turns, and discrepancy capture.
4. Preserve the PAM-C receipt before changing the deployed baseline.
5. Review/merge #75 as a separate product-controller revision; promote it only through its own repo/local/live evidence sequence.
6. Use PAM-C and later prerequisite-remediation dogfood trajectories to drive versioned controller/representation changes rather than silent prompt edits.
7. Keep general learner-facing raw-problem compilation deferred until its separate compiler/validation gate.

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
13. Accepted PAM receipts remain pinned to their exact revisions and cannot be silently reinterpreted after later product changes.

## Known hazards

- prerequisite misdiagnosis may route to the wrong remediation target;
- a representation that looks clearer may still fail to improve behavior;
- one learner trajectory is not population evidence;
- model-generated decomposition must not become canonical without validation;
- local deployment state can drift from public contracts;
- a tutor/model must not reinterpret controller output as permission to advance;
- stale planning comments can regress accepted checkpoint status unless evidence receipts remain explicitly pinned.
