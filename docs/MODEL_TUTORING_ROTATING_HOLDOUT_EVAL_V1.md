# Model tutoring rotating + hidden-holdout evaluation v1

Status: **durable evaluation policy for completion-driven model tutoring.**

This policy refines `docs/MODEL_TUTORING_COMPLETION_DRIVEN_VNEXT.md`. It does not restore a fixed-turn success criterion. It defines how Local Luna should automate repeated, lower-cost evaluation without overfitting to one problem set.

## Decision

Do not rerun all 14 known DSA problems after every implementation change.

Use two distinct evaluation lanes:

```text
ITERATION / DEVELOPMENT LANE
4 known problems per iteration
completion-driven
rotating without immediate reuse
family-stratified when possible
       ↓
fast evidence for engineering changes

PROMOTION / HOLDOUT LANE
genuinely hidden problems
used sparingly
not available to the teacher or engineering loop before the candidate is frozen
       ↓
generalization evidence
```

The old 14-problem corpus remains a public regression/calibration set. Sampling four of those problems is **not** a hidden-holdout test.

## Why four rotating problems

Four completion-driven problems are large enough to expose cross-family failures while keeping each engineering iteration tractable.

The selection policy must avoid repeatedly exercising the same easy subset.

### Shuffle-bag rule

Maintain a durable evaluation ledger and a current public-problem bag.

1. Start an epoch with all eligible public regression problem IDs.
2. Shuffle using a recorded deterministic seed.
3. Draw four problems for the iteration.
4. Remove those problems from the current bag.
5. The next iteration must not contain any problem from the immediately previous iteration.
6. When fewer than four remain, take the remaining problems, create a newly shuffled epoch, and fill the batch from the new epoch while excluding the immediately previous batch.
7. Persist the batch selection **before** running tutoring.

This guarantees broad coverage over time while preventing accidental cherry-picking.

### Family stratification

When the corpus has enough eligible problems, prefer four distinct structural families in one batch.

Example family tags:

- array/hash/set;
- two-pointer / sliding-window / interval;
- stack / search;
- linked-list / pointer mutation;
- tree / recursion;
- graph / BFS / DFS;
- heap / priority;
- grid / traversal.

Family tags are evaluation metadata, not hand-authored teaching stages.

If a perfectly distinct four-family batch is impossible, maximize structural diversity and record why.

## Reproducible randomness

Randomness must be reproducible, not mysterious.

Each iteration records:

- `iteration_id`;
- candidate git commit SHA;
- selection-policy version;
- seed;
- eligible problem IDs;
- previous batch IDs;
- selected four IDs;
- family tags;
- prompt versions/hashes;
- schema versions;
- model identifiers.

A suggested seed derivation is a hash of:

```text
policy_version + candidate_commit + iteration_id
```

Do not choose or change a seed after seeing results.

## Hidden holdout policy

The promotion lane must contain problems that the engineering loop has not used for prompt/schema/controller tuning.

A holdout is strongest when its full problem + evaluator oracle are outside the normal repository-visible development surface until evaluation time.

Recommended local mechanism:

```text
STUDY_OS_HOLDOUT_DIR=<untracked/private path>
```

or an equivalent private CI/evaluator mount.

Do not commit the live holdout answers/oracles into the same repository surface available to Local Luna during ordinary implementation.

### What counts as a holdout

A holdout may be:

1. a private static DSA problem not present in the public 14-problem regression corpus;
2. a private equivalent/transfer problem from the same algorithm family with different surface wording and values;
3. a fresh evaluator-generated problem produced only **after** the candidate commit/prompt is frozen, provided the evaluator independently validates the problem and keeps its solution oracle away from the teacher.

Private static holdouts are preferred for stable promotion evidence. Fresh generated variants are useful supplemental stress tests, not the sole oracle.

### Holdout burn rule

Once a hidden holdout is inspected in enough detail to drive an engineering fix, it is no longer hidden.

Then:

```text
hidden holdout
    ↓ used for diagnosis/fix
burned
    ↓
promote into public regression corpus
    ↓
replace with a fresh hidden case
```

Never repeatedly tune against the same hidden set while still calling it a holdout.

## When to run the holdout lane

Do **not** spend the hidden set on every small iteration.

Default promotion cadence:

```text
implementation change
   ↓
4-problem rotating development batch
   ↓ pass
next implementation change / iteration
   ↓
4-problem rotating development batch
   ↓ pass
continue until one public-rotation epoch has broad coverage
   ↓
hidden promotion batch
```

Also run a hidden promotion batch after a material change to any of:

- decomposer prompt;
- diagnosis prompt;
- teaching-generation prompt;
- TeachingPlan schema semantics;
- progression/completion logic;
- representation selection;
- vocabulary policy;
- assistance policy.

For routine bug fixes that do not alter tutoring semantics, a public rotating batch plus ordinary tests is enough until the next promotion checkpoint.

## Promotion threshold

A candidate is eligible to become the new incumbent only when:

1. focused/unit/property/mutation/type/lint gates are green;
2. rotating public batches show no severe regression and complete individually;
3. every tested learner-visible conversation satisfies the completion-driven contract;
4. a hidden promotion batch completes without a severe tutor-contract failure;
5. live prompt evaluation actually executes held-out model cases;
6. manual review finds no learner-required tutor repair, semantic drift, or vocabulary/representation pathology.

Do not use aggregate success to hide one failed problem.

A full 14-problem public completion-driven sweep remains useful at release/milestone boundaries, but it is not required after every small engineering iteration.

## Vocabulary simplicity contract

Vocabulary is part of the TeachingPlan and validation surface.

The system should optimize in this order:

```text
semantic accuracy
    ↓
learner comprehension
    ↓
brevity / simplicity
```

Never prefer a simpler word if it destroys an important invariant.

