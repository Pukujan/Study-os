# Study OS Roadmap

Date: 2026-09-03
Status: canonical execution roadmap
Primary tracker: #63

## Product direction

Study OS is a deterministic learning-control layer between course/source material and a longitudinal learner record.

The core product problem is the **learner ↔ course representation mismatch**. AI should make source material easier to acquire by changing unnecessary representation difficulty while preserving the target skill. Deterministic code/state controls curriculum progression, assistance, fading, restoration, evidence semantics, and module versions.

```text
COURSE / SOURCE MATERIAL
        ↓
COURSE GRAPH + NODE VERSION
        ↓
DETERMINISTIC COURSE STATE
        ↓
DETERMINISTIC LEARNING CONTROLLER
        ↓ authorized operation
VERSIONED REPRESENTATION ENGINE
        ↓
GPT LEARNER SURFACE
        ↓
DURABLE OPERATIONAL EVIDENCE
        ↓
LEARNER + CONTROLLER STATE
        ↺
```

## Durable assets

The project treats these as durable:

- architecture and ownership boundaries;
- persistent data semantics/migrations;
- raw evidence integrity/provenance;
- course-node/prerequisite/progression contracts;
- learner-control state semantics;
- pedagogical-operation definitions;
- representation lineage and reversible mappings;
- learner/system evaluation semantics;
- module-version provenance;
- replay/evaluation lineage;
- explicit invariants, PDD/SDD/ADR/decision records.

Implementation code is replaceable.

## Current phase — P4

**Deterministic learning controller + representation engine + operational improvement loop.**

P3 durability, continuity, historical reconciliation, and structured curriculum work now support P4 rather than define the center of the product.

The immediate objective is to make every learner-facing teaching action reconstructable as:

```text
course state
+ learner-control state
+ evidence
→ deterministic authorization
→ versioned operation / representation
→ bounded AI realization
→ learner outcome
→ deterministic state transition
```

## P4.0 — Canonical contracts

Highest priority.

- [ ] Define machine-readable course-node/version contract.
- [ ] Define prerequisite and progression-policy semantics.
- [ ] Define deterministic learner-control state machine.
- [ ] Define assistance ceiling/levels and transition rules.
- [ ] Define versioned pedagogical-operation registry.
- [ ] Define representation/version/reversible-mapping contract.
- [ ] Define diagnosis-hypothesis semantics.
- [ ] Define decision record linking evidence, controller decision, operations, representation, and module versions.
- [ ] Define outcome record linking intervention to subsequent learner behavior.
- [ ] Define replay records that are explicitly counterfactual and never learner evidence.

Design authority:

- `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`
- `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`

## P4.1 — Smallest real vertical slice

Do not build a generic framework first.

Implement one complete real course-node loop on the current learner path:

```text
course node/version
→ learner-control state
→ deterministic authorization
→ bounded GPT operation
→ representation/version provenance
→ learner response
→ outcome
→ deterministic state transition
```

Initial operation subset:

- `try_unaided`
- `rename_terms`
- `smaller_step`
- `show_trace`
- `give_hint`
- `restore_original`

Required invariants:

- same canonical inputs + controller version => same authorization;
- GPT cannot directly advance course/mastery state;
- assistance cannot exceed policy ceiling;
- multi-dimensional interventions stay multi-dimensional in data;
- source representation remains restorable where claimed;
- exact learner-facing turns remain durably captured independently of semantic processing.

## P4.2 — Operational improvement loop

Normal learning is the primary system-development dataset.

For meaningful trajectories preserve:

```text
course node/version
learner-control state before
source representation
learner attempt
observed/self-reported difficulty
diagnosis hypothesis/version
authorized operation(s)/version
representation version
assistance level
next learner behavior
fade/restoration outcome
transfer/retention when applicable
module version set
```

Version independently where useful:

- course graph;
- controller/policy;
- operation taxonomy;
- diagnosis;
- representation engine;
- prompts/templates;
- retrieval/ranking;
- assessment;
- learner-state derivation;
- model/provider adapter.

