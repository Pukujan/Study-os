# P4 Planning Reconciliation — Prerequisite-Sensitive Traversal and Representation Selection

Date: 2026-09-07
Status: proposed focused delta; subordinate to Issue #63 and ADR-0016
Related: #63, #65, #66, PR #71

## Purpose

Reconcile the canonical P4 deterministic-learning-controller architecture with two newer facts:

1. the known-problem PIR integration has completed repo-side PAM Checkpoint A assurance; and
2. a separate mutation-testing learning trajectory produced useful product evidence of a pedagogical routing failure before any canonical learner answer was submitted.

This document does **not** create a parallel teaching architecture. It sharpens the already-defined Issue #63 contracts for prerequisites, diagnosis hypotheses, bounded pedagogical operations, representation lineage, deterministic progression, and replayable evidence.

It also does **not** authorize arbitrary learner-facing raw-problem compilation. That remains a later capability after the known-PIR local/live integration sequence is validated.

## Verified planning state

### Proven

- PR #71 is merged.
- Evidence-bearing PR head: `0ccfc9245cc86acdd68587f4bf72158d18ac2070`.
- Merge revision: `151c819e3457ae41fa1810b5060d0101f91bc12a`.
- Normal CI passed on the evidence-bearing head.
- PIR mutation assurance passed on the evidence-bearing head.
- Final mutation population: 1268 total, 1064 killed, 204 survived, zero timeout/other failures, zero unresolved non-equivalent semantic survivors.
- PAM Checkpoint A is passed for the known September-4 sliding-window PIR integration slice.

Do not reopen this mutation-assurance claim unless new evidence invalidates the pinned facts or production-source drift invalidates the survivor audit.

### Next local

PAM Checkpoint B remains the next deployment checkpoint. The local operator should validate the exact PR #71 merge revision `151c819e3457ae41fa1810b5060d0101f91bc12a` using the already-recorded backup, install, test, MCP inventory, health, restart/resume, smoke, and idempotency procedure.

### Next live

After PAM B passes, PAM Checkpoint C should validate the same known-PIR slice through the real Study OS GPT. This preserves the evidentiary chain from repo assurance → exact local deployment → real GPT behavior before the product semantics are changed again.

### Product-design follow-up

The next P4 product delta should add prerequisite-sensitive traversal and representation selection driven by structured learner-difficulty evidence.

### Later

General unfamiliar raw-problem → candidate PIR/decomposition compilation remains later. The current failure is not sufficient evidence to promote a generic live compiler.

## Planning-state audit

### Issue #63 — architecture remains authoritative; execution status is stale

Issue #63 already owns the relevant semantics:

- versioned course/prerequisite control;
- learner-control state;
- `missing_prerequisite`, `representation_interference`, and `decomposition_too_coarse` diagnosis families;
- explicit `change_representation`, `smaller_step`, and `show_trace` operations;
- assistance ceilings;
- representation lineage and restoration;
- module/prompt versioning;
- outcome records and replay;
- later deterministic/cheap/specialized component routing.

No new parallel controller, diagnosis system, or representation framework is required.

The issue checklist is stale as an execution ledger because a reviewed known-PIR deterministic traversal slice now exists and PAM A is passed, while the general P4 contracts remain broader than that implementation. Do not mark all P4.0/P4.1 items complete merely because the known-PIR slice is proven.

### Issue #66 — body checklist is stale; comments contain the current checkpoint truth

The issue body still presents G0-G9 as unchecked. The accepted comments correctly record:

- PAM A: passed;
- PAM B: not started;
- PAM C: not started;
- exact merge/head/CI/mutation evidence;
- the exact local handoff.

Issue #66 also correctly keeps arbitrary raw-problem compilation out of the first live integration slice. Preserve that boundary.

### P4 PDD / SDD / ADR-0016 — architecture is sound; representation/prerequisite detail is incomplete

The existing P4 PDD/SDD already define the right authority boundary and semantic objects. Their main missing detail exposed by the new trajectory is not architectural ownership but the concrete contract for:

- distinguishing a difficulty signal from a canonical assessment attempt;
- blocking a parent node while resolving a prerequisite;
- representing a prerequisite detour and deterministic return edge;
- recording micro-evidence inside that detour;
- selecting a representation by semantic intent rather than unconstrained tutor wording;
- representing uncertainty when the prerequisite diagnosis is not yet established.

