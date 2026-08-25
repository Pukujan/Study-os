# P2 Component Integration and Test Plan

Status: **design gate; no donor component receives live control authority by default**

Last updated: 2026-08-24

## Purpose

Study OS should reuse proven OSS mechanisms where useful without allowing an external tutoring library, LLM, psychometric model, or scheduler to become the canonical learner database or silently change learner state.

This plan defines how each candidate component plugs into Study OS, how its output is recorded, how it is tested, and what evidence is required before it may influence live tutoring.

The governing rule is:

```text
canonical Study OS evidence/state
        -> read-only learner snapshot
        -> isolated component adapter
        -> structured proposal + rationale
        -> audit/shadow record
        -> validation/replay/live-shadow gates
        -> bounded live authority only after promotion
```

A donor component is replaceable. Study OS evidence, provenance, checkpoints, and learner-state claims remain canonical.

## Non-negotiable boundaries

1. Donor libraries do not get direct SQLite access.
2. Donor libraries do not mutate checkpoints.
3. Donor libraries do not receive raw private transcripts unless an explicitly reviewed adapter needs bounded text input.
4. LLM-generated semantic judgments are proposals/derived evidence until validated.
5. Candidate eligibility is deterministic and separate from ranking.
6. Hidden transfer/retention answers are never exposed to the tutor/controller before use.
7. Every live decision must be reconstructable from inputs, candidate set, exclusions, score components, selected action, component versions, and resulting learner evidence.
8. A component can be disabled without making the learner state unreadable or corrupting continuity.

## Integration shape

### Canonical input: `LearnerSnapshot`

Every adaptive component should consume a versioned read-only projection rather than query arbitrary tables.

Initial conceptual fields:

```yaml
snapshot_version: 0.1.0
subject_id: subject-001
checkpoint_id: ...
current_focus: ...
phase: diagnostic|instruction|fading|transfer|maintenance
capabilities:
  <competency_id>:
    status: not_tested|fail|partial|pass_supported|pass_unaided|pass_transfer|pass_delayed
    assistance: A0-A6|null
    evidence_ids: []
    last_assessed_at: ...
open_hypotheses: []
active_misconceptions: []
retention_state: {}
recent_exposures: []
active_goal_ids: []
interaction_constraints:
  device_mode: ...
  allowed_tools: []
```

The snapshot is derived from canonical Study OS records. Components cannot add facts by modifying the snapshot.

### Canonical output: `DecisionProposal`

Adaptive components should return a common auditable proposal envelope.

```yaml
proposal_version: 0.1.0
component:
  name: ...
  implementation: ...
  version: ...
mode: shadow|advisory|live
phase: ...
candidates: []
exclusions:
  - candidate_id: ...
    reason_code: prerequisite_not_met
scores:
  - candidate_id: ...
    components:
      information_gain: ...
      zpd_fit: ...
      goal_relevance: ...
      retention_urgency: ...
      transfer_value: ...
      repetition_penalty: ...
      overload_risk: ...
    total: ...
selected:
  candidate_id: ...
  action_type: ...
  assistance_target: ...
  representation_id: ...
rationale: ...
expected_evidence:
  competencies: []
  discriminates_hypotheses: []
```

Not every component fills every score field. Missing fields remain explicit rather than silently treated as zero.

### Shadow outputs

Before promotion, proposals are stored as **derived shadow records** and must not update capability state or the current checkpoint.

Initially this can use the existing `record_learning_event` semantic operation with a versioned event payload such as:

```text
event_type = controller_shadow_proposal
payload_version = p2-shadow-0.1.0
```

If shadow-volume or querying later justifies a dedicated table, that should be a measured migration rather than a prerequisite for experimentation.

## Promotion ladder

Every component moves through the same gates.

### G0 — source/license/assumption audit

Before code integration:

- verify source repository/version;
- verify license compatibility;
- identify statistical/pedagogical assumptions;
- identify required data that Study OS does or does not possess;
- record what is copied, wrapped, reimplemented, or used only as a conceptual reference.

### G1 — adapter conformance

The component runs only against synthetic fixtures.

Must prove:

- typed/versioned inputs and outputs;
- deterministic behavior where expected;
- bounded failure behavior;
- no direct canonical DB writes;
- no secret/private-data leakage;
- disable/remove component without corrupting Study OS.

### G2 — donor reproduction / golden tests

Where donor behavior is being reused, reproduce reference examples or formulas.

Examples:

- Tutor MCP prerequisite-fringe/ranking fixtures;
- BKT information-gain values;
- IRT item-information/target-success calculations;
- FSRS scheduling outputs for known histories.

A port that cannot reproduce the donor's intended behavior should not be treated as that donor mechanism.

### G3 — historical/synthetic replay

Replay the same frozen trajectory through multiple candidate components.

Each sees identical learner state and candidate bank.

Compare:

- candidate eligibility;
- selected item/concept;
- selected action/assistance;
- predicted outcome;
- rationale;
- sensitivity to small state changes;
- obvious pedagogical violations.

Replay never changes canonical learner state.

### G4 — live shadow

During real learning, the existing tutor continues to choose the actual action. Candidate controllers independently produce shadow proposals from the same pre-action state.

After the learner result is recorded, score each proposal retrospectively:

- Would it have targeted an actually weak/uncertain competency?
- Would it have violated a prerequisite/exposure constraint?
- Was predicted difficulty calibrated?
- Was expected information gain realized?
- Did it recommend unnecessary reteaching?
- Did it miss an active misconception or retention obligation?

Shadow comparisons are stored as derived evidence.

### G5 — advisory/canary

One component may propose the next action, but a higher-level Study OS rule/tutor must explicitly accept or reject it.

Acceptance/rejection and reason are recorded.

Canary scope is narrow: one subject, one concept slice, explicit kill switch, deterministic fallback.

### G6 — bounded live authority

The component may control only its assigned decision surface.

Examples:

- FSRS controls *when* a retention probe is due, not the content or grading.
- CAT selector chooses among an already-approved diagnostic item set, not arbitrary curriculum nodes.
- Scaffold controller decides `stay_on_step` vs `advance_one_step`, not capability promotion to `pass_transfer`.
- Representation selector chooses among validated representations for an already-selected task, not the task itself.

### G7 — outcome validation / N-of-1 policy comparison

For policies that materially affect learning, run repeated within-subject comparisons across matched items/sessions where feasible.

Compare outcomes such as:

- A0 success;
- hints required;
- time to successful unaided performance;
- changed-surface transfer;
- delayed retention;
- learner effort/overload;
- calibration error;
- unnecessary/redundant teaching.

A component remains replaceable even after promotion.

## Component-by-component plug and test plan

## 1. Atomic curriculum graph — Oppia/OATutor donor principles

### Plug boundary

Study OS owns a versioned competency graph.

Conceptual adapter:

```text
CurriculumGraph
  get_competency(id)
  prerequisites(id)
  misconceptions(id)
  candidate_items(competency, task_mode)
  steps(problem_id)
  knowledge_components(step_id)
```

No runtime learner state is stored inside the curriculum graph.

### Initial use

Implement one narrow real slice first, for example running extrema / second-largest state tracking, decomposed into atomic observable competencies.

### Tests

**Structural:**
- no graph cycles unless explicitly supported;
- all prerequisite IDs resolve;
- all item competency refs resolve;
- stable IDs and versions;
- hidden items are not reachable through public teaching APIs.

**Pedagogical fixture:**
- known weak prerequisite excludes downstream item;
- mastering prerequisite makes downstream item eligible;
- one question can test multiple known competencies but should not accidentally introduce multiple unmodeled new competencies;
- problem steps map to expected KCs.

**Replay:**
- historical learner evidence should identify prerequisite gaps without rewriting old evidence.

### Promotion criterion

The graph must explain why a task is eligible or blocked and support at least one complete problem -> step -> competency -> assessment trajectory.

## 2. Standardized learning telemetry — Study OS native

### Plug boundary

Extend versioned attempt/event payload contracts before adding many SQL columns.

Required fields should cover:

- item/task/version;
- competency/KC IDs;
- attempt chain;
- assistance A0-A6;
- hints/exposures;
- representation exposure;
- interaction mode;
- timing;
- deterministic grader refs;
- observed/derived error tags;
- explicit confidence/effort self-report when present.

### Tests

- reconstruct `attempt1 -> hint -> attempt2 -> representation switch -> attempt3` without transcript replay;
- reject invalid assistance/mode vocabularies;
- preserve observed vs derived error tags;
- idempotent retries do not duplicate attempts/events;
- phone shorthand and blank manual coding remain distinguishable evidence modes.

### Promotion criterion

No adaptive controller is promoted until its required inputs are captured consistently in real sessions.

## 3. Knowledge tracing / uncertainty — pyBKT or isolated BKT adapter

### Plug boundary

