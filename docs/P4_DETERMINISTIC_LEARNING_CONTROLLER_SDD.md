# P4 System Design — Deterministic Learning Controller + Versioned Representation Pipeline

Date: 2026-09-03
Status: proposed canonical P4 system design
Parent tracker: #63
Companion: `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`

## Design objective

Make every learner-facing teaching action auditable as a deterministic state/policy decision followed by a bounded representation realization.

The runtime must be able to answer:

```text
What course node was active?
What learner-control state was active?
What evidence was available?
Which operation was authorized?
Which module versions made the decision?
What representation was shown?
What did the learner do next?
What state transition followed?
```

## Architectural modules

```text
CourseEngine
LearningController
DiagnosisModule
OperationRegistry
RepresentationEngine
RetrievalModule
AssessmentModule
LearnerStateDeriver
EvidenceStore
ModelAdapter
```

The interfaces matter more than current implementation language. Individual modules are replaceable if contracts and provenance remain stable.

## Runtime flow

```text
1. receive learner/source event
2. durably record source evidence
3. load pinned course node + learner-control state
4. normalize relevant operational evidence
5. produce diagnosis hypotheses
6. deterministic controller selects/permits next operation
7. representation engine builds versioned transformation plan
8. model/deterministic renderer realizes learner-facing output
9. validate output against operation contract where feasible
10. durably record exact learner-facing turn + decision provenance
11. receive learner response
12. assess/normalize observable outcome
13. deterministic controller transitions state
14. persist derived state with source references
```

Source-turn durability remains below this layer and must not depend on successful semantic processing.

## Core persistent records

The exact schema may reuse/extend existing tables rather than requiring these names verbatim. These are semantic contracts.

### 1. CourseNodeVersion

```yaml
course_node_id: string
course_node_version: string
track_id: string
concept_ids: [string]
prerequisite_node_ids: [string]
source_task_refs: [string]
progression_policy_ref: string
default_assistance_ceiling: A0-A6
restoration_required: boolean
transfer_required: boolean
retention_policy_ref: string | null
status: active | retired
```

A course node is versioned. Editing progression requirements creates a new version rather than silently altering the meaning of historical outcomes.

### 2. LearnerControlState

```yaml
subject_id: string
course_node_id: string
course_node_version: string
state:
  INTRODUCE |
  AWAIT_UNAIDED_ATTEMPT |
  DIAGNOSE |
  AUTHORIZE_OPERATION |
  AWAIT_REATTEMPT |
  FADE_ASSISTANCE |
  RESTORE_SOURCE_REPRESENTATION |
  TRANSFER |
  RETENTION |
  ADVANCE_OR_BLOCK
assistance_ceiling: A0-A6
current_representation_ref: string | null
source_representation_ref: string | null
state_version: string
updated_from_evidence_refs: [string]
```

This state is derived/operational state, not raw evidence.

### 3. DiagnosisHypothesis

```yaml
diagnosis_id: string
subject_id: string
course_node_id: string
family: missing_prerequisite | concept_failure | representation_interference |
        identifier_interference | information_overload | information_underload |
        decomposition_too_coarse | over_decomposition | over_help | uncertain_mixed
confidence: number | null
source_evidence_refs: [string]
diagnosis_module_version: string
status: proposed | supported | contradicted | unresolved
```

The LLM may generate this record, but it remains derived/hypothesis data.

### 4. PedagogicalOperationDefinition

```yaml
operation_name: rename_terms
operation_version: string
allowed_states: [AUTHORIZE_OPERATION]
max_assistance_level: A2
required_inputs: [source_representation, target_concept]
required_outputs: [representation_mapping]
forbidden_effects:
  - change_target_concept
  - advance_course
```

The operation registry is deterministic authority over what an AI generation is allowed to do.

### 5. OperationInvocation / DecisionRecord

```yaml
decision_id: string
subject_id: string
course_node_id: string
course_node_version: string
learner_state_before_ref: string
input_evidence_refs: [string]
diagnosis_refs: [string]
authorized_operations:
  - name: rename_terms
    version: ...
  - name: smaller_step
    version: ...
assistance_level: A2
controller_version: string
module_version_set_ref: string
decision_reason_code: string
created_at: timestamp
```

