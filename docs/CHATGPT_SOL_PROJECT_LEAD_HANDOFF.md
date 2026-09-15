# ChatGPT Sol project lead handoff

Status: **primary cross-chat strategic/research/evaluation handoff for the Study OS DSA model-tutoring project.**

Audience: the next ChatGPT **Sol** session acting as project/research/evaluation lead with the human project principal.

This document exists because the originating ChatGPT conversation became very long and slow. Do not require the human to reconstruct the project from chat history. Start here, verify the current repository state, then continue from durable evidence.

This handoff is intentionally more detailed than an ordinary engineering handoff. Local Luna has separate execution documents. Sol owns the cross-session research/product/evaluation thread; Local Luna implements and runs local experiments under durable direction.

---

## 0. Read order for a new Sol session

Before making a strategic claim or directing a new measured run:

1. Read this document completely.
2. Read `contracts/ai-session-ownership.v0.1.json`.
3. Verify current PR #77 head, draft state, exact-head CI/mutation status, and latest comments/artifacts.
4. Read `contracts/model-tutoring-agent-boundaries.v0.1.json` for measured-run and hidden-holdout isolation.
5. Read `docs/MODEL_TUTORING_LOCAL_AUTONOMOUS_LOOP_V1.md` if directing Local Luna.
6. Read `plugins/study-os-dsa-decomposer/skill.md` and `plugins/study-os-dsa-decomposer/checklist.md` before evaluating decomposition design.
7. Read `docs/MODEL_TUTORING_COMPLETION_DRIVEN_VNEXT.md` and `docs/MODEL_TUTORING_ROTATING_HOLDOUT_EVAL_V1.md` before changing acceptance/evaluation policy.
8. Read `domains/dsa/_knowledge/model-tutoring-evolution/` for FOSSIL-compatible institutional memory and rationale.
9. Read the latest learner-visible evidence before trusting aggregate acceptance summaries.

Never assume an exact SHA or CI state in this handoff is still current. Re-verify the live PR first.

---

# 1. Project leadership model

The durable role split is now explicit in `contracts/ai-session-ownership.v0.1.json`.

## Human project principal

The human user owns product intent and final human judgment. They are actively involved in important research/product decisions and, when useful, serve as the real learner in human-in-the-loop tutoring evaluation.

Do not make the human debug the tutor while acting as learner. During a measured human session, they should respond naturally, not repair Study OS.

## ChatGPT Sol project lead

Sol is the cross-session project/research/evaluation/architecture lead.

Sol should:

- synthesize evidence across runs;
- decide what a failure means at the system level;
- define/maintain evaluation strategy;
- protect against false-green acceptance;
- distinguish generic architecture failures from scenario-specific bugs;
- decide what should be durable in prompts, schemas, controller rules, skills, tests, and FOSSIL knowledge;
- write clear Local Luna implementation/evaluation missions;
- audit Luna results instead of accepting self-reported green status;
- preserve non-claims and uncertainty;
- use human learner evidence as a first-class signal;
- keep hidden holdouts isolated from engineering agents.

Sol should not pretend to execute local Luna work if the environment cannot do so. GitHub/repo work can be performed when tools allow it; local model runs are evidence returned from the user's machine.

## Local Luna engineering orchestrator

Local Luna is the local implementation/runner under Sol's durable direction.

Local Luna may autonomously:

- implement code/schema/test changes;
- add new prompt versions;
- run local public evaluation;
- preserve transcripts/traces/plans/ledgers;
- diagnose public or burned-case failures;
- iterate routine engineering fixes;
- resume long-running bounded loops.

Local Luna does **not** own the overall project success definition or research direction, and must not declare the architecture proven merely because its own metrics pass.

## Measured Luna actors

Measured decomposer/teacher/student roles are frozen-run actors, not project decision-makers. They cannot edit the candidate while measured.

## Terra / independent reviewer

Terra can be used as an independent critic for plans, traces, transcripts, or failure hypotheses. Terra is diagnostic only; it does not override deterministic acceptance or Sol/human strategy.

## Deterministic controller/validators

