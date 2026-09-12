# PR #77 Truthful Replay Recovery Plan

Status: **ACTIVE / execution authority for PR #77**

Last updated: 2026-09-12

PR: #77 — `codex/dsa-conversation-replay-harness`

## Purpose

Fix the learner-visible Study OS tutoring path by making the replay gate measure the real product truthfully.

This plan exists to prevent another architecture-first detour. Until the acceptance gates below pass, work on PR #77 must be justified by a specific learner-visible replay failure.

The product question is:

> Given a realistic learner message, does Luna use Study OS correctly, does Study OS choose the correct deterministic state transition, and does the learner finally see exactly the authorized pedagogical response with the calibrated representation and pacing?

If a change does not make that question more directly testable or fix a demonstrated failure in that path, it is out of scope for this recovery.

## Current known defects in PR #77

The existing replay is not yet a trustworthy product test for three reasons.

### 1. The adapter measures backend text, not Luna's final learner-visible answer

`tools/replay_opencode_adapter.py` currently stops once it sees a Study OS tool result, aborts the OpenCode/Luna session, and returns the backend `learner_visible_markdown` as the assistant response.

That proves only that Study OS returned text. It cannot detect whether Luna would subsequently:

- paraphrase the authorized turn;
- add extra explanation;
- rename variables;
- add a parallel curriculum;
- leak future concepts;
- drop or rewrite the visual;
- otherwise change what the learner actually sees.

The truthful replay must allow Luna to finish normally and capture the final assistant-visible text separately from the backend-authorized text.

### 2. The corpus leaks the expected stage to the actor

`tools/replay_dsa_conversations.py` sends the corpus `turn["stage"]` to the actor, and the adapter includes it in Luna's prompt as `Current stage`.

That value is part of the grader's expectation, not product state. It must never be supplied to the actor.

The actor may receive the actual backend state returned by Study OS. The expected pedagogical stage remains private to the grader.

### 3. The live replay advances a scripted screenplay instead of following actual controller state

The current runner sends corpus turn 0, 1, 2, 3, ... regardless of whether the Study OS controller advanced.

This makes valid controller behavior look like failure. For example, if a learner asks clarifying questions but never answers the current probe, the deterministic controller should remain on that probe. The simulator must not then jump to learner dialogue that assumes the next concept was introduced.

The live learner simulator must choose its next message from the **actual backend step**, not from a predeclared linear stage sequence.

## Non-negotiable recovery constraints

1. **No new tutoring architecture until the truthful replay passes for Two Sum and Sliding Window.**
2. **No new prerequisite engine, generalized DSA compiler, diagnosis subsystem, persistence layer, or controller abstraction may be added to solve a replay failure unless the failure proves it is required.**
3. **The model actor never receives the grading rubric, expected stage, forbidden-term list, or hidden pass conditions.**
4. **Backend-authorized output and Luna-final output are captured as separate evidence.**
5. **The deterministic controller owns state progression. The learner simulator reacts to controller state; it does not dictate it.**
6. **Every failing live turn must identify one primary failure class before code is changed.**
7. **Fix the first trustworthy learner-visible failure before broadening scope.**
8. **Do not claim 10+ problem / 150+ live-turn coverage until those turns actually execute through known canonical Study OS problem assets and Luna finishes each learner-visible response.**
9. **Keep PR #77 draft until the acceptance gates in this document are satisfied.**
10. **A green harness test is not evidence of tutoring quality unless it captures the actual final learner-visible model response.**

## Target evidence model

For every live learner turn, preserve these distinct fields:

```text
learner_message
actual_backend_step_before
luna_selected_action
backend_authorized_text
actual_backend_step_after
luna_final_visible_text
routing_violations
authority_violations
pedagogy_violations
```

Do not collapse backend output and model-visible output into one `assistant_message` field internally. Reports may provide a compatibility field, but the evidence must remain separable.

## Required end-to-end flow

```text
realistic learner message
        ↓
Luna receives only product-visible context + actual backend state
        ↓
Luna selects one allowed Study OS semantic action
        ↓
Study OS MCP/controller evaluates learner response
        ↓
Study OS returns authorized TeachingTurn
        ↓
Luna completes normally
        ↓
capture FINAL Luna learner-visible text
        ↓
compare final text with backend-authorized text
        ↓
grade authorized content against pedagogical contract
        ↓
read actual backend state
        ↓
select next learner behavior for that actual state
```

## Execution plan

### Phase 0 — Freeze scope

Before changing behavior:

- keep PR #77 draft;
- do not add more canonical DSA assets;
- do not add more controller abstractions;
- do not reinterpret the current 3/15 replay result as product evidence;
- retain the current artifact only as historical evidence that exposed the replay-design problem.

Exit condition: this recovery plan is committed and referenced from `docs/HANDOFF.md`.

### Phase 1 — Make the OpenCode/Luna adapter capture the real final response

Primary file: `tools/replay_opencode_adapter.py`

Required changes:

1. Replace `_wait_for_backend_text()` with completion-oriented collection.
2. Do not abort the Luna session immediately after the Study OS tool result appears.
3. Poll until the assistant message is complete according to the OpenCode session/message state available from the local API.
4. Extract and retain:
   - Study OS tool name/action;
   - Study OS backend output;
   - `learner_visible_markdown`;
   - final assistant text emitted by Luna.
5. Return a structured JSON object from the adapter, for example:

```json
{
  "assistant_message": "<final Luna text>",
  "backend_message": "<authorized Study OS markdown>",
  "backend_step_before": "...",
  "backend_step_after": "...",
  "tool_used": "submit_problem_response"
}
```

6. Preserve exact whitespace in both learner-visible strings where possible.
7. If Luna never produces final visible text, report a replay infrastructure failure; do not substitute backend text and call it a model pass.

Required tests:

- adapter does not abort merely because a tool result exists;
- backend and final assistant strings are captured separately;
- extra Luna text after a tool response is detectable;
- missing final Luna text fails closed;
- tool validation errors remain visible as routing/infrastructure evidence rather than silently converted to a pass.

Exit gate:

> A test double that returns backend text `A` and final Luna text `A + extra prose` must fail the authority comparison.

### Phase 2 — Remove hidden expected-stage leakage

Primary files:

- `tools/replay_dsa_conversations.py`
- `tools/replay_opencode_adapter.py`
- relevant replay tests

Required changes:

1. Remove corpus `stage` from `_actor_payload()`.
2. Remove `Current stage: ...` derived from corpus expectations from the Luna prompt.
3. Allow the adapter to provide **actual backend step/state** as observed product state.
4. Keep expected stage and rubric fields entirely inside the grader/corpus path.
5. Add a regression test proving actor payloads do not contain:
   - `expected`;
   - expected `stage`;
   - forbidden-term lists;
   - pass/fail rubric fields.

Exit gate:

> The serialized actor request cannot reveal which stage the grader expects next.

### Phase 3 — Split benchmark replay from stateful live replay

The existing 14-problem / 210-turn corpus remains useful, but it serves a different purpose from a live controller conversation.

#### Lane A — pedagogical benchmark

Purpose:

> Given a hypothetical state-specific tutoring turn, does visible output satisfy the pedagogical contract?

Properties:

- can cover all 14 problems / 210 learner turns;
- may use explicit expected stages because they are grader inputs, not actor inputs;
- does not claim those problems are compiled canonical Study OS assets;
- evaluates representation, pacing, terminology, visuals, question size, and future-concept leakage.

#### Lane B — live stateful Study OS + Luna replay

Purpose:

> Can the actual product conduct a coherent tutoring conversation through its real deterministic state transitions?

Properties:

- only runs problems that `resolve_problem` reports as known;
- learner behavior is selected based on actual backend step/state;
- captures Luna-final text and backend-authorized text separately;
- tests routing, progression, authority preservation, and pedagogy independently.

Do not combine Lane A coverage counts with Lane B live-execution counts.

Exit gate:

> Reports clearly state `benchmark_turns` and `live_executed_turns` separately and cannot describe uncompiled benchmark scenarios as live Study OS passes.

### Phase 4 — Make the live learner simulator state-aware

Start with Two Sum only.

Create a state-aware learner policy keyed by actual canonical step IDs, not by expected corpus sequence.

For each active probe/step, define realistic learner behaviors such as:

- clarification;
- misconception/wrong answer;
- request for visual repetition;
- partial answer;
- recovery;
- correct answer that permits progression.

The policy must contain an eventual valid response for every blocking probe so a full scenario can progress.

Example shape:

```python
LEARNER_BEHAVIORS = {
    "two_sum_goal_probe": [
        "wait what are we actually trying to find?",
        "so target is 9 and nums are the numbers right?",
        "are we returning the values or their positions?",
        "[0, 1]",
    ],
    "two_sum_needed_probe": [
        "is needed just target-num?",
        "i think needed is num-target?",
        "oh so if target is 9 and num is 2, needed is 7?",
        "7",
    ],
}
```

The exact correct responses must come from the canonical asset/controller contract, not invented from the benchmark's desired future stage.

Behavior selection rules:

1. Read actual step.
2. Choose the next unused learner behavior for that step.
3. Submit it through Luna.
4. Read resulting actual step.
5. If step remains unchanged, continue with another behavior valid for that same step.
6. If step advances, switch to the behavior set for the new step.
7. Detect infinite/stalled loops with an explicit per-step turn budget and report `STATE_STALLED` rather than silently jumping ahead.

Exit gate:

> Two Sum can conduct a coherent start-to-finish stateful replay without the simulator assuming progression that the backend has not authorized.

### Phase 5 — Grade three failure dimensions independently

For every live turn, compute three independent verdict groups.

#### A. Routing/state correctness

Examples:

- wrong semantic tool chosen;
- attempted expansion where not allowed;
- controller advanced after an incorrect/unproven response;
- controller failed to advance after the canonical passing response;
- learner simulator stalled because no valid route was available.

Suggested codes:

```text
WRONG_ACTION
UNAUTHORIZED_EXPANSION
UNAUTHORIZED_ADVANCE
EXPECTED_ADVANCE_MISSING
STATE_STALLED
```

#### B. Authority correctness

For `render_mode: verbatim`:

```text
luna_final_visible_text == backend_authorized_text
```

Suggested codes:

```text
MODEL_REWROTE_AUTHORIZED_TEXT
MODEL_ADDED_UNAUTHORIZED_TEXT
MODEL_DROPPED_AUTHORIZED_TEXT
MODEL_RETURNED_NO_FINAL_TEXT
```

This is the direct test for the original GPT/Luna integration risk.

#### C. Pedagogical correctness

Evaluate the backend-authorized learner-visible turn against the calibrated contract:

- correct concept/direction;
- approved variables;
- forbidden aliases absent;
- required visual preserved;
- one-relation pacing where required;
- output budget;
- learner-sized question/check;
- no future concept leakage;
- retry/recovery behavior where specified.

Do not grade backend-authorized content and Luna rewrite behavior under the same failure code.

Exit gate:

> A report can answer separately: “Was the controller right?”, “Did Luna preserve authority?”, and “Was the authorized teaching turn pedagogically good?”

### Phase 6 — Fix Windows reproducibility CI

Primary file: `.github/workflows/ci.yml`

The Windows job currently installs development dependencies but does not make `src/study_os` importable for the Two Sum presentation test.

Use one normal repo-supported solution:

- install the package before the tests; or
- set `PYTHONPATH=src` at the job level if that matches existing CI conventions.

Do not weaken or skip the Windows test.

Exit gate:

> Windows reproducibility tests execute the intended tests rather than failing on `ModuleNotFoundError`.

### Phase 7 — Reduce or classify mutation-gate failures without architecture expansion

The current PR has mutation survivors in the enlarged PIR/controller surface.

Order of operations:

1. First remove any production abstraction added by PR #77 that is not required by a trustworthy Two Sum live replay.
2. Rerun mutation testing on the reduced change.
3. Add targeted tests for meaningful survivors.
4. Classify only genuinely equivalent/unreachable survivors with explicit rationale.
5. Do not create new generalized machinery merely to satisfy mutation metrics.

Exit gate:

> The PR passes its existing trust-kernel mutation policy with no unreviewed survivors attributable to the PR.

### Phase 8 — Truthful Two Sum acceptance

Run the stateful live lane against the real local Luna + Study OS MCP path.

Required acceptance conditions:

```text
known canonical problem: PASS
stateful realistic learner conversation: PASS
clarification without false advance: PASS
wrong answer without false advance: PASS
recovery path: PASS
correct answer advances when expected: PASS
backend-authorized text captured: PASS
Luna-final text captured: PASS
verbatim authority preservation: PASS on every verbatim turn
visual contract: PASS
approved variable map: PASS
forbidden aliases: PASS
first-divergence report: none
```

The number of turns is determined by the stateful conversation, not forced to 15 if the real controller needs more or fewer.

Store the resulting report under `artifacts/` with:

- exact git SHA;
- model/agent identity;
- replay harness schema version;
- canonical problem ID/version;
- timestamp;
- complete turn evidence sufficient to inspect backend vs Luna-visible output.

Exit gate:

> A human can inspect the artifact and verify that the conversation the learner actually saw was correct turn by turn.

### Phase 9 — Truthful Sliding Window acceptance

Repeat the same stateful live process for the existing canonical Sliding Window asset.

Before changing the asset, compare its learner-visible progression against the saved calibrated golden. Known risk: the current production asset may compress `position → index → k → box movement → sum[i]` too aggressively.

If it fails pedagogically:

1. identify the first failing authorized turn;
2. change the lesson asset/content needed for that exact failure;
3. rerun from the beginning;
4. do not introduce a generalized framework unless the concrete failure cannot be solved without one.

Exit gate:

> Both currently known canonical DSA problems pass the truthful live replay.

### Phase 10 — Expand to 10+ real DSA problems and 150+ real learner turns

Only after Two Sum and Sliding Window are green.

For each additional problem:

1. choose a concrete DSA problem;
2. define/compile a canonical problem asset;
3. define its state-aware learner behaviors;
4. run the truthful live lane;
5. fix the first learner-visible failure;
6. preserve the evidence artifact;
7. move to the next problem only after the prior problem passes.

Target:

```text
>= 10 known canonical DSA problems
>= 150 learner turns actually executed through Luna + Study OS
>= 150 final Luna-visible responses captured
0 authority mismatches on verbatim turns
0 unclassified progression failures
pedagogical failures either zero or explicitly blocking merge
```

Do not count benchmark-only turns toward this target.

## Merge gates for PR #77

PR #77 remains draft until all gates required for its claimed scope pass.

Minimum gates before converting out of draft:

- [ ] recovery plan committed and handoff points to it;
- [ ] final Luna output captured independently from backend output;
- [ ] expected-stage leak removed;
- [ ] benchmark and live stateful lanes separated;
- [ ] state-aware learner simulator implemented for Two Sum;
- [ ] routing, authority, and pedagogy verdicts separated;
- [ ] Windows reproducibility CI executes and passes;
- [ ] mutation gate passes under existing policy;
- [ ] truthful Two Sum live replay passes;
- [ ] truthful Sliding Window live replay passes;
- [ ] PR body accurately states actual evidence and does not claim unexecuted 210-turn live coverage.

If PR #77 is intended to claim the original 10+ problem / 150+ live-turn goal, also require:

- [ ] >= 10 canonical known problems;
- [ ] >= 150 real learner turns executed through Luna + Study OS;
- [ ] corresponding final learner-visible Luna responses captured and graded;
- [ ] artifacts identify the exact revision and model used.

If those expansion requirements are intentionally deferred, the PR title/body must be narrowed before merge so the claim matches the evidence.

## First-divergence debugging rule

Once the replay instrument is trustworthy, development follows one loop only:

```text
run truthful replay
→ inspect first divergence
→ classify it as routing / authority / pedagogy / infrastructure
→ make the smallest change that fixes that divergence
→ rerun from the beginning
```

Do not batch speculative improvements across later turns while an earlier trustworthy failure remains unresolved.

## Failure ownership table

| Failure | Owner to inspect first | Typical fix surface |
|---|---|---|
| Luna calls wrong Study OS action | Luna integration/output contract | adapter/system instruction/tool affordance |
| Controller advances on wrong answer | deterministic PIR/controller | response classification/transition |
| Controller refuses valid answer | deterministic PIR/controller | evaluator/expected response definition |
| Backend teaching turn has wrong order | canonical problem asset | representation/transition content |
| Backend teaching turn renames variables | canonical problem asset/validator | approved variable/representation contract |
| Backend is correct but Luna adds prose | Luna learner-surface integration | verbatim output enforcement |
| Visual disappears in backend | canonical asset | learner-visible markdown |
| Visual exists in backend but not final Luna text | Luna learner-surface integration | verbatim output enforcement |
| Script expects future concept while controller stayed put | replay simulator | state-aware learner policy |
| Unknown problem returns `needs_compilation` | problem registry/assets | compile only when expansion phase begins |

## Explicitly out of scope during recovery

Until Two Sum and Sliding Window pass truthfully:

- generalized prerequisite-sensitive remediation;
- new diagnosis architecture;
- broad curriculum compiler work;
- additional persistence schema;
- new generic learning-state abstraction;
- auth/multi-tenancy;
- frontend redesign;
- broad benchmark infrastructure beyond what is required to inspect the live conversation;
- cost optimization;
- mutation-driven refactoring that is unrelated to a real product path.

## Definition of success

The recovery succeeds when the following statement is true and supported by inspectable artifacts:

> A realistic learner can go back and forth with Luna on Study OS. Luna routes each learner turn through the deterministic Study OS path, the controller advances only when justified, the backend emits the calibrated visual/pedagogical turn, and Luna shows that authorized turn to the learner without rewriting it. This behavior has been demonstrated first on Two Sum and Sliding Window, then on at least 10 DSA problems and 150+ real learner turns if that broader scope remains part of PR #77.

That visible behavior—not the amount of infrastructure built—is the acceptance criterion.
