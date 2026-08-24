# Learner Model and Curriculum Audit

Status: **design/research audit; implementation work remains gated**

Last updated: 2026-08-24

## Purpose

Study OS now has a trustworthy local persistence/runtime substrate and a working cross-chat checkpoint/resume path, but those achievements do not mean the learner model or course are complete.

This audit separates four questions that were previously easy to conflate:

1. What is already promised by durable Study OS research/design documents?
2. What can the current live semantic runtime actually record and recover?
3. What durable course/curriculum content actually exists rather than being improvised by the tutor?
4. Which missing capabilities are justified by learning-science, intelligent-tutoring, and programming-education evidence?

The conclusion is that the largest gap is no longer persistence. It is the bridge between **raw learning interaction -> structured telemetry -> derived learner state -> adaptive plan -> durable curriculum**.

## Executive diagnosis

Study OS currently has three maturity levels:

### 1. Rich design intent

The repository already specifies many desirable dimensions:

- multidimensional capabilities rather than one mastery score;
- assistance A0-A6;
- attempts, assessments, representation interventions/outcomes;
- immediate, faded, transfer, and delayed outcomes;
- confidence, difficulty, clarity, overload, confusion, and breakthrough self-report;
- failed-attempt and hint counts;
- time to unaided success;
- derived diagnoses with evidence and competing hypotheses;
- checkpoints with do-not-reteach and next-action semantics;
- a Lesson IR with prerequisites, misconceptions, state models, invariants, representations, and assessments.

These are real durable design commitments, not new ideas invented by this audit.

### 2. Minimal trustworthy live runtime

The v0.1 runtime reliably persists the canonical minimum:

- sessions;
- generic learning events;
- attempts;
- assessments;
- representation interventions/outcomes;
- checkpoints/resume;
- retention-probe scheduling;
- evidence provenance and idempotency.

But many richer signals are either:

- hidden inside free-form JSON rather than standardized;
- not validated against canonical vocabularies;
- not automatically collected by tutor orchestration;
- not projected into `status`/`resume`;
- or have no complete API lifecycle.

### 3. Very thin instantiated curriculum

The active `domains/dsa/sliding-window/` directory is still primarily a design skeleton. Its README names a planned `concept.yaml`, lessons, problems, and assessments, but those durable artifacts have not yet been instantiated.

Therefore the live tutor can preserve state while still improvising substantial portions of what is taught, in what sequence, and by which assessment. Persistent improvisation is not yet a curriculum.

## Existing durable model: what is already planned

### Capability vector

`docs/MEASUREMENT_MODEL.md` already identifies:

- recognition;
- mental model;
- state prediction;
- invariant reasoning;
- semantic procedure;
- pseudocode;
- implementation;
- debugging;
- transfer;
- retention;
- AI oversight.

This should remain the core philosophy. One global mastery percentage would discard important distinctions.

### Assistance

The durable model already separates correctness from assistance:

- A0 — none;
- A1 — task/goal reminder;
- A2 — small cue;
- A3 — structural/subgoal hint;
- A4 — partial representation/code scaffold;
- A5 — worked example;
- A6 — complete solution.

A supported success is not equivalent to an unaided success.

### Representation and intervention

The repository already distinguishes:

- representation family;
- representation version;
- learning operation;
- whether an intervention helped behaviorally;
- self-report versus behavioral evidence.

This is important: “ASCII tree helped” is not a fixed learning-style label. It is contextual evidence about one representation/intervention in one task state.

### Outcome windows

The intended model already separates:

- immediate performance;
- performance after assistance fading;
- changed-surface transfer;
- delayed retrieval.

### Learning-control architecture

`docs/LEARNING_CONTROL_MODEL.md` now defines:

```text
goal
  -> plan
  -> task / episode
  -> attempt
  -> test / assessment
  -> evidence
  -> capability state
  -> diagnosis / next action
  -> plan update
  -> transfer / delayed test
```

It also correctly says that first-class goal and unified study-plan schemas do **not** yet exist.

### Planned competency tracks

Current curriculum architecture names:

- T1 algorithmic foundations;
- T2 software and systems foundations;
- T3 system design and reliability;
- T4 AI systems/evaluation/reliability;
- T5 technical problem framing and diagnosis.