The controller decision must exist separately from the generated tutor text.

### 6. RepresentationVersion

```yaml
representation_id: string
representation_version: string
concept_id: string
source_representation_ref: string | null
parent_representation_ref: string | null
operation_invocation_ref: string
mapping: object
preserved_semantics: [string]
target_difficulty_preserved: [string]
extraneous_difficulty_targeted: [string]
rendering_ref: string | null
restorable: boolean
created_from_evidence_refs: [string]
```

Representation lineage should form a reversible graph where supported:

```text
source R0
  ↓ rename_terms
R1
  ↓ smaller_step
R2
  ↓ restore_original
R3 ≈ R0 source semantics
```

### 7. ModuleVersionSet

```yaml
module_version_set_id: string
course_graph_version: string
controller_version: string
operation_registry_version: string
diagnosis_version: string
representation_engine_version: string
prompt_template_version: string | null
retrieval_version: string | null
assessment_version: string
learner_state_deriver_version: string
model_adapter: string
model_identifier: string | null
```

Each decision references one immutable version set.

### 8. OutcomeRecord

```yaml
outcome_id: string
decision_id: string
learner_response_evidence_refs: [string]
assessment_result_refs: [string]
observed_effect:
  correctness: ...
  independence: ...
  assistance_used: ...
  representation_restored: ...
  transfer: ...
  retention: ...
self_report_refs: [string]
next_state_ref: string
created_at: timestamp
```

Immediate success, restoration, transfer, and retention must remain separable.

### 9. ReplayEvaluation

```yaml
replay_id: string
historical_decision_id: string
candidate_module_version_set_ref: string
candidate_output_ref: string
comparison_metrics: object
created_at: timestamp
kind: offline_counterfactual
```

A replay is **not learner evidence**. It cannot be used as if the learner experienced the candidate output.

## Deterministic controller contract

The controller consumes:

```text
course node/version
learner-control state
prerequisite state
assistance history
recent evidence/outcomes
diagnosis hypotheses
policy version
```

and returns:

```text
next authorized operation set
assistance ceiling
required representation constraints
whether progression is blocked/allowed
whether fade/restoration/transfer/retention is required
reason code
```

The controller should be deterministic for the same canonical inputs and policy version.

If stochastic ranking is later introduced, the random seed/model version/input set must be captured so decisions remain replayable.

## AI generation contract

The model adapter receives a bounded envelope, conceptually:

```yaml
course_node: ...
target_concepts: [...]
learner_state: ...
authorized_operations: [...]
assistance_ceiling: A2
source_representation: ...
representation_constraints: ...
forbidden_actions:
  - advance_course
  - claim_mastery
  - change_target_concept
  - exceed_assistance_ceiling
```

The generated learner-facing response is persisted exactly as source evidence.

Where possible, structured generation should return both:

```text
learner-facing content
+ machine-readable representation/operation metadata
```

but persistence of the exact learner-facing content must not depend on successful structured parsing.

## Assistance semantics

Preserve the existing conceptual scale:

```text
A0 independent
A1 motivational/clarifying
A2 representation change without strategy reveal
A3 conceptual hint
A4 strategy reveal
A5 partial solution
A6 full solution
```

An operation definition declares its maximum typical assistance. The controller may set a stricter ceiling.

The AI cannot self-escalate beyond the current ceiling.

## Progression semantics

A progression policy is code/data, not prompt prose.

Conceptual example:

```yaml
policy_id: dictionary_lookup-v1
advance_if:
  all:
    - metric: unaided_same_surface
      op: eq
      value: pass
    - metric: source_representation_restore
      op: eq
      value: pass
block_if:
  any:
    - metric: prerequisite_gap
      op: eq
      value: true
```

The system should support node-specific policies so trivial concepts do not inherit unnecessarily expensive gates from complex concepts.

## Representation fidelity

The representation engine must distinguish between:

1. semantic transformation;
2. difficulty transformation;
3. pedagogical assistance.