These own encoded invariants and legal progression, not pedagogical truth beyond what is encoded. A deterministic green result is necessary but not sufficient when learner-visible evidence disagrees.

## Hidden evaluator

The hidden evaluator is isolated and owns hidden oracle comparison only. It does not edit the candidate or reveal unburned raw cases to engineering.

---

# 2. Repository / project anchors

Repository:

`Pukujan/Study-os`

Primary PR:

`#77` — branch `codex/dsa-conversation-replay-harness`

Base:

`main`

Canonical tracking issue:

`#63` — deterministic learning controller / representation engine / operational improvement loop.

PR #77 is intentionally **draft**. Do not mark ready/merge based on current evidence alone.

The project is building learner-visible, model-driven DSA tutoring through the real Study OS path, not a hand-authored 14-problem lesson table.

---

# 3. Core product/research objective

The target is a generic tutoring system where Luna can receive a new DSA problem and, through strong inference, derive both:

1. the **algorithm structure**, and
2. the **learning structure required for a learner to derive that algorithm**.

The runtime then adapts to the learner's actual messages while deterministic machinery owns evidence/progression/completion constraints.

The desired high-level architecture is:

```text
raw problem
    ↓
Luna strong-inference decomposer
    ↓
ALGORITHM GRAPH
objects → state → invariant → transition/recurrence → termination → solution
    ↓
BACKWARD PREREQUISITE EXPANSION
    ↓
LEARNING GRAPH
primitive meaning
→ grounded vocabulary/symbol
→ relation/action
→ representation bridge
→ repeated transition/recursion
→ control flow
→ integration/code
    ↓
versioned TeachingPlan
    ↓
deterministic structural/semantic/vocabulary validation
    ↓
learner message
    ↓
Luna diagnosis + evidence-bound assessment
    ↓
deterministic controller authorizes one teaching operation
    ↓
Luna learner-visible generation
    ↓
generation validator
    ↓
learner
    ↺ until earned completion or explicit bounded failure
```

The strong model should spend reasoning on latent structure. The learner should receive small, comprehensible steps, not the model's internal chain of thought.

Persist structured conclusions, not hidden reasoning prose.

---

# 4. Historical evolution: why the project changed

This chronology matters. Do not regress to an older acceptance definition just because an old artifact is simpler.

## 4.1 Original 14 × 15 dual-Luna benchmark

The initial public DSA replay corpus contained 14 problems with 15 learner/teacher exchanges each:

1. Two Sum
2. Contains Duplicate
3. Best Time to Buy/Sell Stock
4. Valid Parentheses
5. Binary Search
6. Reverse Linked List
7. Merge Two Sorted Lists
8. Maximum Depth of Binary Tree
9. BFS Shortest Path
10. Number of Islands
11. Kth Largest Element
12. Sliding Window Maximum Sum
13. Merge Intervals
14. Valid Palindrome

The historical dual-Luna experiment produced 210 exchange pairs / 420 visible messages.

Artifacts include:

- `artifacts/dual-luna-dsa-transcript.jsonl`
- `artifacts/dual-luna-dsa-transcript.md`
- `datasets/dsa-conversation-replay.v0.1.json`
- `tools/run_dual_luna_local_codex.py`

The historical benchmark is now **regression/calibration evidence only**.

It is NOT the product success criterion.

## 4.2 Why fixed 15 turns failed

The initial 15-turn structure came from the benchmark/corpus shape, not from pedagogical truth.

Manual review showed a devastating false positive: Sliding Window could spend all 15 exchanges on the first concept, remain effectively stuck, and still satisfy the old structural acceptance checker because the checker verified schema/provenance/controller consistency but did not require actual plan completion.

This led to the core correction:

**turn count is a metric, not a success condition.**

Current tutoring must be completion-driven with a generous anti-loop ceiling, not exactly 15 turns.

Historical 14×15 should remain stable as differential/calibration data so old behavior can still be compared.

## 4.3 Contains Duplicate semantic failure

An earlier model tutoring run was structurally valid yet learner-visible semantics were wrong: the teacher treated `box` as a boolean duplicate result (`box = true`) rather than a set of previously seen values.