Only the DSA/Python/Sliding Window research slice is active under R0. The other tracks are curriculum architecture, not validated Study OS research findings.

## Gap matrix

| Dimension | Durable design | Live runtime | Current judgment |
|---|---|---|---|
| Attempt history | Experimental episode explicitly includes attempts/re-attempts | Attempt rows exist | **Partial** — no first-class attempt chain/attempt number |
| Assistance level | A0-A6 specified | String field exists | **Partial** — vocabulary not enforced; tutor must classify consistently |
| Hint history/dependency | Hint counts planned | Can be generic events/context | **Missing as standardized model** |
| Representation used | Strongly specified | Intervention/outcome tables exist | **Partial-to-strong** — not fully projected into checkpoint/resume |
| Representation effect | Immediate/faded/behavioral comparison planned | Outcome score can be recorded | **Partial** — contextual comparison/longitudinal summary missing |
| Interaction mode | Not clearly first-class | Could be free-form attempt context | **Missing** |
| Effort/productive struggle | Subjective effort planned | Could be generic event payload | **Partial design, missing standard runtime field** |
| Speed/fluency | Time-to-unaided success planned | Only created timestamps are guaranteed | **Missing standardized timing/active-time telemetry** |
| Error patterns | Misconceptions anticipated in Lesson IR | Generic payload/context can contain tags | **Missing first-class taxonomy + longitudinal projection** |
| Candidate-state/invariant quality | Explicit capability/state-model concept | Assessment can name capability | **Partial** — durable rubrics/items missing |
| Complexity reasoning progression | T1 includes complexity | No competency progression graph | **Planned broadly, not instantiated** |
| Course progression | Tracks and control model exist | No first-class goal/plan/competency graph | **Major gap** |
| Retention scheduling | Strongly planned | Schedule/get-next exist | **Partial** — probe completion/result lifecycle is incomplete |
| Transfer | Required by R0/P2 | Generic assessment/event possible | **Planned but not systematically instantiated** |
| Confidence/calibration | Self-report planned | Generic event possible | **Partial** — calibration against later behavior not derived |
| `do_not_reteach` | Checkpoint design requires it | Stored by checkpoint | **Not returned by current `resume()`** |
| Open hypotheses | Checkpoint schema includes them | No dedicated checkpoint persistence/projection | **Contract/runtime gap** |
| Representation history in resume | Checkpoint schema includes it | Intervention rows exist separately | **Contract/runtime projection gap** |
| Evidence-backed current state | Core invariant | Capability/assistance checkpoint works | **Implemented minimum** |

## Specific runtime gaps

### Attempt records need a stable telemetry contract

`record_attempt` currently has:

- `task_id`;
- `response`;
- `assistance_level`;
- free-form `context`;
- timestamp.

That is intentionally flexible, but without a versioned context contract two tutors can record the same learner behavior differently. Recommended standardized fields include:

- `task_version` / item version;
- `concept_ids` and `competency_ids`;
- `attempt_number`;
- `prior_attempt_id`;
- `interaction_mode`;
- `representation_ids_visible`;
- `assistance_level_before_attempt`;
- `hint_ids` and hint types seen before the answer;
- `feedback_exposure`;
- `started_at`, `submitted_at`, `latency_ms`, and optionally active-time estimate;
- `tools_allowed` / `tools_used`;
- deterministic test result refs;
- `error_tags` with provenance;
- confidence/effort/clarity/overload when explicitly reported.

Do not require a new SQL column for each of these in the first iteration. A versioned, validated attempt-context payload can prove the instrumentation before normalizing only the fields that need indexing/query performance.

### Assistance vocabulary should be enforced

The design has A0-A6, but the service accepts any non-empty assistance string. The service/API should eventually validate the canonical vocabulary plus a version field. Otherwise `small_hint`, `light_hint`, `cue`, and `A2` silently become four incompatible states.

### Hint dependency should become a derived feature

Final correctness alone hides an important learning trajectory:

```text
incorrect A0
-> A2 cue
-> incorrect
-> A3 structural hint
-> correct
-> later matched item correct A0
```

That trajectory carries more information than one `pass` row.

Derived signals can include:

- minimum assistance required for success;
- number/type of hints before success;
- repeated request for the same hint class;
- first later A0 success after supported success;
- regression back to assistance;
- success after hint fading on matched tasks.