A transformation record should state what semantics must remain invariant.

For code, later deterministic/AST-aware transformations may validate stronger equivalence than an LLM alone. For prose/system design, fidelity may require rubric/constraint checks rather than executable equivalence.

## Operational improvement loop

### Online loop

```text
real interaction
→ immutable source evidence
→ normalized decision/outcome
→ versioned module provenance
→ later analysis
```

### Offline development loop

```text
historical trajectories
→ identify controller/representation failures
→ propose module version N+1
→ replay against historical inputs
→ compare structural/quality metrics
→ prospective dogfood with N+1
→ observe real learner outcome
→ retain/promote/revert module version
```

Replay can filter bad candidates cheaply, but only prospective learner behavior can provide new outcome evidence.

## Version promotion rule

A module version should not replace a previous version merely because its prompt/output looks better.

Promotion evidence may include:

- fixes a known invariant violation;
- passes deterministic contract tests;
- improves replay metrics without new violations;
- improves or preserves prospective learner outcomes on real use;
- does not increase answer leakage/over-help materially;
- preserves source restoration and provenance.

The exact promotion thresholds can evolve later. The immutable principle is that version changes are explicit and attributable.

## Long-horizon cheaper routing

Design now for substitution, implement later.

The `RepresentationEngine` interface should allow implementations such as:

```text
LLMRepresentationEngine
ASTRepresentationEngine
TemplateRepresentationEngine
RetrievalRepresentationEngine
HybridRepresentationEngine
```

Likewise diagnosis may later route through:

```text
rules
small classifier
embedding similarity
LLM fallback
```

The controller remains the authority regardless of which implementation fulfills an operation.

## Health model extension

Runtime health should distinguish at least:

```text
storage_integrity
live_capture_status
continuity_status
historical_reconciliation_status
controller_contract_status
module_version_resolvability
```

A valid database with missing learner turns is not end-to-end healthy.

## Failure behavior

Fail closed when:

- required course node/version cannot be resolved;
- controller version is unknown;
- representation source lineage is required but missing;
- operation is not legal in current state;
- requested assistance exceeds ceiling;
- progression evidence is ambiguous;
- replay output is at risk of being mistaken for real learner evidence.

Do not fail closed merely because a nonessential derived diagnosis cannot be generated; the raw interaction should remain durable and recoverable.

## Migration strategy

P4 implementation should first inspect the current runtime schema and reuse existing durable substrates where semantics align.

Prefer additive changes:

1. reuse existing sessions/messages/raw artifacts/events where possible;
2. add stable semantic records only where current schema cannot represent P4 invariants;
3. do not rewrite old evidence to fit new controller semantics;
4. backfill historical records only as explicitly derived/reconciled records with provenance;
5. keep schema migrations minimal and reversible/backup-protected.

## Initial implementation slice

P4.0 should implement the smallest complete vertical slice for one real current course node:

```text
course node/version
→ learner-control state
→ one deterministic progression policy
→ operation registry
→ bounded GPT operation envelope
→ representation/version record
→ decision/module-version provenance
→ next learner outcome
→ deterministic state transition
```

Use the current real DSA learning path rather than inventing a synthetic demo.

Recommended first operation families:

```text
try_unaided
rename_terms
smaller_step
show_trace
give_hint
restore_original
```

Do not build every future operation before real use requires it.

## Acceptance invariants

1. Same canonical state/evidence + same controller version yields the same authorized next action.
2. Every learner-facing intervention identifies its decision, operation(s), representation version, assistance level, and module-version set.
3. AI cannot mutate course progression directly.
4. AI diagnosis remains a hypothesis record.
5. Exact source/learner-facing turns remain durable independently of semantic processing.
6. Multi-dimensional interventions remain multi-dimensional in data.
7. Source representation remains restorable where the operation claims reversibility.
8. Historical operational evidence is immutable across module upgrades.
9. Offline replay is explicitly counterfactual and never becomes learner outcome evidence.
10. New module versions can coexist with old versions and historical decisions remain reproducible.
11. Future non-LLM representation/diagnosis implementations can satisfy the same contracts without changing course/controller semantics.
