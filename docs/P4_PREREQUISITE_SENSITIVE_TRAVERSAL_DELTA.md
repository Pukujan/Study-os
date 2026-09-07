# P4 Delta — Prerequisite-Sensitive Traversal and Representation Selection

Date: 2026-09-07
Status: proposed product/system/test delta
Parent authority: Issue #63, `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`, `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`, ADR-0016
Integration context: Issue #66 and the known-problem PIR slice

## Why this delta exists

A real mutation-testing study trajectory failed before the learner submitted a canonical mutation-testing answer. The learner could not parse the code-first representation, repetition of the same parent-node explanation did not resolve the difficulty, and a concrete capacity/scenario representation made the prerequisite semantics substantially more intelligible.

This is classified as a **system/pedagogical routing failure**, not an assessment failure. Canonical mutation-testing attempts remain zero when the learner never reaches the canonical assessment because prerequisite/representation access failed.

The failure does not justify a second teaching architecture. It exercises concepts already owned by Issue #63:

- `missing_prerequisite`;
- `representation_interference`;
- `decomposition_too_coarse`;
- explicit pedagogical operations including `smaller_step`, `change_representation`, and `show_trace`;
- deterministic prerequisite/progression control;
- assistance ceilings;
- representation lineage and restoration;
- explicit module/prompt versions;
- replayable operational evidence.

## Planning-state audit

### Proven

The first known-problem PIR integration has completed PAM Checkpoint A.

Pinned evidence:

- PR #71 merged;
- merge revision: `151c819e3457ae41fa1810b5060d0101f91bc12a`;
- exact tested PR head: `0ccfc9245cc86acdd68587f4bf72158d18ac2070`;
- normal CI passed on that head;
- PIR Mutation Gate passed on that head;
- 1268 total mutants, 1064 killed, 204 audited survivors;
- 0 timeout/other failures;
- 0 unresolved non-equivalent semantic survivors.

Do not reopen this mutation-assurance claim unless new evidence invalidates the pinned result.

### Next local

PAM B remains the immediate execution checkpoint:

> deploy and validate the merged known-problem PIR slice locally, including restart/resume and compatibility, without semantic local-only repairs.

PAM B should use the already-pinned PR #71 merge revision. This delta does **not** require changing that deployment candidate.

### Next live

PAM C remains the first real Study OS GPT dogfood checkpoint for the known canonical PIR integration.

### Product-design follow-up

The mutation-testing failure creates a new product requirement for prerequisite-sensitive traversal and bounded representation adaptation. The requirement should be implemented as an extension of P4 authority after the baseline local deployment is validated, unless PAM B uncovers a blocking defect that must return to GitHub first.

### Later

Arbitrary learner-facing raw-problem -> PIR compilation remains later work. PAM A does not make the generic compiler safe for live use.

The intended future architecture remains:

```text
raw unfamiliar task
→ versioned decomposition/compiler prompt
→ schema-constrained candidate concept/prerequisite graph
→ deterministic validation
→ versioned graph
→ deterministic runtime traversal
→ diagnosis/adaptation
→ bounded representation realization
```

For unfamiliar/no-dataset problems, candidate prerequisite edges may be uncertain. Preserve confidence/unresolved status, allow cheap diagnostic probes, and fail closed for progression claims that require unresolved prerequisites to be satisfied.

The LLM may propose semantic decomposition, prerequisite hypotheses, diagnosis hypotheses, and representation candidates. It may not own progression, mastery, prerequisite satisfaction, assistance escalation, or canonical learner-state mutation.

## PDD delta

### Required learner behavior

When learner evidence indicates that the current parent representation cannot be parsed, the product should support this control sequence:

```text
parent concept
→ learner difficulty evidence
→ diagnosis hypothesis
→ prerequisite resolution/probe
→ deterministic block of parent assessment/progression
→ authorize smaller_step / change_representation / show_trace
→ versioned prerequisite representation
→ micro-evidence
→ return to parent concept
```

The system must not require a bespoke tutor instruction such as “use a theater next time.” The useful property of a successful concrete example must be encoded as representation semantics, not as a hard-coded story.

### Assessment boundary

