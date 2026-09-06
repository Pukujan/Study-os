# P4/PIR Test & Verification Design — Study OS GPT Canonical PIR Integration

Date: 2026-09-05
Status: proposed verification authority
Tracker: #66
Companions:
- `docs/P4_PIR_GPT_INTEGRATION_PDD.md`
- `docs/P4_PIR_GPT_INTEGRATION_SDD.md`

## Verification objective

Prove mechanically that the first production-facing PIR teaching slice preserves the September-4 pedagogical constraints while remaining compatible with the existing Study OS application/MCP and evidence architecture.

A visually plausible GPT conversation is not sufficient evidence.

## Required quality gates

Every mergeable implementation must pass:

```text
ruff
mypy --strict
pytest
branch coverage gate already required by repository
application/MCP inventory checks
schema/generated-artifact checks
historical replay tests
pedagogical data-mutation tests
```

Before the trust kernel is declared stable for local deployment, run `mutmut` against the new controller/assessment/renderer core and resolve all critical non-equivalent surviving mutants.

## Traceability matrix

### INV-001 — pinned canonical identity

Requirement: a problem run never silently changes its canonical PIR revision.

Threats:
- restart loads latest asset instead of pinned asset;
- deployment changes current run semantics;
- GPT names a different problem version.

Tests:
- start run, install/register newer asset, get current turn → original revision remains;
- restart/reopen repository → original revision remains;
- missing pinned asset → fail blocked/unavailable, never auto-upgrade.

Mutation:
- replace stored revision lookup with registry latest → test must fail.

### INV-002 — explicit transition authorization

Requirement: only declared outcome edges may advance the run.

Tests:
- each CORRECT/PARTIAL/INCORRECT historical edge;
- unknown outcome rejected;
- direct future-step request rejected;
- stale turn submission rejected;
- duplicate current transition cannot execute twice.

Mutations:
- delete edge check;
- replace target with next list element;
- accept stale turn.

All must be killed.

### INV-003 — PARTIAL is first-class

Historical requirement: correct box contents without requested arithmetic is PARTIAL, not INCORRECT or CORRECT.

Tests:
- exact historical response;
- equivalent whitespace/sequence normalization;
- correct sum → CORRECT;
- wrong values → INCORRECT;
- box contents only → PARTIAL.

Mutations:
- PARTIAL → INCORRECT;
- PARTIAL → CORRECT.

Both must fail.

### INV-004 — renderer-safe/controller-only separation

Requirement: expected answers, grading predicates, hidden correction targets and future-node data are never learner-visible.

Tests:
- recursively inspect serialized TeachingTurn for forbidden controller fields;
- answer-leak mutation fixture is rejected;
- MCP projection contains only renderer-safe turn fields;
- errors do not dump internal controller objects.

Mutation:
- include expected value in TeachingTurn serializer → fail.

### INV-005 — representation continuity

Requirement: required representation elements survive bridges that declare preservation.

Historical examples:
- array/index/box persists through sum validation;
- representation restored before recurrence bridge when required;
- source representation retained when code is introduced.

Tests:
- renderer assertions for required element IDs;
- exact/frozen Markdown fixture where required;
- representation-drop mutation rejected;
- variable-role mutation rejected.

### INV-006 — correction mutation budget

Requirement: corrections preserve already-correct learner work and may modify only declared elements.

Tests:
- max-comparison repair preserves prior code/variables;
- append repair preserves already-correct else recurrence;
- mutation that changes unrelated correct element rejected.

### INV-007 — no answer leakage

Tests:
- exercises never include their own expected answer;
- chart labels do not expose target response;
- controller oracle inaccessible through `get_problem_turn`;
- future code solution absent before authorized exposure.

Data mutations:
- inject answer in chart;
- inject recurrence before bridge;
- inject final loop early.

### INV-008 — no unsupported mastery

Requirement: final historical exposure is `assembled_mastery_unproven`.

Tests:
- final exposure path status exact;
- fatigue/meta stop does not create INCORRECT assessment;
- learner self-report such as “I get it” cannot transition to validated completion;
- no runtime code path aliases assembled exposure to mastery.

Mutations:
- final status → completed/mastered;
- meta response → correct/mastered.

### INV-009 — deterministic state/turn behavior

For a pinned asset/controller/renderer revision:

```text
same run state + same accepted learner response
→ same outcome + same authorized next state + same renderer-safe turn
```

Tests:
- repeated pure controller evaluation identity;
- serialize/deserialize run state and re-render identity;
- unrelated later evidence does not mutate earlier frozen turn identity.

### INV-010 — idempotent mutating operations

Tests:
- same `start_problem` key/input returns same run;
- same `submit_problem_response` key/input returns same transition/result;
- same `request_problem_expansion` key/input returns same result;
- same key with different input returns conflict;
- retry after response-loss does not duplicate attempt/evidence.

### INV-011 — atomic durable advancement

Tests with failure injection/fake repository:
- evidence write fails → run does not advance;
- run-state write fails → no successful next turn acknowledged;
- idempotency result write participates in required transaction semantics;
- reopen after failure shows last committed state only.

### INV-012 — restart/resume

Tests:
- advance N steps, recreate service/repository, get current turn → same step/revision;
- terminal assembled state survives restart;
- active expansion state survives restart if persisted by design;
- missing/corrupt persisted identity fails closed.

### INV-013 — existing MCP compatibility

