# Study OS model tutoring evolution — why fixed 14×15 became completion-driven

Date synthesized: 2026-09-14 / 2026-09-15 UTC
Scope: Study OS DSA model-tutoring architecture, PR #77, Issue #63
Evidence class: project/domain design rationale synthesized from the current product-development conversation plus repository evidence
Integrity note: this is **not** a byte-exact export of the ChatGPT conversation. It preserves the decisions, evidence chain, corrections, and reasons that must survive future sessions. Raw historical learner calibration remains preserved separately under `sessions/2026-09-04/sliding-window-pedagogy-calibration/`.

## Executive conclusion

The old target:

```text
14 problems
× exactly 15 learner/teacher exchanges
= 210 exchanges
```

was useful as a regression harness, but it was never a defensible definition of successful tutoring.

The product acceptance rule is now:

> Generate a fine-grained dependency/bridge graph for the problem, teach it adaptively until the required learner evidence and terminal/integration conditions are satisfied, and fail explicitly if the tutor stalls or violates the contract. Conversation length is a measured outcome, not the success condition.

The fixed 15-turn corpus remains valuable as a compact calibration/regression fixture. It must not be used as the learner-facing completion criterion.

## How we got here

### 1. The original 14×15 corpus was intentionally compressed

`datasets/dsa-conversation-replay.v0.1.json` was built as a learner-visible regression corpus. Each problem contains a compact sequence of learner situations across coarse stages. The corpus is useful for checking visible behavior, variable/representation continuity, forbidden leakage, and stage-sensitive response behavior.

It was never evidence that real learners should finish every DSA problem in fifteen exchanges.

The mistake happened when the regression shape started being treated as the product proof shape.

### 2. The first 14-problem dual-Luna run diagnosed the old architecture

The earlier 14-problem / 210-exchange experiment showed that the harness itself worked, but the production tutoring path did not generalize:

- only Two Sum and Sliding Window received substantive teaching;
- most other problems fell into `needs_compilation` / reviewed-asset behavior;
- internal product jargon leaked into learner-visible responses;
- once some assets reached an assembled state, teaching could freeze;
- where teaching did occur, the pedagogical encoding could diverge from the calibrated learner trajectory.

This led to the architectural direction:

```text
learner problem/message
      ↓
Luna diagnosis + decomposition
      ↓
structured plan / assessment
      ↓
deterministic validation + authorized operation
      ↓
Luna learner-visible generation
      ↓
semantic / representation / assistance validation
      ↓
learner
```

The model writes/adapts the teaching. Deterministic code owns progression legality, evidence semantics, assistance limits, semantic invariants, provenance, and completion rules.

### 3. Contains Duplicate exposed two first-order trust failures

The first model-driven Contains Duplicate pilot looked good, but manual review found two holes:

1. progression was indirectly driven by scripted corpus `learner_signal` rather than actual learner-message evidence;
2. the final no-duplicate condition `return False` had not been explicitly established.

The architecture was corrected so Luna must assess the actual learner message and bind a verbatim `evidence_quote`; deterministic code authorizes progression from that assessment. The corpus signal became student-simulation metadata only.

### 4. The next Contains Duplicate run exposed semantic drift despite structural validity

A fresh run passed the then-current acceptance checker, but manual learner-visible review found that Luna had silently changed the meaning of `box`, teaching it as a boolean yes/no result rather than the collection of previously encountered numbers.

That established an important principle:

```text
schema-valid
+ progression-valid
+ evidence-valid
+ formatting-valid
≠ pedagogically/semantically valid
```

The semantic gate was strengthened. Deterministic code still did not write the lesson, but it began enforcing stable concept/variable meaning.

### 5. We then generalized across all 14 problems

The next implementation produced:

- 14 model-generated teaching plans;
- 210 exchanges / 420 learner-visible messages;
- generic traces with prompt/model/schema provenance;
- aggregate acceptance reported as passed;
- prompt-regression infrastructure;
- no need for a hand-authored lesson per problem.

This was a real architectural advance: the model/schema path operated across the complete DSA corpus.

But manual review found that the acceptance definition was still wrong.

### 6. Sliding Window proved the 15-turn success condition was a false positive

In the generic 14×15 run, the Sliding Window scenario consumed all fifteen exchanges while the controller remained on concept index `0`, `identify-fixed-contiguous-window`.

The final trace turn still recorded:

```text
turn_index = 14
active_concept_index = 0
active_concept_id = identify-fixed-contiguous-window
advance = false
```

