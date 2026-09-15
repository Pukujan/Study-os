# Local Luna autonomous model-tutoring loop v1

Status: **primary local orchestration handoff for the next model-tutoring implementation/evaluation cycle.**

This document combines the completion-driven tutoring contract, DSA decomposition skill, rotating public batches, prompt versioning, and private hidden-promotion boundary into one resumable local engineering loop.

## Read first

Local Luna must read, in order:

1. `plugins/study-os-dsa-decomposer/skill.md`
2. `plugins/study-os-dsa-decomposer/checklist.md`
3. `docs/MODEL_TUTORING_COMPLETION_DRIVEN_VNEXT.md`
4. `docs/MODEL_TUTORING_ROTATING_HOLDOUT_EVAL_V1.md`
5. `contracts/model-tutoring-agent-boundaries.v0.1.json`
6. `domains/dsa/_knowledge/model-tutoring-evolution/README.md`
7. current `src/study_os/prompt_registry.py`
8. current TeachingPlan/controller/runner/acceptance tests and Issue #63 / PR #77 evidence

Historical 14×15 artifacts are regression/calibration evidence, not the current completion target.

## Immediate truth about readiness

The architecture/policy is ready to implement locally, but the current PR head is **not yet ready for an expensive measured tutoring run**.

Known preflight work includes the current Pyright errors in generic model-tutoring code plus the vNext completion/vocabulary/rotation/holdout orchestration that still needs implementation.

Do not spend model inference until the engineering baseline is green.

## Local-only goal

After this handoff is implemented, the full improvement loop can run on the learner's local machine:

```text
public repo + local Luna
        ↓
build/fix candidate
        ↓
unit/property/mutation/type/lint gates
        ↓
freeze candidate identity
        ↓
automatically select 4 public regression problems
        ↓
completion-driven measured learner ↔ teacher runs
        ↓
deterministic acceptance + learner-visible review
        ↓
public diagnosis / generic fix
        ↓
new candidate
        ↓
different public batch
        ↓
...
        ↓
promotion checkpoint
        ↓
isolated private holdout evaluator
        ↓
promote incumbent or reject
```

No cloud service is required by the architecture except whatever model runtime Local Luna itself uses. GitHub remains source/evidence/CI; local Study OS remains the place to run the long engineering loop.

## Roles and who checks the run

### 1. Engineering orchestrator — Local Luna

Owns:

- code/schema/test changes;
- new prompt versions;
- public rotating evaluation;
- reading public/ burned failure artifacts;
- generic diagnosis/fixes;
- durable iteration ledger.

Must not see unburned hidden holdout problems or hidden oracles.

### 2. Measured decomposer

Uses `plugins/study-os-dsa-decomposer/skill.md` with the strongest available reasoning to produce the algorithm graph + learning graph + vocabulary/representation plan for the current problem.

Receives only the current problem statement and frozen prompt/schema/skill bundle.

Cannot write code/prompts/schema during a measured run.

### 3. Deterministic validators/controller

Primary trust boundary during every public and hidden run.

Checks:

- TeachingPlan schema;
- prerequisite legality;
- vocabulary/symbol grounding;
- semantic invariants;
- stable variable/concept meanings;
- evidence binding to actual learner messages;
- correction → changed retry → verification policy;
- assistance ceilings;
- representation continuity/authorized repair;
- completion/base/integration evidence;
- stall/anti-loop behavior;
- prompt/model/schema/run provenance.

A model cannot self-certify these conditions.

### 4. Per-problem acceptance checker

After a run, independently reconstructs state/trace and must report pass only if the generated plan is actually complete.

No aggregate pass can hide one failed problem.

### 5. Learner-visible reviewer

For public development runs, a separate reviewer pass (Local Luna or Terra) inspects the visible transcript for semantic/pedagogical pathologies not yet encoded in deterministic gates.

Reviewer findings are diagnostic evidence, not permission to override a deterministic failure.

Any repeatable finding should be promoted into an automated invariant/test.

### 6. Hidden holdout evaluator

At promotion checkpoints, a separate **isolated local evaluator process/agent** receives:

- the frozen candidate;
- private hidden problem statements;
- private evaluator oracles.