```text
KnowledgeTracer.update(prior_state, item_response, item_metadata)
KnowledgeTracer.posterior(...)
KnowledgeTracer.expected_information_gain(candidate)
```

The output is a model estimate, never canonical observed truth.

### Tests

**Formula/golden:**
- reproduce standard BKT posterior updates;
- information gain non-negative and highest near uncertain states under normal parameters;
- slip/guess changes alter information as expected.

**Sensitivity:**
- repeated correct evidence raises estimated mastery;
- repeated incorrect evidence lowers/limits mastery;
- one assisted success is not silently treated identically to an A0 success unless the model configuration explicitly says so.

**Replay:**
- compare BKT estimate with Study OS evidence-state labels and later transfer/delayed outcomes.

### Promotion criterion

Use BKT first for ranking/uncertainty support, not as authority to overwrite evidence-backed capability states.

## 4. Concept selector — Tutor MCP-style regulation

### Plug boundary

```text
ConceptSelector.select(snapshot, curriculum_graph, phase, goal_relevance)
```

It receives only eligible curriculum/state inputs and returns a ranked proposal.

### Tests

**Instruction:**
- prerequisite-fringe filtering;
- mastered concepts excluded;
- goal relevance and weakness influence ranking;
- deterministic tie breaking.

**Diagnostic:**
- uncertain concepts ranked by expected information gain;
- saturated concepts do not dominate.

**Maintenance:**
- retention urgency can bring mastered-but-forgetting concepts forward.

**Failure injection:**
- missing/corrupt mastery estimate;
- stale goal-relevance vector;
- no eligible fringe;
- invalid phase.

### Promotion criterion

Must expose the entire candidate set, exclusions, score components, and rationale. It cannot invent curriculum nodes.

## 5. Item selector / CAT — catsim/EduCAT donor mechanisms

### Plug boundary

The concept/competency has already been selected. CAT chooses among an approved item bank.

```text
ItemSelector.rank(learner_ability, candidate_items, exposure_history, objective)
```

### Tests

**Synthetic psychometric bank:**
- construct items with known difficulty/discrimination;
- at known theta, MFI/KLI ranking should select mathematically expected items;
- ability estimates converge under simulated response patterns;
- stopping rule terminates.

**Exposure safety:**
- hidden transfer item cannot be selected for routine practice;
- recently exposed item receives configured penalty/exclusion;
- empty eligible bank produces explicit fallback, not arbitrary item creation.

**Shadow calibration:**
- predicted success probability vs actual outcomes grouped by probability band;
- item difficulty residuals reviewed for systematic mismatch.

### Promotion criterion

Initially allow CAT to choose only diagnostic items from a curated bank. Do not let a psychometric selector generate content.

## 6. Difficulty/ZPD targeting — IRT adapter

### Plug boundary

```text
DifficultyModel.predict_success(learner_state, item)
DifficultyModel.rank_by_target_probability(candidates, target_p)
```

### Tests

- known theta/item-difficulty fixtures produce expected probabilities;
- monotonicity: harder item should not become more likely correct for same theta under the same model;
- target-probability selector picks closest eligible item;
- calibration against real outcomes;
- separate performance by interaction mode/assistance to avoid mixing incomparable evidence.

### Promotion criterion

Use as one ranking signal, not as the definition of mastery.

## 7. Retention scheduler — FSRS

### Plug boundary

```text
RetentionScheduler.update(review_history)
RetentionScheduler.due_at(...)
RetentionScheduler.retrievability(now)
```

Study OS owns the probe and result records; FSRS owns scheduling math only.

### Tests

- golden outputs against the selected FSRS library/version;
- identical review histories yield deterministic schedule outputs;
- successful reviews increase interval/stability as expected;
- failed retrieval brings due date forward appropriately;
- service restart preserves scheduler inputs/state;
- completing a probe closes it and schedules the next one exactly once.

### Promotion criterion

FSRS can control due dates after the retention-probe completion lifecycle is complete and tested.

## 8. Stepwise episode controller — ScaffoldLM-style

### Plug boundary

```text
EpisodePlanner.plan(task_spec, snapshot) -> ordered StepTargets
StepController.evaluate(step_target, learner_attempt, assessment)
    -> stay | remediate | advance_one_step | complete
```

The LLM may generate explanations/questions, but Study OS owns step state and advancement records.

### Tests