Yet aggregate acceptance still reported the scenario/run as passing because the checker validated internal consistency turn-by-turn but did not require completion of the generated plan.

This was the decisive evidence that:

> “fifteen internally legal turns happened” is not the same as “Study OS taught the problem.”

The acceptance gate had confused **conversation validity** with **teaching completion**.

### 7. The original verified Sliding Window trajectory showed how long real learning can be

The preserved 2026-09-04 Sliding Window calibration spans eight raw transcript parts and a much richer dependency graph than the five-stage regression fixture.

The later transcript analysis reconstructs a trajectory approximately like:

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
→ semantic equivalence of recompute vs sliding update
→ j = k - 1
→ recurrence
→ repeated recurrence as i changes
→ enumerate(a)
→ append conversion
→ first Python window loop
→ validate against original array/index/box representation
→ identify max value
→ max_sum = S[0]
→ S[0] = S[i] when i = 0
→ concrete S[1] / S[2] comparisons
→ generalized S[i] comparison
→ max loop
→ combine loops
→ if / else bridge
→ break condition
→ len(a)
→ arbitrary-k first-box calculation
→ range(k)
→ x as inner-loop index
→ same S[i] changing as x changes
→ full integrated loop
```

That is roughly thirty-plus meaningful dependencies/bridges for one algorithm, before counting all learner mistakes, partial answers, elaboration requests, retries, verification checks, and representation repairs.

Therefore 15 turns is obviously too short for realistic completion, and 40 turns can also be too short. Tree recursion, graph traversal, dynamic programming, heap/state algorithms, and other complex topics can legitimately require even longer trajectories.

## What the historical Sliding Window session taught about representation

The key learner preference was not “always show more diagrams” and not “always use algebra immediately.”

The successful pattern was:

```text
GROUND THE OBJECT / SYMBOL
        ↓
SHOW ONE RELATION
        ↓
SHOW THE ACTION / STATE CHANGE
        ↓
CHANGED EXAMPLE
        ↓
GENERALIZE
        ↓
DERIVE CONTROL FLOW
        ↓
DERIVE CODE
```

For Sliding Window, compact algebra/index notation became dramatically easier once each symbol had a grounded meaning:

```text
S[i] = a[i] + a[i+1] + ... + a[i+j]
S[i] = S[i-1] - a[i-1] + a[i+j]
```

The learner explicitly reported that this made the loop obvious and that earlier explanations had required too much decoding.

This should become a first-class learner-calibrated representation preference:

> Prefer grounded, compact symbolic / algebraic / state-transition reasoning early when it preserves the problem structure and reduces representational friction.

Do not generalize this into “every algorithm begins with an equation.” The relation should be native to the structure:

- arrays/sliding window: index/algebra state relation;
- binary tree/recursion: recursive relation and call/return state;
- BFS/graph: queue + visited + frontier state transition;
- linked list: pointer-state transition;
- grid traversal: cell/neighbor/visited state transition;
- heap: structural/ordering invariant plus state mutation.

The common pedagogical pattern is **fine-grained relational decomposition**, not one universal notation.

## Correction, retry, and verification are part of the algorithmic teaching path

The strongest calibrated controller rule from the original transcript was:

```text
learner answer
    ↓
correct?
    ├─ yes → show/confirm why briefly → verify when needed → advance
    └─ no
         ↓
       preserve any correct sub-operation
         ↓
       correct the failed relation using the same grounded representation
         ↓
       changed retry
         ↓
       retry correct?
          ├─ no → repair again
          └─ yes → independent verification after meaningful prior error
                    ↓
                  advance
