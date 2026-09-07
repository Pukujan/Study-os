# P4 Automated Dataset-Shaped Pedagogy Pipeline

Date: 2026-09-07
Status: proposed architecture clarification; subordinate to Issue #63, ADR-0016, the frozen September-4 calibration evidence, and PR #73

## Purpose

Restore the original Study OS product direction that became under-emphasized during recent reactive failure analysis:

> The learner should not have to keep correcting the tutor's pedagogy.
>
> Study OS should automatically compile or select a structured, dataset-shaped pedagogical plan, then execute each step through a deterministic controller and a tightly targeted learner-facing output contract.

The target is not a larger tutoring prompt. It is an automated authoring + validation + execution pipeline.

The historical learner corrections remain valuable because they define invariants and regression cases. They are not the intended runtime control mechanism.

## Existing Study OS direction this clarifies

The existing donor audit already recommends a composite approach rather than free-form tutoring:

- Oppia/OATutor-style atomic competencies, prerequisites, misconceptions, steps and scaffolds;
- ScaffoldLM-style ordered intermediate targets and assess/remediate/advance behavior;
- deterministic prerequisite eligibility and progression;
- LLM-generated representations and constrained item variants behind validation boundaries;
- offline/shadow reproduction before live promotion.

This document applies that direction to P4 prerequisite-sensitive traversal, representation selection, and Luna/Sol calibration.

## Product objective

For a supported problem, Study OS should be able to produce and execute something conceptually equivalent to:

```text
SOURCE PROBLEM / CURRICULUM ITEM
        ↓
AUTOMATED PEDAGOGICAL AUTHORING
        ↓
versioned competency + prerequisite graph
        ↓
versioned problem-step graph
        ↓
step-specific representation + exercise + feedback contracts
        ↓
deterministic validation / promotion
        ↓
EXECUTABLE TEACHING PLAN
        ↓
deterministic learner-state controller
        ↓
TARGETED TURN SPEC
        ↓
bounded Luna/Sol realization
        ↓
output validator
        ↓
learner
        ↓
evidence / retry / prerequisite detour / advance
```

The learner should not be responsible for repeatedly saying:

- use the chart again;
- that exercise tests the wrong thing;
- you moved too far;
- do not show me the answer;
- explain one relationship only;
- go back because I do not understand the code.

Those failure classes should be prevented or rerouted by the system.

## Two-machine architecture

### Machine A — automated pedagogy author/compiler

This is the authoring/decomposition layer.

Its job is to convert source material into a candidate structured teaching artifact, not to tutor live from scratch.

Conceptual input:

```yaml
source_item:
  source_id: string
  problem_text: string
  source_code_or_solution: object | null
  domain: string
  curriculum_context: object | null
  known_competencies: [string]
  known_prerequisites: [string]
```

Conceptual output:

```yaml
PedagogicalPlanCandidate:
  plan_id: string
  source_item_ref: string
  compiler_version: string
  compiler_prompt_version: string
  compiler_schema_version: string
  model_provider_version: string

  competencies:
    - competency_id: string
      observable_behavior: string
      prerequisites: [string]
      misconception_hypotheses: [string]

  steps:
    - step_id: string
      target_relation: string
      competency_refs: [string]
      prerequisite_refs: [string]
      entry_requirements: [string]
      representation_intent_ref: string
      exercise_contract_ref: string | null
      feedback_policy_ref: string
      advance_policy_ref: string
      forbidden_future_relations: [string]

  edges:
    - from_step: string
      to_step: string
      condition_ref: string

  prerequisite_detours:
    - trigger_hypothesis: string
      prerequisite_ref: string
      return_step_ref: string

  representations: [RepresentationIntentSpec]
  exercises: [ExerciseContract]
  output_contracts: [TargetedTurnSpec]
```

This is intentionally dataset-shaped. It resembles the useful structural atoms found in educational content systems:

```text
problem
  → step
      → competency / knowledge component
      → prerequisite
      → answer/assessment contract
      → hint pathway
      → scaffold subproblem
      → representation
      → retry/verification behavior
```

Study OS adds stronger representation-state, evidence, provenance, deterministic progression, restoration, and prerequisite-detour semantics.

### Machine B — deterministic teaching executor

This is the online runtime.