It may inject the current hidden problem statement into the measured decomposer/teacher/student run.

It must never inject the oracle into those measured agents.

It returns only a sanitized promotion report to the engineering orchestrator.

The engineering orchestrator/prompt-fixer does not receive the holdout root or raw hidden case content.

## Hidden holdout — practical local isolation

Do not give the main engineering Luna `STUDY_OS_HOLDOUT_DIR`.

Recommended process boundary:

```text
engineering shell/process
  env: no STUDY_OS_HOLDOUT_DIR
  repo: writable
  prompts/code: editable
        │
        │ frozen candidate bundle / commit identity
        ▼
holdout evaluator process
  env: STUDY_OS_HOLDOUT_DIR=/private/untracked/path
  repo/candidate: read-only snapshot
  prompts/code: not editable
  holdout: readable
        │
        ├─ inject problem statement only → measured decomposer
        ├─ inject problem statement only → measured teacher/student context
        └─ oracle stays evaluator-only
        │
        ▼
sanitary result
  pass/fail
  aggregate metrics
  stable failure codes
  family-level diagnostic category
  opaque case token if a burn is required
```

The measured decomposer/teacher may see the current hidden **problem statement** because they must solve/teach it, but they receive no directory path and no oracle.

### Burn workflow

If a hidden failure needs raw case inspection to fix:

```text
opaque failing holdout token
        ↓
explicit burn action
        ↓
export reviewed problem + relevant evidence into public regression
        ↓
mark hidden case burned
        ↓
engineering Luna may inspect and fix
        ↓
replace hidden case before relying on that holdout bank again
```

This keeps holdout management practical: no elaborate remote security system is required, only process/env/workspace separation and an explicit burn command.

## Prompt versioning

The repository already has immutable content-addressed prompt definitions in `src/study_os/prompt_registry.py`.

Preserve that design.

For the next implementation:

- do not edit historical `study-os.model-tutoring-decompose.v1` semantics in place;
- register a new decomposition prompt version for the skill-based strong-inference contract;
- create a new diagnosis prompt version if correct-but-tentative/confidence handling materially changes;
- create a new generation prompt version if vocabulary grounding or bounded generation semantics materially change;
- every plan/turn/iteration report must persist version + SHA-256 hash + model identifier + schema version + run/candidate identity.

Candidate identity changes whenever any prompt content/hash, code commit, schema semantic version, decomposer skill version, or evaluation-policy version changes.

## Reasoning against the public dataset

Use `datasets/dsa-conversation-replay.v0.1.json` and preserved calibration transcripts as **public regression/calibration evidence**.

Allowed uses:

- differential behavior checks;
- learner-style simulation;
- known semantic invariants;
- representation/vocabulary calibration;
- historical failure regression;
- rotation batch selection.

Do not pass hidden benchmark acceptance labels/solution assertions into the measured teacher.

Do not optimize solely for exact transcript wording/order.

The decomposer's algorithm model must be derived from the supplied problem under the skill contract, not copied from a hand-authored 14-problem lesson table.

## Long-running local state machine

Implement a resumable orchestrator, conceptually:

```text
PRECHECK
  ↓
BUILD_CANDIDATE
  ↓
TEST
  ├─ fail → FIX → TEST
  └─ pass
       ↓
FREEZE_CANDIDATE
       ↓
SELECT_PUBLIC_BATCH_4
       ↓
RUN_PUBLIC_BATCH
       ↓
CHECK_ACCEPTANCE
  ├─ fail → DIAGNOSE_PUBLIC → FIX → new candidate
  └─ pass
       ↓
APPEND_LEDGER
       ↓
MORE_PUBLIC_EPOCH_COVERAGE?
  ├─ yes → next candidate/next 4
  └─ no
       ↓
PROMOTION_HOLDOUT
  ├─ fail without raw reveal → reject candidate, continue public engineering
  ├─ needs diagnosis → burn case → public regression → fix
  └─ pass → mark candidate incumbent
       ↓
CONTINUE FUTURE ITERATIONS
```

The loop must be restartable from its durable ledger and batch manifests. A crash/restart must not silently reseed or choose a different batch for the same frozen candidate/iteration.

## Suggested local orchestration surface

