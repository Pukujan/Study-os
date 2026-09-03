# Study OS Roadmap

Date: 2026-09-03
Status: proposed canonical execution roadmap

## Product direction

Study OS is an adaptive learning control layer between structured learning material and a longitudinal learner record.

The current learner-facing surface remains the GPT app. The dedicated frontend is deferred, not rejected.

The product-development loop is driven by real learner use:

```text
structured source material
 -> learner attempt
 -> observed friction
 -> diagnosis
 -> representation / information / assistance / granularity operation
 -> learner response
 -> fade or restore difficulty
 -> transfer / retention when warranted
 -> learner + system evidence
```

The project should optimize for preserving and improving this operational loop, not for maximizing implementation complexity or satisfying old sequencing checklists.

## Durable assets vs replaceable implementation

Study OS treats these as durable project assets:

- architecture and ownership boundaries;
- persistent data semantics and migrations;
- raw evidence provenance and integrity;
- normalized operational event semantics;
- learner-state and system-evaluation contracts;
- curriculum/task provenance and competency structure;
- representation/intervention definitions;
- explicit invariants, PDD/SDD/ADR decisions, and failure-recovery guarantees.

Implementation code is replaceable when necessary. Verification exists to protect the architecture, data, and user-visible semantics that matter; it is not itself the product objective.

## Current primary phase

**Operational dogfooding + durable evidence + structured curriculum acquisition.**

The near-term system is:

```text
GPT learner surface
      |
      +--> local Study OS runtime --> SQLite + private evidence store
      |
      +--> structured curriculum/tasks from approved sources
      |
      +--> real operational learning trajectories
                 |
                 +--> representation failures
                 +--> information-load failures
                 +--> assistance failures
                 +--> task-granularity failures
                 +--> learner/system evaluation
```

## P3.0 — Durable-or-recoverable learner evidence

This is the immediate engineering priority.

### Core invariant

> No silent learner-evidence loss.

A learning interaction must be either:

1. durably acknowledged by the local Study OS runtime; or
2. explicitly known to be missing/uncertain and recoverable through reconciliation/backfill.

A remote/network failure before the local runtime receives a turn cannot be made impossible by SQLite. Therefore the end-to-end architecture must combine reliable local persistence with later reconciliation.

### Required architecture

Preserve at least three layers:

```text
raw evidence
 -> normalized operational records
 -> derived learner/system state
```

Derived state must remain rebuildable from lower-level evidence where its contract claims derivability.

### Near-term requirements

- durable commit before successful write acknowledgement;
- idempotency-safe retries;
- no duplicate durable records from exact retry;
- explicit correlation/operation identifiers;
- visible failed/unknown write state;
- restart-safe persistence;
- integrity/doctor checks;
- backup + restore verification;
- transcript/conversation reconciliation for remote failures;
- immutable/private raw evidence boundary;
- provenance from derived learner/system claims back to evidence.

This work should receive focused PDD/SDD/invariant treatment because it protects the longitudinal data asset.

## P3.1 — Continuous GPT dogfooding

Subject 001 continues learning through the GPT app while development proceeds.

This is not postponed until a dedicated frontend or fully autonomous adaptive controller exists.

Real use should preserve, when observable:

- source task/reference;
- learner attempt;
- confusion/failure signal;
- tutor/Study OS operation;
- representation used;
- assistance level;
- information amount/expansion/compression;
- dynamic decomposition/recomposition;
- explicit learner feedback;
- subsequent attempt/outcome;
- assistance fade;
- original-format recovery;
- changed-surface transfer;
- delayed retention when applicable.

Operational learning episodes are product-development evidence. They remain subject-level evidence unless replicated more broadly.

## P3.2 — Structured curriculum/data in parallel

Approved public/open sources may be used to build structured curriculum in parallel with the operational research loop.

Curriculum expansion is no longer globally blocked on completing one narrow Sliding Window research gate.

The data/curriculum layer should preserve:

- source and rights/provenance;
- source version/hash where practical;
- competency/task mappings;
- prerequisites;
- task/item version;
- expected reasoning or rubric where supported;
- authored/source representation;
- difficulty evidence/estimate;
- distinction among reported-real, aggregate, curated, synthetic, and external/private sources.

Public source material is candidate learning material, not automatically a good learner-facing representation.

## P3.3 — Representation and operational adaptive learning

The principal adaptive hypothesis is that some apparent learning difficulty comes from the representation or delivery of information rather than inability to learn the target concept.

Study OS should preserve the distinction between productive target difficulty and extraneous representation difficulty.

Candidate operation families now include:

- representation translation;
- identifier/variable-name normalization;
- language simplification;
- information compression;
- information expansion;
- progressive disclosure;
- task decomposition;
- task recomposition;
- worked example / concrete example;
- deterministic trace;
- pseudocode/code translation;
- hinting;
- assistance fade;
- original/source representation restoration;
- transfer and retention probes.

Candidate failure families include:

- representation translation overhead;
- variable-name semantic interference;
- information overload;
- information underload;
- over-help;
- under-help;
- over-decomposition;
- under-decomposition;
- answer leakage;
- transformation-fidelity failure;
- representation dependency / failure to survive restoration.

These categories remain versioned hypotheses/operational labels until their semantics and evidence requirements are sufficiently stable.

## Learner and system are evaluated separately

Study OS should not collapse learner quality and system quality into one score.

Learner evidence may include:

- correctness;
- reasoning;
- independence;
- implementation where relevant;
- explanation;
- original-format recovery;
- transfer;
- retention;
- representation robustness.

System evidence may include:

- diagnosis accuracy;
- representation effectiveness;
- information calibration;
- assistance efficiency;
- over-help/under-help rate;
- decomposition/recomposition quality;
- transformation fidelity;
- answer leakage;
- fade success;
- transfer/retention preservation;
- prediction/grading calibration.

Immediate assisted success alone is not sufficient evidence for either durable learner capability or system effectiveness.

## Frontend and multimodal representations

A dedicated frontend remains important but is not the current critical path.

The GPT app currently provides a coherent free-form learner interaction surface and continues to generate high-value operational evidence.

When the dedicated frontend becomes active, it should consume the same semantic operations rather than redefine learner state. Likely interaction controls include:

- I did not understand;
- simplify;
- shorter / more detail;
- smaller step / step by step;
- change representation;
- show trace/diagram/code/pseudocode;
- rename confusing terms;
- small hint;
- let me try alone;
- show original.

Mermaid, diagrams, audio tutoring, generated imagery, and later video should be treated as representation modalities with provenance and outcomes, not as automatically beneficial features.

## Engineering assurance policy

Keep PDD/SDD, invariants, architecture boundaries, data-integrity tests, migration discipline, provenance, idempotency, recovery, and compatibility where they protect durable semantics.

Broader engineering-hardening techniques remain available but are risk-driven rather than blanket near-term gates. Mutation testing, large synthetic learner simulations, exhaustive hidden engineering holdouts, chaos matrices, formal methods, and frontend/platform hardening should be activated when a concrete failure model or product surface justifies them.

## Issue disposition plan

Do not erase historical issue logs. They preserve how the architecture developed.

After this roadmap is reviewed, update issue status deliberately:

| Issue | Proposed disposition | Reason |
| --- | --- | --- |
| #1 initial harness | Supersede/close as historical | bootstrap checklist and Sliding Window sequencing are stale; evidence-loop concepts remain valid |
| #2 research-before-product | Supersede/close | real product dogfooding and research now run together |
| #3 mobile adaptive DSA | Supersede as execution tracker; retain semantics | valuable representation/fade semantics, but mobile-first narrow scope is stale |
| #4 local-first runtime | Preserve as accepted architecture | local runtime + SQLite/private evidence remains central |
| #5 P0/P1 runtime tracker | Supersede after reliability work is re-tracked | historical runtime acceptance is useful; current failure is more specifically durable capture/reconciliation |
| #10 learner/adaptive integration | Reframe and keep | valuable learner, representation, assistance, curriculum and outcome semantics; `OSS-first` is no longer the primary identity |
| #21 engineering assurance | Reframe/demote to risk-driven assurance backlog | architecture/data protections remain; blanket hardening sequence is no longer near-term product priority |
| #26 application/frontend boundary | Park/defer | frontend architecture remains useful but is not current priority |
| #27 SWE/platform closure | Close/not planned for now | tied to deferred HTTP/frontend expansion and over-prioritizes implementation hardening |
| #42 curriculum | Reframe and keep | structured public curriculum may expand in parallel; old global expansion gate is stale |

No issue should be closed solely because this roadmap proposes it. Closure/reframing is a separate reviewed cleanup action.

## Pull-request relationship

Current draft work is complementary:

- PR #49: retrospective public-safe methodology evidence;
- PR #50: interview/public-source evidence plan and verified source registry;
- PR #51: canonical operational learner episodes exposing representation failures.

These should be reviewed on their own evidence/privacy boundaries; this roadmap does not merge them automatically.

## Immediate execution order

1. diagnose and restore the real GPT -> local Study OS write path;
2. specify and implement durable-or-recoverable capture/reconciliation invariants;
3. continue Subject 001 course learning through the GPT during that work;
4. begin small-sample ingestion/normalization from approved curriculum sources and expand structured curriculum deliberately;
5. record real representation/information/assistance/decomposition operations and outcomes;
6. evolve learner and system evaluation from real trajectories;
7. harden implementation selectively where failures or new product surfaces justify it;
8. activate dedicated frontend/multimodal product work when it has higher value than continued GPT dogfooding.

## Roadmap governance

`docs/ROADMAP.md`, `docs/CURRENT_STATE.md`, `docs/HANDOFF.md`, and `docs/DECISIONS.md` are the current planning authority after this reset is accepted.

Issues and Git history preserve historical plans. An old unchecked issue item is not automatically current execution priority when it conflicts with a later accepted decision/roadmap.
