# Completion-driven model tutoring vNext

Status: **PRIMARY execution delta for PR #77 after the 14-problem fixed-turn run.**

This document supersedes any earlier instruction that treats `15 exchanges per problem`, `14 × 15 = 210 exchanges`, or any other fixed turn count as the success condition for model tutoring.

The 15-turn corpus remains a useful **regression/calibration fixture**. It is not the learner-facing completion criterion.

## Why this change exists

The generic 14-problem run proved that one model-generated teaching-plan/controller path can execute across all scenarios, but manual review exposed a false-positive acceptance condition: a scenario can consume all 15 benchmark turns while remaining on the first concept and still appear structurally valid.

The original learner-calibrated Sliding Window trajectory also shows that realistic teaching can require dozens of dependency bridges plus correction, retry, verification, representation repair, and final integration. A fixed 15-turn or 40-turn budget is therefore not a pedagogical definition of success.

The product question is now:

> Can Study OS decompose each problem into the smallest useful dependency/bridge graph, teach that graph adaptively until required learner evidence exists, and reach integrated completion without requiring the learner to debug the tutor?

## Non-negotiable acceptance change

Success is **completion-driven**, not turn-count-driven.

A problem passes only when all required teaching-plan concepts/bridges and terminal/integration evidence are satisfied.

A run does **not** pass merely because it reached N turns.

Conceptually:

```text
problem
  ↓
generated fine-grained dependency graph
  ↓
teach current concept/bridge
  ↓
learner evidence sufficient?
  ├─ yes → advance one legal edge
  └─ no
      ├─ clarification/elaboration
      ├─ partial-success isolation
      ├─ correction
      ├─ changed retry
      └─ verification
  ↓
all required concepts/bridges satisfied?
  ├─ no → continue
  └─ yes
      ↓
terminal/base/integration check
      ↓
PASS
```

The runner may enforce a large configurable **anti-loop budget** so a broken tutor cannot run forever. Budget exhaustion is a failure/diagnostic, never success. The budget must not be used as an expected teaching length or as evidence of completion.

For the next local proof, use a default anti-loop ceiling of **250 learner/teacher exchanges per problem**, configurable from the CLI. If a valid trajectory reaches the ceiling while still making measurable progress, diagnose whether the plan is over-fragmented or whether the ceiling should be raised; do not force-pass or truncate the lesson.

## Fine-grained decomposition requirement

The decomposer must not emit five coarse stages merely because the regression corpus has five labels.

It should generate the smallest useful dependency graph needed to make the algorithm derivable by the learner.

The preserved Sliding Window trajectory is the calibration model for **granularity**, not a universal content template. It required bridges such as:

```text
problem
→ numbers(a)
→ position(p)
→ index(i)
→ k
→ visible box
→ i as box start
→ S[i]
→ S[i+1]
→ recompute/sliding equivalence
→ j = k - 1
→ recurrence
→ repeated recurrence
→ enumerate(a)
→ append conversion
→ first Python window loop
→ validate against original representation
→ max tracking
→ S[0] → S[i]
→ concrete comparisons
→ generalized comparison
→ combine loops
→ if/else bridge
→ stop condition
→ len(a)
→ arbitrary-k first window
→ range(k)
→ x
→ same S[i] changing as x changes
→ integrated loop
```

Other algorithms must receive equally careful decomposition when their structure demands it. Examples:

### Binary tree / recursion

```text
node
→ left/right child
→ leaf
→ empty child / None
→ meaning of depth
→ result returned by left subtree
→ result returned by right subtree
→ choose max
→ +1 for current node
→ base case
→ recursive relation
→ call/return trace
→ code
→ integrated verification
```

### BFS / graph traversal

```text
node
→ edge / neighbor
→ adjacency representation
→ current node
→ queue meaning
→ FIFO
→ visited meaning
→ why visited is needed
→ frontier / level
→ dequeue current
→ inspect neighbors
→ enqueue unvisited neighbors
→ repeated state transition
→ distance / shortest-path relation when applicable
→ termination
→ unreachable/base behavior
→ code
→ integrated verification
```

### Linked-list reversal