ADR-0016 does not need supersession. This delta is an application of the accepted decision.

### `docs/ROADMAP.md` — stale execution order

The current execution order still says to freeze P4 design, audit runtime/schema, and implement the first real deterministic course-node loop. Those were overtaken by the known-PIR integration work. The roadmap should distinguish:

1. known PIR integration + PAM A — proven;
2. PAM B exact local deployment — next;
3. PAM C real GPT validation — next live;
4. prerequisite-sensitive traversal/representation adaptation — next product slice;
5. unfamiliar raw-problem compilation — later.

### `docs/CURRENT_STATE.md` — stale immediate priority

It still describes the primary task as defining/implementing the smallest deterministic learning-control loop and does not record the merged known-PIR slice or PAM A status. It should be updated after checkpoint sequencing is reconciled.

### `docs/HANDOFF.md` — stale implementation handoff

It still says the runtime/schema audit is complete and the “Phase 2 smallest vertical slice” is next. That is no longer current. The immediate operational handoff is PAM B on the pinned PR #71 merge, followed by PAM C.

### `PROJECT_MANIFEST.yaml` — sequencing is substantially correct

The manifest already says the next milestone is known sliding-window PIR validation through MCP/schema/restart/live deployment before arbitrary raw-problem compilation. Preserve this. A later planning-state edit may make the PAM A/B/C statuses explicit, but the current milestone must not be rewritten to imply general compilation is ready.

## New operational evidence classification

The mutation-testing study trajectory should be treated as a **system/pedagogical routing failure**, not a learner assessment failure.

Observed behavior:

- a code-first representation was not understood;
- repeating the same conceptual node did not resolve the confusion;
- the learner requested a visual/structured representation;
- a concrete capacity/boundary scenario was substantially more intuitive;
- no canonical mutation-testing response was submitted;
- therefore no canonical mutation-testing attempt/failure should be inferred from the difficulty signal.

Plausible diagnosis hypotheses include:

- `missing_prerequisite`;
- `representation_interference`;
- `decomposition_too_coarse`;
- inappropriate entry representation.

These remain hypotheses until supported by diagnostic micro-evidence.

## PDD delta

### Product behavior

When learner evidence indicates inability to parse the current representation before a canonical answer is attempted, Study OS should support this control path:

```text
parent concept
→ difficulty evidence
→ diagnosis hypothesis set
→ prerequisite resolution/probe
→ deterministic parent-progression block
→ authorized smaller_step / change_representation / show_trace
→ versioned prerequisite representation
→ micro-evidence
→ prerequisite resolved or remains unresolved
→ deterministic return to parent when allowed
→ restore/bridge toward parent/source representation
```

The tutor/model should not require a bespoke prompt such as “use a theater example next time.” The semantic adaptation must arise from versioned policy, representation contracts, and structured controller state.

### Difficulty signal is not an assessment attempt

A learner utterance equivalent to “I do not know how the code works” is learner-facing difficulty evidence. Unless the current assessment contract explicitly defines that utterance as a valid canonical response, it must not create a canonical incorrect attempt merely because it was emitted while an assessment turn was visible.

The ingestion path must distinguish at least:

```text
canonical_response_candidate
learner_difficulty_signal
clarification_or_meta_request
```

Free-language intent classification may be model-assisted, but canonical attempt creation and grading remain deterministic and contract-bound.

### Parent blocking and prerequisite detour

Once the controller determines that prerequisite resolution is required:

- the parent node remains the canonical return target;
- parent progression/assessment is blocked;
- the detour is explicit and durable;
- only authorized prerequisite operations are available;
- micro-evidence belongs to the prerequisite detour, not to the parent assessment;
- return to the parent occurs only through a deterministic return condition.

### Representation selection

“Chart” or “visual” must not be an unconstrained tutor interpretation. Representation selection should operate on a semantic intent contract.

Candidate representation families include:

```text
decision_tree
state_flow
sequence_trace
comparison_view
table
source_code
pseudocode
concrete_scenario
prose
```

A renderer may choose a concrete realization only after the controller/representation policy has fixed the required semantic intent.

### Uncertainty

For unfamiliar or weakly modeled material, diagnosis/prerequisite state must support:

- candidate prerequisite hypotheses;
- confidence where meaningful;
- `proposed | supported | contradicted | unresolved` status;
- cheap diagnostic probes;
- fail-closed parent progression when required evidence is absent.