Correct intended meaning:

```text
box = values seen before current num
check num in box BEFORE adding num
if present → return true
otherwise add num
if exhausted → return false
```

This proved:

```text
schema-valid
+ progression-valid
+ evidence-valid
≠ semantic-valid
```

Semantic-role consistency became a deterministic concern.

## 4.4 Evidence-bound progression

A prior one-problem pilot incorrectly advanced using scripted corpus learner signals instead of the actual learner utterance.

The corrected controller principle is:

- assess only actual learner text;
- `demonstrated` requires evidence from the learner's message;
- evidence quote must be verbatim;
- controller progression follows demonstrated evidence, not hidden corpus labels;
- uncertainty/question form alone must not erase a semantically correct proposition.

## 4.5 The original Sliding Window transcript was much longer/richer than the 15-turn fixture

The human-calibrated Sliding Window work revealed dozens of conceptual/representation bridges, including array/index meanings, `k`, visible window/box, `S[i]`, recurrence, repeated recurrence, `enumerate`, append conversion, max tracking, control flow, boundaries, `range(k)`, inner accumulation, etc.

The lesson was not "Sliding Window needs a fixed number of turns." The lesson was:

**algorithm complexity and teaching complexity are not the same thing.**

A compact algorithmic relation can require a long learning dependency graph.

This drove the current decomposer design.

## 4.6 Correction/retry/verification policy

The historical calibrated learner evidence suggested that after a wrong answer, a single corrected retry is not necessarily sufficient.

Preferred generic shape:

```text
wrong / partial
→ targeted repair using stable representation
→ changed retry
→ independent verification
→ advance only when evidence supports the node
```

This should be implemented at the right granularity. If a concept node contains many obligations, a learner can demonstrate one clause while still missing the rest; this must not falsely advance the whole node.

## 4.7 Learner must not debug the tutor

The original long transcript included learner turns spent correcting/criticizing broken teacher representations.

Those are tutor failures, not desired pedagogical behavior.

The learner may:

- be wrong;
- be uncertain;
- need elaboration;
- need a changed representation;
- ask why;
- need repeated verification.

The learner should not need to:

- discover semantic misinformation;
- repair the lesson plan;
- tell the tutor which prerequisite it skipped;
- correct the algorithm for the tutor;
- police controller progression.

---

# 5. Representation and vocabulary decisions

## 5.1 Small-step decomposition should apply to all DSA families

Do not interpret the Sliding Window experience as an array-only special case.

Every problem should be decomposed aggressively into small dependencies.

Examples:

### Reverse Linked List

Core state transition:

```text
save next = curr.next
curr.next = prev
(prev, curr) → (curr, next)
```

Backward prerequisites include node/arrow meaning, `curr`, preserved successor, `prev`, reversed prefix, advance, and terminal return.

### Maximum Depth of Binary Tree

Core recurrence:

```text
depth(None) = 0
depth(node) = 1 + max(depth(node.left), depth(node.right))
```

Backward prerequisites include node/child meaning, empty child, returned subtree depth, `max`, and why current node contributes `+1`.

### BFS

Core state model can be expressed relationally/state-transition style:

```text
Q = nodes waiting to process
V = nodes already discovered
current = pop_front(Q)
for neighbor of current:
    if neighbor not in V:
        add neighbor to V
        add neighbor to Q
```

The reusable learner path is often:

```text
objects → state → invariant → transition → repetition/recursion → code
```

## 5.2 Algebra/symbolic/state-transition preference

The human learner has found grounded algebraic/symbolic/state-transition reasoning genuinely helpful.

Do not reduce this to "always start with algebra." Instead:

**Prefer compact relational/algebraic/state-transition representations when they simplify the problem, but ground every object/symbol first.**

Preferred pattern:

```text
ground object
→ ground symbol or simple term
→ show one relation/action
→ changed example
→ generalize
→ derive repeated transition/recursion
→ derive control flow
→ derive code
```

Avoid dumping a recurrence/formula before symbol meanings are stable.

## 5.3 Vocabulary contract

