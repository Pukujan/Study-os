# P4 Runtime and Schema Audit

Date: 2026-09-04  
Audit commit: `7f39f747d5c2d362d1ba95597e7001fd6ecdafda`  
Primary tracker: #63

## Scope and safety

This is a read-only audit of the P4 planning boundary. No learner database,
private evidence file, migration, GPT configuration, or transcript was
modified.

The P4 authority documents require a mapping from each semantic object to the
current implementation before adding persistent semantics. The names below
are contracts, not a requirement that the database use the same table names.

## Live runtime observation

The live runtime was inspected through the WSL checkout using the configured
local service path:

```text
runtime root: /root/.study-os
database: /root/.study-os/db/study-os.sqlite3
private evidence root: /root/.study-os/evidence
schema version: 1
```

The current store contains the P3/P2 substrate but no P4-specific tables. The
read-only counts were:

```text
subjects: 3
sessions: 7
messages: 48
raw_artifacts: 50
learning_events: 6
attempts: 29
assessments: 1
checkpoints: 3
representations: 0
interventions: 0
representation_outcomes: 0
```

For `subject-001`, three sessions contain 46 messages and 48 raw artifacts;
two accepted checkpoints exist. The store has no persisted course-node
identity, learner-control state machine state, authoritative controller
decision, module-version set, or replay record. The repository curriculum is
not loaded into the runtime `concepts` table (the live count is zero), so a
course definition must remain explicitly pinned to its repository version
until a runtime course registry is intentionally added.

Doctor passed with schema version 1, all required tables present, zero foreign
key violations, valid checkpoint pointers/sources, valid evidence links, and
valid raw artifact/message hashes. The existing P3 evidence is therefore a
usable input substrate, not evidence that P4 control semantics already exist.

## Semantic-object mapping

| P4 object | Existing support | Gap | Proposed additive change |
| --- | --- | --- | --- |
| `CourseNodeVersion` | `competencies.v0.1.json`, `items.v0.1.json`, and `episode-plan.v0.1.json` are versioned and validated by `curriculum.loader`; `concepts` is only a generic empty runtime table. | No single node contract with source refs, node status, assistance ceiling, restoration/transfer/retention gates, or stable policy reference. | Add a versioned repository course-node contract for the first slice. Persist only an immutable node reference/hash if runtime queries require it; do not backfill old checkpoints as P4 nodes. |
| `ProgressionPolicy` | Episode-plan `advance_requires` and `propose_scaffold_action` provide a deterministic, persistence-free policy. `curriculum-control-policy` is explicitly design/advisory-only. | No node-specific executable policy contract attached to a real runtime state or decision; current policy proposal is shadow-only. | Add a pure versioned policy evaluator for one node. It must return reason codes and gates, and fail closed on ambiguous/unsupported evidence. |
| `LearnerControlState` | `checkpoints.capability_state_json`, `assistance_state_json`, `current_focus`, plus the read-only `LearnerSnapshot` projection. | Checkpoints are subject-level snapshots, not a node/version state machine. No `state_version`, assistance ceiling, current/source representation refs, or evidence-based transition record. | Add a dedicated derived control-state record or an explicitly versioned state payload with immutable transition provenance. Do not overload capability claims into transcript evidence. |
| `DiagnosisHypothesis` | `learning_events` supports `evidence_class='derived'`, payload versions, and source IDs; adaptive contracts carry `open_hypotheses` and diagnostic proposals. | No canonical diagnosis schema, family/status/confidence validation, or node linkage. | Store hypotheses as derived, source-linked records with explicit status and module version. Reuse the event substrate first if its contract can enforce these fields; otherwise add a narrow table. |
| `PedagogicalOperationDefinition` | Curriculum items name learning operations and representation families; `SelectedAction.learning_operation` and tutor-policy checks exist. | No deterministic registry with legal states, maximum assistance, required inputs, or forbidden effects. | Add a versioned operation registry containing only `try_unaided`, `rename_terms`, `smaller_step`, `show_trace`, `give_hint`, and `restore_original` for the first slice. |
| `DecisionRecord` / `OperationInvocation` | `DecisionProposal` is auditable and deterministic in isolated adaptive tests; `interventions` records operation and representation version. | Proposals are not authoritative decisions. No durable decision ID, before-state ref, evidence set, authorized operation set, controller version, or module-set ref. | Add a persisted decision record separate from the learner-facing message, then link each operation invocation to it. GPT cannot create or mutate the decision directly. |
| `RepresentationVersion` and mapping/lineage | `representations` stores family/version/definition; `interventions` links a representation and records operation/version/bottleneck. | No source/parent lineage, mapping, preserved semantics, restorable flag, rendering ref, or evidence refs. | Reuse existing representation identity where possible, but add a versioned lineage payload/record and link it to the decision. Keep source representation addressable. |
| `ModuleVersionSet` | Individual adaptive modules expose versions in proposals and fixtures. | No immutable bundle pinning course graph, controller, operation registry, diagnosis, representation, assessment, learner-state, and model adapter versions. | Add an immutable module-set record referenced by every P4 decision. |
| `OutcomeRecord` | `attempts`, `assessments`, and `representation_outcomes` separately capture behavior and intervention-linked evidence. | No single decision-linked outcome distinguishing correctness, independence, assistance, restoration, transfer, retention, self-report, and next state. | Add a narrow outcome record that references existing attempts/assessments/evidence; never rewrite historical rows. |
| `ReplayEvaluation` | Public curriculum fixtures and P2 tests support deterministic replay-like comparison; shadow proposals are stored as derived events. | No explicit counterfactual record or learner-evidence exclusion at the persistence boundary. | Defer persistence until the first real trajectory exists, but reserve an explicit `offline_counterfactual` record contract. Replay output must never feed learner state. |

