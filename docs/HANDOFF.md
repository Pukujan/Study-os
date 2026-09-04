# Agent Handoff

Last updated: 2026-09-03
Primary tracker: #63

## Current phase

**P4 — deterministic learning controller + versioned representation engine + operational improvement loop.**

The product center is no longer persistence repair or an abstract research gate. Study OS is being used for real learning, and the next architecture should make AI teaching behavior deterministic at the control layer while keeping representation generation flexible and versioned.

## Accepted live foundation

Current accepted operational foundation includes:

- learner-facing surface: Study OS GPT;
- stable learner identity: `subject-001`;
- live root: `/root/.study-os`;
- canonical store: SQLite + private evidence store;
- real user/assistant source-turn durability;
- cross-chat continuity via `resume_learning_context`;
- source evidence distinct from mastery/capability;
- local backup/restore + doctor/integrity protections;
- historical reconciliation mechanism for missing pre-capture evidence.

P3 remains supporting infrastructure. Do not restart a broad infrastructure phase unless a real failure requires it.

## Historical recovery — completed for supplied source

The user-authorized historical transcript source has been fully processed to the limit of what that source can establish.

Receipt: `docs/HISTORICAL_TRANSCRIPT_RECOVERY_RECEIPT.md`

Accepted result:

```text
source SHA verified: PASS
reviewed outer turns: 34
backfilled missing: 34
nested headings ignored: 50
second reconciliation added: 0
existing structured learner state unchanged: PASS
hash/link integrity: PASS
backup/restore: PASS
doctor: PASS
source exhausted: yes
conversation complete: NOT_ESTABLISHED
```

Canonical target session after recovery:

```text
0446d18d-046b-4b8b-a00f-f2f629787bda
messages: 4 → 38
raw_artifacts: 4 → 40
```

Do not repeat recovery from this same source. Only reopen historical reconciliation if genuinely new/stronger source evidence appears.

## Product thesis

The core moat is the learner ↔ course representation problem.

```text
COURSE / SOURCE
      ↓
DETERMINISTIC COURSE STATE
      ↓
DETERMINISTIC LEARNING CONTROLLER
      ↓ authorized pedagogical operation
VERSIONED REPRESENTATION ENGINE
      ↓
GPT LEARNER SURFACE
      ↓
DURABLE OPERATIONAL EVIDENCE
      ↓
LEARNER / CONTROLLER STATE
      ↺
```

Preserve productive target difficulty. Remove unnecessary representation difficulty during acquisition. Fade assistance and restore authentic/source representations later.

## Authority boundary

Study OS code/state controls:

- course node/version and prerequisites;
- learner-control state;
- allowed next operations;
- assistance ceiling;
- progression/blocking;
- fade/restoration requirements;
- transfer/retention requirements where applicable;
- evidence/provenance semantics;
- module versions.

AI may:

- propose diagnosis hypotheses;
- generate an authorized explanation/representation operation;
- transform terminology, examples, traces, pseudocode, or code under explicit constraints.

AI may not silently advance curriculum or mark mastery.

## Planning authority

Read in this order:

1. Issue #63
2. `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`
3. `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`
4. `docs/ADR-0016-deterministic-learning-control.md`
5. `docs/ROADMAP.md`
6. `docs/CURRENT_STATE.md`
7. latest accepted `docs/DECISIONS.md`
8. supporting P3 durability/reconciliation docs as needed

## Early product-discovery evidence

Recovered historical learning around dictionaries/Two Sum exposed:

- `seen` produced semantic interference because of prior set association;
- `index_by_num` remained confusing;
- `box` was self-reported as clearer;
- a later dictionary lookup was answered correctly;
- the same intervention also reduced task complexity/context.

Evidence boundary:

```text
observed:
  confusion before; later lookup correct

self-reported:
  box clearer

derived/proposed:
  identifier semantic interference contributed

not proven:
  renaming alone caused improvement
```

Therefore representation changes and decomposition/context changes must be recorded independently.

## P4 semantic objects to stabilize

Do not jump directly to implementation without preserving these contracts:

```text
CourseNodeVersion
ProgressionPolicy
LearnerControlState
DiagnosisHypothesis
PedagogicalOperationDefinition
DecisionRecord / OperationInvocation
RepresentationVersion + mapping/lineage
ModuleVersionSet
OutcomeRecord
ReplayEvaluation
```

Exact table names are not mandated. Reuse existing runtime structures wherever semantics already fit.

## Immediate Luna task — audit completed

