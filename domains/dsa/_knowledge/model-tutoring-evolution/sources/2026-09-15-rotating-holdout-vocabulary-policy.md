# Study OS model tutoring — rotating evaluation, hidden holdouts, and vocabulary control

Date synthesized: 2026-09-15 UTC
Scope: completion-driven DSA model-tutoring evaluation and learner-facing vocabulary
Evidence class: project/domain design rationale synthesized from the active Study OS product-development conversation and prior calibrated tutoring evidence

## Decision summary

The completion-driven architecture should not rerun all 14 known DSA problems after every engineering change, and it should not call four randomly selected known problems a hidden holdout.

Use two lanes:

```text
public development rotation
4 completion-driven problems per iteration
shuffle-bag + family diversity + no immediate reuse

hidden promotion lane
genuinely unseen problems
used sparingly after the candidate is frozen
```

The public 14-problem corpus remains regression/calibration evidence. Repeated development runs should draw from it without replacement across an epoch so the engineering loop gets broad but tractable coverage.

A hidden holdout must remain outside the normal repository-visible development surface until evaluation time. Once a hidden case is inspected to drive a fix, it is burned, promoted into regression, and replaced.

## Why pure random-four is insufficient

Pure random selection can repeatedly choose easy or structurally similar problems and leave entire algorithm families untested. It is also hard to reproduce after a failure.

The preferred public selection algorithm is:

1. maintain a durable shuffle bag of eligible public problems;
2. derive and record a deterministic seed before results are known;
3. draw four without replacement;
4. forbid overlap with the immediately previous batch;
5. maximize structural-family diversity when possible;
6. persist the selected batch before inference;
7. keep an append-only evaluation ledger.

This gives randomness without cherry-picking and coverage without rerunning the full suite every time.

## Why hidden holdouts are separate

The known 14 problems have already influenced prompts, schemas, decomposition examples, validators, and architecture decisions. They can prove regression resistance but not strong unseen generalization.

A promotion holdout should therefore be private/untracked or mounted only during evaluation. It may contain static unseen DSA problems or validated fresh transfer variants created after the candidate commit is frozen.

The tutor receives the problem statement required for teaching. It does not receive the hidden evaluator oracle, expected teaching path, or answer key.

## Holdout burn rule

A hidden problem remains a holdout only while it has not been used to tune the architecture.

```text
hidden case
  ↓ fails
inspect enough to diagnose/fix
  ↓
case is burned
  ↓
move into public regression
  ↓
replace with new hidden case
```

Repeatedly tuning on a fixed hidden set and continuing to call it hidden is prohibited.

## Vocabulary decision

Vocabulary simplicity is a first-class teaching-plan concern.

The priority order is:

```text
semantic accuracy
→ learner comprehension
→ brevity/simplicity
```

New technical vocabulary should normally be introduced through grounded plain language:

```text
simple concrete expression
→ grounded behavior/meaning
→ canonical technical term
→ stable reuse
```

Examples:

- `node with no children` → `leaf`;
- `line of nodes waiting their turn` → `queue`;
- `arrow to the next node` → `next` / reference semantics.

A simple metaphor such as `box` is only valid if it preserves the important semantics. The same learner-facing word must not silently change meaning later.

Vocabulary validation should watch for undefined terms, synonym drift, term overload, vocabulary jumps, symbols before meaning, premature formalism, and metaphors that break invariants.

## Strong-inference decomposer decision

Use strong reasoning before learner-visible generation to infer both:

1. an algorithm graph: objects → state → invariant → transition/recurrence → termination → solution;
2. a learning graph: primitive meaning → grounded symbols/terms → relations → representation bridges → state transitions → control flow/recursion → integration.

The model may consider multiple candidate representations, then select one using semantic stability, grounding cost, hidden bridge count, representation-switch cost, derivability, vocabulary/cognitive load, and learner-calibrated representation evidence.

For the current calibrated learner, grounded symbolic/algebraic/state-transition representations receive a positive prior when they genuinely simplify the problem. This is not a mandate to start every problem with an equation.

Persist structured inference results and rationale; do not require or expose private chain-of-thought.

## Long-running empirical loop

The system should accumulate evidence indefinitely:

```text
candidate
→ ordinary tests
→ four-problem public rotation
→ diagnosis/fix
→ next non-repeating rotation
→ broad public epoch coverage
→ hidden promotion checkpoint
→ incumbent/reject
→ continue
```

Failures become regression tests. Burned holdouts become public regression cases. New hidden cases replenish the private bank.

The objective is not a static benchmark score. It is increasing robustness to new problems, learner errors, wording, and representation needs without adding per-problem teaching code.

Primary executable policy: `docs/MODEL_TUTORING_ROTATING_HOLDOUT_EVAL_V1.md`.