```text
node / next link
→ curr
→ prev
→ preserve next
→ reverse one pointer
→ advance prev
→ advance curr
→ repeated state transition
→ termination
→ returned head
→ code
→ integrated verification
```

The deterministic controller remains generic. These are examples of decomposition quality, not scenario-specific hard-coded stage lists.

## Learner-calibrated representation preference

For the current learner evidence, prefer **grounded compact symbolic / algebraic / state-transition reasoning early**, because the Sliding Window calibration showed that this representation materially reduced friction once symbols were individually grounded.

Do **not** interpret this as "dump an equation first" or "all DSA is algebra".

The preferred sequence is:

```text
GROUND THE OBJECT/SYMBOL
        ↓
SHOW ONE RELATION
        ↓
SHOW THE ACTION / STATE CHANGE
        ↓
CHANGED EXAMPLE
        ↓
GENERALIZE THE RELATION
        ↓
DERIVE CONTROL FLOW
        ↓
DERIVE CODE
```

For arrays this may become an index/algebra recurrence. For trees it may become a recursive relation. For BFS it may become a queue/visited state transition. For linked lists it may become a pointer-state transition.

The decomposer should therefore expose, per concept/bridge where appropriate:

- primitive objects and their meanings;
- symbols/identifiers and grounded meanings;
- state before;
- one allowed action/relation;
- state after;
- prerequisite bridge;
- representation family;
- evidence required before advancing;
- candidate repair representation if the current representation causes friction.

## Learner behavior allowed during measured runs

The simulated learner should be realistic and may:

- misunderstand;
- answer incorrectly;
- give a partial answer;
- ask "why?";
- ask for a smaller step;
- ask for another example;
- request elaboration;
- express uncertainty;
- need a different representation;
- need repeated retries;
- understand the concept but struggle with notation or a representation bridge.

These are legitimate learning events and should increase conversation length naturally.

## Learner must not be required to repair the tutor

A measured run must not depend on the learner identifying and correcting tutor defects.

The learner should **not** need to:

- discover algorithmic misinformation;
- tell the teacher that a semantic invariant is wrong;
- repair a broken teaching plan;
- police skipped prerequisites;
- tell the teacher that it changed a variable's meaning;
- repeatedly demand restoration of a required representation because the contract was violated;
- explain to the teacher what the correct pedagogical order should have been.

If the teacher violates a semantic/representation/dependency contract, classify it as a **tutor/system failure**. The acceptance run fails. Terra or Luna may diagnose it afterward, but the learner is not the recovery mechanism.

Meta-feedback such as "too much text", "that notation is confusing", or "show it another way" is valid learner evidence about representation friction. It is not a requirement that the learner know the correct lesson design.

## Correction / retry / verification contract

Preserve the strongest calibration rule from the original transcript:

```text
learner attempt
    ↓
correct and sufficiently independent?
    ├─ yes → show/confirm why briefly → verify when needed → advance
    └─ no
         ↓
       identify correct sub-operation if any
         ↓
       correct the failed relation using the same grounded representation
         ↓
       changed retry
         ↓
       retry correct?
          ├─ no → repair again
          └─ yes → one independent verification when the prior error exposed instability
                    ↓
                  advance
```

A single corrected retry after a real conceptual error is not automatically sufficient evidence to advance.

At the same time, do not treat every confirmation-question phrasing as failure. A learner can state the correct relation tentatively. Diagnosis must distinguish **semantic correctness + low confidence** from **lack of understanding**. Low confidence may trigger a verification turn without indefinitely blocking progression.

## Teaching-plan schema vNext requirements

Extend the generic TeachingPlan so completion can be judged without fixed turn counts. At minimum support:

- fine-grained concept/bridge nodes;
- prerequisite edges;
- node kind, e.g. `object`, `meaning`, `relation`, `state_transition`, `representation_bridge`, `control_flow`, `terminal`, `integration`;
- grounded symbols/variables and stable meanings;
- state-before/state-after relation where applicable;
- representation requirements;
- semantic invariants;
- completion evidence requirements per node;
- retry/verification policy;
- allowed assistance ceiling;
- terminal/base behavior;
- integration evidence required for problem completion;
- prompt/model/schema/run provenance.