### Fluency needs timing with caution

The design correctly says speed is not equivalent to learning. Still, repeated accurate A0 performance that becomes faster can be useful evidence of procedural fluency.

Track timing only alongside:

- correctness;
- assistance;
- task difficulty/version;
- interaction mode/device constraints;
- transfer/retention status.

Do not compare phone shorthand latency to full manual coding latency as if they are the same task.

### Interaction mode is missing

Study OS should distinguish evidence collected under materially different modes, for example:

- `manual_code_blank`;
- `manual_code_scaffolded`;
- `phone_shorthand`;
- `verbal_explanation`;
- `state_prediction`;
- `code_trace`;
- `code_reading`;
- `parsons_completion`;
- `debug_existing_code`;
- `ai_oversight_review`.

A correct verbal explanation and a correct blank implementation can support different capabilities without one invalidating the other.

### Error taxonomy should be empirical, not only prewritten

Useful categories may include:

- syntax/operator slip;
- language transfer/interference;
- value-vs-index confusion;
- mutation/aliasing misconception;
- loop-boundary/off-by-one;
- state initialization;
- incorrect update order;
- invariant violation;
- incorrect termination;
- return/control-flow placement;
- data-structure selection;
- complexity misconception;
- debugging-strategy failure.

But the system should preserve the original observed error and treat the tag as derived unless deterministic. Repeated patterns should emerge from evidence rather than forcing every mistake into a tutor-preferred taxonomy.

### Retention probe lifecycle is incomplete

The DB has probe `status` and `result_json`; the semantic API can schedule a probe and get the next scheduled probe. There is no canonical semantic operation that completes a scheduled probe and attaches its behavioral result.

Two reasonable v0.2 options:

1. add `retention_probe_id` to an assessment and atomically mark that probe completed; or
2. add a dedicated `record_retention_probe_result` semantic operation.

Option 1 keeps the semantic surface smaller and reuses assessments. Whichever is selected should prevent completed probes from remaining perpetually “scheduled.”

## Checkpoint/status projection gap

A checkpoint should be a compact learner-state projection, not an attempt log. The durable checkpoint design is richer than current live `status()`/`resume()` outputs.

A future contract revision should consider exposing:

- capability vector with evidence refs;
- current/last-successful assistance and next fade target;
- representation history summary;
- open hypotheses + confidence + supporting evidence;
- `do_not_reteach`;
- retention due / next scheduled probe;
- last meaningful assessment/progress timestamp;
- next high-information probe/action.

The fresh tutor should still avoid full transcript replay. Richer resume should mean **better projection**, not larger prompt history.

## Curriculum audit

### Existing Lesson IR is a good skeleton

The Lesson IR already supports:

- goal;
- prerequisites;
- trigger signals;
- deterministic state model;
- invariants;
- common misconceptions;
- L0-L10 difficulty targets;
- representations;
- assessments;
- transfer skills;
- source references.

The main missing work is instantiation and orchestration.

### Sliding Window content is not yet a durable course

The current directory documents a planned structure:

```text
concept.yaml
knowledge/
lessons/
  001-window-as-region/
  002-maintaining-validity/
  003-invariant-to-code/
problems/
assessments/
```

but those course artifacts are not yet present. A tutor can therefore jump ahead, skip prerequisites, repeat already-mastered material, or invent assessments whose difficulty is not comparable across sessions.

### T1 needs a competency/prerequisite map before more ad-hoc lessons

The active research slice can remain Sliding Window while the **curriculum architecture** becomes broader. A sensible T1 Python/algorithmic foundation map should cover, at minimum:

#### Python/program mechanics

- values, variables, primitive types, expressions, assignment;
- equality/comparison/boolean logic;
- conditionals;
- `for`/`while` iteration and loop control;
- functions, parameters, return values, scope;
- strings, lists, tuples, indexing and slicing;
- iteration with index/value (`range`, `enumerate`);
- sets and dictionaries/maps;
- mutability, references/aliasing, copying;
- exceptions/runtime errors;
- modules/library use;
- reading and tracing existing code;
- tests and systematic debugging.

#### Algorithmic primitives

- counters/accumulators;
- extrema and index/value tracking;
- running/prefix state;
- search and simple sorting;
- asymptotic time/space reasoning;
- recursion and call-stack reasoning.

