---
name: study-os-dsa-decomposer
description: Use strong inference to derive a compact algorithm model, reverse its prerequisites into a learner-facing dependency graph, choose grounded vocabulary/representations, and emit a versioned TeachingPlan candidate for Study OS. Use before completion-driven DSA tutoring or when revising decomposition quality.
---

# Study OS DSA Decomposer

Skill version: `study-os-dsa-decomposer.v1`

## Purpose

Use Local Luna's strongest available reasoning to discover the **latent algorithm structure** and the **learning dependency structure** before learner-visible tutoring begins.

This skill does **not** author the final lesson transcript and does not own progression. It produces a structured candidate TeachingPlan that deterministic validation must approve before runtime tutoring.

Do not expose private chain-of-thought. Persist only structured conclusions, compact rationales, alternatives, invariants, dependencies, and provenance.

## Core rule

Do not begin by inventing lesson stages.

First derive the solution structure. Then work backward from that solution and ask what must already be understood for every relation, transition, symbol, and terminal condition to make sense. Reverse those prerequisites to obtain the teaching order.

Conceptually:

```text
raw problem
   ↓
strong structural inference
   ↓
ALGORITHM GRAPH
objects → state → invariant → transition/recurrence → terminal/base → integrated solution
   ↓
backward prerequisite analysis
   ↓
LEARNING GRAPH
primitive meaning → vocabulary/symbol grounding → relations → representation bridges → state transition → control flow/recursion → integration
   ↓
TeachingPlan candidate
   ↓
checklist + schema + deterministic semantic validation
```

Algorithm complexity and teaching complexity are different quantities. A tiny final recurrence may require many learning bridges.

## Step 1 — solve structurally before teaching

Infer the algorithm without using hidden evaluator answers or benchmark acceptance labels.

Externalize:

- primitive objects;
- state variables and stable meanings;
- information that must persist;
- invariant(s);
- one-step transition, recurrence, pointer update, queue/stack update, or equivalent state relation;
- what remains unchanged across a transition;
- terminal/base condition;
- unreachable/empty behavior where relevant;
- integrated solution behavior;
- minimal implementation obligations.

Prefer the smallest accurate state model that makes the solution mechanically derivable.

Do not force ordinary algebra on every algorithm. Use the relation native to the structure:

- arrays/sliding window: index/algebra relation when useful;
- linked list: pointer-state transition;
- tree/recursion: recursive return relation + base case;
- BFS/DFS: queue/stack + visited/frontier state transition;
- grid traversal: cell/neighborhood/visited transition;
- heap: ordering invariant + mutation;
- dynamic programming: state definition + recurrence + base conditions;
- interval/two-pointer: boundary/state transition.

For the calibrated learner, grounded compact symbolic/algebraic/state-transition representations receive a positive prior when they reduce representational friction.

## Step 2 — generate candidate representations

Generate more than one plausible representation when the problem admits materially different forms.

Examples:

```text
A. concrete visual/state trace
B. compact symbolic relation
C. brute-force-to-improved transition comparison
```

Score candidates qualitatively against:

- semantic accuracy;
- derivability of the algorithm;
- number of hidden bridges;
- symbol-grounding cost;
- representation-switch cost;
- learner-calibrated preference evidence;
- cognitive load;
- semantic stability;
- ability to preserve simple vocabulary.

Persist the selected representation and a compact rationale. Persist materially rejected representation families and why they were rejected. Do not persist private chain-of-thought.

## Step 3 — backward prerequisite expansion

For every element of the algorithm graph, recursively ask:

> What must the learner already understand for this statement or transition to be obvious rather than a leap?

Expand dependencies until they reach sufficiently primitive learner-facing concepts.

Examples:

### Sliding Window

```text
S[i] = S[i-1] - a[i-1] + a[i+k-1]
        ↑
meaning of S[i]
        ↑
window beginning at i
        ↑
i and array indexing
        ↑
positions in the array
```

### Maximum Depth of Binary Tree

```text
D(node) = 1 + max(D(left), D(right))
D(None) = 0
        ↑
what depth means
        ↑
what an empty child contributes
        ↑
what value comes back from each subtree
        ↑
why max chooses the deeper side
        ↑
why +1 counts the current node
```

### Reverse Linked List

```text
next = curr.next
curr.next = prev
(prev, curr) → (curr, next)
        ↑
node / next link
        ↑
meaning of curr and prev
        ↑
why next must be preserved before rewiring
```

### BFS

```text
(Q, V) → (Q', V')
        ↑
node / edge / neighbor
        ↑
waiting line semantics
        ↑
queue / FIFO
        ↑
visited meaning
        ↑
why a newly discovered node is marked before/when queued
```