Tests:
- all current application/MCP conformance tests remain green;
- generated action schema matches new MCP contract version;
- application-operation inventory matches MCP tool inventory;
- semantic-tool-only prohibitions remain green;
- no generic SQL/shell/file/code tool added.

### INV-014 — evidence semantics preserved

Tests:
- submitted learner response produces one durable attempt/evidence chain;
- canonical run/step/revision included in context;
- raw conversation evidence remains distinct from derived outcome;
- derived classification cannot rewrite source turn;
- subject/run mismatch rejected.

### INV-015 — expansion cannot advance

Tests for each allowed request kind:
- `why`;
- `easier_example`;
- `more_detail`;
- `repeat_representation`;
- `clarify_term`.

The returned turn may change presentation/expansion state but canonical advancement gate remains unchanged until a valid response outcome occurs.

Mutation:
- expansion sets next canonical step → fail.

## Historical replay gate

Production integration replay must cover the high-value September-4 behaviors already frozen in the PIR project.

At minimum assert this ordered frontier:

```text
concrete window/index grounding
→ i as box start
→ sum[i]
→ successive sums
→ recurrence bridge
→ repeated recurrence / changing i
→ loop concept
→ Python loop translation
→ source representation restoration
→ max tracking
→ arbitrary k / boundary
→ final combined loop exposure
→ assembled_mastery_unproven
```

Required historical branch checks:

1. correct contents, missing sum → PARTIAL arithmetic repair;
2. representation discontinuity cannot be accepted as a valid recurrence bridge;
3. recurrence cannot be skipped directly to loop/code;
4. max comparison wrong direction routes localized correction;
5. correct recurrence content is preserved while append-specific repair occurs;
6. final fatigue/meta stop is not an incorrect assessment or mastery evidence.

Historical replay tests protect fidelity, not generalization.

## Pedagogical data/specification mutation suite

For each valid canonical fixture create one-mutant-at-a-time cases where practical.

Required mutation classes:

- `REPRESENTATION_DROPPED`;
- `VARIABLE_ROLE_CHANGED`;
- `LANGUAGE_REGISTER_JUMP` where register is constrained by the fixture;
- `TOO_MANY_NEW_VARIABLES`;
- `UNSUPPORTED_ADVANCE`;
- `SKIPPED_BRIDGE`;
- `OVER_DECOMPOSITION`;
- `UNDER_DECOMPOSITION`;
- `ANSWER_LEAKAGE`;
- `CHART_COMPLEXITY_JUMP`;
- `PROBLEM_CONTEXT_LOST`;
- `CORRECTION_CHANGED_TOO_MUCH`;
- `WRONG_ABSTRACTION_LEVEL`;
- `SELF_REPORT_TREATED_AS_MASTERY`.

A required mutation must either:

- be rejected by fixture/controller validation;
- become explicitly unresolved/blocked; or
- trigger the named failure code.

It may not silently render as a normal valid lesson.

## Implementation mutation testing

Initial `mutmut` target modules:

```text
problem asset validation
assessment classification
transition authorization
representation requirement checks
renderer-safe serialization
problem-run status/mastery gate
idempotency checks
```

Critical mutants include:

- invert outcome comparison;
- remove PARTIAL branch;
- bypass turn-id check;
- omit representation requirement;
- expose expected answer;
- change terminal status;
- ignore pinned revision;
- allow expansion to advance;
- convert conflict into success.

Critical non-equivalent survivors must be zero before the first local deployment checkpoint is declared green.

## Property/metamorphic tests

Where pure boundaries permit Hypothesis:

- valid model JSON round-trip preserves semantic identity;
- arbitrary whitespace in learner integer-sequence input does not change classification;
- changing unrelated metadata cannot change deterministic outcome;
- appending later unrelated evidence cannot change an earlier frozen TeachingTurn;
- same canonical asset serialized in canonical order produces stable content identity;
- invalid future-step insertion always violates transition validation.

## Live-local validation by Luna

The local validation is a separate evidence lane from CI.

Luna must record:

```text
Study OS commit
PIR asset/revision
DB schema before/after
MCP contract version before/after
tool inventory before/after
full local test result
doctor result
known sliding-window smoke result
restart/resume result
GPT action-schema update result
sanitized live GPT validation result
unreviewed/local-only changes = none, or explicit list
```

A local test pass does not override failed public CI or design tests.

## Live GPT dogfood acceptance

A real Study OS GPT session must demonstrate:

- problem resolves to the known canonical asset;
- first TeachingTurn is backend-authorized;
- GPT does not rewrite critical representation state;
- historical PARTIAL behavior can be exercised;
- clarification can be requested without progression jump;
- transition sequence is durable;
- restart/resume is correct;
- final status remains mastery-unproven;
- raw learner/assistant turns remain durably captured.

Any discrepancy becomes a new regression fixture/issue entry rather than being dismissed as prompt variance.

## PAM evidence checkpoints

Checkpoint A — design + implementation verification:
- exact commit;
- PDD/SDD/TDD versions;
- CI result;
- historical replay result;
- data mutation result;
- implementation mutation result;
- known risks/unproven claims.

Checkpoint B — local MCP deployment:
- exact deployed commit;
- migration/runtime receipt;
- old/new tool inventory;
- health/restart/resume evidence;
- no unreviewed local semantic changes.

Checkpoint C — live GPT PIR dogfood:
- exact deployed revisions;
- sanitized run identity;
- observed path/result;
- regressions discovered;
- explicit claim boundary: product-integration validation only, not learning efficacy/generalization.