Vocabulary simplicity should be first-class.

Priority:

1. semantic accuracy;
2. learner comprehension;
3. brevity.

Useful pattern:

```text
simple grounded phrase
→ canonical term
→ stable future usage
```

Examples:

```text
"node with no children" → leaf
"line of nodes waiting their turn" → queue
visible arrow → next/reference relation
```

Do not oversimplify in ways that destroy an invariant. A queue is better grounded as a waiting line than a generic "box" because order matters.

Important failure categories include:

- `UNDEFINED_TERM`
- `SYNONYM_DRIFT`
- `TERM_OVERLOAD`
- `VOCABULARY_JUMP`
- `SYMBOL_BEFORE_MEANING`
- `FORMALISM_TOO_EARLY`
- `METAPHOR_BREAKS_INVARIANT`

---

# 6. Strong inference / decomposer design

The decomposer procedure should not start by inventing lesson stages.

It should:

1. solve the problem structurally;
2. identify primitive objects;
3. identify persistent state;
4. identify invariants;
5. identify transition/recurrence;
6. identify base/terminal condition;
7. identify solution derivation;
8. propose candidate representations;
9. work backward from every relation: "what must the learner already understand for this to make sense?";
10. recursively expand prerequisites;
11. reverse that dependency structure into a learning graph;
12. attach vocabulary/symbol grounding;
13. define evidence/completion conditions;
14. run an adversarial plan critic/checklist before measured tutoring.

Durable skill:

`plugins/study-os-dsa-decomposer/skill.md`

Checklist:

`plugins/study-os-dsa-decomposer/checklist.md`

Use the strongest available local reasoning for decomposition/critique. The output should be structured and inspectable; do not depend on exposed hidden chain of thought.

---

# 7. Prompt/schema philosophy

Prompt, schema, controller, and eval each have different jobs.

## Prompt / skill

Steer model inference and generation.

## Schema

Externalize claims so they are inspectable/versioned.

The long-term desired TeachingPlan representation includes algorithm graph, learning graph, variable roles, vocabulary/symbol grounding, representations, semantic invariants, completion evidence, terminal/base behavior, assistance/retry policies, and provenance.

## Deterministic code

Own the trust boundary:

- legal progression;
- evidence binding;
- variable-role consistency;
- semantic invariants;
- vocabulary/symbol grounding where enforceable;
- assistance limits;
- completion;
- anti-loop behavior;
- provenance;
- hidden-data isolation.

## Acceptance / review

Judge learner-visible quality and actual completion without leaking evaluator answers into teaching.

---

# 8. Prompt versioning

`src/study_os/prompt_registry.py` provides immutable content-addressed prompt versions/hashes.

Never silently change historical prompt semantics.

Material behavior changes should receive new versions, e.g.:

- `study-os.model-tutoring-decompose.v2`
- `study-os.model-tutoring-diagnose.v2`
- `study-os.model-tutoring-generate.v2`

Every measured artifact should bind prompt version/hash, model identifier, TeachingPlan schema, trace schema, run/candidate identity, and relevant skill/evaluation-policy version.

At the time of the September 15 transcript audit, measured qualification artifacts still referenced `decompose.v1` / TeachingPlan `v0.1`, which was a major reason **not** to call the new fine-grained decomposer proven even though the conversations were improving.

Re-verify whether newer versions have since been implemented before repeating this claim.

---

# 9. Public rotating evaluation and hidden holdout

## 9.1 Routine public iteration

Routine engineering evaluation should use 4 public problems selected after candidate freeze.

Desired properties:

- deterministic recorded seed;
- without-replacement shuffle-bag coverage;
- no immediate-repeat batch;
- structural-family diversity when possible;
- every problem completion-driven;
- batch fails if any problem fails;
- persistent global development rotation history separate from per-candidate qualification coverage.

Important: a previous qualification implementation repeatedly selected the same four after each candidate reset. That is an overfitting risk and was explicitly flagged in manual audit. Re-verify it has been fixed before trusting new rotating evidence.

## 9.2 Hidden promotion

Public rotation is not a hidden holdout.

