# Study OS

Study OS is a learning control system that sits between **course/source material** and a **longitudinal learner record**.

Its core problem is the learner ↔ course representation mismatch: a learner may be blocked not only by the target concept, but by the author's terminology, variable names, notation, control flow, decomposition, amount of context, or representation.

Study OS uses AI to adapt those representations while deterministic code/state controls what is being learned, what assistance is allowed, when the learner may advance, and how evidence is interpreted.

> Current phase: **P4 — deterministic learning controller + versioned representation engine + operational improvement loop.** See Issue #63.

## Product thesis

The goal is not a generic AI tutor.

The intended differentiated capability is a **learner-specific intermediate representation layer**:

```text
COURSE / SOURCE MATERIAL
        ↓
CANONICAL COURSE GRAPH
        ↓
DETERMINISTIC COURSE STATE
        ↓
DETERMINISTIC LEARNING CONTROLLER
        ↓ authorized operation
AI / REPRESENTATION ENGINE
        ↓
LEARNER
        ↓
DURABLE OPERATIONAL EVIDENCE
        ↓
LEARNER + CONTROLLER STATE
        ↺
```

Study OS should preserve **productive target difficulty** while reducing **extraneous representation difficulty** during acquisition, then fade assistance and restore authentic/source representations so the learner does not become dependent on simplification.

## Authority boundary

Study OS code/state controls:

- active course node and prerequisites;
- learner-control state;
- allowed next pedagogical operations;
- assistance ceiling;
- advancement/blocking rules;
- assistance fading;
- source-representation restoration;
- transfer/retention requirements where applicable;
- evidence/provenance semantics;
- module-version provenance.

AI may:

- propose diagnosis hypotheses;
- generate a realization of an authorized operation;
- transform terminology, representation, examples, traces, pseudocode, or explanations under explicit constraints.

AI does **not** silently own curriculum progression or mastery.

## Current learner-facing surface

The current product surface is the Study OS GPT app.

A dedicated frontend remains useful later, but GPT currently provides the fastest coherent interface for real learning while the deterministic control/data layer develops underneath it.

The canonical live learner store is local Study OS:

```text
SQLite + private evidence store
```

GitHub stores architecture, schemas, decisions, tests, public-safe evidence, and project lineage. It is not the live learner database.

## Durable evidence

Live source-turn capture and cross-chat continuity are implemented and accepted for the current Study OS GPT path.

The core durability invariant is:

> **No silent learner-evidence loss.**

Every locally received learner-facing turn should be durably committed before acknowledgement. Failures must remain visible/recoverable, and remote turns missed before local receipt must be reconcilable from source evidence rather than invented.

Evidence hierarchy:

```text
RAW / SOURCE EVIDENCE
        ↓
NORMALIZED OPERATIONAL RECORDS
        ↓
DERIVED LEARNER + SYSTEM STATE
```

Transcript language never silently becomes mastery.

Raw learner evidence is private by default. A specific historical recovery transcript was explicitly authorized for public recovery transport; that exception does not change the default privacy boundary.

## Operational learning loop

Normal Study OS use is also the primary product-development data stream.

For meaningful learning trajectories, preserve:

```text
course node/version
→ learner state before
→ source representation
→ learner attempt
→ observed/self-reported difficulty
→ diagnosis hypothesis
→ authorized pedagogical operation
→ exact representation/intervention version
→ assistance level
→ next learner behavior
→ fade/source-restoration result
→ transfer/retention when required
```

This lets Study OS improve from real longitudinal use without rewriting history.

## First-class pedagogical operations

Initial operation families include:

- `try_unaided`
- `explain`
- `rename_terms`
- `change_representation`
- `smaller_step`
- `remove_context`
- `expand_detail`
- `compress_detail`
- `show_trace`
- `explain_invariant`
- `give_hint`
- `show_worked_example`
- `restore_original`
- `transfer_probe`
- `retention_probe`

An intervention can contain multiple operations. Study OS should not attribute improvement to one variable when several things changed together.

## Early operational evidence

Historical real use exposed an important product-discovery sequence around LeetCode Two Sum and dictionary semantics:

```text
seen
→ still confusing because of prior set association
index_by_num
→ still confusing
box
→ learner reports clearer representation
→ subsequent dictionary lookup answered correctly
```

This supports a **candidate representation-interference hypothesis**, not a universal rule and not proof that renaming alone caused the improvement. The intervention also reduced task complexity/context, so representation and decomposition must remain separate variables.

The broader design implication is that Study OS must be able to adapt very small representation dimensions—such as one identifier—not only switch between large modalities like prose and diagrams.

## Deterministic learning control

The target conceptual state machine is:

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

Course-node progression requirements live in machine-readable policy rather than tutor intuition.

## Modular versioning

Study OS should version independently where practical:

- course graph;
- controller/policy;
- operation taxonomy;
- diagnosis module;
- representation engine;
- prompt/template;
- retrieval/ranking;
- assessment;
- learner-state derivation;
- model/provider adapter.

Every operational decision should be reconstructable from the module versions that produced it.

Historical evidence remains immutable. New module versions can be replayed against old inputs as **counterfactual evaluation**, but replay outputs are never treated as learner outcomes that actually occurred.

## Longitudinal development path

Study OS should be used continuously while the learner progresses through increasingly difficult material:

```text
Python/DSA foundations
→ LeetCode-style problems
→ complex DSA
→ system design
→ AI-system reasoning / debugging
```

The growing operational transcript becomes a versioned evaluation corpus for discovering controller/representation successes and failures.

Once the contracts are stable and repeated real trajectories exist, authenticated/beta users can test which mechanisms generalize and which require personalization. Subject 001 longitudinal evidence remains subject-level evidence until broader replication exists.

## Long-horizon cost/distribution direction

This is not a current implementation priority, but the architecture should permit replacing large-LLM work with cheaper components when the product behavior is understood.

Possible future representation/diagnosis implementations include:

- parser / AST / compiler transforms;
- deterministic traces and static analysis;
- identifier/terminology rewriting;
- templates;
- retrieval/cached validated representations;
- sentence embeddings / sentence transformers;
- small classifiers or task-specific models;
- IR-to-IR and language/notation converters;
- constrained LLM fallback for ambiguous/generative work.

The controller contract should remain stable regardless of which implementation fulfills an authorized operation.

## Architecture and planning authority

Start here:

- [`docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`](docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md)
- [`docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`](docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md)
- [`docs/DECISIONS.md`](docs/DECISIONS.md)
- [`docs/HANDOFF.md`](docs/HANDOFF.md)

P3 durability/reconciliation specifications remain supporting infrastructure and historical design authority for evidence capture.

## Repository boundary

Study OS owns:

- learner/session source evidence;
- operational learning events and episodes;
- course/control state;
- learner-state derivations;
- representation definitions/versions;
- intervention decisions/outcomes;
- assessment, transfer, and retention evidence;
- module-version provenance and replay evaluation.

FOSSIL remains optional downstream lineage/research promotion, not runtime learner-state authority.

Implementation code is replaceable. The durable assets are the architecture, data semantics, provenance, control contracts, representations, curriculum structure, and longitudinal evidence.