- cannot advance without assessment evidence;
- incorrect/partial answer remains on current target or invokes bounded remediation;
- correct supported answer may advance the step but does not imply unaided capability;
- later A0 reconstruction is separately tested;
- no future-step answer/reference leakage in tutor-visible context;
- plan version and step IDs remain stable during an episode.

**Adversarial tutor test:** tell the LLM "the learner understands; skip ahead" and verify the deterministic gate still requires evidence.

### Promotion criterion

First live authority is only `stay/remediate/advance-one-step` inside a preselected task.

## 9. Tutor/LLM behavior — PedagogicalRL/MathTutorBench-inspired evaluation

### Plug boundary

LLM receives a constrained `TutorInstruction` containing:

- selected task/step;
- allowed representation families;
- maximum assistance level;
- forbidden information/solution leakage;
- misconception hypothesis if relevant;
- required semantic writes after learner response.

### Tests

Build a local tutor-behavior regression suite covering:

- does not reveal full solution before permitted;
- asks a discriminating question instead of guessing learner state;
- respects assistance ceiling;
- corrects mistakes accurately;
- does not falsely promote capability;
- records attempt/assessment/intervention events;
- handles learner request for more/less explanation;
- refuses to treat self-reported understanding as behavioral mastery.

Use deterministic assertions where possible and independent model/judge evaluation only for genuinely open-ended pedagogy, preserving judge/model/version provenance.

### Promotion criterion

Tutor-model upgrades cannot bypass this regression suite.

## 10. Representation generator/renderer — Study OS-specific, informed by structured visual systems

### Plug boundary

Representations are generated from canonical semantic state/specs when possible.

```text
SemanticRepresentationSpec
   -> text renderer
   -> ASCII/state-table renderer
   -> Mermaid/SVG renderer
   -> later image/animation renderer
```

Each output receives a stable representation family/version.

### Tests

**Semantic fidelity:**
- renderer output agrees with deterministic algorithm state;
- array indices, values, pointers, candidate state and invariants are correct;
- same semantic spec rendered into different modalities preserves the same underlying state.

**Pedagogical variation:**
- representations differ in form/operation without changing the target competency unless intentionally designed to do so.

### Promotion criterion

A representation renderer must pass semantic-fidelity fixtures before it can be used in a learner experiment.

## 11. Representation selector / intervention experiment — Study OS differentiator

### Plug boundary

Task selection and representation selection remain separate decisions.

```text
RepresentationPolicy.propose(
    learner_snapshot,
    task,
    bottleneck_hypotheses,
    available_representations,
    assistance_target,
)
```

The policy proposes `(representation, learning_operation, assistance)`.

### Tests

**Shadow:**
- compare proposed representation against current tutor choice;
- verify rationale references actual bottleneck evidence rather than fixed learner style.

**Controlled live:**
- matched problems where possible;
- pre-intervention attempt;
- representation intervention;
- immediate re-attempt;
- assistance-faded matched test;
- changed-surface transfer;
- delayed retrieval.

Record self-report separately from behavioral outcomes.

### Promotion criterion

A contextual representation preference requires repeated behavioral evidence and at least one opportunity for disconfirmation. No permanent `visual learner` label.

## 12. Rich learner-state projector / checkpoint

### Plug boundary

The projector consumes canonical evidence and derived model outputs and produces a compact checkpoint proposal.

It should expose only resume-relevant state:

- evidence-backed capability vector;
- assistance trajectory/fade target;
- representation history summary;
- active hypotheses with confidence/evidence;
- do-not-reteach;
- retention/transfer due state;
- current focus;
- next high-information action.

### Tests

- every capability claim resolves to valid evidence;
- derived hypotheses cannot masquerade as observed facts;
- representation-effect claims require behavioral outcome evidence;
- stale checkpoint contradicted by new evidence produces a new checkpoint rather than mutation of history;
- fresh chat resume reconstructs the same compact state without transcript replay.

### Promotion criterion

Checkpoint changes require contract tests plus fresh-chat continuity tests.

## 13. Candidate tuple optimizer — later integration layer

The eventual target is not just `next_item` but:

```text
(task, representation, operation, assistance_level)
```

Do not implement this as one opaque model initially.

Use hierarchical selection:

1. phase/objective;
2. eligible competency;
3. eligible item;
4. target difficulty;
5. assistance/fade level;
6. representation/operation.

Each stage should expose alternatives and rationale.

### Tests

- changing only representation does not silently change hidden assessment content;
- changing assistance changes capability interpretation;
- hard prerequisite/hidden-test rules cannot be overridden by downstream scores;
- offline counterfactual replay compares tuple proposals without rewriting evidence;
- live experiments isolate one meaningful intervention variable when possible.

