# Local Luna handoff — next completion-driven 4-problem iteration

Status: **next execution handoff after the completion-driven + rotating-evaluation policy decisions.**

Read first:

1. `docs/MODEL_TUTORING_COMPLETION_DRIVEN_VNEXT.md`
2. `docs/MODEL_TUTORING_ROTATING_HOLDOUT_EVAL_V1.md`
3. `domains/dsa/_knowledge/model-tutoring-evolution/README.md`
4. current PR #77 / Issue #63 evidence

Do not start the expensive learner ↔ tutor run until the preflight implementation below is complete.

## Goal of this iteration

Run **exactly four public regression DSA problems** through the new completion-driven generic model-tutoring path, selected only after the candidate implementation/prompt/schema commit is frozen.

This is a development iteration, not a promotion holdout.

The four problems must:

- come from the existing public DSA regression corpus;
- be selected by the durable shuffle-bag policy;
- not overlap the immediately previous rotating batch;
- maximize structural-family diversity when possible;
- run until actual TeachingPlan completion or explicit failure;
- use the learner-calibrated vocabulary + symbolic/state-transition policies;
- preserve full prompt/model/schema/run provenance.

Do not manually choose four problems because they look convenient.

## Phase 0 — fix current engineering baseline first

The current PR line has a known Pyright failure in the generic model-tutoring implementation (`Any | None` flowing into required string fields).

Before model inference:

```bash
git pull --ff-only
pytest -q
ruff check .
pyright
```

Fix failures generically. Do not spend a learner-model run on a type-red candidate.

## Phase 1 — implement vNext TeachingPlan inference contract

The decomposer should use strong inference before learner-visible tutoring to produce:

### Algorithm graph

```text
primitive objects
→ state
→ invariant
→ transition / recurrence
→ terminal/base condition
→ integrated solution
```

### Learning graph

```text
primitive meaning
→ vocabulary / symbol grounding
→ relation
→ representation bridge
→ state transition
→ control flow / recursion
→ integration
```

Algorithm complexity and learning complexity are different quantities.

The plan should support candidate representation generation/selection and persist a compact structured rationale without exposing private chain-of-thought.

For the calibrated learner, grounded algebraic/symbolic/state-transition representations receive a positive prior when they simplify the structure, but no universal equation-first rule is allowed.

## Phase 2 — implement vocabulary contract

Add schema/model support and validation for vocabulary grounding.

At minimum support equivalent semantics for:

- canonical term;
- starter/simple expression;
- grounding requirement;
- introduction node;
- stable concept binding;
- allowed/forbidden aliases;
- learner-facing symbols requiring grounding.

Add validator/test coverage for:

- undefined technical term;
- synonym drift;
- term overload;
- vocabulary jump;
- symbol-before-meaning;
- premature formalism;
- metaphor breaking an invariant.

Default learner-facing policy: normally introduce at most one genuinely new technical term and one new semantic relation in a turn unless the plan explicitly justifies more.

Do not simplify terminology at the cost of semantic accuracy.

## Phase 3 — implement completion-driven runner + rotating evaluation ledger

The runner must no longer depend on exactly 15 learner exchanges.

Implement or generalize one orchestration entry point with equivalent behavior to:

```bash
python tools/run_model_tutoring_iteration.py \
  --policy configs/model-tutoring-eval-policy.v1.json \
  --batch-size 4 \
  --completion-driven \
  --max-exchanges-per-problem 250
```

Exact file/command names may differ if a cleaner implementation already exists.

Required behavior:

1. read an append-only evaluation ledger;
2. derive eligible public problems;
3. derive/record the deterministic selection seed;
4. apply shuffle-bag + no-immediate-repeat + family-diversity policy;
5. persist batch manifest **before** tutoring inference;
6. run each selected problem until completion or explicit failure;
7. run vNext acceptance per problem;
8. execute live prompt-evaluation cases required by policy;
9. append results to the ledger;
10. emit a compact iteration report.

Recommended durable files:

```text
configs/model-tutoring-eval-policy.v1.json
artifacts/model-tutoring-eval-ledger.jsonl
artifacts/model-tutoring-iteration-<id>-batch.json
artifacts/model-tutoring-iteration-<id>-plans.jsonl
artifacts/model-tutoring-iteration-<id>-transcript.jsonl
artifacts/model-tutoring-iteration-<id>-transcript.md
artifacts/model-tutoring-iteration-<id>-trace.jsonl
artifacts/model-tutoring-iteration-<id>-acceptance.json
artifacts/model-tutoring-iteration-<id>-prompt-eval.json
```

Do not overwrite historical 14×15 or prior vNext artifacts.

## Phase 4 — tests before inference

Add focused tests that must pass before the 4-problem model run:

1. incomplete-plan false-positive regression;
2. correct-but-tentative learner evidence;
3. wrong → correction → changed retry → independent verification;
4. learner never required to correct tutor semantics;
5. grounded-symbol requirement;
6. vocabulary contract failures listed above;
7. schema supports array/index, linked-list pointer, tree recursion, and graph queue/visited state;
8. completion impossible until all required nodes + terminal/integration evidence exist;
9. anti-loop budget exhaustion is explicit failure;
10. batch selector never repeats a problem from the immediately previous batch;
11. shuffle-bag eventually covers every eligible public problem;
12. batch selection is reproducible from recorded seed;
13. family diversity is maximized subject to eligibility;
14. holdout lane cannot read hidden evaluator oracle into the teacher prompt;
15. a prompt-eval report with no live model variant cannot claim full prompt-eval pass.

Then run normal repo gates.

## Phase 5 — freeze candidate before selecting the four

This order is mandatory:

```text
implementation + prompts + schemas complete
        ↓
focused/full tests green
        ↓
commit candidate
        ↓
freeze prompt hashes/schema versions
        ↓
ONLY NOW select next four public problems
        ↓
persist batch manifest
        ↓
run tutoring
```

Do not inspect/select a convenient batch and then tune the implementation specifically for those four before calling the run an evaluation.

## Phase 6 — measured 4-problem run

For every selected problem, require:

- generated fine-grained TeachingPlan;
- learner-visible completion-driven conversation;
- realistic learner wrong/partial/uncertain/elaboration behavior;
- no learner repair of tutor contract failures;
- vocabulary grounding/stability;
- representation continuity or authorized repair;
- terminal/base/integration completion;
- no fixed-turn pass;
- per-problem acceptance.

The 250-exchange value is a configurable runaway ceiling only. It is not a target or expected length.

If one problem fails, the batch fails.

## Phase 7 — diagnosis and next iteration

Use Luna and optional Terra to classify failure causes after the measured run.

Generic fix categories include:

- decomposer missing bridge;
- bad representation selection;
- vocabulary grounding failure;
- diagnosis/evidence error;
- correction/retry policy error;
- controller/completion bug;
- semantic validator gap;
- assistance/answer leakage;
- tutor generation error;
- anti-loop/stall behavior.

A failed public problem may be used for engineering diagnosis because it is already public regression evidence.

After fixes:

- preserve the failed run artifacts;
- add regression tests;
- create a new candidate commit;
- run the **next** four-problem batch according to the selector;
- do not simply rerun the same four as the next claimed breadth evaluation. The failed problems remain available for focused regression checks separately.

## Hidden promotion lane — not this first run

Do not burn the hidden bank merely to validate ordinary runner plumbing.

After a broad public-rotation epoch passes and the architecture is a credible promotion candidate, run a separate hidden batch from a private/untracked source such as:

```text
STUDY_OS_HOLDOUT_DIR
```

A hidden problem used to drive a fix becomes burned and moves into public regression; replenish the private holdout bank afterward.

## Completion of this handoff

This handoff is complete when:

1. current type/lint/test baseline is green;
2. vNext decomposer + vocabulary + completion semantics are implemented;
3. rotation/ledger automation exists and is tested;
4. candidate is frozen before selection;
5. exactly four public regression problems are selected automatically under policy;
6. all four run completion-driven;
7. acceptance + live prompt evaluation execute;
8. results are manually reviewed;
9. artifacts and ledger entry are committed/pushed;
10. Issue #63 / PR #77 are updated with evidence and next action.

If the four fail, do not hide the failure. Preserve it, fix the generic cause, and continue the long-running rotation.
