# P4 Product Design — Prerequisite-Sensitive Remediation

Date: 2026-09-07
Status: focused P4 delta
Parent tracker: #63
Related integration tracker: #66

## Problem

The deterministic learning architecture already distinguishes target difficulty from representation difficulty, but the current executable scaffold path can remain on the same target after learner confusion even when the learner cannot parse a prerequisite representation.

A recent public-safe dogfood regression exposed this failure shape:

```text
parent concept probe
→ learner cannot parse code-first representation
→ tutor repeats/rephrases parent explanation
→ learner remains confused
→ no valid canonical parent answer exists
```

The correct product behavior is not to record a task failure or depend on a bespoke tutor instruction. Study OS should diagnose the barrier as a derived hypothesis, block parent progression, descend to a canonical prerequisite when justified, change representation under a bounded operation, collect micro-evidence, then return to the parent target.

## Product objective

Make this route reconstructable as:

```text
canonical learner evidence
→ versioned structured diagnosis proposal
→ deterministic prerequisite-sensitive routing
→ authorized operation set
→ versioned representation constraints
→ bounded learner-facing realization
→ behavioral micro-evidence
→ deterministic parent re-entry decision
```

The tutor/model remains a proposer and renderer, not progression authority.

## Learner-facing behavior

When the learner cannot understand the representation required to answer the active task, Study OS should be able to:

1. preserve the learner statement as source evidence;
2. propose one or more diagnosis hypotheses such as `missing_prerequisite`, `representation_interference`, or `decomposition_too_coarse`;
3. avoid recording a canonical failure for the parent task until a valid behavioral parent probe occurs;
4. identify an unsatisfied prerequisite only from the canonical prerequisite graph;
5. fail closed when the prerequisite diagnosis is ambiguous;
6. authorize bounded operations such as `smaller_step`, `change_representation`, and `show_trace`;
7. express representation intent structurally rather than with a one-off story;
8. collect one small behavioral probe on the remediation target;
9. return to the parent target only through controller authorization.

## Representation intent

A request for a "chart" or simpler explanation must not be treated as an unconstrained instruction to the tutor model.

Representation candidates should carry machine-readable intent such as:

```yaml
representation_family: decision_tree
semantic_roles:
  state: current_capacity_usage
  threshold: capacity_limit
  decision: allow_or_reject
required_structure:
  - one_root_condition
  - two_outcome_branches
  - explicit_boundary_state
forbidden_features:
  - source_code_primary
  - dense_table_primary
code_visibility: hidden
interaction_granularity: single_probe
```

The concrete domain/example may vary. The invariant is the structural teaching requirement.

## Versioned prompt engineering

For unfamiliar evidence patterns, an LLM may propose diagnosis in a schema-constrained form. The prompt itself is versioned.

Initial artifacts:

- `prompts/p4/diagnosis-proposal.v0.1.md`
- `schemas/p4-diagnosis-proposal.schema.json`
- `study_os.adaptive.diagnosis.DiagnosisProposal`

The model output may contain hypotheses and representation signals. It may not contain progression authority.

## No-dataset / unfamiliar-problem strategy

This delta does **not** enable arbitrary raw-problem compilation in the learner-facing product.

The long-horizon design remains:

```text
unfamiliar problem
→ versioned semantic/decomposition compiler prompt
→ schema-constrained candidate graph
→ deterministic graph validation
→ versioned canonical graph
→ normal deterministic learning controller
```

When no learner dataset exists, uncertainty should remain explicit. The system should use cheap diagnostic probes rather than fabricate learner prerequisites or mastery.

Operational learner evidence can later improve ranking of diagnosis and representations, but the first correct architecture does not require a pre-existing dataset.

## Authority boundary

Study OS code/state controls:

- active parent competency;
- canonical prerequisite membership/order;
- prerequisite satisfaction;
- progression blocking;
- remediation target authorization;
- assistance ceiling;
- legal operation set;
- re-entry to the parent target;
- evidence semantics.

AI may:

- propose diagnosis hypotheses under the pinned schema/prompt;
- propose representation signals;
- realize an authorized representation.

AI may not:

- invent prerequisite IDs;
- convert confusion into canonical incorrect evidence;
- advance the parent task;
- claim prerequisite mastery;
- exceed assistance ceiling;
- redefine the target concept;
- silently alter prompt/schema versions.

## Scope

This focused delta includes:

- a strict structured diagnosis proposal contract;
- a deterministic prerequisite-sensitive remediation router in shadow mode;
- richer structured representation constraints;
- a public-safe regression fixture derived from the failed mutation-lab trajectory;
- specification and verification updates.

## Non-goals

- arbitrary raw-problem → canonical PIR compilation;
- production promotion of the P2/P4 adaptive controller to live authority;
- changing the validated PIR semantics from #66;
- changing PAM B/C sequencing;
- hard-coding theater/ticket examples as universal pedagogy;
- fixed learner-style classification;
- population-level learning claims.

## Success criteria

The regression case must prove:

```text
code/representation confusion
→ no canonical parent failure
→ parent progression blocked
→ structured diagnosis version pinned
→ specific canonical prerequisite selected when evidence supports it
→ ambiguous prerequisite diagnosis fails closed
→ authorized bounded remediation operations exposed
→ representation structural constraints reach the renderer envelope
→ deterministic same-input replay
```

This is a controller/representation correctness improvement, not proof that the chosen representation improves learning generally.