Do not require every node to use algebra. The schema must support algebraic relations, recursive relations, pointer transitions, queue/stack transitions, grid-state transitions, and other appropriate representations.

## Controller vNext requirements

The generic controller must:

1. authorize at most one legal dependency transition at a time;
2. remain on the active node when evidence is insufficient;
3. distinguish partial success from complete failure;
4. enforce retry + verification after meaningful errors according to policy;
5. permit bounded elaboration/representation changes without advancing;
6. treat semantically correct but tentative answers as possible evidence plus confidence uncertainty, not automatic `not_yet`;
7. detect lack of progress / repeated cycles;
8. never mark a problem complete until every required node and terminal/integration condition is satisfied;
9. never use corpus `learner_signal` labels as progression evidence;
10. never require learner correction of tutor contract violations.

## Acceptance vNext requirements

The acceptance gate must fail a problem if any of the following occurs:

- conversation ends before required plan nodes are covered;
- final concept/integration node is never reached;
- required terminal/base behavior is missing;
- the controller remains on one node until the run ends and still reports success;
- required retry/verification behavior is skipped after a meaningful error;
- advancement occurs without actual learner evidence;
- learner evidence is fabricated or not bound to the learner message;
- a variable/symbol changes meaning;
- a required representation is dropped in a way that breaks the active relation;
- assistance exceeds the ceiling;
- a future solution is leaked prematurely;
- the teacher produces semantic misinformation;
- the measured learner must correct the teacher for the run to recover;
- anti-loop budget is exhausted;
- prompt/model/schema provenance is missing or inconsistent.

The gate should report per problem:

- generated node count;
- required node count;
- nodes completed;
- bridges completed;
- exchanges used;
- retries;
- verifications;
- elaboration/representation-change events;
- tutor-contract failures;
- loop/stall diagnostics;
- terminal/integration status;
- final pass/fail.

Aggregate success requires **every selected problem to pass individually**. Turn count is reported as a metric only.

## Prompt evaluation vNext

The current prompt-evaluation receipt is structural and does not execute live held-out model variants. Replace/extend it with real model evaluation.

For each candidate prompt version:

1. run the fixed regression corpus;
2. run held-out learner-message paraphrases;
3. run changed numeric/example values;
4. run equivalent problem-statement paraphrases;
5. run completion-driven conversations for representative structural families at minimum:
   - array/hash;
   - sliding window;
   - linked list;
   - binary tree/recursion;
   - graph/BFS or DFS;
   - heap/priority or interval family when present;
6. compare completion, semantic failures, stalls, representation changes, learner repair burden, and exchange cost against the incumbent prompt.

A prompt version is not promoted merely because provenance is valid or the original artifact passed.

## Local Luna + optional Terra execution loop

Local Luna owns implementation and reruns.

Terra, when available, is an independent diagnostician after failures. Terra never becomes the acceptance authority and never feeds hidden expected answers into the measured teacher.

```text
implement vNext
   ↓
focused tests
   ↓
property/stateful + mutation tests
   ↓
short completion-driven smoke on structural families
   ↓
full 14-problem completion-driven run
   ↓
vNext acceptance
   ↓
manual review + optional Terra diagnostics
   ↓
generic fix
   ↓
rerun until all selected problems genuinely complete
```

## Tests to add before the next expensive local run

### 1. Acceptance false-positive regression

Synthetic plan with 3 concepts. Generate 15/40/100 internally valid turns that never leave concept 0. Acceptance **must fail** for incomplete plan coverage.

### 2. Correct-but-tentative diagnosis regression

Examples such as:

```text
"For p=4 and k=2, the values are 6 and 1, right?"
"So depth here would be 1 + max(left, right)?"
```

must not be automatically classified as concept failure merely because they contain a question mark. The controller may require verification before advancing.

### 3. Correction branch regression

After a wrong answer, mutation of the controller to skip changed retry or required verification must be killed.

### 4. Fine-grained plan regression

