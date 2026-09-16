# MT-E001 — Sol calibration-artifact transfer to Two Sum

**Status:** proposed  
**Owner/tracker:** Issue #63 / PR #77 context  
**Primary question:** Can a fresh Sol tutoring session transfer the pedagogical/decomposition method extracted from the successful Sliding Window calibration to a different DSA problem without reading the raw Sliding Window transcript?

## Why run this experiment

The current system has accumulated several prompt/schema/controller attempts, but learner-facing quality has remained difficult to judge automatically. The September 4 Sliding Window session is qualitatively different: decomposition was refined interactively until the learner could follow a long chain of small bridges.

Before trying to make Luna cheaper/better, first test whether that successful method can be distilled into a durable artifact that another strong Sol session can actually use on a different problem.

This experiment is intentionally **human-review first**. The primary output is not an aggregate score. It is the complete rendered teaching interaction so the product owner can inspect every explanation, state/chart, transition, learner response, and decomposition decision from top to bottom.

## Experimental sequence

```text
September-4 Sliding Window source evidence
        ↓
reviewed durable calibration artifact v0.1
        ↓
freeze artifact hash/version
        ↓
NEW ISOLATED SOL TEACHER SESSION
        +
Two Sum problem only
        ↓
Sol produces a decomposition/teaching plan
        ↓
Sol teaches a frozen synthetic learner
        ↕
until earned completion or anti-loop failure
        ↓
persist plan + transcript + trace
        ↓
render self-contained HTML review page
        ↓
owner reviews every exchange + diagrams/charts
        ↓
export checkbox/comments as TSV/JSON
        ↓
classify defects
        ↓
change ONE relevant artifact/runner/prompt dimension
        ↓
MT-E001 iteration N+1
```

## Phase A — durable calibration artifact

Create a reviewed public-safe artifact derived from the Sliding Window calibration. The raw transcript remains source evidence and is not passed to the measured Sol teacher.

Proposed durable paths:

```text
calibration/cases/sliding-window.subject-001.2026-09-04/
    transfer-calibration.v0.1.json
    transfer-calibration.v0.1.md
```

The JSON is the measured model input. The Markdown is a human-readable rendering of the same semantic content.

The artifact should capture only reusable, reviewed calibration knowledge, with provenance back to the existing calibration source. Minimum sections:

1. `identity`
   - stable calibration ID;
   - artifact version;
   - source calibration/session ID;
   - review status;
   - content hash/provenance.

2. `successful_learning_trajectory`
   - the preserved fine-grained Sliding Window dependency sequence;
   - each bridge's pedagogical purpose;
   - no claim that the sequence is universally required.

3. `decomposition_principles`
   - expose learner-sized prerequisite bridges rather than expert-sized algorithm stages;
   - introduce one semantic relation/action at a time when possible;
   - ground object/term/symbol before using it in a relation;
   - concrete state/action before abstraction/control flow/code;
   - preserve useful representations across neighboring nodes;
   - treat learner confusion as possible missing prerequisite/representation evidence rather than automatically requesting more prose.

4. `interaction_policy`
   - introduce/probe;
   - correct in the same grounded representation when wrong;
   - changed retry;
   - verify recovery when instability is observed;
   - advance only when the current bridge has adequate evidence;
   - partial-success isolation rather than re-teaching already-demonstrated suboperations.

5. `representation_policy`
   - stable representation lineage;
   - answer-reveal policy;
   - avoid accidental value/index collisions;
   - preserve scaffolding until the dependent relation is stable;
   - code should map back to already-grounded semantics.

6. `anti_overfit_constraints`
   - do not copy Sliding Window vocabulary/content into unrelated algorithms;
   - `box`, `S[i]`, `range(k)`, etc. are examples, not universal stages;
   - infer the new problem's own objects/state/relations;
   - the calibration target is decomposition granularity/control behavior.

7. `known_failure_patterns`
   - large conceptual jumps;
   - prompt-only paraphrase loops;
   - structurally valid but semantically wrong explanations;
   - premature code/technical terminology;
   - repeated confirmation without information gain;
   - plan completion inferred from turn count;
   - learner required to repair tutor errors.