```

A single corrected retry after a meaningful conceptual error was explicitly insufficient evidence to advance in the original calibration.

This means realistic conversation length must expand when the learner gets parts wrong or requests elaboration. That is not a failure of the test. It is the behavior the test is supposed to exercise.

## The learner must not be required to debug the tutor

The historical calibration contains many learner messages correcting the tutor's pedagogy or representation. Those turns were useful product-discovery evidence, but they should **not** become the desired operating mode.

Measured learners may legitimately:

- misunderstand;
- answer incorrectly;
- partially answer;
- ask why;
- ask for a smaller step;
- ask for another example;
- request another representation;
- report that an explanation is too long or confusing;
- express uncertainty even when the relation is semantically correct.

Measured learners should not need to:

- discover algorithmic misinformation;
- tell the teacher a variable meaning changed;
- repair a broken teaching plan;
- police skipped prerequisites;
- tell the teacher the required pedagogical order;
- restore a representation the system illegally dropped;
- act as the semantic validator for the tutor.

If the tutor violates a semantic, dependency, representation, or assistance contract, the run should fail at the tutor/system boundary. Terra or Luna may diagnose it after the measured run, but the learner is not the repair mechanism.

## Correct-but-tentative learner language must not cause indefinite stalls

The generic 14×15 run exposed a second problem: Luna could classify a semantically correct learner statement as `not_yet` merely because it was phrased as a question, for example a confirmation such as “those are the window values, right?”

The diagnosis layer must separate:

```text
semantic correctness
from
confidence / certainty
```

A correct but tentative answer may justify one verification turn. It should not automatically reset or indefinitely block concept progression.

## New completion-driven acceptance model

Success is now defined by required evidence and plan completion:

```text
problem
  ↓
model-generated fine-grained dependency/bridge graph
  ↓
current concept/bridge
  ↓
learner evidence sufficient?
  ├─ yes → advance one legal edge
  └─ no  → clarify / elaborate / repair / retry / verify
  ↓
all required nodes complete?
  ├─ no → continue
  └─ yes
      ↓
terminal/base/integration evidence
      ↓