A model may propose the hypothesis. It may not mark the prerequisite satisfied.

## SDD delta

The following are extensions to the existing Issue #63/P4 semantic objects, not a second architecture.

### 1. DifficultyEvidence

Conceptual contract:

```yaml
difficulty_evidence_id: string
subject_id: string
parent_course_node_ref: string
parent_step_ref: string | null
source_turn_ref: string
evidence_kind: learner_difficulty_signal | clarification_or_meta_request
claimed_barrier: string | null
canonical_attempt_created: false
created_at: timestamp
```

Raw learner text remains source evidence. `claimed_barrier` is derived and must reference the source turn.

### 2. DiagnosisHypothesis — preserve existing type

Reuse the existing P4 `DiagnosisHypothesis`. For this failure class, likely families are `missing_prerequisite`, `representation_interference`, and `decomposition_too_coarse`.

A hypothesis may propose a prerequisite target, but it cannot satisfy it:

```yaml
candidate_prerequisite_node_ref: string | null
confidence: number | null
status: proposed | supported | contradicted | unresolved
probe_policy_ref: string | null
```

### 3. PrerequisiteTraversalFrame

Add an explicit deterministic traversal frame rather than mutating the parent node implicitly:

```yaml
frame_id: string
parent_node_ref: string
parent_step_ref: string | null
prerequisite_node_ref: string
entry_diagnosis_refs: [string]
parent_progression_blocked: true
status: probing | active | resolved | unresolved
return_policy_ref: string
entry_representation_ref: string | null
current_representation_ref: string | null
micro_evidence_refs: [string]
created_at: timestamp
resolved_at: timestamp | null
```

The controller owns push/advance/resolve/pop semantics for this frame.

### 4. RepresentationIntentSpec

Extend the existing representation concept so `learner_visible_markdown + visible_components` is a renderer output, not the whole semantic contract.

Conceptual shape:

```yaml
representation_intent_id: string
representation_policy_version: string
family: decision_tree | state_flow | sequence_trace | comparison_view | table |
        source_code | pseudocode | concrete_scenario | prose
semantic_roles:
  - role_id: bounded_resource
  - role_id: current_usage
  - role_id: boundary_predicate
required_relationships:
  - current_usage is compared against bounded_resource
  - boundary_predicate changes behavior at the boundary
required_boundary_states:
  - below_boundary
  - at_boundary
  - above_boundary
preserved_semantics:
  - target mutation/operator effect
forbidden_complexity:
  - unrelated implementation details
  - additional unintroduced variables
code_visibility: hidden | optional | secondary | primary | required
source_representation_ref: string | null
parent_representation_ref: string | null
restorable_mapping: object | null
rendering_prompt_version: string | null
```

The example semantic roles above are illustrative. The contract must not encode one hard-coded theater/ticket story.

### 5. Operation authorization

Reuse the existing operation registry. A prerequisite frame can authorize a bounded subset such as:

```text
smaller_step
change_representation
show_trace
explain
restore_original
```

Operation selection remains deterministic for the same canonical state/policy inputs. The model only realizes an authorized operation.

### 6. Micro-evidence and return

Prerequisite probes produce evidence against the prerequisite node/frame. They do not update the parent assessment outcome.

A deterministic return policy may require, for example:

```text
prerequisite probe accepted
AND representation mapping remains restorable
→ resolve frame
→ return to parent bridge/retry state
```

If the prerequisite remains unresolved, the parent remains blocked.

### 7. Persistence/restart

Any active prerequisite traversal frame must survive restart/resume. If the existing `problem_runs` state cannot represent the detour without ambiguity, use an additive durable record or explicitly versioned run-state extension after the schema change is reviewed.

Do not overload an opaque GPT conversation message as the authoritative detour state.

### 8. Current PIR expansion boundary

The current v0.4 known-PIR `request_problem_expansion` contract is non-advancing presentation expansion. It should not be silently reinterpreted as prerequisite satisfaction or parent-state mutation.

A future implementation may reuse the same learner-facing ingress if the contract is explicitly versioned and the backend records diagnosis/traversal state, or it may add a dedicated semantic operation. Either way, changing this behavior requires a reviewed contract/version change; it must not be hidden prompt behavior.

### 9. Module versions

Preserve independent versions, where applicable, for:

- course/decomposition graph;
- decomposer prompt/template;
- decomposer schema;
- controller/progression policy;
- diagnosis module;
- pedagogical operation registry;
- representation policy;
- representation rendering prompt;
- assessment;
- learner-state derivation;
- model/provider adapter.

A learner-facing decision should pin the relevant immutable version set.

## Unfamiliar-problem architecture — later, not enabled by this delta

The eventual path should be:

```text
raw unfamiliar task
→ versioned decomposition/compiler prompt
→ schema-constrained candidate concept/prerequisite graph
→ deterministic graph validation
→ versioned accepted graph
→ deterministic runtime traversal
→ diagnosis/adaptation
→ bounded representation realization
```

The LLM may propose:

- semantic decomposition;
- prerequisite graph edges;
- diagnosis hypotheses;
- representation candidates.

The LLM must not directly own:

- progression;
- mastery;
- prerequisite satisfaction;
- assistance escalation;
- canonical learner-state mutation.

Unknown/low-confidence prerequisite structure remains explicitly unresolved and can trigger cheap probes or fail-closed progression. A candidate graph is not canonical until deterministic validation and the applicable review/promotion policy accept a versioned artifact.

## TDD / regression delta

### New invariants

#### INV-PREQ-001 — difficulty evidence is not a canonical failure

Given a current parent probe and learner evidence semantically equivalent to “I do not know how the code works”:

- record the source learner turn;
- record normalized difficulty evidence;
- canonical parent attempt count remains unchanged;
- no `incorrect` parent outcome is created merely from the difficulty signal.

#### INV-PREQ-002 — parent progression blocks during prerequisite resolution

When a supported controller decision enters a prerequisite frame:

- the parent cannot advance;
- a direct parent success/skip transition is rejected;
- restart/resume restores the same parent block and active prerequisite frame.

#### INV-PREQ-003 — diagnosis is hypothesis data

Model-proposed `missing_prerequisite` / `representation_interference` / `decomposition_too_coarse` diagnoses remain `proposed` or `unresolved` until the configured evidence policy changes status.

Mutating model output from `proposed` directly to prerequisite-satisfied must fail.

#### INV-PREQ-004 — adaptation requires authorization

A representation may change only through authorized operation(s) and a valid representation intent. Unauthorized modality/complexity changes fail closed or remain unresolved.

#### INV-PREQ-005 — representation semantics survive family change

Changing from source code to a simpler family must preserve declared semantic roles, relationships, boundary states, and target concept while respecting forbidden complexity and code-visibility constraints.

Mutations that drop a required relationship, hide a required boundary state, or introduce unapproved implementation complexity must be rejected.

#### INV-PREQ-006 — micro-evidence is scoped to the prerequisite

A successful prerequisite micro-probe may resolve the prerequisite frame but does not itself mark the parent concept correct/mastered.

#### INV-PREQ-007 — deterministic return

For the same parent state, prerequisite frame, evidence, and policy versions, the return decision is identical. Return restores the authorized parent bridge/source mapping; it does not jump to a future parent node.

### Public-safe regression fixture specification

Fixture identity proposal:

```text
p4.prerequisite-routing.code-confusion.v1
```

Synthetic setup:

```yaml
parent_node:
  id: mutation_testing.operator_effect
  source_representation_family: source_code
  target_semantics:
    - explain the behavioral effect of a boundary-operator mutation

prerequisite_node:
  id: boolean_boundary_semantics
  target_semantics:
    - distinguish below, at, and above a threshold

learner_event:
  kind: learner_difficulty_signal
  text: "I don't know how the code works"

expected_controller_behavior:
  canonical_parent_attempt_delta: 0
  parent_progression_blocked: true
  diagnosis_hypotheses_allowed:
    - missing_prerequisite
    - representation_interference
    - decomposition_too_coarse
  authorized_operations:
    - smaller_step
    - change_representation
    - show_trace
  prerequisite_resolution_required: true
```

Required representation intent for the prerequisite:

```yaml
family: concrete_scenario | state_flow | table | sequence_trace
required_relationships:
  - current quantity is compared with a threshold/capacity
  - the boundary operator changes the at-boundary behavior
required_boundary_states:
  - below_boundary
  - at_boundary
  - above_boundary
preserved_semantics:
  - behavioral effect of the operator mutation
forbidden_complexity:
  - unrelated source-code details
code_visibility: hidden | secondary
restorable_mapping_required: true
```