Unburned hidden cases must live outside the public repo and outside engineering Luna's access.

The evaluator can inject the current hidden problem statement into a measured run because the measured decomposer/teacher need the problem. The oracle remains evaluator-only.

If a raw hidden case must be exposed to engineering to fix a failure:

```text
burn case
→ remove from future hidden eligibility
→ promote reviewed case into public regression
→ fix publicly
→ replenish private holdout bank
```

Do not let the main engineering Luna or prompt-fixing agents browse unburned hidden cases.

---

# 10. Latest major automated evidence before the human test

A qualification evidence commit was pushed as:

`3d5aca4` — "Add qualification epoch transcripts and ledgers"

The preserved epoch-10 merged transcript contained 75 exchanges over:

- Contains Duplicate — 18 exchanges
- Reverse Linked List — 15 exchanges
- Number of Islands — 12 exchanges
- Kth Largest — 30 exchanges

Learner-visible tutoring was materially better than the old 15-turn stall behavior. Errors, repairs, retries, visual/state explanations, and terminal behavior were present.

However manual Sol audit found important false-green risks.

## 10.1 Qualification rotation bug

The qualification loop repeatedly tested the same four scenarios across candidate epochs:

- Contains Duplicate
- Kth Largest
- Number of Islands
- Reverse Linked List

This meant per-candidate reset was also resetting development selection, undermining the intended anti-overfitting rotation.

The required design is:

- per-candidate qualification coverage may reset;
- global development shuffle-bag history must persist.

## 10.2 Generated plans were still coarse

Inspected plans remained around 4–5 macro concepts rather than the richer backward-expanded graph envisioned by the new decomposer design.

This suggested learner-visible conversations were improving partly through model improvisation within coarse nodes rather than because fine-grained reverse decomposition had been proven.

## 10.3 Number of Islands false advancement

The clearest new false positive:

The plan's `explore-component-with-stack` concept required marking, pushing, exploring valid neighbors, and continuing until stack exhaustion / full component coverage.

The learner only demonstrated:

> mark every newly discovered cell as `0` before pushing it onto the stack

The teacher then supplied the remaining exploration/completion behavior and the controller advanced the entire macro concept.

This is exactly the kind of false-green progression the project must prevent.

Likely generic resolution:

- finer dependency nodes, and/or
- evidence must entail all required obligations of a node before advancement.

Example decomposition:

```text
mark discovered cell
→ add to frontier
→ pop current cell
→ enumerate valid neighbors
→ discover/mark unseen land neighbor
→ repeat
→ stack empty means component complete
```

Then `mark-before-push` can complete one node without incorrectly certifying the whole DFS process.

## 10.4 Qualification ledger inconsistency

The preserved evidence included useful transcripts but the qualification receipt itself was not a clean terminal qualification artifact. At the audit point, ledgers remained `RUNNING`, epoch-10 public batch was recorded failed with runner exit 1 in one preserved ledger, and hidden promotion had not occurred.

Therefore do not treat the old epoch evidence as final reliability qualification.

## 10.5 Exact-head CI at that point

CI had become green on the evidence head. The remaining issues were evaluation/decomposition semantics, not basic type/CI breakage.

A PR #77 audit comment was written with these findings. If newer work claims these are fixed, verify exact code/artifacts rather than assuming.

---

# 11. Human-in-the-loop test: current immediate milestone

The project had gone too long without a real human learner review. The next immediate evaluation milestone is therefore a human-student session.

A thin human learner adapter was added to the repo:

`tools/run_model_tutoring_human_student.py`

Key principle:

**replace only the simulated student.**

Keep real Study OS behavior for:

- Luna decomposition;
- Luna diagnosis;
- Luna generation;
- local Study OS MCP routing;
- deterministic controller;
- generation validation;
- completion-driven stopping;
- transcript/trace/plan checkpointing.

The runner was added and then corrected so the human sees teacher text only after it has entered the validated accepted conversation. Rejected generation retries must not leak into the human surface.

The first recommended human problem is:

`bfs-shortest-path`

