# Curriculum Control Architecture

Status: **Issue #42 C0/C1 design + proficiency-gate specification; no runtime authority change**

This document defines how Study OS names curriculum areas, represents DSA proficiency, and frames daily study objectives without collapsing evidence into one score or turning a study plan into learner truth.

The machine-readable companion is `contracts/curriculum-control-policy.v0.1.json`.

## Scope and authority

The active research gate remains R0. Current research evidence is still limited to DSA/Python and the narrow concept-family work already identified in project state. The broader curriculum map below is architecture for future activation, not evidence that Study OS has validated teaching procedures in every track.

C0/C1 do not:

- change learner-state persistence or runtime semantics;
- add public MCP tools;
- add HTTP/frontend behavior;
- grant adaptive components live authority;
- turn a planning heuristic into a mastery claim.

## Namespace rule

Study OS previously used `T*` for two unrelated concepts:

- Issue #3 used `T0`–`T6` for DSA proficiency;
- `docs/LEARNING_CONTROL_MODEL.md` used `T1`–`T5` for broad competency tracks.

Those dimensions are now separated.

Older audit snapshots, including `docs/LEARNER_MODEL_CURRICULUM_AUDIT.md`, may still quote the old `T1`–`T5` broad-track labels as historical design text. Those labels are superseded by this policy and must not be treated as current canonical track IDs or used to reinterpret previously recorded evidence.

### Curriculum tracks

Canonical track IDs are:

| ID | Track | Current status |
| --- | --- | --- |
| `ALG` | Algorithmic foundations | active research slice |
| `SWE` | Software engineering foundations | planned architecture |
| `MATH` | Math and statistics foundations | planned architecture |
| `DATA` | Data foundations | planned architecture |
| `ML` | Machine learning | planned architecture |
| `DL` | Deep learning | planned architecture |
| `AIE` | AI engineering | planned architecture |
| `SYS` | Production systems and reliability | planned architecture |
| `DIAG` | Technical problem framing and diagnosis | planned architecture |

The map is intentionally not a strict staircase. For example, SWE can grow in parallel with ALG, and practical AIE work can begin before all DL theory is complete as long as the learner does not confuse application skill with model-training understanding.

### DSA proficiency

Issue #3's tier meanings are preserved under an explicit DSA namespace:

| Canonical | Legacy prose | Meaning |
| --- | --- | --- |
| `DSA0` | `T0` | Orientation |
| `DSA1` | `T1` | Guided Easy |
| `DSA2` | `T2` | Independent Easy |
| `DSA3` | `T3` | Guided Medium |
| `DSA4` | `T4` | Independent Medium |
| `DSA5` | `T5` | Interview Ready |
| `DSA6` | `T6` | Advanced |

Legacy `T0`–`T6` labels remain documentation compatibility aliases for Issue #3 only. New machine-readable state should use the explicit DSA namespace if/when proficiency state becomes canonical.

Do not invent one universal proficiency scale for SWE, ML, AI engineering, or other tracks merely for UI symmetry. Each future track needs observable capabilities and evidence gates appropriate to the construct being measured.

## Distinct learning dimensions

These dimensions must remain separate:

- **track** — the competency family being developed;
- **competency** — an observable behavior;
- **capability state** — evidence-backed state such as `pass_supported` or `pass_unaided`;
- **assistance** — A0–A6 support actually exposed;
- **task difficulty** — authored/learner-relative multidimensional load and the learning operation;
- **representation effectiveness** — contextual evidence about an intervention;
- **proficiency tier** — repeated evidence across items/sessions that satisfies a broader capability gate;
- **daily study goal** — a derived, revisable plan for what evidence to collect next.

A dashboard may later summarize these dimensions, but a summary must never become the authority that overrides a missing critical capability.

## DSA proficiency promotion policy

The C1 policy turns Issue #3's prose gate into an explicit, provisional promotion matrix.

The initial default requires at least two distinct unseen items. More than one session is required when practical. This is a configurable operating threshold, not a validated population-level pedagogical constant.

For independent bands (`DSA2`, `DSA4`, `DSA5`, `DSA6`), promotion requires relevant evidence of:

- unaided performance rather than supported-only success;
- changed-surface transfer;
- delayed retrieval;
- the critical capabilities named by the band, such as implementation or debugging when those are part of the claim.

Promotion must be blocked when any of the following is the only apparent basis for advancement:

- one successful item;
- supported-only success for an independent band;
- self-report without behavioral evidence;
- a high average hiding an implementation gap;
- a high average hiding a transfer gap;
- reuse of a teaching/exposed item as if it were unseen evidence;
- AI-assisted construction recorded as unaided manual implementation;
- immediate success silently promoted into transfer or delayed mastery.

This policy intentionally favors false negatives over unsupported proficiency claims during the research phase. The threshold can later be calibrated from actual trajectories without rewriting the underlying evidence history.

