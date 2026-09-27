# Luna B Implementation Handoff — Practical Mutation-Testing Course

## Mission

Implement and locally validate the existing experimental Study OS mutation-testing course on branch `codex/mutation-study-slice` (draft PR #72), then stop engineering and begin the learner-facing course.

This session is completely separate from PR #71. Another Luna session owns the production mutation-testing gate and PAM A work.

## Authority

Read these first and treat them as binding:

- `docs/MUTATION_STUDY_SLICE_PDD.md`
- `docs/MUTATION_STUDY_SLICE_SDD.md`
- `docs/MUTATION_STUDY_SLICE_TDD.md`
- `src/study_os/experimental/mutation_study.py`
- `tools/mutation_study_slice.py`
- `tests/test_mutation_study_slice.py`

This file clarifies the intended curriculum and local implementation workflow. If it conflicts with the PDD/SDD/TDD safety or persistence invariants, the PDD/SDD/TDD wins.

## Course intent

This is not a lecture course. Target pacing is approximately 75-80% practical work and 20-25% theory.

The learner should first encounter an intuitive systems failure, predict the consequence, inspect or execute the mutation/test, and only then receive the formal theory that explains what happened.

Canonical learning cycle:

```text
small product/system rule
  -> realistic failure
  -> deliberate code mutation
  -> learner predicts consequence
  -> run/inspect test
  -> strengthen test or classify survivor
  -> short theory extraction
  -> one transfer question
```

Do not front-load mutation-operator taxonomy, mutation-score mathematics, or research history.

## Course outcome

At the end of the slice, Subject 001 should be able to inspect an unfamiliar mutation-testing result and answer:

1. What product/system invariant changed?
2. Should the existing tests have detected it?
3. Is the survivor semantic, equivalent, or diagnostic/non-authority?
4. What behavioral test would kill a meaningful survivor?
5. Should the survivor block release?
6. Where is mutation testing useful around deterministic cloud/ML/LLM authority?

Completion of this slice is not durable mastery. It is immediate evidence from this lesson only.

## Seven practical labs

### Lab 1 — Cloud API rate limiter

System:
A multi-tenant API rejects requests at or above a quota.

Minimal implementation:

```python
def allow_request(count: int, limit: int) -> bool:
    return count < limit
```

Mutation:
`<` becomes `<=`.

Practical learner task:
Given tests for 9/10 and 11/10 but no test for 10/10, predict whether the mutant survives and identify the missing boundary case.

Theory only after the practical result:
- mutant;
- killed vs survived;
- code coverage vs oracle strength;
- boundary mutation.

Acceptance evidence:
Learner can explain why line coverage can be high while the test oracle remains weak.

### Lab 2 — Idempotent distributed job

System:
A cloud worker receives retryable requests. The same idempotency key must never execute the job twice.

Minimal implementation:

```python
if idempotency_key in completed_jobs:
    return completed_jobs[idempotency_key]
return execute_job()
```

Mutation:
Remove or invert the existing-job branch.

Practical learner task:
Design the strongest test: submit the same key twice and assert one execution and the same replayed result.

Theory after result:
- stateful/semantic mutants;
- retry behavior;
- why a low-count survivor can be more important than many cosmetic survivors;
- mutation testing as invariant testing.

Acceptance evidence:
Learner distinguishes a single-request happy-path test from an idempotency contract test.

### Lab 3 — Circuit breaker

System:
A downstream dependency is considered unhealthy after exactly three consecutive failures.

Minimal implementation:

```python
failures += 1
if failures >= 3:
    state = OPEN
```

Mutation:
`>= 3` becomes `> 3`.

Practical learner task:
Construct the exact event sequence that distinguishes original and mutant: three consecutive failures must open the breaker.

Theory after result:
- temporal/state-machine mutations;
- transition-boundary tests;
- state-machine oracle strength.

Acceptance evidence:
Learner identifies the event sequence that kills the threshold mutant.

### Lab 4 — Feature rollout gate

System:
A risky feature is available only to users who are beta members AND belong to tenant ACME.

Minimal implementation:

```python
return user.is_beta and user.tenant == "ACME"
```

Mutation:
`and` becomes `or`.

Practical learner task:
Identify the forbidden cohorts admitted by the mutant and design the truth-table-style behavioral tests.

Theory after result:
- boolean-operator mutation;
- negative tests;
- policy gates;
- blast-radius containment.

Acceptance evidence:
Learner tests beta+ACME, beta+other, nonbeta+ACME, and nonbeta+other rather than only the allowed cohort.

### Lab 5 — ML deployment gate

System:
A candidate ML model deploys only when recall is above the minimum AND false-positive rate is below the maximum.

Minimal implementation:

```python
if recall >= min_recall and false_positive_rate <= max_fpr:
    deploy(candidate)
```

Mutation:
`and` becomes `or`, or one comparison is weakened.

Practical learner task:
Create a candidate that passes one metric and fails the other, then show why it must not deploy.

Theory after result:
- mutation testing does not prove model intelligence or accuracy;
- mutation testing can validate deterministic ML infrastructure;
- evaluation thresholds, promotion policy, data/metric gates, serving controls.

Acceptance evidence:
Learner separates stochastic model quality from deterministic deployment authority.

### Lab 6 — LLM tool authorization

System:
An LLM can propose a privileged tool call, but execution requires BOTH permission and fresh approval.

Minimal implementation:

```python
if has_permission and approval_is_fresh:
    execute_tool_call()
```

Mutation:
`and` becomes `or`.

Practical learner task:
Construct the two forbidden states:
- permission=true, fresh approval=false;
- permission=false, fresh approval=true.
Both must reject.

Theory after result:
- mutation testing is strongest around deterministic AI trust boundaries;
- permissions, approvals, evidence gates, schemas, state transitions, persistence and provenance;
- mutation testing does not directly measure open-ended LLM reasoning quality.

Acceptance evidence:
Learner explains why a surviving authorization mutant is more consequential than a wording mutation.

### Lab 7 — Study OS capstone

System:
A learner response may change pedagogical state only when its `turn_id` matches the current expected turn.

Minimal invariant:

```python
if submitted_turn_id != expected_turn_id:
    reject_stale_turn()
```

Mutation:
Weaken, invert or bypass the freshness comparison.

Practical learner task:
Classify the survivor before being shown the answer, explain the product failure it can permit, and propose a behavioral test proving stale requests:
- fail closed;
- write no attempts/events;
- do not advance state.

Theory after result:
- semantic vs equivalent vs diagnostic survivor;
- mutation score is evidence, not a universal release threshold;
- equivalent-mutant problem;
- explicit survivor audit;
- release gates should target unresolved non-equivalent mutations in claimed critical invariants.

Acceptance evidence:
Learner can analyze an unfamiliar Study-OS-style authority mutant without relying on definition recall.

## Research and provenance references

These references establish the underlying mutation-testing technique and modern practice. The course itself remains a Study OS experimental curriculum and is not claimed to have been independently benchmarked.

1. Mutmut documentation
   https://mutmut.readthedocs.io/en/latest/
   Relevant practical workflow:
   - `mutmut run`
   - `mutmut browse`
   - targeted mutant/function reruns
   - applying mutants to disk
   - subtle operators such as `< -> <=`

2. Practical Mutation Testing at Scale: A View from Google
   IEEE Transactions on Software Engineering, 2021.
   https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/
   Key relevance:
   - mutation testing as test-suite adequacy;
   - incremental mutation on changed code;
   - filtering low-value mutants;
   - empirical use across 24,000+ developers and 1,000+ projects.

3. State of Mutation Testing at Google
   https://research.google/pubs/state-of-mutation-testing-at-google/
   Key relevance:
   - industrial code-review integration;
   - scalability limitations of brute-force mutation;
   - selecting actionable mutants.

4. An Industrial Application of Mutation Testing: Lessons, Challenges, and Research Directions
   https://research.google/pubs/an-industrial-application-of-mutation-testing-lessons-challenges-and-research-directions/
   Key relevance:
   - equivalent, redundant and uninteresting mutants;
   - mutation adequacy is not always practical or desirable;
   - industrial costs/benefits.

5. Mutation Testing Advances: An Analysis and Survey
   Advances in Computers 112 (2019).
   DOI: 10.1016/bs.adcom.2018.03.015
   https://www.sciencedirect.com/science/article/pii/S0065245818300305
   Key relevance:
   - mature research survey;
   - mutation operators;
   - equivalent-mutant problem;
   - empirical methodology and threats to validity.

6. Defects4J
   https://defects4j.org/
   Key relevance:
   - reproducible corpus of real software faults;
   - controlled empirical software-testing experiments;
   - explicit environment/reproducibility constraints.

The learner does not need to read these before the labs. Luna may surface a brief provenance note after a lab when useful.

## Local implementation constraints

Keep this experiment isolated:

- branch: `codex/mutation-study-slice`;
- draft PR: #72;
- never modify PR #71 from this session;
- dedicated SQLite DB;
- no production Study OS migration for v0;
- no production MCP contract expansion for v0 unless the existing CLI design is proven insufficient by a failing acceptance test;
- no LLM self-grading.

Recommended DB:

`~/.local/share/study-os/mutation-study.sqlite`

## Deterministic authority boundary

Luna owns:

- conversational explanation;
- examples;
- Socratic questioning;
- diagrams/charts;
- pacing within a canonical lab;
- asking the canonical probe.

The adapter owns:

- current canonical node;
- legal final answers;
- correctness;
- advancement;
- attempt persistence;
- assistance level;
- completion;
- status reconstruction.

Luna must never write or infer canonical progress without an adapter call.

## Assistance semantics

Record the lowest level actually used before the learner's final answer:

- A0 — no assistance;
- A1 — task/goal reminder;
- A2 — small cue;
- A3 — structural/subgoal hint;
- A4 — partial representation/scaffold.

Do not record an assisted answer as A0.

## Required implementation work

The current experimental adapter may still contain the earlier abstract five-node lesson. Update it so the canonical lesson graph reflects the seven practical labs above.

Requirements:

- version the new graph as a new lesson revision (do not silently reuse mutation-testing.v0 if semantics change);
- keep answer keys deterministic;
- expose enough structured lab content in each turn for Luna to render the scenario without inventing the canonical rule;
- after a correct response, return a short `theory_after` field;
- incorrect answers return corrective guidance but no theory dump and no advance;
- status exposes all seven labs in canonical order;
- preserve existing SQLite evidence semantics or migrate only this dedicated experimental DB if required;
- tests must assert the actual seven-node graph, not merely a count.

## Required validation

### Dedicated contract suite

Run:

```bash
PYTHONPATH=src python -m unittest tests.test_mutation_study_slice -v
```

Tests must prove:

1. first node is the cloud rate-limiter lab;
2. incorrect legal answer persists and does not advance;
3. invalid answer writes no evidence;
4. correct answer advances exactly one node;
5. assistance A0-A4 is validated and persisted;
6. separate operations reconstruct state from SQLite;
7. the seven labs occur in the documented order;
8. theory is not returned for an incorrect answer;
9. theory is returned only after correct completion of a lab;
10. all seven correct answers complete the run;
11. completed run rejects further responses.

### Relevant repo validation

Run the normal checks needed for touched files, at minimum:

```bash
python -m compileall src/study_os/experimental tools/mutation_study_slice.py tests/test_mutation_study_slice.py
python -m ruff check src/study_os/experimental tools/mutation_study_slice.py tests/test_mutation_study_slice.py
python -m pyright src/study_os/experimental
```

If repository CI expects more, run the repository's standard CI-equivalent suite as practical.

### Separate-process SQLite smoke

Use a fresh DB.

Process 1:
```bash
python tools/mutation_study_slice.py start --db ~/.local/share/study-os/mutation-study.sqlite --subject-id subject-001
```

Capture `run_id`.

Process 2:
```bash
python tools/mutation_study_slice.py next --db ~/.local/share/study-os/mutation-study.sqlite --run-id RUN_ID
```

Process 3:
submit one legal incorrect answer to Lab 1.

Process 4:
query status and prove:
- attempt=1;
- mastered=false;
- current lab unchanged.

Process 5:
submit the correct Lab 1 answer.

Process 6:
query next/status and prove:
- Lab 1 mastered;
- Lab 2 current;
- attempt history preserved.

Terminate/restart shell/process context and repeat `next` / `status` using the same DB and run ID.

### Learner-facing orchestration smoke

Simulate:

```text
start
 -> rate limiter scenario
 -> learner predicts wrong
 -> adapter rejects advance
 -> Luna gives small practical cue
 -> learner predicts correctly
 -> adapter advances
 -> Luna gives short theory extraction
 -> idempotency lab appears
 -> process restart
 -> resume idempotency lab
```

No answer key may be disclosed before final learner response.

## READY TO STUDY gate

Do not tell the user the course is ready until ALL are true:

- seven-lab practical graph implemented;
- PDD/SDD/TDD remain satisfied;
- dedicated tests green;
- lint/type checks green;
- separate-process SQLite smoke green;
- restart/resume green;
- learner-facing orchestration smoke green;
- no production Study OS DB used;
- PR #71 untouched;
- exact commit SHA recorded.

Then STOP ENGINEERING.

Do not generalize the framework, add a frontend, add FSRS, add free-text grading, or expand the course.

Report exactly:

```text
READY TO STUDY

Branch:
Commit:
Dedicated tests:
Lint/type:
SQLite separate-process smoke:
Restart/resume:
Learner orchestration smoke:
Database path:
Run ID:
First lab: Cloud API rate limiter
```

Then immediately begin Lab 1 with Subject 001.

## Non-goals

- finishing PR #71;
- proving mutation testing is universally superior;
- achieving a particular mutation score;
- testing open-ended LLM intelligence;
- designing a general curriculum compiler;
- claiming durable mastery from this one session.