Reason: recent automated qualification had heavily exercised the same four non-BFS problems. BFS provides a different structural family and directly tests graph representation, queue/frontier vocabulary, visited state, and state-transition teaching.

Run locally:

```bash
git checkout codex/dsa-conversation-replay-harness
git pull --ff-only
python tools/run_model_tutoring_human_student.py --scenario bfs-shortest-path
```

Resume after interruption:

```bash
python tools/run_model_tutoring_human_student.py --scenario bfs-shortest-path --resume
```

Human-test artifacts:

- `artifacts/human-student-model-tutoring-transcript.md`
- `artifacts/human-student-model-tutoring-transcript.jsonl`
- `artifacts/human-student-model-tutoring-trace.jsonl`
- `artifacts/human-student-model-tutoring-plans.jsonl`

Before the learner finishes, do not show them the generated plan/trace/expected concepts. Keep the learner uncontaminated.

During the session the human should respond naturally:

- ask questions when confused;
- make natural mistakes;
- ask for elaboration;
- use symbolic/algebraic/state-transition language if it genuinely helps;
- not intentionally help the system pass;
- not intentionally act confused;
- not repair the tutor.

If something makes no sense, a natural statement like "I don't understand why that follows" is sufficient. Tutor recovery is part of what is being measured.

---

# 12. How Sol should review the human test

Do not reduce the result to `completion_candidate=true/false`.

Review four layers together:

```text
1. human subjective experience
2. learner-visible transcript
3. generated TeachingPlan
4. controller trace / evidence decisions
```

After the run, ask the human things like:

- Where did it first click?
- Where were you confused?
- Did anything feel repetitive?
- Did Study OS move on before you understood?
- Did it stay too long after you understood?
- Which representation/explanation helped most?
- Did any term/symbol appear before it had a clear meaning?
- Did the tutor say anything you thought was wrong?
- Did you ever feel you had to fix the tutor?
- At the end, could you derive/explain BFS without copying the tutor?

Then compare those reports to internal state.

Important mismatch classes:

- controller complete + human not understanding = **false positive**;
- human understanding + controller stuck/drilling = **false negative / overteaching**;
- human confusion caused by missing bridge = decomposition failure;
- human correcting tutor = tutor semantic/representation failure;
- teacher repeatedly rephrasing without new leverage = repair-loop failure;
- vocabulary appearing before meaning = vocabulary-contract failure.

Useful generic failure codes:

- `MISSING_PREREQUISITE`
- `CONCEPT_TOO_COARSE`
- `PREMATURE_ADVANCEMENT`
- `FALSE_COMPLETION`
- `OVERTEACHING`
- `VOCABULARY_JUMP`
- `SYMBOL_BEFORE_MEANING`
- `REPRESENTATION_INTERFERENCE`
- `SEMANTIC_TUTOR_ERROR`
- `DIAGNOSIS_FALSE_NEGATIVE`
- `DIAGNOSIS_FALSE_POSITIVE`
- `REPETITIVE_REPAIR_LOOP`
- `TERMINAL_BEHAVIOR_GAP`

Freeze the candidate for the measured human session. Preserve evidence first. Do not silently patch prompts/code mid-session and continue pretending it was one run.

---

# 13. What to do immediately after the first human BFS test

The next Sol session should:

1. verify the exact candidate SHA used for the human session;
2. fetch/read the human transcript, trace, and plan;
3. collect the human's subjective review before over-interpreting internals;
4. reconstruct every advancement decision and compare it to actual learner evidence;
5. inspect whether the generated decomposition was genuinely fine-grained or still macro-stage based;
6. inspect vocabulary grounding (`queue`, `FIFO`, `frontier`, `visited`, `neighbor`, `node`, `edge`, `distance`, etc.);
7. inspect whether compact symbolic/state-transition reasoning helped or was premature;
8. identify generic root causes only after the evidence is preserved;
9. write important findings durably into PR #77 / Issue #63 / FOSSIL pack as appropriate;
10. only then issue Local Luna a new implementation mission.

Do not immediately launch another large autonomous qualification loop before extracting the human signal.

---

# 14. Long-running reliability goal

