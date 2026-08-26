# Learning Control Model

Status: **design clarification; does not expand Research Gate R0**

Study OS currently has strong evidence, checkpoint, validation, capability-state, curriculum-item, and scaffold-control machinery, but its learning-control concepts are distributed across several documents and schemas. This document makes the control loop explicit and separates the **active research study** from broader **planned learner-development tracks**.

The curriculum/proficiency namespace and daily evidence-goal policy are defined in `docs/CURRICULUM_CONTROL_ARCHITECTURE.md` and `contracts/curriculum-control-policy.v0.1.json`.

## Scope rule

There is still only **one active research study**:

- subject: `subject-001`
- domain: DSA
- language: Python
- current R0 concept-family work: Sliding Window / running-extrema foundations
- gate: Research Gate R0

The broader tracks below are **planned competency tracks**, not simultaneous research programs and not evidence that Study OS has validated learning procedures outside DSA. They should be activated only when the current gate and learner needs justify them.

## Curriculum track namespace

Track identifiers describe **what family of capabilities is being developed**. They are not proficiency levels.

Canonical track IDs are:

- `ALG` — Python fluency, manual implementation, DSA, complexity, debugging, and transfer;
- `SWE` — Git, modules, typing, testing, APIs, SQL/databases, concurrency, and software design;
- `MATH` — algebra, linear algebra, probability/statistics, calculus, and optimization as needed;
- `DATA` — NumPy, pandas, visualization, and data handling;
- `ML` — classical ML, training/evaluation, baselines, leakage, calibration, and error analysis;
- `DL` — PyTorch, neural networks, optimization, embeddings, attention, and transformers;
- `AIE` — LLM APIs, structured outputs, tool calling, retrieval/RAG, evals, workflows, and agents;
- `SYS` — production engineering, reliability, model serving, caching/queues, distributed systems, and system design;
- `DIAG` — technical problem framing, debugging, evidence acquisition, hypothesis testing, and communication.

Current status: only `ALG` is part of the active R0 research slice. Every other track is curriculum architecture until explicitly activated.

These tracks are not a strict staircase. Some development can proceed in parallel, provided evidence conditions remain explicit. For example, SWE can strengthen alongside ALG, and practical AIE work can occur before all DL theory is complete without being mistaken for deep model-training mastery.

## Proficiency is a separate namespace

Issue #3's DSA tier meanings are preserved, but new curriculum-track identifiers no longer use `T*`.

The canonical DSA proficiency namespace is:

- `DSA0` — Orientation (`T0` legacy prose);
- `DSA1` — Guided Easy (`T1` legacy prose);
- `DSA2` — Independent Easy (`T2` legacy prose);
- `DSA3` — Guided Medium (`T3` legacy prose);
- `DSA4` — Independent Medium (`T4` legacy prose);
- `DSA5` — Interview Ready (`T5` legacy prose);
- `DSA6` — Advanced (`T6` legacy prose).

A proficiency tier is a **repeated cross-item/session capability gate**, not a curriculum track and not one mastery percentage. Do not invent one universal proficiency scale for future tracks until those tracks have their own observable capability/evidence requirements.

## Canonical learning-control loop

Study OS should conceptually organize learning as:

```text
goal
  -> plan
  -> task / learning episode
  -> attempt
  -> test / assessment
  -> evidence
  -> capability state
  -> diagnosis / next-action decision
  -> plan update
  -> transfer / delayed test
```

These concepts must remain distinct. In particular, a plan is not evidence, a score is not a goal, and a model diagnosis is not observed truth.

## Goal system

A **goal** states a desired capability and the evidence required to consider that capability demonstrated.

A goal should eventually contain at least:

- goal ID;
- competency track;
- capability/behavior;
- target context;
- target assistance level;
- required outcome window (immediate, faded, transfer, delayed);
- success evidence requirements;
- priority/status;
- parent goal when hierarchical.

Example:

```yaml
goal: solve_sliding_window_unaided
track: ALG
capability: implementation
target_assistance: A0
required_evidence:
  - matched_problem_pass
  - changed_surface_transfer_pass
  - delayed_retrieval_pass
```

### Current implementation status

Study OS does **not yet have a first-class canonical goal object/schema**. Goal-like state exists implicitly through:

- the project/research goal;
- checkpoint `current_focus`;
- checkpoint `next_action` / `next_probe`;
- capability state and retention scheduling.

A durable multi-goal schema should not be added merely for completeness; define it when the live learning loop needs canonical multi-goal planning.

## Plan system

A **study plan** is an ordered, revisable strategy for collecting the evidence required by one or more goals.

A plan may specify:

- active goals;
- planned concepts/tasks;
- intended assessments;
- assistance/fading strategy;
- transfer/retention schedule;
- prerequisites;
- time allocation;
- stop/replan conditions.

Plans are hypotheses about how to make progress. They must be updated when evidence contradicts them.

### Current implementation status

Study OS has a **partial plan system**, distributed across:

- `docs/RESEARCH_PLAN.md` for the active experiment;
- versioned curriculum item/episode sequencing;
- checkpoint `next_action`, `next_probe`, and retention due state;
- shadow agent/tutor proposals.

There is **no unified canonical learner study-plan schema yet**.

### Daily evidence goals

Issue #42 adds a narrower planning concept without pretending the full plan system exists.

A **daily evidence goal** is a derived, revisable objective for the current study period. It should eventually answer:

> Given canonical learner evidence, due retention, current phase, explicit priorities, and available study budget, what bounded evidence objective should be pursued next?

It may include target track/competency, current evidence refs, desired next capability state, interaction mode, maximum assistance/fade target, due retention, a transfer probe, priority, optional time/effort budget, stop/replan condition, and rationale/provenance.

A daily goal is not observed evidence, not mastery authority, and not a quota. Time spent or number of items completed may constrain a session but cannot by themselves prove progress.

The initial advisory control skeleton is:

```text
due retention
  -> highest-value active competency
  -> diagnose if ambiguous
  -> practice/remediate
  -> fade
  -> transfer if warranted
  -> checkpoint
  -> schedule next probe
```

Runtime implementation of a daily-goal selector is deferred until the richer learner-state prerequisites are available and must begin shadow-only.

## Task / episode system

The canonical atomic learning unit remains the learning episode:

`pre-state -> task -> attempt -> failure/uncertainty -> diagnosis -> intervention -> re-attempt -> assessment -> fade -> transfer -> delayed evidence`

A plan can contain many episodes. A single session can contain many episodes. One goal can require evidence from many episodes.

## Test / assessment system

Study OS already has a strong testing concept at two levels.

### Learner tests

Learner assessment should include, as relevant:

- deterministic correctness;
- explanation/state prediction;
- implementation;
- debugging;
- assistance-faded retest;
- changed-surface transfer;
- delayed retention;
- AI oversight / correction of generated work.

Hidden transfer items must remain separate from teaching examples.

### System tests

The implementation validation strategy already covers static contracts, DB/migrations, evidence integrity, service semantics, MCP conformance, checkpoint/resume, backup/restore, failure injection, privacy, cross-session acceptance, and learning-validity checks.

The learner test system and software test system are related but must not be conflated.

## Scoring and capability-state system

Study OS deliberately does **not** use one global mastery score.

The current canonical capability states are:

- `not_tested`
- `fail`
- `partial`
- `pass_supported`
- `pass_unaided`
- `pass_transfer`
- `pass_delayed`

Correctness is also interpreted together with assistance level:

- A0 none;
- A1 reminder;
- A2 small cue;
- A3 structural/subgoal hint;
- A4 partial representation/scaffold;
- A5 worked example;
- A6 complete solution.

This is the current scoring philosophy: **a vector of evidence-backed capability states, not one percentage**.

Derived confidence values belong to hypotheses/diagnoses and must not be confused with calibrated probability of learner mastery unless calibration has actually been established.

## DSA proficiency promotion