It must not ask the model to rediscover the pedagogical graph every turn.

Given:

```text
accepted plan revision
+ current learner/controller state
+ current step
+ evidence
```

it chooses:

```text
authorized operation
+ exact target relation
+ exact representation intent
+ exact exercise/feedback mode
+ information budget
+ progression permissions
```

Then the model receives only a bounded realization task.

## Targeted output contract

The targeted-output method should be first-class and typed.

Conceptual contract:

```yaml
TargetedTurnSpec:
  turn_spec_id: string
  plan_revision: string
  step_id: string
  target_relation: string
  operation: explain | probe | validate | correct | retry | verify | bridge | restore

  representation:
    family: table | state_flow | sequence_trace | comparison_view |
            concrete_scenario | diagram | pseudocode | source_code | prose
    mode: teach | exercise | correction | validation | restore
    required_semantic_roles: [string]
    required_relationships: [string]
    required_state_variables: [string]
    preserve_from_previous: [string]
    forbidden_components: [string]
    answer_cues: allowed | forbidden
    code_visibility: hidden | optional | secondary | primary | required

  information_budget:
    new_relations_max: integer
    new_symbols_max: integer
    explanatory_sentences_max: integer
    questions_max: integer

  exercise:
    target_relation: string | null
    held_constant: [string]
    changed_dimension: [string]
    allowed_response_kinds: [string]
    partial_suboperations: [string]
    forbidden_neighboring_targets: [string]

  progression:
    may_advance: boolean
    parent_progression_blocked: boolean
    assistance_ceiling: string

  safety:
    hidden_answer_refs: [string]
    forbidden_future_relations: [string]
```

The learner-facing model should not decide these fields. It realizes them.

## Output validation

Before a turn reaches the learner, Study OS should validate the candidate realization against the `TargetedTurnSpec`.

Hard checks where mechanically possible:

```text
required representation family realized?
required semantic roles present?
required relationships present?
required state preserved?
forbidden future concepts absent?
answer cues obey teach/exercise mode?
exercise targets the active relation?
information budget respected?
code visibility respected?
hidden assessment answer absent?
progression authorization respected?
```

Failure policy:

```text
candidate fails contract
→ regenerate under same TargetedTurnSpec
→ if repeat failure, try alternate renderer/template
→ if still failing and policy permits, escalate model tier
→ otherwise fail closed
```

This is how Luna should be calibrated: reduce the amount of pedagogical freedom Luna has to get wrong before deciding that Sol is required.

## Automated task decomposition

Task decomposition should not remain a manually handcrafted activity forever.

The intended path is:

```text
source problem
→ candidate competency decomposition
→ candidate prerequisite graph
→ candidate bridge graph
→ candidate step/scaffold structure
→ deterministic schema + graph validation
→ replay against known goldens/regressions
→ differential/reference evaluation where useful
→ accepted versioned teaching plan
```

Important distinction:

- **Automated authoring is desired now in shadow/offline evaluation.**
- **Arbitrary unreviewed raw-problem compilation into live canonical learner state remains deferred.**

Those are compatible positions.

We can automate generation and evaluation before trusting automatic promotion.

## Dataset-shaped calibration corpus

The calibration corpus should combine several evidence classes rather than depend on one model's transcript.

### 1. Historical learner-approved Study OS trajectories

Use public-safe derived fixtures from the September-4 sliding-window calibration:

- task/bridge ordering;
- representation continuity;
- teaching vs exercise cue differences;
- partial-response preservation;
- correction → retry → verification;
- restoration before validation;
- information-budget failures;
- wrong-target exercise failures.

### 2. Structured donor/dataset-shaped content

Use donor structures as authoring/evaluation references, not as a monolithic runtime dependency:

```text
atomic competency / prerequisite
problem → step
step → KC/competency
step → hint/scaffold
misconception → remediation
repeated opportunity / attempt evidence
```

### 3. Synthetic adversarial fixtures

Generate cases that deliberately test:

- missing prerequisite;
- skipped bridge;
- representation dropped;
- code shown when code_visibility=hidden;
- exercise probes neighboring/easier fact instead of target relation;
- answer leakage;
- too much information;
- too little required context;
- premature abstraction/generalization;
- meta-feedback misclassified as learner failure.

### 4. Luna/Sol differential realizations