Reject obviously coarse plans that collapse a structurally complex problem into a few ungrounded macro stages when key representation bridges are missing. Use semantic requirements, not a fixed minimum node number.

### 5. Symbol grounding regression

Reject use of a symbol in a relation before the plan establishes its meaning when that symbol is learner-facing.

### 6. Representation-family tests

Prove the schema/controller can express and validate at least:

- array/index algebraic transition;
- recursive tree relation;
- queue/visited graph transition;
- linked-list pointer transition.

### 7. Learner-does-not-debug-teacher test

Inject a teacher semantic error. Acceptance must fail immediately or at the validation boundary. Do not generate a learner message whose role is to repair the teacher.

### 8. Completion property/stateful test

Random learner outcomes can extend a run arbitrarily within budget, but success is impossible until every required node and integration condition is satisfied.

### 9. Anti-loop test

Repeated no-progress states eventually produce an explicit stall/budget diagnostic, never `passed`.

### 10. Live prompt evaluation test

At least one held-out/paraphrased live model case must execute for candidate prompt evaluation; a report with `live_model_variants_executed = false` cannot be called a complete prompt-evaluation pass.

## Next local execution sequence

Local Luna should first fast-forward to the latest PR branch and read this file before changing code.

Then:

```bash
git pull --ff-only

# 1. Implement vNext schema/controller/acceptance/prompt updates with focused tests.
pytest -q \
  tests/test_teaching_plan.py \
  tests/test_generic_model_tutoring.py \
  tests/test_model_tutoring_all_dsa_acceptance.py

# 2. Run the broader suite and type/lint checks required by the repo.
pytest -q
ruff check .
pyright

# 3. Run completion-driven structural-family smoke tests first.
# Exact CLI may change during implementation; the runner must support:
#   --completion-driven
#   --max-exchanges-per-problem 250
#   --scenario <id> (repeatable)

# Required smoke families before full run:
#   contains-duplicate-set
#   sliding-window-max-sum
#   reverse-linked-list
#   maximum-depth-binary-tree
#   bfs-shortest-path

# 4. If smoke passes, run ALL 14 problems completion-driven.
# Do not use exactly-15-turn mode as the product acceptance proof.

# 5. Run vNext acceptance + live prompt evaluation.

# 6. Persist transcript, plans, traces, acceptance, prompt-eval,
#    and optional Terra diagnostics, then update Issue #63 and PR #77.
```

The local implementation may choose exact command/file names, but the required behavior above is authoritative.

## Evidence/artifact expectations

Do not overwrite historical fixed-turn evidence. Preserve it as a prior experiment.

Create new vNext artifacts, for example:

```text
artifacts/model-tutoring-completion-vnext-transcript.jsonl
artifacts/model-tutoring-completion-vnext-transcript.md
artifacts/model-tutoring-completion-vnext-plans.jsonl
artifacts/model-tutoring-completion-vnext-trace.jsonl
artifacts/model-tutoring-completion-vnext-acceptance.json
artifacts/model-tutoring-completion-vnext-prompt-evaluation.json
artifacts/model-tutoring-completion-vnext-terra-diagnostics.jsonl   # if used
```

Every artifact must retain immutable prompt/model/schema/run provenance.

## Completion boundary for this phase

Do not call model tutoring proven until:

1. the fixed-turn success criterion has been removed from product acceptance;
2. all selected problems run until actual plan completion or explicit failure;
3. fine-grained decomposition is generated rather than hand-authored per problem;
4. grounded symbolic/state-transition reasoning is available early for this learner without forcing every problem into the same representation;
5. correction/retry/verification behavior is enforced;
6. semantically correct tentative answers do not cause indefinite stalls;
7. teacher contract violations fail without requiring learner repair;
8. tree, graph, linked-list, and array families are represented by the same generic schema/controller;
9. real held-out live prompt evaluation runs;
10. the full 14-problem completion-driven run passes every problem individually;
11. manual review confirms the learner-visible trajectories are coherent and the learner is learning rather than debugging the tutor;
12. ordinary CI and the relevant mutation gate are green on the exact evidence-bearing head.

Until then, keep PR #77 draft.