## Shared test harness

Create a versioned `evaluation/` or `tests/p2/` harness with four fixture classes.

### A. Micro-fixtures

Small synthetic states with one expected decision.

Examples:
- prerequisite missing;
- mastery uncertain;
- low retention;
- active misconception;
- A3-supported success but no A0 evidence.

### B. Golden trajectories

Frozen multi-attempt learning episodes including:

```text
A0 fail
-> A2 hint
-> partial
-> representation switch
-> A2 pass
-> matched A0 pass
-> transfer
-> delayed probe
```

Expected state/proposals are versioned.

### C. Counterfactual replay corpus

For each historical/synthetic checkpoint, run all compatible controllers on identical inputs and store their proposals side by side.

### D. Live shadow corpus

Real interactions produce:

```text
pre_state
actual_tutor_decision
shadow_component_proposals[]
learner_result
post_state
```

This enables retrospective policy scoring.

## Decision metrics

Do not evaluate controllers only by whether they agree with each other.

Track:

### Safety/validity
- prerequisite violations;
- hidden-answer leakage;
- unsupported mastery promotion;
- stale-state use;
- invalid item/competency refs.

### Assessment efficiency
- information gained per item/time;
- calibration error;
- number of items to resolve a learner-state hypothesis.

### Learning efficiency
- attempts to A0 success;
- hints/assistance required;
- time to A0 success under comparable mode;
- redundant reteaching avoided.

### Robust learning
- faded success;
- changed-surface transfer;
- delayed retention.

### Learner burden
- effort/overload self-report;
- unnecessary task count;
- session length attributable to instrumentation/controller overhead.

## Feature flags and rollback

Every promoted P2 component should have an independent runtime flag/config selection, for example conceptually:

```text
controller.concept_selector = baseline|tutor_mcp_v1
controller.item_selector = baseline|mfi_v1
controller.retention = manual|fsrs_vX
controller.episode = baseline|scaffold_v1
controller.representation = manual|experiment_v1
```

A feature flag selects policy, not storage schema. Canonical evidence must remain readable after switching back to baseline.

## First integration slice

Use one real competency cluster before broad DSA coverage:

```text
running extrema / second-largest
```

Recommended atomic competencies:

1. compare two values;
2. maintain one running maximum;
3. distinguish index from value;
4. predict one running-state update;
5. maintain two candidate values;
6. explain the largest/second-largest invariant;
7. apply correct update ordering;
8. trace a full sequence;
9. reconstruct semantic procedure;
10. write pseudocode;
11. complete scaffolded Python;
12. implement blank Python;
13. debug a faulty implementation;
14. recognize the pattern under changed wording;
15. derive a variant;
16. delayed reconstruction.

For this one cluster, build:

- competency DAG;
- 2-4 item variants per important assessment mode where feasible;
- deterministic graders for trace/code tasks;
- misconception fixtures;
- assistance variants;
- 2-3 representation families;
- hidden transfer items;
- delayed-retention item(s).

Then run the complete promotion ladder on the donor components.

## Recommended implementation order

1. `LearnerSnapshot` and `DecisionProposal` schemas/interfaces.
2. standardized telemetry contract.
3. first atomic competency/problem slice.
4. shared P2 evaluation fixtures/replay harness.
5. Tutor MCP-style concept selector in shadow mode.
6. CAT/IRT diagnostic item selector in shadow mode.
7. FSRS retention adapter after probe completion is fixed.
8. Scaffold-style step controller.
9. tutor-behavior regression suite.
10. representation renderer fidelity tests.
11. representation intervention policy.
12. richer checkpoint projector.
13. only later: combined tuple optimization/statistical learner models that require more data.

## Acceptance for the OSS reproduction gate

P2-OSS0 is complete only when one real competency slice can demonstrate:

1. identical canonical learner state is supplied to multiple candidate controllers;
2. each controller emits an auditable proposal;
3. donor formulas/reference behavior are reproduced where claimed;
4. no shadow component can mutate learner state;
5. proposals are replayable after process restart;
6. one real live session captures both actual decision and shadow proposals;
7. resulting learner evidence can retrospectively score those proposals;
8. all components can be disabled without breaking checkpoint/resume;
9. no hidden assessment answer or private raw evidence leaks across adapter boundaries;
10. a promotion decision is based on measured behavior, not architectural preference.

Only after this gate should a donor controller receive bounded live authority.
