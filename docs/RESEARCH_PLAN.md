# Research Plan: DSA Slice 0

Status: **pre-build research phase**

The goal is to validate the measurement and adaptation procedure before investing in a full learning product.

## Primary research question

Can Study OS observe a representation-transition failure in DSA learning, select or construct a different representation/operation, and produce measurable improvement that survives assistance removal, changed-surface transfer, and delay?

## Secondary questions

1. Where does Subject 001's learning most often break: recognition, mental model, invariant, state transition, pseudocode, syntax, implementation, debugging, or transfer?
2. Which representation operations help which bottlenecks?
3. When does adding another representation help versus overload?
4. When does AI assistance become dependency rather than scaffold?
5. Does learner self-report predict objective improvement?
6. Can the system distinguish a Python-language gap from an algorithmic reasoning gap?
7. How much session instrumentation can be captured without harming the learning experience?

## Study context: Subject 001

Public-safe research profile:

- primary prior coding background: JavaScript;
- no formal Python learning sequence completed;
- uses AI heavily to build technical projects and scripts;
- can often make software work through AI-guided construction while wanting stronger unaided code comprehension and implementation ability;
- currently moving into Python scripting, DSA, and interview-relevant coding fundamentals;
- capable of reporting live confusion and describing why a changed explanation/representation did or did not help.

This profile makes Subject 001 a strong initial **design participant** because the gap between AI-assisted productivity and unaided procedural fluency is itself part of the research problem.

It does not make Subject 001 representative of all learners.

## Concept family

Start with **Sliding Window** because it permits controlled observation of several representation transitions:

`problem wording -> contiguous-region recognition -> window state -> invariant -> expand/shrink transition -> semantic pseudocode -> Python control flow -> transfer`

## Representation families under test

Initial set only:

- textual causal explanation;
- static pointer/array figure;
- Mermaid flowchart;
- deterministic state trace;
- invariant statement;
- semantic pseudocode;
- Python scaffold;
- blank Python implementation.

Audio/video/image-generation experiments are deferred until the core loop is validated.

## Learning operations

A representation is not an intervention by itself. Record the operation:

- `expand` — expose hidden expert steps;
- `decompose` — split a task into subgoals;
- `trace` — follow concrete state transitions;
- `predict` — learner predicts next state;
- `explain` — learner explains why;
- `contrast` — compare two algorithms/states;
- `abstract` — concrete execution to invariant/pattern;
- `specialize` — general pattern to concrete case;
- `reconstruct` — recreate without reference;
- `debug` — locate/correct a fault;
- `translate` — convert between diagram/pseudocode/code/etc.;
- `fade` — deliberately remove support;
- `transfer` — apply under changed surface conditions.

## Difficulty ladder

Difficulty is not LeetCode Easy/Medium/Hard alone.

- L0 Observe
- L1 Predict
- L2 Explain
- L3 Reconstruct
- L4 Produce semantic pseudocode
- L5 Scaffolded implementation
- L6 Blank implementation
- L7 Debug incorrect implementation
- L8 Recognize pattern from unfamiliar wording
- L9 Transfer to changed-surface problem
- L10 Derive/modify algorithm under new constraint

Subject state is multidimensional; do not collapse the ladder into one mastery scalar.

## Experimental unit

A learning episode:

`pre-state -> task -> attempt -> observed failure/uncertainty -> diagnosis hypothesis -> intervention -> re-attempt -> assessment -> fade -> transfer -> delayed retrieval`

One conversation may contain multiple episodes.

## Evidence hierarchy

### Observed
- submitted answer/code;
- state predictions;
- tests passed/failed;
- hint count;
- elapsed time when measured;
- transcript spans;
- assistance level.

### Self-reported
- what felt confusing;
- what changed understanding;
- perceived difficulty;
- confidence;
- overload/frustration.

### Derived
- likely failure transition;
- candidate misconception;
- inferred prerequisite gap;
- recommended next representation.

Derived evidence must cite observed/self-reported event IDs and confidence.

## Minimal experimental protocol

### Phase A — baseline

Give a problem with no solution representation. Ask for:

1. pattern recognition;
2. verbal mental model;
3. next-state prediction where applicable;
4. semantic procedure/pseudocode;
5. implementation attempt.

Stop at the earliest stable failure rather than flooding the learner with all assessments.

### Phase B — diagnose

Generate at least two plausible failure hypotheses when ambiguity exists. Use a small probe to distinguish them.

Example:
- H1: learner does not understand the window invariant;
- H2: learner understands invariant but cannot express loop/control-flow semantics.

### Phase C — intervene

Choose one representation + operation. Record version and rationale. Avoid changing multiple variables unless the goal is exploratory rather than causal.

### Phase D — immediate retest

Use a fresh but closely matched item. Record assistance.

### Phase E — fade

Remove the representation/hints and require reconstruction or blank implementation.

### Phase F — transfer

Use a changed-surface problem where superficial cues differ.

### Phase G — delayed retrieval

Repeat after delay using a different form. Do not show the prior lesson first.

## Suggested single-case design progression

We are not claiming formal WWC-standard causal evidence in v0.1. We can still borrow good single-case practices:

1. repeated baseline measures before calling a weakness stable;
2. repeated outcome measures rather than one post-test;
3. alternating interventions when equivalent problems permit;
4. replication across multiple problems;
5. explicit phase boundaries;
6. record confounds and deviations;
7. do not infer population-level effectiveness from one participant.

Reference: What Works Clearinghouse Single-Case Design resources: https://ies.ed.gov/ncee/wwc/Handbooks

## Success criteria for Research Gate R0

Before building a general UI, we need one complete, auditable trajectory satisfying all of:

- raw evidence preserved privately and hashed;
- normalized transcript with source provenance;
- at least one failure transition identified;
- intervention representation + operation + version recorded;
- immediate behavior measured;
- scaffold removal attempted;
- hidden/changed-surface transfer measured;
- delayed retrieval measured;
- self-report and behavioral results compared;
- another agent can reconstruct what happened from repo artifacts;
- learner reports that instrumentation overhead remained acceptable.

## Research Gate R1: replication within Subject 001

Before adding many DSA families or rich media:

- reproduce at least one intervention effect across multiple matched problems/sessions;
- demonstrate at least one case where a preferred representation did **not** improve outcomes;
- demonstrate at least one AI-overreliance case and successful scaffold fading;
- validate that the learner-state model can be wrong and corrected without rewriting history.

## Research Gate R2: external participant

Only after R0/R1 should we consider a second participant. At that point, test whether the procedure transfers—not whether Subject 001's preferred representation transfers.

## Development priorities during research phase

Allowed now:

- schemas;
- deterministic transcript preservation;
- event/episode normalization;
- small reference visualizations;
- evaluation harness;
- hidden problem fixtures;
- CI/research-integrity checks;
- agent handoff/manifest;
- FOSSIL export prototype after canonical Study OS records exist.

Deferred:

- full web product;
- production hosting/CD;
- many DSA patterns;
- video generation;
- image-generation pipelines;
- recommendation engine trained on sparse data;
- public claims of pedagogical effectiveness.
