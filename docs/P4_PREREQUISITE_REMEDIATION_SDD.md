# P4 System Design — Prerequisite-Sensitive Remediation

Date: 2026-09-07
Status: focused P4 design delta
Parent: `docs/P4_PREREQUISITE_REMEDIATION_PDD.md`

## Design objective

Add the smallest deterministic control layer needed to distinguish:

```text
learner failed the target
```

from:

```text
learner could not yet parse a prerequisite/representation required to attempt the target
```

without giving the LLM progression authority.

## Runtime flow

```text
1. learner/source turn is durably recorded
2. caller loads active parent competency + canonical ordered prerequisites
3. versioned diagnosis prompt/model emits schema-constrained DiagnosisProposal
4. strict parser rejects unknown fields/versions/invalid references
5. prerequisite remediation router consumes:
     LearnerSnapshot
     DiagnosisProposal
     parent candidate/competency
     canonical ordered prerequisite IDs
     assistance ceiling
6. router deterministically returns DecisionProposal
7. if prerequisite route is authorized:
     parent progression remains blocked
     target becomes one canonical unsatisfied prerequisite
8. representation policy runs only after the remediation target/task is selected
9. selected representation exposes structural rendering constraints
10. learner-facing model realizes only the authorized envelope
11. behavioral micro-evidence is recorded
12. controller later decides whether parent re-entry is legal
```

## New module: structured diagnosis

File:

`src/study_os/adaptive/diagnosis.py`

### `DiagnosisHypothesis`

Fields:

```yaml
diagnosis_id: string
family: enum
source_evidence_ids: [string]
suspected_competency_ids: [string]
confidence: number | null
status: proposed | supported | contradicted | unresolved
```

Important invariants:

- source evidence is mandatory;
- suspected competency IDs are hypotheses only;
- the object contains no progression field;
- confidence may be null;
- unknown fields fail closed.

### `RepresentationSignals`

```yaml
requested_families: [string]
avoid_families: [string]
code_visibility: unspecified | hide_initially | allow | require
interaction_granularity: unspecified | single_probe | multi_part
```

These signals describe evidence/request state. They are not rendering authorization.

### `DiagnosisProposal`

Version pins:

```text
schema_version = 0.1.0
prompt_version = p4-diagnosis-proposal.v0.1
```

The proposal records the model adapter and canonical source evidence IDs.

## Prompt/schema boundary

Artifacts:

```text
prompts/p4/diagnosis-proposal.v0.1.md
schemas/p4-diagnosis-proposal.schema.json
```

The model is used as a structured hypothesis generator for unfamiliar evidence patterns.

Prompt changes create a new prompt version.
Schema meaning changes create a new schema version.
Historical diagnosis proposals retain their original versions.

The deterministic router must not consume arbitrary free-form tutor prose as authority.

## New module: prerequisite remediation router

File:

`src/study_os/adaptive/prerequisite_remediation.py`

Version:

`0.1.0`

### Inputs

```text
LearnerSnapshot
DiagnosisProposal
parent_candidate_id
parent_competency_id
ordered_prerequisite_ids
assistance_ceiling
```

The prerequisite list must come from canonical course/curriculum state, never from model output.

### Route A — supported missing prerequisite

If:

- diagnosis contains `missing_prerequisite`;
- the suspected competency is an unsatisfied canonical prerequisite;

then:

```text
parent progression = blocked
selected target = prerequisite
primary operation = smaller_step
authorized operation set may additionally include:
  change_representation
  show_trace
```

The router requires `behavioral_micro_probe` next.

### Route B — ambiguous prerequisite

If multiple canonical prerequisites are unsatisfied and the diagnosis does not identify one safely:

```text
selected = none
progression = blocked
diagnostic_probe_required = true
```

The router must not guess.

### Route C — representation/decomposition failure without established prerequisite gap

If diagnosis contains `representation_interference` and/or `decomposition_too_coarse` but no established missing prerequisite:

```text
target remains parent competency
progression remains blocked
operation = change_representation or smaller_step
```

This prevents representation difficulty from silently changing the target skill.

### Route D — insufficient diagnosis

Fail closed and request more behavioral evidence.

## Parent-attempt semantics

A learner statement such as “I do not understand the code” is source evidence about the interaction, not automatically a canonical incorrect answer to the parent task.

The remediation proposal therefore emits:

```text
canonical_parent_attempt_recording:
  forbidden_until_parent_behavioral_probe
```

Persistence code remains responsible for enforcing the distinction between source events and canonical task attempts.

## Representation contract extension

`RepresentationCandidate` gains optional structured constraints:

```yaml
semantic_roles: object<string,string>
required_structure: [string]
forbidden_features: [string]
code_visibility: unspecified | hidden | allowed | required
interaction_granularity: unspecified | single_probe | multi_part
```

The representation policy remains downstream of task/competency selection and continues to enforce:

- same selected task;
- same selected competency;
- allowed representation family;
- semantic validation;
- assistance ceiling.

On selection it surfaces the structural constraint block through `expected_evidence` so the bounded renderer/model envelope can consume it.

This intentionally separates:

```text
WHAT target is legal
    = prerequisite remediation router

WHICH representation is legal/useful for that target
    = representation policy

HOW the authorized representation is worded/rendered
    = model/renderer
```

## Visual intent

“Use a chart” is too ambiguous as a canonical operation.

A representation should state semantic requirements instead. Example:

```text
decision_tree
+ one root condition
+ two outcome branches
+ explicit boundary state
+ source code hidden initially
+ one micro-probe
```

A renderer may realize that structure differently while preserving the contract.

## Unfamiliar-problem boundary

This design supports structured diagnosis of unfamiliar learner difficulty now.

It does **not** make an LLM-generated concept/prerequisite graph canonical.

Later raw-problem compilation must remain a separate pipeline:

```text
versioned compiler prompt
→ schema output
→ graph validation
→ canonical graph version
```

Only after that graph is accepted may this remediation controller traverse it.

## Persistence and provenance

This delta does not require a new database migration.

Existing source evidence and derived learning-event substrates can persist:

- learner/source turns;
- diagnosis proposal as derived evidence;
- controller DecisionProposal;
- subsequent micro-probe outcome.

Future live promotion should attach the full module-version set including:

```text
diagnosis schema version
diagnosis prompt version
diagnosis model adapter
prerequisite remediation router version
representation policy version
representation version
controller policy version
```

## Failure behavior

Fail closed when:

- diagnosis schema/prompt version is unknown;
- unknown diagnosis fields appear;
- source evidence is absent;
- suspected prerequisite is not in the canonical graph;
- multiple prerequisites are missing and diagnosis is ambiguous;
- assistance ceiling is invalid;
- representation candidate changes the selected task/competency;
- representation semantic fidelity is unvalidated.

Do not fail source-turn durability merely because structured diagnosis fails.

## Sequencing

This work is additive to Issue #63 and does not supersede Issue #66.

Existing sequence remains:

```text
known PIR assurance (PAM A) — complete
→ PAM B local deployment validation
→ PAM C live Study OS GPT dogfood
```

General raw-problem compilation remains later.
