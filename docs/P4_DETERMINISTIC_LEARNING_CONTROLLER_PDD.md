# P4 Product Design — Deterministic Learning Controller + Representation Engine

Date: 2026-09-03
Status: proposed canonical P4 product design
Parent tracker: #63

## Product thesis

Study OS exists to solve the mismatch between **how a course/source represents a concept** and **how a learner can most productively acquire that concept**.

The product should use AI to transform representation, explanation, decomposition, terminology, examples, and modality while preserving the target skill. The curriculum path, learner-control state, assistance policy, advancement criteria, evidence semantics, and module-version provenance remain controlled by deterministic code/state.

The LLM is therefore a bounded cognition/generation component, not the authority for curriculum progression or mastery.

## Core architecture

```text
COURSE / SOURCE MATERIAL
        ↓
CANONICAL COURSE GRAPH + NODE VERSION
        ↓
DETERMINISTIC COURSE STATE
        ↓
DETERMINISTIC LEARNING CONTROLLER
        ↓ authorized pedagogical operation
REPRESENTATION ENGINE
        ↓
LEARNER-FACING GPT RESPONSE
        ↓
LEARNER RESPONSE / ATTEMPT
        ↓
DURABLE OPERATIONAL EVIDENCE
        ↓
OUTCOME + LEARNER/CONTROLLER STATE
        ↺
```

The durable evidence hierarchy remains:

```text
RAW / SOURCE EVIDENCE
        ↓
NORMALIZED OPERATIONAL RECORDS
        ↓
DERIVED LEARNER + SYSTEM STATE
```

## Product moat

The intended differentiated capability is not generic AI tutoring.

It is a **learner-specific intermediate representation layer** that can:

1. detect whether a barrier is likely conceptual, prerequisite-related, representational, informational, or decomposition-related;
2. authorize a bounded pedagogical operation;
3. transform only the relevant dimensions of the source material;
4. preserve the underlying target difficulty;
5. observe the learner's next behavior;
6. fade assistance;
7. restore authentic/source representations;
8. learn from longitudinal operational trajectories through explicit module versioning.

The historical `seen → index_by_num → box` episode is an early subject-level example of representation interference. It is not evidence that `box` is universally superior or that renaming alone caused the observed improvement.

## Authority boundary

### Deterministic Study OS authority

Code/state controls:

- active course/competency node;
- prerequisite satisfaction;
- current learning-control state;
- allowed next pedagogical operations;
- assistance ceiling;
- progression and blocking rules;
- when assistance must fade;
- when source/authentic representation must be restored;
- transfer/retention requirements where applicable;
- evidence and provenance semantics;
- module version set attached to each decision.

### AI authority

AI may:

- propose diagnosis hypotheses;
- realize an authorized pedagogical operation;
- generate an explanation/example/trace/pseudocode/code rendering under constraints;
- transform representation under an explicit reversible contract;
- suggest candidate follow-up observations to the deterministic controller.

AI may not silently:

- advance course state;
- mark a prerequisite satisfied;
- declare mastery from conversation language;
- raise assistance above policy;
- alter the target concept;
- rewrite historical learner state;
- hide which representation/operation/version produced an interaction.

## Productive vs extraneous difficulty

Study OS should preserve **productive target difficulty** while reducing **extraneous representation difficulty**.

Possible representation/decomposition dimensions include:

- identifier/variable naming;
- terminology;
- notation;
- problem wording;
- abstraction level;
- code/control-flow style;
- index/value presentation;
- API vocabulary;
- prose/table/trace/diagram/pseudocode/code;
- context amount;
- step granularity;
- decomposition/recomposition.

The product must never infer that easier immediate performance proves the target skill was preserved. Restoration, unaided work, transfer, or retention provide stronger evidence where required.

## First-class pedagogical operations

Initial operation vocabulary:

```text
try_unaided
explain
rename_terms
change_representation
smaller_step
remove_context
expand_detail
compress_detail
show_trace
explain_invariant
give_hint
show_worked_example
restore_original
transfer_probe
retention_probe
```

Operations are versioned semantic contracts, not free-text tutor labels.

A learner-facing intervention may contain multiple operation dimensions. The system must record each material change rather than attributing an outcome to one convenient explanation.

Example:

```text
rename_terms: seen → box
smaller_step: Two Sum → isolated dictionary lookup
remove_context: remove enumerate/target/complement logic
```

An improvement after this intervention does not prove identifier renaming alone caused the improvement.

## Representation contract

Every meaningful adapted representation should preserve:

```yaml
representation_id: ...
representation_version: ...
concept_id: dictionary_lookup
source_representation_ref: ...
operations:
  - rename_terms
mapping:
  seen: box
reason_evidence_refs:
  - ...
preserved_semantics:
  - dictionary key maps to stored value
target_difficulty_preserved:
  - perform dictionary lookup
extraneous_difficulty_targeted:
  - identifier semantic interference
restorable: true
```

The source representation remains addressable. Simplification is an acquisition strategy, not a permanent fork from authentic material.

## Learning-control state machine

Initial conceptual state machine:

```text
INTRODUCE
  ↓
AWAIT_UNAIDED_ATTEMPT
  ↓
DIAGNOSE
  ↓
AUTHORIZE_OPERATION
  ↓
AWAIT_REATTEMPT
  ↓
FADE_ASSISTANCE
  ↓
RESTORE_SOURCE_REPRESENTATION
  ↓
TRANSFER / RETENTION WHEN REQUIRED
  ↓
ADVANCE_OR_BLOCK
```

A node may skip states when its policy does not require them. Trivial material should not be forced through expensive transfer/retention gates.

## Diagnosis model

Candidate diagnosis families:

- missing prerequisite;
- target-concept failure;
- representation interference;
- terminology/identifier interference;
- excessive information/context;
- insufficient information;
- task/decomposition too coarse;
- over-decomposition;
- over-help / dependence;
- uncertain/mixed.

Diagnosis is an evidence-backed **hypothesis**. AI-proposed diagnosis remains derived data until learner behavior supports or contradicts it.

## Deterministic course progression

Course nodes should become machine-readable contracts.

Example:

```yaml
node_id: dictionary_lookup
node_version: 1
prerequisites:
  - dictionary_literal
  - key_value_semantics
advance_when:
  - condition: unaided_same_surface
    result: pass
  - condition: source_representation_restore
    result: pass
retention_required: false
```

A harder node may require transfer or delayed retention. Advancement is never based only on the tutor saying the learner seems ready.

## Operational transcript as development data

Now that real GPT turns are durably captured across sessions, normal learning is the primary product-development data stream.

For meaningful trajectories preserve:

```text
course node/version
learner-control state before
target concept
source representation
learner attempt
observed/self-reported difficulty
diagnosis hypothesis/version
authorized operation(s)/version
exact representation version
assistance level
learner-facing response reference
next learner behavior
fade/restoration result
transfer/retention result when applicable
module version set
```

This history should allow Study OS to improve through **modular versioning and replay**, not hidden prompt drift.

## Modular evolution

Independently version where practical:

- course graph;
- controller/policy;
- operation taxonomy;
- diagnosis module;
- representation transform;
- prompt/template;
- retrieval/ranking;
- assessment;
- learner-state derivation;
- model/provider adapter.

Every operational decision should pin the versions that produced it.

Historical evidence is immutable. A later module may replay an old input or produce a counterfactual output, but the replay must never be written as if the learner actually experienced it.

## Longitudinal dogfooding plan

Study OS should be used continuously through increasingly difficult material:

```text
Python/DSA foundations
→ arrays/dictionaries/patterns
→ LeetCode-style problems
→ complex DSA
→ system design
→ AI-system reasoning / debugging
```

The purpose is both to learn and to accumulate real trajectories that stress the controller at increasing complexity.

High-value evidence includes cases where:

- the learner initially cannot decode or solve source material;
- Study OS identifies a plausible barrier;
- a bounded operation changes representation/decomposition;
- learner behavior improves;
- assistance fades;
- authentic/source representation is restored;
- changed problems can be handled with less/no assistance;
- retention survives where the node requires it.

These are strong within-learner trajectories, not population-level proof.

## Expansion gate

Authenticated/beta users are a later phase after longitudinal dogfooding establishes sufficiently stable contracts and repeated real trajectories.

The multi-user question is different:

> Which mechanisms generalize, which require learner-specific policies, and which fail across learners?

Before beta, require at minimum:

- reliable durability/continuity;
- auditable deterministic controller contracts;
- multiple versioned real trajectories;
- repeated useful representation operations;
- source restoration/fading checks;
- known major controller failure modes;
- trustworthy evidence semantics.

## Long-horizon inference-cost strategy

This is architectural foresight, not current implementation priority.

The representation/controller boundary should permit future replacement of large-LLM work with cheaper deterministic or specialized components when operational evidence shows the function is stable enough.

Candidate future components:

- rules/state machines;
- parser/AST/compiler transformations;
- deterministic program traces;
- identifier/terminology rewriting;
- templates;
- retrieval/cached validated representations;
- sentence embeddings / sentence transformers;
- small classifiers;
- small task-specific models;
- IR-to-IR transforms;
- language/notation converters;
- static analysis;
- search/ranking.

Future routing may be:

```text
controller authorizes operation
        ↓
deterministic transform available? ─ yes → use it
        ↓ no
retrieval/template/small model sufficient? ─ yes → use it
        ↓ no
constrained LLM generation
        ↓
validate against operation contract
```

Cost optimization follows validated product behavior. Do not optimize away the LLM before Study OS has learned which operations actually matter.

## P4 success condition

P4 succeeds when real learner-facing teaching behavior can be reconstructed as:

```text
course state
+ learner-control state
+ evidence
→ deterministic authorization
→ versioned operation/representation
→ bounded AI realization
→ learner outcome
→ deterministic state transition
```

and when accumulated real trajectories can be replayed against newer module versions without corrupting historical evidence.

## Explicitly out of scope for current P4 implementation

- broad frontend work;
- video-generation infrastructure;
- general multimodal platform work;
- production multi-user authentication;
- population efficacy claims;
- premature inference-cost optimization;
- deep FOSSIL integration;
- unrelated blanket hardening.