The desired long-running objective is not "pass one four-problem batch."

A candidate can only become decomposition-reliability-qualified after a frozen candidate demonstrates broad reliability without editing between qualification batches, followed by hidden transfer evidence.

Conceptually:

```text
build candidate
→ repo/tests green
→ freeze candidate
→ rotating public batch 1
→ rotating public batch 2
→ ... broad public epoch
→ same candidate remains healthy
→ isolated hidden promotion batch
→ promotion verdict
```

Any prompt/code/schema/skill/evaluation-policy change creates a new candidate identity and resets that candidate's qualification evidence.

The development process can be resumable/bounded per invocation, but the durable project goal persists across invocations.

Do not run an uncontrolled infinite self-edit loop. Persist candidate/evidence/next-action state and resume safely.

---

# 15. Public dataset versus future SFT

The current process is **not supervised fine-tuning**.

It is eval-driven system optimization around a frozen foundation model:

```text
prompt + skill + schema + controller
→ model outputs
→ deterministic/public/human eval
→ diagnose
→ change prompt/skill/schema/controller
→ new version
→ reevaluate
```

Model weights are not being updated.

However the process is intentionally creating the kind of curated evidence that could later become an SFT dataset:

```text
problem
→ bad decomposition
→ failure diagnosis
→ corrected decomposition

learner message
→ bad diagnosis
→ corrected diagnosis

TeachingPlan
→ bad teacher response
→ corrected response
```

Do **not** rush into SFT while the target behavior is still being discovered. First stabilize the target contract and evaluator; otherwise fine-tuning risks teaching the model our current mistakes.

If SFT becomes a later phase, preserve separate train/tuning/public-regression/validation/true-hidden-test boundaries.

Even after fine-tuning, keep deterministic schema/controller/evidence/completion/provenance checks.

---

# 16. FOSSIL institutional memory

The architectural rationale is preserved in a FOSSIL Core-compatible pack:

`domains/dsa/_knowledge/model-tutoring-evolution/`

Stable pack ID previously established:

`pack_3b5bd2d571fd2238ff15e10a5502d3d7`

The pack records why:

- 14×15 was superseded;
- fixed turn counts are calibration, not product completion;
- semantic false greens matter;
- grounded algebra/state transitions are useful;
- vocabulary grounding matters;
- decomposition should use skill + checklist;
- rotating public evaluation and isolated hidden holdouts are separate;
- prompt versions must be immutable;
- learner should not debug the tutor.

When a new strategic decision materially changes project rationale, update institutional memory rather than relying only on a chat message.

---

# 17. Durable authority map

Use these documents for different layers of authority.

## Project/session ownership

`contracts/ai-session-ownership.v0.1.json`

Defines human ↔ Sol ↔ Local Luna ↔ measured-agent leadership and escalation.

## Measured agent / hidden data access

`contracts/model-tutoring-agent-boundaries.v0.1.json`

Defines engineering, decomposer, teacher, student, reviewer, and hidden evaluator access controls.

## Local engineering loop

`docs/MODEL_TUTORING_LOCAL_AUTONOMOUS_LOOP_V1.md`

Primary Local Luna orchestration handoff.

## Decomposer procedure

`plugins/study-os-dsa-decomposer/skill.md`

## Decomposer acceptance checklist

`plugins/study-os-dsa-decomposer/checklist.md`

## Completion-driven tutoring policy

`docs/MODEL_TUTORING_COMPLETION_DRIVEN_VNEXT.md`

## Rotating/hidden evaluation policy

`docs/MODEL_TUTORING_ROTATING_HOLDOUT_EVAL_V1.md`

## Strategic evolution / institutional memory

`domains/dsa/_knowledge/model-tutoring-evolution/`

## Current engineering/evidence discussion

PR #77 and Issue #63.

---

# 18. Non-claims the next Sol session must preserve

Unless newer evidence has explicitly superseded them, do not claim:

- the tutoring architecture is merge-ready;
- decomposition reliability is proven;
- a green deterministic checker alone proves learner understanding;
- the 14×15 historical dataset is the success criterion;
- the preserved epoch-10 75-exchange merge is final qualification;
- hidden holdout promotion has passed;
- the new fine-grained reverse-solution decomposer has been proven merely because the skill file exists;
- Local Luna can self-certify its own research success;
- the human test succeeded before reviewing the human learner evidence;
- a particular local run occurred unless an artifact/log/commit supports it.

---

# 19. Positive facts established so far

These are the major durable wins that should not be lost:

- generic all-DSA model tutoring path exists;
- model-generated plans exist for all 14 public problems;
- learner-visible teacher responses are generated through the Study OS path;
- prompt registry/hash/provenance exists;
- deterministic controller/evidence binding exists;
- completion-driven runner mode exists;
- learner-visible conversations became materially better than the original `needs_compilation`-dominated evidence;
- correction/retry and variable-length conversations are now represented in measured artifacts;
- local resumable orchestration/qualification infrastructure exists;
- public/hidden role boundary policy exists;
- FOSSIL-compatible institutional memory exists;
- DSA decomposer skill/checklist exist;
- human-student adapter exists;
- exact-head CI had become green around the latest evidence/human-runner work, but must be reverified on current head;
- the project is now explicitly restoring real human learner evaluation rather than relying only on simulated students.

---

# 20. What the next Sol should optimize for

The next phase is not primarily about adding more machinery.

Optimize for **truthful evidence about whether Study OS teaches a real learner well**.

The best next signal is the first human BFS session.

Then use that evidence to answer:

1. Is the generated decomposition actually small enough?
2. Does it work backward from a sound solution/state model?
3. Are vocabulary and symbols grounded before use?
4. Does the controller advance only when the learner demonstrated the full active obligation?
5. Does the tutor recover from natural confusion without learner repair?
6. Does the representation reduce cognitive load?
7. Does the tutor stop when understanding is genuinely earned rather than because a counter reached a threshold?
8. Is the same generic machinery plausible for arrays, linked lists, trees, graphs, heaps, recursion, grids, and future unseen algorithms?

Only after this human evidence should Sol decide the next decomposition/prompt/schema/controller iteration.

---

# 21. New Sol session startup checklist

A fresh ChatGPT Sol session should begin with this operational checklist:

```text
[ ] Read this handoff.
[ ] Read contracts/ai-session-ownership.v0.1.json.
[ ] Verify PR #77 current head/draft state.
[ ] Verify current exact-head CI + mutation status.
[ ] Read latest PR #77 / Issue #63 comments after this handoff.
[ ] Check whether human BFS artifacts now exist.
[ ] If they exist: review them before directing more autonomous runs.
[ ] If they do not exist: keep the human test as immediate milestone unless newer human direction changed priorities.
[ ] Re-check whether rotation bug / coarse-plan false advancement / prompt-schema version gaps have been fixed on the current head.
[ ] Preserve hidden holdout isolation.
[ ] Write major new decisions durably, then direct Local Luna with a concrete mission.
```

---

# 22. Communication style with the human principal

The user prefers direct execution and concrete evidence over architecture-only discussion.

Do not make them repeat information already available in repo/tools.

Do not ask unnecessary clarifying questions when the repo can answer them.

When Local Luna reports success, verify exact artifacts/head rather than simply agreeing.

When a failure is found, prefer creating a precise durable fix/handoff/test over merely narrating the failure.

The user is willing to make important product/research decisions interactively with Sol. Preserve that collaboration: Sol leads synthesis and proposes the next evidence-bearing move; the human provides product intent and real learner judgment.

---

# 23. Final orientation

The project has moved from:

```text
"Can Study OS produce 15 turns on 14 DSA problems?"
```

to:

```text
"Can a model-driven Study OS independently infer a sound algorithm model,
reverse it into a fine-grained learning graph,
teach a real learner through confusion using simple grounded representations,
and prove completion without the learner debugging the tutor?"
```

That is the actual research/product question.

Sol owns keeping the project pointed at that question.

Local Luna owns doing the local engineering and measured execution required to answer it.

The human principal owns whether the resulting learning experience is actually the product they want.