#### DSA/problem families

- hash map/set lookup patterns;
- two pointers;
- sliding window;
- stack/queue/deque;
- linked-list fundamentals;
- tree representations and traversal/BST reasoning;
- heap/priority queue;
- graph representation, BFS/DFS, topological reasoning;
- recursion/backtracking;
- dynamic programming foundations;
- mixed recognition/transfer/debugging/AI-oversight tasks.

This is not a claim that every topic should be taught immediately or in a rigid order. The prerequisite graph should encode what evidence allows a topic to be introduced, skipped, revisited, or assessed.

### Every competency should have multiple task modes

A course should not infer competence from one kind of question. Where relevant, generate/version tasks across:

```text
observe
-> predict
-> explain
-> trace
-> reconstruct
-> Parsons/completion
-> semantic pseudocode
-> scaffolded code
-> blank implementation
-> debug
-> recognize from unfamiliar wording
-> transfer
-> delayed retrieval
```

This extends the existing L0-L10 ladder without replacing it.

### Problems and assessments need stable identities/versions

For longitudinal evidence, Study OS needs to know whether two attempts are actually comparable. Durable problem/assessment specs should eventually carry:

- item ID/version;
- concepts/knowledge components;
- intended capability;
- task mode;
- expected assistance condition;
- difficulty assumptions;
- deterministic oracle/tests where possible;
- scoring rubric;
- exposure status (teaching, practice, hidden transfer, delayed-retention pool);
- prerequisite requirements;
- source/provenance.

Do not expose hidden transfer answers to the tutor before use.

## Research evidence informing the design

### Retrieval and spacing

Distributed practice has a strong evidence base. A 2025 classroom meta-analysis of 22 reports / 31 effect sizes (>3,000 learners) found a moderate advantage for distributed over massed practice (`d = 0.54`). Retrieval-practice research likewise supports later retention and can support transfer for complex/rule-based learning.

Implication: delayed retrieval should be part of the control loop rather than an optional note in a checkpoint.

References:

- Mawson, R. D., & Kang, S. H. K. (2025). *The Distributed Practice Effect on Classroom Learning: A Meta-Analytic Review of Applied Research.* https://doi.org/10.3390/bs15060771
- Opitz, B., & Kubik, V. (2024). *Far transfer of retrieval-practice benefits: rule-based learning as the underlying mechanism.* https://doi.org/10.1186/s41235-024-00598-y

### Assistance, worked examples, and fading

Cognitive-load research supports high guidance for novices, followed by fading as knowledge grows. A 2025 meta-analysis of the expertise-reversal effect found low-prior-knowledge learners benefited from higher assistance while higher-prior-knowledge learners benefited from lower assistance.

Implication: Study OS should adapt assistance based on behavioral evidence and deliberately test whether support can be removed.

References:

- Sweller, J., van Merriënboer, J. J. G., & Paas, F. (2019). *Cognitive Architecture and Instructional Design: 20 Years Later.* https://doi.org/10.1007/s10648-019-09465-5
- *A cornerstone of adaptivity — A meta-analysis of the expertise reversal effect.* Learning and Instruction 98 (2025), 102142. https://doi.org/10.1016/j.learninstruc.2025.102142
- Koedinger, K. R., & Aleven, V. (2007). *Exploring the Assistance Dilemma in Experiments with Cognitive Tutors.* https://doi.org/10.1007/s10648-007-9049-0

### Programming should not be blank-code-only

Programming education research supports separating prerequisite skills such as reading/tracing, prediction, code completion/Parsons problems, writing, and debugging.

A multinational study found many novices weak at code tracing/completion, suggesting these can be prerequisite skills rather than merely easier versions of programming. A 2024 experiment found prediction-first activities can outperform a tell-and-practice production routine. The Parsons-problem literature explicitly motivates completion/reordering tasks because blank-page coding can overwhelm novices.

Implication: Study OS should record task mode and gather evidence across multiple modes before declaring implementation competence.

References:

- Lister, R. et al. (2004). *A multi-national study of reading and tracing skills in novice programmers.* https://doi.org/10.1145/1044550.1041673
- *Prediction versus production for teaching computer programming.* Learning and Instruction 91 (2024), 101871. https://doi.org/10.1016/j.learninstruc.2023.101871
- Ericson, B. J. et al. (2022). *Parsons Problems and Beyond: Systematic Literature Review and Empirical Study Designs.* https://doi.org/10.1145/3571785.3574127