## Manual versus AI-assisted evidence

Study OS should not create one simplistic "manual score" and one "AI score." Instead, preserve the task/interaction/assistance provenance that makes the evidence interpretable.

For example, these are materially different evidence conditions:

- blank manual implementation;
- scaffolded manual implementation;
- code reading or debugging;
- AI oversight/review;
- AI-assisted construction;
- verbal explanation or phone shorthand when full implementation is not being measured.

AI-assisted success can support capabilities such as oversight, decomposition, architecture, or debugging. It cannot be relabelled as A0 blank-manual implementation merely because the final code is correct.

## Daily evidence-goal model

Study OS does not yet have a canonical learner study-plan schema or daily planner runtime. C0/C1 defines the planning semantics only.

A daily evidence goal answers:

> Given canonical learner evidence, due retention, current phase, explicit priorities, and an available study budget, what bounded evidence objective should this study period pursue?

A future advisory goal should be capable of carrying:

- goal/plan version;
- target track and competency;
- current capability state plus evidence references;
- desired next evidence state;
- task/interaction mode;
- maximum assistance or fade target;
- due retention obligations;
- a transfer probe when warranted;
- explicit priority/interview need;
- optional time/effort budget;
- stop/replan condition;
- rationale and provenance.

The goal itself is **derived evidence/planning state**, not observed learner truth and not mastery authority.

Time spent and item counts may constrain a session, but neither is sufficient evidence of progress. "Study for 90 minutes" and "solve five problems" are operational quotas, not capability states.

## Initial deterministic daily loop

Before any optimized or model-driven planner, the preferred advisory sequence is:

```text
due retention
  -> highest-value active competency
  -> diagnose if ambiguous
  -> practice/remediate
  -> fade assistance
  -> transfer if warranted
  -> checkpoint
  -> schedule next probe
```

This sequence is a control skeleton, not a requirement that every session contain every phase. For example, a short session may consist only of a due delayed-retention probe and checkpoint.

## Relationship to current Study OS control logic

The existing scaffold controller already enforces a compatible micro-policy:

- fail/partial -> remediate the same atomic target;
- supported success -> fade rather than advance;
- unaided success -> advance at most one planned step;
- transfer and delayed mastery cannot be awarded by the instructional micro-controller.

The daily-goal layer sits **above** that micro-loop. It chooses which evidence objective should be attempted; it must not bypass the lower-level prerequisite, assistance, capability, retention, or evidence rules.

## Roadmap placement

### C0 — taxonomy/design convergence

Safe now. Resolve track/tier naming, document the broad curriculum architecture, and define daily evidence-goal semantics. No runtime change.

### C1 — proficiency-gate specification

Safe now. Formalize DSA repeated-evidence promotion and negative cases against canonical capability states, assistance, transfer, and delayed evidence. Keep the result read-only/advisory.

### C2 — learner-state prerequisites

Depends on Issue #10 richer `LearnerSnapshot` projection, especially capability evidence refs, assistance history, active goals/current phase, recent exposure summary, constraints, explicit fade target, and next high-information action.

### C3 — shadow daily-goal selector

After C2, implement a deterministic baseline and any competing adaptive planner behind the existing `LearnerSnapshot -> DecisionProposal -> shadow/audit` boundary. No live authority.

### C4 — real learning validation

Use R0/R1/G4 trajectories to compare planned objectives against downstream unaided, transfer, and delayed outcomes.

### C5 — bounded advisory/live authority

Only after the relevant Issue #21 mutation/negative-control, protected-holdout, and seeded-policy-simulation gates plus Issue #10 promotion requirements. Require explicit accept/reject logging and a kill switch before bounded live selection.

## Curriculum expansion rule

Do not instantiate the entire Python-to-ML-to-AI roadmap at once.

Broad architecture can be durable now, but content should continue to arrive as narrow, versioned slices:

```text
track
  -> competency/prerequisite graph
  -> atomic competencies
  -> versioned item bank
  -> episode plan
  -> diagnostic/practice/transfer/retention evidence
```

The existing running-extrema slice is the reference shape. Near-term instantiated learning should continue to prioritize the active manual-Python/DSA objective while the measurement/control loop is validated. Math/data/ML/DL/AIE/SYS content should be instantiated only when an explicit learner goal and prerequisite/evidence design justify it.

## Compatibility and change policy

- Curriculum-track identifiers and proficiency-scale identifiers are independently versioned semantic concepts.
- The `DSA0`–`DSA6` mapping preserves the meaning of Issue #3's `T0`–`T6` prose; it does not retroactively fabricate stored tier evidence.
- A future proficiency implementation must cite the policy version and evidence used to derive the tier candidate.
- Promotion thresholds may change by policy version; observed attempts/assessments remain immutable evidence.
- Daily-plan recommendations must record their own version/rationale so replay can distinguish a planner change from a learner change.