Difficulty accessing a prerequisite representation is not a failed canonical assessment of the parent concept.

If no canonical parent response was submitted:

- canonical parent attempt count does not increment;
- no `incorrect` parent outcome is fabricated;
- learner-facing difficulty evidence is still durable;
- diagnosis remains a hypothesis;
- remediation evidence is separately attributable.

### Parent progression gate

A parent node is blocked when a required prerequisite is unresolved or evidence supports a prerequisite-access failure under the active controller policy.

A parent node may resume only after the controller receives the required micro-evidence or explicitly resolves the prerequisite according to the pinned policy version.

## SDD delta

### Extend existing semantic objects; do not fork them

The implementation should extend the P4 contracts rather than create PIR-only duplicates of `LearnerControlState`, `DiagnosisHypothesis`, `PedagogicalOperationDefinition`, `RepresentationVersion`, or module provenance.

The current known-problem PIR runtime may remain a narrow executable projection during PAM B. The later implementation should converge PIR traversal with P4 control semantics behind the application boundary.

### Prerequisite detour state

A learner-control state needs enough explicit state to reconstruct a deterministic detour, conceptually:

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

Exact persistence shape is implementation-defined and should reuse existing durable records where semantics fit.

### Diagnosis contract

At minimum support these hypothesis families for this failure class:

- `missing_prerequisite`;
- `representation_interference`;
- `decomposition_too_coarse`;
- `uncertain_mixed`.

A hypothesis should include source evidence, module version, confidence when available, and `proposed | supported | contradicted | unresolved` status.

Diagnosis itself never advances or blocks the course; the deterministic controller applies policy to the hypothesis/evidence set.

### Deterministic prerequisite selection

For a known graph, the controller selects from declared prerequisite nodes/edges and diagnostic probes. An LLM may rank/propose candidates only where policy permits; the accepted prerequisite node/edge is recorded by deterministic validation/selection.

For an unfamiliar candidate graph, unresolved prerequisite hypotheses remain explicit and must not be silently promoted to satisfied edges.

### Representation contract

The current PIR `RepresentationSpec` (`learner_visible_markdown + visible_components`) is sufficient for the proven known-problem slice but is too weak for adaptive representation selection.

The P4 representation contract should evolve toward semantic intent such as:

```yaml
representation_id: ...
representation_version: ...
family: decision_tree | state_flow | sequence_trace | comparison_view | table | source_code | concrete_scenario
semantic_roles:
  - role: capacity
  - role: occupied
  - role: candidate_change
required_relationships:
  - occupied <= capacity
required_boundary_state:
  - full_capacity_state
preserved_semantics:
  - the decision changes when the boundary condition is reached
forbidden_complexity:
  - implementation syntax
  - unrelated variables
code_visibility: hidden
source_representation_ref: ...
parent_representation_ref: ...
restorable_mapping: ...
operation_refs:
  - change_representation@...
  - smaller_step@...
```

The concrete scenario family may be realized as theater tickets, seats, containers, queue capacity, or another semantically equivalent surface. The contract preserves the roles/relationships/boundary condition that made the concrete example useful; it does not hard-code a single story.

### Representation realization authority

The controller authorizes operation family, assistance ceiling, target prerequisite, and required representation constraints. A representation module/model realizes a candidate under that envelope. Candidate output is validated against required/forbidden semantics where feasible before learner exposure.

### Versioning

Independently pin, where relevant:

- course/decomposition graph version;
- decomposer prompt/template version;
- decomposer schema version;
- controller/progression policy version;
- diagnosis module version;
- pedagogical operation registry version;
- representation policy version;
- representation rendering prompt/template version;
- assessment version;
- learner-state derivation version;
- model/provider adapter version.

No hidden prompt drift is allowed to change historical meaning.

## TDD / verification delta

### REG-PED-001 — prerequisite-access failure must not become parent failure

Given a parent mutation-testing probe and learner-facing evidence equivalent to:

> I don't know how the code works.

where no canonical mutation-testing answer has been submitted, require:

1. difficulty evidence is durably recorded;
2. a diagnosis hypothesis is proposed/recorded;
3. parent assessment/progression is blocked;
4. parent canonical attempts remain unchanged;
5. the controller resolves or probes a prerequisite;
6. only allowed `smaller_step`, `change_representation`, `show_trace`, or stricter-policy operations are authorized;
7. the representation satisfies the pinned semantic representation contract;
8. micro-evidence is collected on the prerequisite;
9. return to the parent requires the pinned return condition;
10. no parent `incorrect` outcome exists solely because the prerequisite representation was not parsable.

### REG-PED-002 — repeating the same representation is insufficient remediation

Mutation: replace the authorized representation change with a repetition of the same code-first representation.

Expected: regression fails when the diagnosis/policy requires a representation-family change or smaller-step detour.

### REG-PED-003 — tutor cannot choose an arbitrary child and advance

Mutation: allow the LLM to select any prerequisite/child and mark it satisfied.

Expected: fail. Candidate prerequisite selection must be validated against the pinned graph/policy, and satisfaction requires evidence/policy.

### REG-PED-004 — representation semantic contract

Mutations that must fail validation or become explicitly unresolved include:

- required boundary state removed;
- semantic role mapping changed;
- preserved relationship changed;
- forbidden source-code complexity reintroduced;
- parent/source lineage removed when restoration is required;
- representation claims a different target concept.

### REG-PED-005 — micro-evidence and return

The detour may not return to the parent solely because an explanation was displayed or the learner self-reports understanding. The pinned policy must specify acceptable micro-evidence.

### REG-PED-006 — uncertain unfamiliar prerequisite

For an unfamiliar problem graph with an unresolved prerequisite hypothesis:

- record the hypothesis and confidence/unresolved state;
- permit a cheap diagnostic probe when policy allows;
- do not assert prerequisite satisfaction without accepted evidence;
- fail closed for parent progression when the prerequisite is required and remains unresolved.

## Public-safe regression fixture

The companion fixture is:

`tests/fixtures/pir/mutation_testing_prerequisite_routing.v1.json`

It contains only synthetic/public-safe semantics and no private learner transcript.

## Sequencing recommendation

1. Keep PR #71 / PAM A closed and accepted.
2. Execute PAM B on exact merge revision `151c819e3457ae41fa1810b5060d0101f91bc12a`.
3. If PAM B passes, preserve that receipt as the baseline deployment attestation.
4. Implement the prerequisite-sensitive P4 delta in a new reviewed revision; do not patch the local runtime semantically.
5. Run normal CI/contract/regression testing for that revision.
6. Deploy the reviewed delta through the same local change-control discipline.
7. Use PAM C / real GPT dogfood to exercise both the original known PIR path and the new prerequisite-sensitive behavior as applicable.
8. Keep generic unfamiliar-problem compilation behind its separate design/validation gate.

PAM C should not be redefined so that the new feature becomes a hidden prerequisite for validating the already-proven first known-PIR integration. If the live dogfood naturally exposes the prerequisite failure, record it as product evidence and test the reviewed follow-up version separately.

## Work appropriate for persistent local Luna later

After design/checkpoint authority approves the implementation delta, delegate mechanical persistent execution such as:

- implement additive controller/state persistence required by the reviewed design;
- extend the existing PIR/P4 controller rather than create a parallel controller;
- implement semantic representation-contract validation;
- add/extend deterministic prerequisite graph fixtures;
- implement the public regression tests from this document;
- run focused pytest/property loops;
- run mutation testing over newly introduced authority logic;
- perform local DB migration rehearsal if a migration is approved;
- restart/resume and idempotency loops;
- local MCP deployment and service/log inspection;
- return an exact candidate SHA and sanitized test receipts.

Luna must not redefine progression, mastery, prerequisite satisfaction, representation invariants, regression oracles, or gate thresholds to obtain green results.

## Explicit non-goals

This delta does not:

- reopen PR #71 mutation assurance;
- mark PAM B or PAM C complete;
- make the generic raw-problem compiler production-ready;
- create a new learner profile architecture;
- hard-code theater/ticket semantics;
- allow GPT/model output to mutate canonical learner state directly;
- require broad local deployment from this planning lane.