### Process history matters in programming

A review of process-oriented novice-programming research found value in analyzing repeated submissions, compilation/error behavior, code evolution, debugging patterns, and programming-state trajectories rather than only final solutions.

Implication: attempt history, errors, timing, and transitions are legitimate learner evidence. However, low-level telemetry alone cannot reliably reveal learner intent, so observed logs must be paired with task context and cautious derived interpretation.

Reference:

- Villamor, M. M. (2020). *A review on process-oriented approaches for analyzing novice solutions to programming problems.* https://doi.org/10.1186/s41039-020-00130-y

### Metacognitive confidence is useful but fallible

Judgments of learning are susceptible to illusions and biases; perceived fluency or ease can diverge from later memory/performance.

Implication: record confidence/clarity, but evaluate calibration against later unaided, transfer, and delayed behavior instead of promoting self-report directly to mastery.

References:

- Yang, C. et al. (2021). *How to assess the contributions of processing fluency and beliefs to the formation of judgments of learning: methods and pitfalls.* https://doi.org/10.1007/s11409-020-09254-4
- Bjork, R. A., Dunlosky, J., & Kornell, N. (2013). *Self-Regulated Learning: Beliefs, Techniques, and Illusions.* https://doi.org/10.1146/annurev-psych-113011-143823

### Intelligent tutors can help, but pedagogy is the mechanism

A large meta-analysis (107 effect sizes, 14,321 participants) found intelligent tutoring systems outperformed several non-individualized comparison conditions on average, though such systems are heterogeneous and their systematic instructional design is part of the likely benefit.

Implication: adding an LLM/controller is not itself the learning intervention. Study OS should make its learner model, tasks, feedback, assistance, and evidence rules inspectable.

Reference:

- Ma, W., Adesope, O. O., Nesbit, J. C., & Liu, Q. (2014). *Intelligent Tutoring Systems and Learning Outcomes: A Meta-Analysis.* https://doi.org/10.1037/a0037123

### Do not jump to opaque knowledge tracing yet

Knowledge-tracing research offers Bayesian, performance-factor, and deep models, but explainability remains an active research issue. Study OS currently has sparse, heterogeneous N=1 evidence and unusually strong provenance requirements.

Implication: retain interpretable evidence-backed capability states and explicit features first. Consider BKT/PFA-like probabilistic models only after there are enough repeated, consistently tagged knowledge-component attempts to estimate them meaningfully. Do not introduce Deep Knowledge Tracing merely because it is more sophisticated.

Reference:

- Bai, Y. et al. (2024). *A Survey of Explainable Knowledge Tracing.* https://arxiv.org/abs/2403.07279

### Curriculum breadth benchmark

ACM/IEEE-CS/AAAI CS2023 emphasizes early competence in reading/writing programs, fundamental programming constructs, built-in data structures such as dictionaries/maps, testing/debugging, data structures, algorithms, and performance reasoning. It explicitly notes that generative AI does not eliminate the need for program-understanding foundations.

Implication: Study OS may keep Sliding Window as the active R0 experiment while still defining a durable T1 competency graph broad enough to prevent prerequisite gaps.

Reference:

- ACM/IEEE-CS/AAAI CS2023 Curricula Guidelines: https://csed.acm.org/wp-content/uploads/2023/09/Version-Gamma.pdf

## Recommended architecture: four learner-state layers

### Layer 1 — append-only learning telemetry

Record what actually happened:

- task/item/version;
- attempt chain;
- answer/code/state prediction;
- deterministic outcomes;
- assistance/hints;
- representations shown;
- interaction mode;
- timing;
- feedback/tools exposure;
- self-report;
- raw/derived error tags with provenance.

### Layer 2 — derived learner features

Compute cautious summaries from evidence:

- repeated error patterns;
- minimum assistance needed;
- hint dependency/fading trajectory;
- fluency trend under comparable tasks;
- confidence calibration;
- contextual representation effects;
- learning curve by competency;
- retention/retrieval history;
- current misconception hypotheses.

Derived features must remain revisable and evidence-linked.

### Layer 3 — current learner checkpoint

Project only the state necessary to resume effectively:

- evidence-backed capability vector;
- current/last successful assistance;
- next fade target;
- representation history summary;
- open hypotheses;
- do-not-reteach;
- current focus;
- next high-information action/probe;
- transfer/retention due state.

Do not turn the checkpoint into the full event log.

### Layer 4 — curriculum/control model

Maintain:

- learner goals;
- competency definitions/prerequisite DAG;
- versioned lesson/task/problem/assessment specs;
- active study plan;
- progression and exit criteria;
- hidden transfer pools;
- spacing/interleaving scheduler;
- deterministic adaptation policy initially.

This layer decides what evidence to collect next; it must not overwrite the evidence itself.

## Recommended P2 sequencing

### P2A — Instrumentation contract first

Goal: stop losing learning-process information while avoiding a premature giant schema migration.

Implement/version:

- standardized attempt context;
- standardized event payloads;
- controlled vocabularies for assistance and interaction mode;
- attempt-chain IDs;
- hint exposure;
- timing fields;
- representation exposure;
- error tags;
- competency/item IDs;
- tutor orchestration rules saying when each semantic write is mandatory.

Acceptance should demonstrate that a real learning exchange such as

```text
attempt 1 -> hint -> attempt 2 -> changed representation -> attempt 3 success
```

can be reconstructed from canonical Study OS records without reading the full transcript.

### P2B — Rich learner-state projection

Goal: make fresh-chat resume pedagogically useful, not merely technically continuous.

Revise the checkpoint/status/resume contract to expose the relevant compact state, including representation/hypothesis/retention/do-not-reteach data.

Also complete the retention-probe result lifecycle.

### P2C — Durable T1 curriculum skeleton

Goal: stop relying on tutor improvisation for sequence and assessment.

Create:

- competency/prerequisite graph;
- Python-foundation competencies;
- algorithmic primitive competencies;
- DSA family competencies;
- stable task-mode taxonomy;
- item/assessment spec schema if Lesson IR is insufficient;
- first real Sliding Window concept/lesson/problem/assessment artifacts.

This can happen without broadening the R0 research claim.

### P2D — Adaptive controller

Only after structured telemetry and curriculum exist, add deterministic rules for:

- next competency/task selection;
- remediation;
- hint fading/reintroduction;
- spacing/interleaving;
- transfer scheduling;
- confidence-calibration probes;
- stale-checkpoint detection/replanning.

### P2E — Statistical learner modeling later

Once enough repeated tagged evidence exists, evaluate whether interpretable statistical models add value over rule-based evidence states. Candidate approaches include BKT/PFA-like models. Opaque deep models should need a demonstrated incremental benefit and an explanation strategy.

## What should NOT be built yet

- a giant normalized table for every imaginable telemetry field before real instrumentation is tested;
- one global “mastery %”;
- fixed “visual/auditory learner” preferences;
- a deep knowledge-tracing model on sparse N=1 data;
- dozens of DSA lesson families before one complete audited trajectory works;
- adaptive recommendations whose decision evidence cannot be inspected;
- automatic promotion from conversational confidence to capability;
- curriculum changes that silently change the active R0 research claim.

## Immediate repository actions suggested by this audit

1. Treat PR #7 (`codex/p1-http-mcp-transport`) as the deployed P1 transport lineage; reconcile it with latest `main` before merge.
2. Retire/close duplicate PR #8 after checking whether any transport tests should be retained separately.
3. Update stale manifest/handoff phase text that still describes P0 as active.
4. Update Issue #5 P1 checkboxes only for continuity properties that have actually been demonstrated; do not infer untested service-restart/intervention conditions.
5. Create a P2 tracker whose first milestone is **instrumentation completeness**, not another infrastructure layer.
6. Author the first real durable Sliding Window course artifacts only after the competency/task telemetry contract is clear enough to measure them.

## Success criterion for the next learner-model milestone

A fresh tutor should be able to answer, from Study OS canonical state and without transcript replay:

> What is the learner trying to achieve; what have they actually demonstrated; under what assistance and task modes; what recurring errors or hypotheses remain; which representations have behavioral evidence of helping or not helping; what should not be retaught; and what is the next highest-information task, fade, transfer, or retention probe?

If the runtime cannot answer those questions, checkpoint persistence is working but the learner model is not yet sufficiently operational.