### Phase 1 — architecture/schema audit — complete

1. Pulled latest `main` at `7f39f747d5c2d362d1ba95597e7001fd6ecdafda`.
2. Read Issue #63 + P4 PDD/SDD + ADR-0016.
3. Inspected current runtime schema/service/MCP contracts against each P4 semantic object.
4. Recorded the mapping and live read-only runtime observation in
   `docs/P4_RUNTIME_SCHEMA_AUDIT.md`.

The audit found that the P3/P2 durable substrate is healthy, but no P4-specific
course-node, learner-control, authoritative decision, module-set, outcome, or
replay records exist yet. The first implementation candidate is the existing
versioned `dsa.extrema.update_order@0.1.0` slice; the live `sliding-window`
checkpoint must not be relabeled to that node without an explicit pinned
course definition.

The mapping is:

```text
P4 semantic object
→ existing table/type/service support
→ gap
→ proposed reuse/additive change
```

5. Do **not** add schema merely because the design document names an object. Reuse existing durable structures where semantics align.
6. Identify the smallest real current course node suitable for the first vertical slice.

### Phase 2 — proposed smallest vertical slice — next

Design before implementation:

```text
real course node/version
→ learner-control state
→ one deterministic progression policy
→ operation registry subset
→ bounded GPT operation envelope
→ representation/version provenance
→ learner response/outcome
→ deterministic state transition
```

Initial operation subset:

- `try_unaided`
- `rename_terms`
- `smaller_step`
- `show_trace`
- `give_hint`
- `restore_original`

The focused TDD/implementation handoff is recorded at the end of
`docs/P4_RUNTIME_SCHEMA_AUDIT.md`. New persistent semantics will require an
additive, reversible migration; do not change the live learner store until
those tests and the migration plan are reviewed.

## Operational improvement loop

Now that sessions persist across chats, normal learning is product-development data.

For meaningful trajectories preserve:

```text
course node/version
learner state before
source representation
attempt
observed/self-reported difficulty
diagnosis hypothesis/version
authorized operation(s)/version
representation version
assistance level
next learner behavior
fade/source-restoration outcome
transfer/retention when applicable
module version set
```

System changes must be explicit module versions, not silent prompt drift.

Development loop:

```text
real trajectories
→ identify failure
→ module version N+1
→ offline replay
→ prospective real use
→ keep/promote/revert
```

Replay output is counterfactual system evaluation, never historical learner evidence.

## Longitudinal dogfooding objective

Keep using Study OS through increasingly difficult real material:

```text
Python/DSA
→ LeetCode
→ complex DSA
→ system design
→ AI-system reasoning/debugging
```

Harder material should expose failures in diagnosis, decomposition, representation, assistance, restoration, and progression. Extend states/operations only when real evidence warrants them.

## Later beta/user expansion

Do not build production auth/multi-tenancy now.

After repeated stable trajectories exist on harder material, beta/authenticated users can test:

> Which mechanisms generalize, which require personalization, and which fail across learners?

Subject 001 remains subject-level evidence until replicated.

## Long-horizon cost architecture

Do not optimize inference cost now, but preserve replaceable module interfaces.

Future implementations may include:

- parsers/AST/compiler transforms;
- deterministic traces/static analysis;
- terminology rewriting;
- templates;
- retrieval/cached validated representations;
- sentence embeddings/transformers;
- small classifiers/task-specific models;
- IR/language/notation converters;
- constrained LLM fallback.

The controller remains authority regardless of which implementation fulfills an operation.

## Non-negotiable invariants

1. No silent learner-evidence loss.
2. Course progression is controlled by code/state.
3. AI behavior is bounded by explicit authorized operations.
4. Transcript text alone never becomes mastery.
5. AI diagnosis remains a hypothesis.
6. Multi-dimensional interventions remain multi-dimensional in data.
7. Source representation remains restorable where claimed.
8. Raw evidence survives module/model changes.
9. Historical learner outcomes are immutable.
10. Replay/counterfactual outputs never masquerade as experienced learner evidence.
11. Module evolution is explicit/versioned.
12. Same canonical controller inputs + controller version produce the same authorization.
13. Future non-LLM components must be able to fulfill the same module contracts.
14. Generic SQL/shell/file MCP access remains prohibited.

## Deprioritized

- broad frontend work;
- video infrastructure;
- generic multimodal platform work;
- production multi-user auth;
- deep FOSSIL integration;
- premature LLM-cost optimization;
- broad hardening unrelated to control/data/evidence integrity.