### Isolation requirement

The measured Sol teacher MUST NOT receive:

- the eight raw Sliding Window transcript parts;
- the existing Two Sum regression turn script/expected assertions;
- hidden evaluator answers;
- prior MT-E001 transcripts/reviewer comments unless the iteration explicitly declares them as a changed input.

It receives only:

- the frozen transfer-calibration artifact;
- the public Two Sum problem statement/declared variables needed by the experiment;
- its role/runner contract;
- the visible conversation accumulated in the current run.

This is how we test whether the durable artifact actually carries the useful method.

## Phase B — freeze the synthetic learner

The student is an experimental instrument. Keep it fixed while comparing teacher/artifact iterations.

Initial proposal:

- teacher model: `gpt-5.6-sol`;
- student model: `gpt-5.6-luna` or another explicitly pinned cheaper model;
- fresh independent model session per role;
- student receives no calibration artifact, teaching plan, hidden solution, or evaluator rubric;
- student receives the problem and visible conversation only;
- student contract is versioned and unchanged across MT-E001 iterations unless the student itself is the variable being tested.

Student behavioral contract:

- realistic beginner rather than adversarial benchmark bot;
- answer only from the visible teaching/context plus ordinary beginner knowledge;
- may be wrong, partial, uncertain, or ask `why` / request a smaller step;
- do not magically infer skipped prerequisites;
- do not identify/fix tutor defects on the tutor's behalf;
- do not jump to a complete known solution before it has been earned;
- concise human-like replies;
- when asked to perform one operation, actually attempt that operation.

The exact student prompt/model/hash must be persisted with every run.

## Phase C — Two Sum transfer run

First target problem:

> Given `nums` and `target`, return indices of two numbers whose sum is `target`.

The teacher must derive its own learner-resolution dependency graph from the durable calibration artifact. Do not pre-seed the old regression corpus's five stages (`anchor`, `needed`, `box`, `order`, `loop`) as the expected answer.

Those historical stages may be used **afterward** as secondary comparison evidence, but not as teacher-visible decomposition instructions.

### Turn count

No fixed success length.

Run until:

- the teaching plan's required nodes/bridges and integration evidence are completed; or
- the anti-loop ceiling is exhausted; or
- a hard semantic/runner failure stops the experiment.

Initial anti-loop ceiling: 150 learner/teacher exchanges. This is a safety cap, not an expected lesson length.

## Phase D — durable run outputs

Each iteration gets an immutable directory, for example:

```text
artifacts/model-tutoring-experiments/MT-E001/run-001/
    run-manifest.json
    calibration-input.json
    teaching-plan.json
    transcript.jsonl
    trace.jsonl
    review.html
    review-template.tsv
```

Do not overwrite a previous run. `run-002` must point to `run-001` and describe the exact changed variable(s).

### `run-manifest.json`

Persist at least:

- experiment ID and iteration;
- exact repository commit;
- calibration artifact path/version/hash;
- teacher model/prompt/version/hash;
- student model/prompt/version/hash;
- runner version/hash;
- problem identity/text;
- anti-loop ceiling;
- start/end status;
- completion/failure reason;
- output file hashes when practical.

## Phase E — HTML is the primary human review surface

`review.html` should be self-contained and viewable locally in a browser without a server.

Requirements:

### Full-session reading

Top of page:

- experiment/run identity;
- exact problem statement;
- teacher/student model IDs;
- calibration artifact version/hash;
- completion status and exchange count;
- collapsible generated teaching/dependency plan.

Then render **every accepted exchange in chronological order**.

For each exchange show:

```text
Exchange N
active concept / bridge (if available)
controller/operation metadata (collapsed by default)

STUDENT
<exact visible student message>

TEACHER
<exact visible teacher message>

REVIEW
[ ] teacher weak
[ ] student weak / unrealistic
[ ] missing bridge
[ ] step too large
[ ] bad representation
[ ] diagram/chart weak
[ ] unnecessary repetition / stuck
[ ] semantic error
[ ] premature abstraction/code
[ ] answer leak
[ ] progression/assessment wrong
[ ] other

comment: [........................................]
```