## Existing MCP/application boundary

The public semantic MCP surface is still the approved 15-tool v0.3 contract.
It exposes durability, attempts, assessments, representations, checkpoints,
continuity, retention, doctor, and export. It does not expose a P4 controller
or a generic SQL/file/shell escape hatch.

`MCPServer.call_tool` preserves `StudyOSError` categories. The `/actions`
route delegates through that server and returns the resulting semantic error
object, so current tests already preserve `not_found` and `conflict` for
Actions requests. Unexpected exceptions remain `internal_error`, as they
should. No unrelated HTTP change is required by this audit.

Source-turn durability remains correctly below P4: `append_conversation_turn`
captures immutable evidence, inserts `raw_artifacts` and `messages`, records
idempotency, and runs the post-commit hook only after the durable transaction.
P4 must not make that capture conditional on diagnosis, representation, or
controller success.

## Smallest real vertical slice

The first implementation candidate is:

```text
course node: dsa.extrema.update_order@0.1.0
source: domains/dsa/running-extrema/{competencies,items,episode-plan}.v0.1
```

This is the only complete, versioned, schema-validated, executable DSA slice
currently present in the repository. It has real prerequisite data, bounded
assistance, observable task modes, a deterministic episode plan, and existing
tests for fade-versus-advance behavior. It is a repository curriculum slice,
not a claim that the learner has already demonstrated the node.

The live checkpoint currently focuses on `sliding-window`; that focus must not
be silently relabeled as `dsa.extrema.update_order`. If the first live slice
must align with that exact focus, the next prerequisite is authoring a real
versioned sliding-window node and item, not pretending the existing README is
an executable node. The P4 implementation should use the running-extrema
slice for contract/controller tests and only route live learner behavior to a
node that has been explicitly pinned.

## Focused implementation handoff

The next coding increment should be test-first and limited to the selected
node:

1. Add machine-readable node/policy/operation contracts and validators.
2. Implement a pure controller whose canonical input is node/version,
   control state, prerequisite state, assistance history, recent evidence,
   diagnosis hypotheses, and policy version.
3. Add the smallest additive persistence needed for a durable control-state
   transition, decision/module provenance, representation lineage, and
   decision-linked outcome. Reuse existing sessions, messages,
   `raw_artifacts`, attempts, assessments, and learning events as evidence.
4. Add a bounded operation envelope. It must prohibit course advancement,
   mastery claims, target changes, and assistance above the deterministic
   ceiling.
5. Record exact learner-facing output as source evidence independently of
   structured operation metadata.
6. Keep replay out of canonical learner state; add its explicit contract only
   when the real trajectory provides an input worth replaying.

The first focused tests should establish:

- same canonical inputs plus controller version produce the same authorization;
- illegal operations, unknown versions, ambiguous progression evidence, and
  over-ceiling assistance fail closed;
- supported success fades assistance before advancement;
- source representation can be restored and remains linked to its adapted
  representation;
- identifier renaming and task decomposition remain separate operation
  dimensions;
- transcript/self-report evidence does not become capability or mastery;
- the exact learner-facing turn remains durable if semantic processing fails;
- a decision, operation, representation, module set, outcome, and next-state
  chain can be reconstructed after restart.

No P4 runtime behavior or schema migration is implemented by this audit.