PASS
```

Turn count is an output metric only.

The runner may use a large configurable anti-loop ceiling to catch a broken tutor. The current vNext default is 250 exchanges/problem. Reaching the ceiling means **failure/diagnostic**, never successful completion. The ceiling is not a recommended lesson length and may need to increase for genuinely complex algorithms if progress is still measurable.

## Why future tree/graph/recursive problems may be substantially longer

A problem's required conversation length should emerge from its dependency graph and learner behavior.

For example, Maximum Depth of Binary Tree may require separate grounding of:

```text
node
→ left/right child
→ leaf
→ None / empty subtree
→ meaning of depth
→ left recursive result
→ right recursive result
→ max relation
→ +1 for current node
→ base case
→ recursive call/return trace
→ code
→ integration
```

BFS shortest path may require:

```text
node
→ edge/neighbor
→ adjacency representation
→ current node
→ queue
→ FIFO
→ visited
→ why visited is required
→ frontier/level
→ dequeue
→ inspect neighbors
→ enqueue unvisited neighbors
→ repeated state transition
→ distance relation
→ why BFS gives shortest path for the target graph class
→ termination
→ unreachable behavior
→ code
→ integration
```

Each concept can require explanation, an independent probe, correction, changed retry, verification, or another representation. Therefore 100+ exchanges can be legitimate. The architecture must not hard-code “tree = N turns” or “graph = N turns”; it should teach until the required evidence exists.

## Prompt vs schema vs deterministic code

Do not collapse these responsibilities.

### Prompt

Prompt versions steer Luna to:

- decompose into small bridges;
- ground symbols before relations;
- diagnose the current learner message;
- propose representation changes;
- generate one bounded teaching move;
- avoid jumping ahead.

Prompt behavior is probabilistic and must be versioned/evaluated.

### Schema

The TeachingPlan/turn schemas expose Luna's claims so they can be checked:

- concepts and prerequisite edges;
- node/bridge kinds;
- variable/symbol meanings;
- state-before/state-after relations;
- semantic invariants;
- representation requirements;
- completion evidence;
- retry/verification policy;
- terminal/integration conditions;
- prompt/model/schema/run provenance.

### Deterministic controller / validator

Code owns:

- legal state transitions;
- evidence binding to actual learner messages;
- assistance ceilings;
- no concept skip/backtrack unless explicitly authorized;
- stable variable/symbol semantics;
- required retry/verification behavior;
- completion checks;
- anti-loop/stall detection;
- provenance integrity;
- rejection of tutor semantic/representation violations.

The deterministic layer does **not** author the lesson prose.

## Prompt evaluation lesson

The generic all-DSA run recorded prompt provenance and structural prompt evaluation, but the artifact did not execute real held-out live model variants. A prompt-evaluation report that only validates structure/provenance or replays the original run is not enough.

Future prompt promotion must include real model execution across:

- the fixed regression corpus;
- learner-message paraphrases;
- changed numeric/example values;
- equivalent problem-statement paraphrases;
- representative structural families: array/hash, sliding window, linked list, tree/recursion, graph traversal, and additional families present in the corpus.

Compare semantic failures, completion, stalls, representation changes, learner repair burden, and exchange cost against the incumbent prompt.

## Future watch-outs

Future agents should explicitly guard against these regressions:

1. **Fixed-turn proxy regression** — treating 15, 40, 100, 150, 250, or any other number as proof of teaching success.
2. **Coarse-plan regression** — collapsing a complex algorithm into a handful of broad stages because that is easier to validate.
3. **Benchmark-label leakage** — using corpus `learner_signal` or hidden expected assertions as learner evidence or teacher guidance.
4. **Correct-but-tentative stall** — interpreting a question mark or low confidence as absence of semantic understanding.
5. **Learner-as-debugger regression** — allowing tutor mistakes to be repaired by requiring the simulated learner to diagnose the teacher.
6. **Semantic-drift false green** — accepting a response because required terms/variables appear even though their meanings changed.
7. **Representation-drift false green** — dropping the representation that carries the current relation while still passing structural checks.
8. **Per-problem special casing** — replacing hand-authored lessons with hard-coded scenario-specific controller branches.
9. **Prompt-only control** — assuming a stronger prompt can replace schema/state/evidence enforcement.
10. **Schema-only control** — accepting structurally valid plans/responses without learner-visible semantic review.
11. **Incomplete-plan false positive** — passing a run that never reaches required nodes or terminal/integration behavior.
12. **Stale artifact authority** — leaving an earlier `accepted=true` artifact authoritative after manual review invalidates it.
13. **No live prompt eval** — calling prompt evaluation complete when no held-out live model variants ran.
14. **Assistance creep** — solving the problem for the learner while still recording legal progression.
15. **Over-fragmentation** — producing so many micro-nodes that the learner is drilled indefinitely; granularity must be the smallest *useful* dependency graph, not maximal atomization.
16. **Premature generalization of learner preference** — treating one learner's success with grounded symbolic/state-transition reasoning as a universal population rule.
17. **Loss of source restoration/transfer** — simplifying representation without eventually proving the learner can reconnect to authentic terminology/code when the curriculum requires it.
18. **Anti-loop ceiling misuse** — treating budget exhaustion as a normal stopping condition rather than a failure signal.
19. **Model agreement as evidence** — Luna/Terra agreeing with each other is not learner evidence or external truth.
20. **Historical evidence rewriting** — never rewrite old transcripts/traces to make a new architecture look correct; preserve old failures and supersede interpretations explicitly.

## Durable authority references

Repository paths relevant to this rationale:

- `docs/MODEL_TUTORING_COMPLETION_DRIVEN_VNEXT.md` — current execution delta;
- `docs/ALL_DSA_MODEL_TUTORING_HANDOFF.md` — prior generic 14-problem authority, retained as historical context;
- `datasets/dsa-conversation-replay.v0.1.json` — compact fixed-turn regression/calibration corpus;
- `artifacts/model-tutoring-all-dsa-acceptance.json` — historical all-DSA fixed-turn acceptance artifact;
- `artifacts/model-tutoring-all-dsa-trace.jsonl` — historical traces, including Sliding Window remaining at concept index 0 through turn 14;
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/` — original learner-driven calibration evidence;
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/derived/next-session-analysis-handoff.md` — reconstructed fine-grained dependency progression and failure taxonomy;
- `domains/dsa/sliding-window/golden/beginner-progressive-box-index-sum.v0.1.md` — learner-calibrated early sequence;
- `domains/dsa/sliding-window/golden/beginner-sum-enumerate-append.v0.1.md` — learner-calibrated next bridges;
- Issue #63 — canonical P4 tracker;
- PR #77 — implementation/evidence branch.

Important historical commits/heads referenced during this evolution include:

- `5113336` — fresh evidence-bound Contains Duplicate v0.2 run that passed the then-current gate before semantic manual review found the `box` meaning regression;
- `86eff24` — generic 14-problem / 210-exchange run with generated plans and a structurally passing aggregate acceptance report;
- `7d70891182c02d2006b1ed43bc29df18d3741df4` — introduction of the completion-driven vNext contract.

## Scope / epistemic boundary

These claims are strong project-level evidence about what Study OS should test next and what failed in its own harnesses.

They are **not** population-level claims about all learners.

The representation preference for grounded symbolic/algebraic/state-transition reasoning is learner-calibrated evidence for the current subject and should remain subject-/context-sensitive until replicated.

The fixed-turn corpus remains useful and should not be deleted. Its status changes from "completion proof" to "compact regression/calibration fixture".