Do not impose a fixed node count. Generate the **smallest useful dependency/bridge graph**: neither five coarse macro stages nor maximal micro-fragmentation.

## Step 4 — reverse the graph into teaching order

The teaching order must respect prerequisite edges.

Preferred learner-calibrated progression:

```text
ground object / simple expression
→ ground symbol or canonical technical term
→ show one relation/action
→ changed example
→ generalize
→ derive repeated transition / recursion
→ derive control flow
→ derive code
→ integrated verification
```

Code should normally be downstream of the relation/state model, not the first representation.

## Step 5 — vocabulary contract

For every learner-facing technical term or symbol that is not already assumed stable, emit vocabulary metadata:

- canonical term;
- simplest accurate starter expression;
- definition/behavior;
- concept binding;
- introduction node;
- grounding required before canonical use;
- allowed aliases, if any;
- forbidden/confusing aliases, if material.

Optimize in this order:

```text
semantic accuracy
→ learner comprehension
→ brevity
```

Examples:

```text
"node with no children" → leaf
"line of nodes waiting their turn" → queue
"arrow from this node to the next node" → next link / pointer
```

Do not use a simpler metaphor if it removes an important invariant. For example, a generic "box" is not an adequate replacement for a queue if ordering is the concept being learned.

Once a term/object is grounded, keep its meaning stable. Do not rename the same object casually across turns.

## Step 6 — evidence and completion design

For every required learning node, externalize:

- prerequisite node IDs;
- node kind;
- concept/bridge target;
- learner-facing representation family;
- allowed variables/symbols;
- semantic invariants;
- vocabulary requirements;
- evidence required to count the node complete;
- retry/verification policy after meaningful error;
- assistance ceiling;
- candidate repair representation if the current representation creates friction.

The overall plan must explicitly contain:

- terminal/base behavior;
- integration evidence;
- completion condition that does not depend on a fixed number of turns.

## Step 7 — correction path design

Preserve this calibrated branch after a meaningful conceptual error:

```text
identify any correct sub-operation
→ repair the failed relation in the same grounded representation
→ changed retry
→ independent verification when the prior error exposed instability
→ only then advance
```

A learner may be semantically correct but tentative. Confidence and correctness are separate dimensions. A question mark does not automatically mean `not_yet`; low confidence can trigger verification without forcing indefinite stalling.

## Step 8 — adversarial self-critique

Before returning the candidate plan, run a separate critique pass over the structured result.

Try to find:

- missing prerequisite;
- undefined term;
- symbol-before-meaning;
- semantic-role mutation;
- relation that does not actually imply the algorithm;
- missing base/terminal case;
- premature code/formalism;
- unnecessary vocabulary;
- representation bridge that is too large;
- plan that requires the learner to repair tutor mistakes;
- completion condition that could pass while required nodes remain unfinished.

Revise the structured plan when the critique finds a real defect.

## Required structured output

The exact schema may evolve, but the decomposition result must expose equivalent semantics for:

```json
{
  "algorithm_graph": {},
  "primitive_objects": [],
  "state_variables": [],
  "invariants": [],
  "transitions": [],
  "terminal_conditions": [],
  "integration_conditions": [],
  "core_relation": null,
  "candidate_representations": [],
  "selected_representation": {},
  "rejected_representation_families": [],
  "learning_graph": {},
  "vocabulary": [],
  "symbols": [],
  "completion_evidence": [],
  "compact_rationale": {},
  "provenance": {}
}
```

The structured output is not permission to teach. It must pass `plugins/study-os-dsa-decomposer/checklist.md`, the current TeachingPlan schema, and deterministic semantic validation.

## Prompt versioning

This skill is a reasoning procedure, not a substitute for prompt provenance.

The current repository already uses immutable content-addressed prompt definitions. Any material change to the decomposition prompt must receive a new prompt version and SHA-256 content hash. Do not overwrite historical prompt text after evidence has been recorded.

The next implementation should create a new decomposition prompt version rather than mutating `study-os.model-tutoring-decompose.v1` in place.

## Hidden-holdout integrity

Do not request, search for, or inspect hidden evaluator oracles.

In a hidden promotion run, the measured decomposer may receive the hidden **problem statement** injected by the evaluator because decomposition is impossible without the problem. It must not receive the hidden solution/evaluator oracle, and it must not have permission to modify prompts/code during the measured run.

The engineering/prompt-fixing agent must not receive raw hidden problem/oracle content unless that case is explicitly burned and promoted into public regression.

## Output quality boundary

The skill succeeds only when the structured model is sufficient for a learner to derive the algorithm through legal dependency steps. A plausible topic outline is not enough.