The initial C1 proficiency policy is deliberately conservative and configurable.

For independent DSA bands (`DSA2`, `DSA4`, `DSA5`, `DSA6`), promotion requires relevant repeated evidence that includes unaided performance, changed-surface transfer, delayed retrieval, and any critical capability named by the claim such as implementation/debugging.

Do not promote from:

- one successful item;
- supported-only success into an independent band;
- self-report alone;
- an average that hides an implementation or transfer gap;
- an exposed teaching item relabeled as unseen evidence;
- AI-assisted construction relabeled as unaided manual implementation;
- immediate success inferred as transfer or delayed mastery.

The current machine policy uses at least two distinct unseen items as an initial configurable default and asks for more than one session when practical. That threshold is an operating policy, not a validated population-level pedagogical constant.

## Manual versus AI-assisted evidence

Manual and AI-assisted work should remain distinguishable through interaction-mode and assistance provenance rather than through a fabricated universal dual score.

Examples include:

- blank manual implementation;
- scaffolded manual implementation;
- code reading/debugging;
- AI oversight/review;
- AI-assisted construction;
- verbal/phone shorthand when full implementation is not being measured.

AI-assisted success can support capabilities such as oversight, architecture, decomposition, or debugging. It cannot silently become A0 blank-manual implementation evidence.

## Scoring technical problem framing

For `DIAG`, do not score whether the learner guessed the hidden root cause immediately. Score observable diagnostic behavior.

Initial dimensions:

1. `goal_identification` — establishes what success means;
2. `ambiguity_detection` — notices underspecification;
3. `evidence_acquisition` — requests relevant actual/expected examples, traces, or metrics;
4. `system_decomposition` — maps plausible failure boundaries;
5. `hypothesis_generation` — produces multiple plausible explanations when warranted;
6. `experiment_design` — proposes tests that discriminate between hypotheses;
7. `trust_reasoning` — identifies what evidence would justify believing an output/score;
8. `uncertainty_handling` — separates known, inferred, and unknown;
9. `tradeoff_reasoning` — recognizes cost/latency/quality/reliability tradeoffs;
10. `technical_communication` — communicates at an appropriate depth and drills down on request.

These should use the same evidence-state philosophy as other capabilities rather than a permanent personality-style score.

## Suggested current time allocation

While basic DSA/Python fluency is being restored, the current planning heuristic remains:

- **50%** `ALG`;
- **35%** `SWE`/`SYS`;
- **15%** `DIAG`.

After DSA reaches a stable interview-maintenance level, a reasonable current heuristic is:

- **25%** `ALG`;
- **45%** `SWE`/`SYS`;
- **30%** `AIE`/`DIAG`.

These percentages are not a validated pedagogical claim and are not the permanent allocation for the broader Python-to-ML-to-AI roadmap. When explicit MATH/DATA/ML/DL goals become active, allocation should be recomputed from learner goals, prerequisites, retention obligations, and observed interview/project gaps.

## Activation rule for new tracks

A planned track may become an active Study OS learning/research slice only after:

1. the learner has a concrete goal requiring it;
2. expected capabilities and observable evidence are defined;
3. suitable assessment/transfer criteria exist;
4. activating it does not invalidate or silently bypass the current research gate;
5. project state is updated explicitly in the manifest/handoff if the active scope changes.

Until then, the nine-track map is a **curriculum architecture**, while R0 remains a narrow DSA/Python research experiment.

## Open design work

Do not implement all of these immediately. Subsequent design/implementation decisions should determine when Study OS needs first-class schemas/services for:

- durable multi-goal state;
- unified study plans;
- assessment/test specifications across domains;
- competency definitions outside the instantiated DSA slice;
- time-allocation policies;
- shadow then promoted daily-plan selection;
- technical-diagnosis scenario fixtures;
- eval rubrics for open-ended engineering judgment.

Any such implementation must preserve the existing observed/self-reported/derived evidence boundary, multidimensional capability model, and Issue #10/#21 promotion/verification gates.