Development loop:

```text
real trajectories
→ identify failure
→ propose module version N+1
→ offline replay
→ contract/quality comparison
→ prospective real dogfood
→ keep/promote/revert
```

Replay output never becomes historical learner outcome evidence.

## P4.3 — Learn through increasing complexity

Use Study OS continuously through the actual learning path:

```text
Python / DSA foundations
→ arrays / dictionaries / common patterns
→ LeetCode-style problems
→ complex DSA
→ system design
→ AI-system reasoning and debugging
```

The system should accumulate high-value trajectories where it can distinguish:

- actual concept difficulty;
- missing prerequisite;
- representation/terminology interference;
- excessive or insufficient information;
- task decomposition too coarse/fine;
- too much assistance/dependence.

As complexity increases, verify that simplified representations can be faded and authentic/source representations restored.

## Supporting P3 work

P3 remains important infrastructure:

### Durability / continuity

Keep:

- durable source-turn capture;
- idempotency/retry safety;
- cross-chat continuity;
- backup/restore;
- doctor/integrity checks;
- historical reconciliation where source evidence exists.

Core invariant:

> No silent learner-evidence loss.

### Structured curriculum

Continue acquiring/structuring approved source material as required by actual learning goals.

Preserve:

- provenance/rights;
- source version/hash where practical;
- competency/prerequisite mapping;
- source representation;
- task/item version;
- evidence class.

Public/source curriculum is candidate material, not automatically a good learner-facing representation.

## Later phase — beta/authenticated users

Do not prioritize this until longitudinal dogfooding has produced repeated stable trajectories on harder material.

Candidate gate:

- reliable durability/continuity;
- auditable controller contracts;
- multiple versioned real trajectories;
- repeated useful representation operations;
- source restoration/fading checks;
- known major controller failure modes;
- trustworthy evidence semantics.

Then test:

> Which mechanisms generalize, which require personalization, and which fail across learners?

Subject 001 remains a design participant, not a population proxy.

## Much later — inference-cost/distribution optimization

Do not optimize this now, but preserve module boundaries that allow it later.

Potential cheaper implementations:

- state/rules;
- parser/AST/compiler transformations;
- deterministic traces/static analysis;
- terminology/identifier rewriting;
- validated templates;
- retrieval/cached representations;
- sentence embeddings/sentence transformers;
- small classifiers/task-specific models;
- IR-to-IR or language/notation conversion;
- constrained LLM fallback.

Future routing:

```text
authorized operation
        ↓
deterministic transform available? ─ yes → use it
        ↓ no
retrieval/template/small model enough? ─ yes → use it
        ↓ no
constrained LLM generation
        ↓
contract validation
```

Cost optimization follows validated product behavior, not the reverse.

## Deprioritized now

- broad frontend work;
- video-generation infrastructure;
- generic multimodal platform work;
- production authentication/multi-tenancy;
- broad population research;
- deep FOSSIL integration;
- premature LLM-cost optimization;
- blanket hardening unrelated to control/data/evidence integrity.

## Current execution order

1. Freeze P4 PDD/SDD and invariants.
2. Inspect current runtime/schema against P4 semantic contracts.
3. Design the smallest additive data changes required; reuse existing evidence substrates.
4. Implement one real current course-node/control loop.
5. Route learner-facing GPT teaching through explicit `course_node + learner_state + authorized_operation` context.
6. Record decision/representation/module provenance and learner outcome.
7. Keep learning normally and let real failures drive the next operation/state additions.
8. Add replay/version-comparison once multiple real trajectories exist.
9. Expand to complex DSA/system design before considering beta-user architecture.

## Roadmap governance

`docs/ROADMAP.md`, `docs/CURRENT_STATE.md`, `docs/HANDOFF.md`, `docs/DECISIONS.md`, the P4 PDD/SDD, and Issue #63 are current planning authority.

Historical issues and plans remain lineage. An old unchecked item is not current priority when superseded by later accepted product direction.