Acceptance sequence:

```text
difficulty evidence recorded
→ diagnosis hypothesis recorded
→ parent blocked
→ prerequisite frame entered/probed
→ bounded simpler representation rendered
→ prerequisite micro-evidence collected
→ frame resolved only if policy accepts evidence
→ return to parent bridge/retry
→ parent assessment becomes eligible again
```

Forbidden outcomes:

- canonical parent `incorrect` solely from the difficulty utterance;
- repeating the same parent code probe without an authorized diagnostic/representation decision;
- model-selected progression without controller authorization;
- hard-coded dependence on one concrete story such as theater tickets;
- micro-probe success being promoted directly to parent mastery.

### Mutation/adversarial cases

Add tests that fail when a mutant:

- creates a parent incorrect attempt from a difficulty signal;
- removes the parent block;
- lets an expansion/prerequisite detour advance the parent;
- marks a proposed diagnosis as satisfied;
- drops one required boundary state;
- changes the target semantics during representation change;
- makes source code mandatory despite a policy-authorized lower-complexity representation;
- loses the active prerequisite frame across restart;
- returns to a future parent node instead of the blocked parent;
- records prerequisite micro-evidence as parent mastery evidence.

## Sequencing recommendation

1. **Do not alter the PR #71 deployed semantic baseline before PAM B.** Run PAM B on exact merge `151c819e3457ae41fa1810b5060d0101f91bc12a`.
2. **Run PAM C on the same known-PIR integration line after PAM B.** This validates the originally assured slice end-to-end and prevents the new product delta from obscuring whether the baseline deployment itself works.
3. **Review this prerequisite/representation delta in parallel as design work, but keep runtime changes out of the PAM B/C baseline.**
4. After baseline PAM C, implement the smallest prerequisite-sensitive vertical extension against a versioned known/synthetic graph. Give that change its own repo-side verification, local restart/resume validation, and live dogfood receipt.
5. Only after the deterministic prerequisite/adaptation loop is stable should unfamiliar raw-problem compilation move toward learner-facing product use. Compilation itself needs its own schema-constrained candidate graph, deterministic validation, versioning, and uncertainty gates.

If PAM B or C discovers a reusable baseline defect, fix that defect through a reviewed GitHub change before proceeding; do not patch semantics locally.

## Work suitable for persistent local Luna later

After strong-model review freezes the delta and after PAM B/C sequencing permits implementation, persistent local Luna is well suited to:

- run the exact PAM B deployment/restart/resume procedure and return the sanitized receipt;
- implement mechanical schema/model changes from an approved SDD/TDD;
- add deterministic fixture loaders/validators;
- implement traversal-frame persistence and restart/resume wiring to the approved contract;
- implement representation-intent validation and renderer plumbing without changing semantics;
- add/extend spec-conforming tests for the frozen invariants;
- run targeted pytest/property/state-machine loops;
- run mutation testing on the new prerequisite/representation trust kernel;
- exercise local SQLite migration/rollback and idempotency paths;
- inspect logs and fix environment/integration defects that do not change the approved pedagogy.

Luna should not:

- redefine diagnosis semantics;
- decide which prerequisite counts as satisfied;
- weaken the parent-block invariant;
- change the representation contract to make a fixture pass;
- lower mutation/test gates;
- authorize unfamiliar live compilation;
- self-approve the new checkpoint.

## Repository-change recommendation

Keep this planning delta on a review branch/draft PR until the exact PAM B baseline is executed, so `main` does not create ambiguity about which revision the local operator must install. After PAM B (and preferably baseline PAM C), reconcile the canonical planning files in a focused merge:

- `docs/ROADMAP.md` — replace stale first-vertical-slice execution order with PAM A/B/C + product follow-up sequencing;
- `docs/CURRENT_STATE.md` — record known-PIR implementation and PAM A as proven, B/C outstanding, and the new routing failure as product evidence;
- `docs/HANDOFF.md` — replace the obsolete “Phase 2 smallest vertical slice next” handoff with exact B/C and later prerequisite-adaptation work;
- `PROJECT_MANIFEST.yaml` — preserve the existing compiler deferral and optionally make PAM checkpoint state explicit;
- Issue #63 — add a reconciliation comment; do not create a parallel architecture tracker;
- Issue #66 — preserve the exact PAM A/B/C evidence and compiler non-goal; update status accounting without claiming B/C complete.