For the exact same `TargetedTurnSpec`, compare candidate realizations.

This tests renderer/model capability after decomposition, routing, representation selection, and exercise targeting have already been fixed upstream.

Sol is a donor/reference. It is not the gold plan generator or grading authority.

## Mutation-testing application

For the mutation-testing trajectory, the automated authoring/evaluation path should produce a structure more like:

```text
parent: mutation operator behavioral effect
        ↓ requires
boolean/comparison boundary semantics
        ↓
operator changes condition at boundary
        ↓
connect visual boundary behavior to source-code operator
        ↓
return to mutation-testing parent
```

If the learner says:

```text
I don't know how the code works
```

Machine B should not improvise another explanation of the same code.

It should classify difficulty evidence, consult the accepted prerequisite/bridge structure, block the parent if required, and emit a targeted prerequisite turn such as:

```yaml
operation: bridge
representation.family: table | state_flow | concrete_scenario
representation.code_visibility: hidden
information_budget.new_relations_max: 1
exercise.target_relation: boundary behavior
progression.parent_progression_blocked: true
```

Only after prerequisite micro-evidence supports the return should the controller emit a bridge back toward pseudocode/source code.

## Automation responsibilities vs model responsibilities

### Deterministic / structured system owns

- accepted problem/competency/step identity;
- prerequisite graph;
- current learner path;
- allowed next step;
- prerequisite detour state;
- representation intent;
- exercise target;
- answer-cue policy;
- information budget;
- assistance ceiling;
- progression/mastery authority;
- evidence classification gates;
- version/provenance;
- output-contract validation.

### LLM may propose during authoring

- candidate decomposition;
- candidate prerequisite edges;
- candidate bridge steps;
- candidate misconception hypotheses;
- candidate representations;
- candidate exercise variants.

These remain proposed until the applicable validation/promotion policy accepts a versioned artifact.

### LLM may realize during tutoring

- wording;
- concrete examples within allowed semantics;
- chart/diagram/table realization;
- bounded Socratic questions;
- explanations constrained by the turn spec.

The LLM does not own canonical progression.

## Phased implementation

### AUTO-0 — schema-first authoring contracts

Define executable schemas for:

- competency/prerequisite graph;
- problem-step graph;
- bridge node;
- representation intent;
- exercise contract;
- targeted turn spec;
- authoring provenance/version set.

### AUTO-1 — offline compiler on frozen cases

Run an automated author/compiler against:

1. the known sliding-window problem;
2. the public-safe mutation-testing boundary fixture.

Compare generated candidate plans against historical/golden invariants.

Do not promote automatically to live runtime.

### AUTO-2 — targeted output renderer + validator

Given a frozen `TargetedTurnSpec`, generate Luna and Sol realizations and validate them mechanically.

Measure regeneration rate, hard-failure rate, representation compliance, exercise-target compliance, answer leakage, and information-budget compliance.

### AUTO-3 — automatic candidate-plan evaluation

Evaluate author/compiler candidates with:

- graph/schema validation;
- prerequisite/bridge invariants;
- golden replay;
- mutation/adversarial plan transforms;
- differential model realization;
- explicit unresolved-state handling.

### AUTO-4 — reviewed promotion

Allow a validated candidate plan to become an accepted versioned teaching artifact after the promotion gate.

Initially retain human/reviewed promotion for unfamiliar problems while the compiler is still being calibrated.

### AUTO-5 — increasingly automatic promotion

Only after measured reliability on diverse held-out tasks should Study OS consider policy-driven automatic promotion for bounded problem families.

This is later than automated generation/evaluation; it does not need to block building the compiler now.

## Success criterion

The system is moving in the intended direction when a new supported task can be handled as:

```text
problem arrives
→ Study OS creates/selects structured plan
→ validator accepts plan
→ controller selects exact next pedagogical action
→ targeted output is generated and validated
→ learner responds
→ deterministic branch occurs
```

without the learner repeatedly acting as the tutor's pedagogy debugger.

## Bottom line

The original goal remains:

> automate the decomposition and targeted teaching behavior using structured educational-data-style artifacts, while keeping learner-state/progression authority deterministic.

The September-4 transcript is the regression corpus that teaches us what the schemas and validators must prevent. It is not the runtime operating procedure.