### Diagram fidelity

Learner-visible teacher/student text must preserve whitespace exactly enough to inspect ASCII diagrams, boxes, index rows, pointer traces, queue states, and code blocks.

Use a monospace/preformatted renderer for message bodies by default rather than Markdown normalization that may collapse spacing.

The review page should make it easy to compare whether Sol produces grounded diagrams/state charts analogous in *clarity* to the successful Sliding Window interaction without forcing identical visual content.

### Review persistence/export

Checkbox/comment edits should persist locally in the browser when practical (for example `localStorage` keyed by run ID), with buttons to:

- export reviewer annotations as TSV;
- export reviewer annotations as JSON;
- clear local review state only with an explicit action.

The exported TSV should contain one row per exchange and retain exact exchange ID/concept plus the checkbox columns and free-text comment.

No reviewer annotation should mutate the original transcript/trace files.

## Phase F — review questions

Primary human review is qualitative and turn-local, but the run-level questions are:

1. Did Sol discover a learner-sized dependency graph rather than five expert-sized stages?
2. Did each new concept follow from already-grounded concepts?
3. Could the learner understand why each new variable/object existed before using it?
4. Did examples/diagrams make state and action visible?
5. Did the representation stay stable long enough to be useful?
6. Were errors corrected at the smallest failed relation?
7. Did retries use changed examples instead of paraphrasing the same prompt?
8. Did Sol avoid premature solution/code leakage?
9. Did the lesson eventually integrate the pieces into a correct Two Sum solution?
10. Did the synthetic learner behave plausibly enough that tutor quality could be judged?
11. Where did the owner feel substantially more friction than in the calibrated Sliding Window session?

## Phase G — iteration policy

After owner review, classify each flagged exchange by likely source:

```text
CALIBRATION_ARTIFACT
DECOMPOSITION
TEACHER_REALIZATION
REPRESENTATION
DIAGNOSIS/PROGRESSION
SYNTHETIC_STUDENT
RUNNER/RENDERER
UNKNOWN
```

Then change the smallest relevant surface.

Examples:

- missing prerequisite across several turns → revise calibration artifact/decomposer instruction;
- plan is good but explanation is dense → teacher realization contract;
- ASCII chart loses spacing → renderer only, do not change pedagogy;
- student suddenly knows hash-map solution → student contract;
- correct learner answer classified wrong → diagnosis/progression logic.

Each iteration records:

- predecessor run;
- owner annotations used;
- hypothesis for the change;
- exact files/prompts/artifacts changed;
- whether previous defects disappeared;
- any new regressions.

## Acceptance for this experiment

MT-E001 is not considered successful because the code ran or Two Sum was eventually solved.

A useful first success requires all of the following:

- a durable reviewed Sliding Window transfer-calibration artifact exists;
- the measured Sol session did not read the raw Sliding Window transcript;
- the Sol plan/lesson was generated for Two Sum rather than hard-coded from the existing Two Sum regression stages;
- the run reached integrated completion before the anti-loop ceiling;
- the complete interaction is inspectable in the self-contained HTML renderer;
- the owner completed turn-level review;
- no unresolved severe semantic error, answer leak, learner-must-fix-tutor event, or persistent stuck loop remains;
- the owner judges the decomposition/teaching sufficiently clear to justify testing the same artifact on another structurally different problem.

This is **subjective product-calibration evidence plus objective trace/provenance**, not proof of general learning effectiveness.

## Out of scope until MT-E001 is useful

- Luna teacher distillation/calibration;
- fine-tuning;
- large public qualification batches;
- automatic scoring replacing owner review;
- claiming the extracted pedagogy generalizes across learners;
- modifying the raw Sliding Window evidence;
- promoting the transfer artifact to runtime authority.

## Next experiment if MT-E001 works

Run the same frozen artifact/reviewer workflow on a structurally different problem such as Reverse Linked List, BFS, or recursive tree depth. Accumulate reviewed Sol-quality transfer cases first. Only then run matched Luna teacher experiments under the same artifact, student, renderer, and review schema to determine what quality gap remains and whether cheaper Luna tutoring can inherit the calibration.
