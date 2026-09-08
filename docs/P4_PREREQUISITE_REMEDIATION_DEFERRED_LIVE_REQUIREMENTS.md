# P4 Prerequisite-Sensitive Remediation — Deferred Live-Authority Requirements

Date: 2026-09-08
Status: deferred requirements preserved during PR #74 → PR #75 reconciliation
Parent authority: Issue #63, `docs/P4_PREREQUISITE_REMEDIATION_PDD.md`, `docs/P4_PREREQUISITE_REMEDIATION_SDD.md`, `docs/P4_PREREQUISITE_REMEDIATION_TDD.md`

## Purpose

PR #75 implements the smallest shadow-mode controller and representation-contract delta needed to address the observed mutation-lab routing failure. This document preserves requirements from the earlier planning-only PR #74 that are intentionally **not** claimed complete by the focused shadow implementation.

These requirements matter before prerequisite-sensitive remediation may be promoted to durable live authority.

## 1. Persistent prerequisite detour / return state

The shadow router currently emits a deterministic `DecisionProposal`; it does not establish a new persistent learner-control state machine for prerequisite detours.

Before live authority, the durable control layer must be able to reconstruct a detour conceptually equivalent to:

```yaml
active_parent_node_ref: ...
active_node_ref: ...
blocked_parent_reason: prerequisite_unresolved | prerequisite_access_failure | null
active_prerequisite_ref: ... | null
return_parent_node_ref: ... | null
diagnosis_refs: [...]
authorized_operation_refs: [...]
representation_ref: ...
assistance_ceiling: ...
```

Exact persistence shape is implementation-defined and should reuse existing Study OS evidence/control substrates where semantics fit.

Required invariant:

> A prerequisite detour cannot return to the parent merely because an explanation was displayed or the learner self-reports understanding. Parent re-entry requires the behavioral evidence and policy condition pinned by the active controller version.

## 2. Representation lineage and restoration

The focused representation extension carries structural rendering constraints. Before live authority, representations that claim to simplify or transform an authentic/source representation must also preserve enough lineage to support audit and restoration.

The mature representation contract should be able to pin, where applicable:

```yaml
representation_id: ...
representation_version: ...
family: ...
semantic_roles: {...}
required_relationships: [...]
required_boundary_state: [...]
preserved_semantics: [...]
forbidden_complexity: [...]
source_representation_ref: ...
parent_representation_ref: ...
restorable_mapping: ...
operation_refs: [...]
```

Required invariants:

- semantic simplification may not silently change the target concept;
- required relationships/boundary states remain explicit;
- source/authentic representation remains restorable where the product claims restoration;
- representation version/provenance remains independent of model/provider changes.

## 3. Uncertain prerequisite hypotheses

For known canonical graphs, the router must continue to select only canonical unsatisfied prerequisites.

For future unfamiliar-problem graphs, prerequisite edges may be uncertain. Before such graphs can become learner-facing authority, the system must preserve:

- proposed prerequisite identity;
- confidence or explicit unknown confidence;
- `proposed | supported | contradicted | unresolved` status;
- source evidence/provenance;
- cheap diagnostic probes where policy permits;
- fail-closed parent progression when a required prerequisite remains unresolved.

An LLM-generated prerequisite candidate is never equivalent to prerequisite satisfaction.

## 4. Live persistence/evidence chain

Before promotion beyond shadow/advisory authority, an integration test must prove an evidence chain equivalent to:

```text
observed learner difficulty event
→ derived DiagnosisProposal
→ derived deterministic controller decision
→ learner-facing representation realization
→ observed behavioral prerequisite micro-probe
→ controller-authorized parent re-entry or continued block
```

The test must also prove that no parent `INCORRECT`/canonical attempt is fabricated before a valid parent behavioral probe.

Do not introduce a parallel transcript/evidence store for this feature.

## 5. Regression requirements retained from PR #74

Before live promotion, preserve tests for at least:

1. repeating the same representation when policy requires a representation-family change or smaller step does not satisfy remediation;
2. model/tutor cannot choose an arbitrary child/prerequisite and mark it satisfied;
3. removing a required boundary state or semantic relationship invalidates the representation or leaves it explicitly unresolved;
4. representation lineage/restorability is preserved where required;
5. micro-evidence is required before parent return;
6. unresolved unfamiliar prerequisite hypotheses fail closed where parent progression depends on them.

## 6. Persistent local executor boundary

A later persistent local executor (for example Luna) may implement reviewed mechanical work such as:

- additive controller/state persistence;
- prerequisite detour/return semantics inside the existing P4/PIR boundary;
- semantic representation-contract validation;
- deterministic/property/mutation tests for new authority logic;
- reviewed migration + restart/resume behavior if persistence changes are approved;
- local service/MCP integration and deployment validation;
- exact candidate SHA + sanitized receipts.

The executor may **not**:

- redefine progression or mastery;
- decide prerequisite satisfaction without the accepted evidence policy;
- replace deterministic controller authority with tutor/model judgment;
- hard-code one analogy/story as representation policy;
- weaken regression/mutation oracles or thresholds;
- introduce arbitrary raw-problem compilation into the live learner path;
- make local-only semantic repairs that are absent from reviewed GitHub state.

## 7. Sequencing

The accepted project sequence is now:

```text
PAM A known-PIR assurance — PASSED
PAM B pinned local deployment / restart-resume validation — PASSED
PAM C real Study OS GPT known-PIR dogfood — NEXT / NOT YET CLAIMED
```

The accepted PAM-B receipt is pinned to deployment baseline `151c819e3457ae41fa1810b5060d0101f91bc12a`; PR #75 is not part of that historical receipt.

PR #75 is separate product-controller work and remains shadow/spec verification until explicitly promoted through its own reviewed evidence.

General learner-facing raw-problem compilation remains a later, separately validated gate.