### Ground-before-term rule

For a new learner-facing technical term:

```text
simple concrete expression
    ↓
meaning / behavior grounded
    ↓
canonical technical term introduced
    ↓
stable term reused thereafter
```

Examples:

```text
"node with no children" → leaf
"line of nodes waiting their turn" → queue
"arrow to the next node" → next/reference
```

`box` is allowed only when its mapping preserves the required semantics. Once `box` means one thing in a trajectory, the tutor must not silently reuse it for a different role.

### Vocabulary-plan fields

A TeachingPlan should be able to expose, where useful:

- `canonical_term`;
- `starter_expression`;
- `grounding_required`;
- `introduced_at_node`;
- `stable_subject_ref` / concept binding;
- allowed aliases after grounding;
- forbidden aliases when they would change semantics;
- learner-facing symbols that require grounding before use.

### Vocabulary validator failures

The deterministic validation/evaluation layer should detect at least:

- `UNDEFINED_TERM` — technical term used before grounding;
- `SYNONYM_DRIFT` — same concept is unnecessarily renamed;
- `TERM_OVERLOAD` — one simple word is reused for different semantic roles;
- `VOCABULARY_JUMP` — too many new technical terms introduced in one turn;
- `SYMBOL_BEFORE_MEANING` — learner-facing symbol appears before its meaning is grounded;
- `FORMALISM_TOO_EARLY` — an abstraction is used before prerequisite concrete meaning;
- `METAPHOR_BREAKS_INVARIANT` — a simple analogy hides or changes an important property.

Default learner-facing budget: introduce no more than one genuinely new technical term and one new semantic relation per turn unless the plan explicitly justifies a larger bundle.

This is a default, not a rigid universal count.

## Strong-inference decomposer contract

Use the strongest available reasoning primarily **before** the visible teaching turn.

The decomposer should infer two related graphs:

### Algorithm graph

```text
primitive objects
→ state
→ invariant
→ transition / recurrence
→ termination/base condition
→ solution
```

### Learning graph

```text
primitive learner meaning
→ grounded symbols/terms
→ relations
→ representation bridges
→ state transitions
→ control flow / recursion
→ integration
```

Algorithm complexity and teaching complexity are not assumed to be equal.

The decomposer should generate several candidate representations when useful, for example:

- concrete/visual;
- grounded algebra/index relation;
- state-transition notation;
- recursive relation;
- pointer-state representation;
- queue/frontier representation.

Then score/select among candidates using learner-calibrated evidence such as:

- semantic accuracy;
- grounding cost;
- number of hidden bridges;
- representation-switch cost;
- derivability of the algorithm;
- cognitive/vocabulary load;
- known learner representation preference;
- stability of variable/term meanings.

For the currently calibrated learner, grounded compact symbolic/algebraic/state-transition representations receive a positive prior when they genuinely simplify the structure.

Do not expose private chain-of-thought. Persist the structured result:

- chosen representation;
- brief rationale;
- rejected representation families where material;
- state model;
- invariants;
- dependency graph;
- vocabulary plan;
- terminal/integration conditions.

## Automated long-running evaluation ledger

Add a durable append-only ledger, for example:

```text
artifacts/model-tutoring-eval-ledger.jsonl
```

Each iteration record should include:

```json
{
  "iteration_id": "...",
  "candidate_commit": "...",
  "policy_version": "study-os.model-tutoring-eval.v1",
  "lane": "public_rotation|hidden_promotion",
  "selection_seed": "...",
  "selected_problem_ids": [],
  "previous_problem_ids": [],
  "family_tags": {},
  "prompt_versions": {},
  "schema_versions": {},
  "run_ids": [],
  "per_problem_status": {},
  "severe_failure_count": 0,
  "manual_review_status": "pending|passed|failed",
  "holdout_disposition": "not_applicable|still_hidden|burned_to_regression"
}
```

The ledger must be written so future Local Luna iterations can select the next batch without relying on chat memory.

## Runner automation requirements

The local runner should eventually support a single orchestration command with semantics equivalent to:

```bash
python tools/run_model_tutoring_iteration.py \
  --policy configs/model-tutoring-eval-policy.v1.json \
  --batch-size 4 \
  --completion-driven \
  --max-exchanges-per-problem 250
```

Expected behavior:

1. read the durable ledger;
2. select the next four public problems using shuffle-bag + diversity constraints;
3. persist the batch manifest before inference;
4. generate/decompose each problem with versioned provenance;
5. run learner ↔ tutor until completion or explicit failure;
6. run acceptance and live prompt checks;
7. append the result to the ledger;
8. emit a compact iteration report;
9. never silently promote a failed candidate.

A separate flag/command should run the private holdout lane, for example:

```bash
python tools/run_model_tutoring_iteration.py \
  --lane hidden-promotion \
  --holdout-dir "$STUDY_OS_HOLDOUT_DIR" \
  --batch-size 4 \
  --completion-driven
```

The implementation may choose better command names; the policy semantics are authoritative.

## Long-running goal

Treat model tutoring as an ongoing empirical system, not a one-time 14-problem benchmark.

The loop is:

```text
candidate prompt/schema/controller
        ↓
normal tests
        ↓
4-problem rotating completion batch
        ↓
manual/automated diagnosis
        ↓
generic fix
        ↓
next non-repeating 4-problem batch
        ↓
...
        ↓
hidden promotion checkpoint
        ↓
new incumbent or reject
        ↓
continue
```

Historical batches remain evidence. New failures become regression tests. Burned holdouts become public regression cases. The hidden bank is replenished.

The goal is not to maximize a score on one static corpus. The goal is to make the tutoring architecture increasingly robust to **new problems, new learner errors, new wording, and new representation needs** without adding per-problem teaching code.