Local Luna may choose cleaner names, but implement equivalent behavior to:

```bash
python tools/run_model_tutoring_autonomous_loop.py \
  --public-dataset datasets/dsa-conversation-replay.v0.1.json \
  --agent-boundaries contracts/model-tutoring-agent-boundaries.v0.1.json \
  --batch-size 4 \
  --max-exchanges-per-problem 250 \
  --resume
```

Useful modes:

```text
--preflight-only
--one-public-iteration
--public-iterations N
--until-public-epoch-complete
--promotion-holdout
--burn-holdout-case <opaque-token>
--resume
```

Do not implement an infinite unbounded self-edit loop with no promotion controls. The long-running goal should be a durable sequence of frozen candidates and measured evaluations.

## Durable ledger

Persist append-only iteration records with at least:

- iteration ID;
- parent/incumbent candidate ID;
- candidate commit SHA;
- prompt versions/hashes;
- skill/checklist versions;
- TeachingPlan/trace schema versions;
- model identifiers;
- public selection seed;
- eligible public problem IDs;
- previous batch IDs;
- selected four IDs + family tags;
- per-problem completion status;
- exchange counts;
- retry/verification/elaboration counts;
- deterministic failure codes;
- reviewer findings;
- prompt-evaluation result;
- candidate outcome (`rejected`, `continue_testing`, `promotion_eligible`, `incumbent`);
- hidden promotion report reference containing no raw hidden data.

Recommended path remains:

`artifacts/model-tutoring-eval-ledger.jsonl`

## Public rotating batch policy

For each routine iteration:

- exactly four public problems;
- candidate frozen before selection;
- deterministic recorded seed;
- no overlap with immediately previous batch;
- without-replacement coverage within an epoch;
- maximize structural-family diversity when possible;
- each problem completion-driven;
- batch fails if any individual problem fails.

Do not manually pick convenient problems after seeing a candidate.

## Hidden promotion cadence

Do not spend hidden cases every iteration.

Run hidden promotion after broad public rotation is credible, and after material changes to core tutoring semantics when promotion evidence is needed.

A default practical cadence is one hidden promotion checkpoint after a full public shuffle-bag epoch has been exercised across successive four-problem iterations, provided the latest candidate remains non-regressive.

## Preflight implementation tasks before the next four

Local Luna should now:

1. fix current Pyright failures generically;
2. add/validate the new DSA decomposer skill contract in the local orchestration path;
3. version the decomposition prompt rather than overwrite v1;
4. extend TeachingPlan semantics for algorithm graph, learning graph, vocabulary grounding, completion evidence, retry/verification, and compact representation rationale;
5. implement deterministic checklist-equivalent validation;
6. implement completion-driven runner semantics;
7. implement public shuffle-bag selector and append-only ledger;
8. implement the role boundary contract and ensure ordinary engineering processes cannot read the holdout env/path;
9. implement isolated holdout evaluator + sanitized report + burn workflow;
10. add focused/property/mutation tests for all of the above;
11. run full repo gates;
12. commit/freeze the candidate;
13. only then select and execute the first automatic four-problem public batch.

## Tests required for isolation

At minimum add tests proving:

- engineering role cannot resolve/read `STUDY_OS_HOLDOUT_DIR` through the ordinary loop;
- hidden oracle never appears in decomposer/teacher/student prompts, traces, transcripts, or public artifacts;
- evaluator can validate a hidden case against the oracle;
- sanitized report cannot reconstruct raw hidden solution/problem content;
- frozen candidate is read-only in holdout evaluation;
- revealing/burning a hidden case removes it from future hidden eligibility;
- burned case can enter public regression with provenance;
- a replaced hidden case has a new private identity;
- public batch selection remains reproducible and no-immediate-repeat after restart.

## Stop / promotion conditions

A candidate is not promotion-ready unless:

- repo gates are green;
- public rotating completion evidence is healthy;
- learner-visible review is coherent;
- live prompt evaluation actually executed;
- no learner had to repair tutor semantics;
- hidden evaluator passes a genuinely unburned promotion batch;
- exact candidate prompt/schema/model/skill provenance is present.

Keep PR #77 draft until those conditions have credible evidence.
