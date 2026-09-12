# Agent Handoff

Last updated: 2026-09-12
Primary tracker: #63

## Immediate execution authority — PR #77 dual-Luna transcript

The current user-directed objective for PR #77 is **not automated judging**. The immediate artifact is a full raw conversation between two independent Luna roles:

```text
local Luna — realistic student
        ↓
local Luna — teacher through the real Study OS learner-facing path
        ↓
raw transcript only
```

Read `docs/DUAL_LUNA_RAW_TRANSCRIPT.md` before doing further PR #77 work.

Default evidence target:

- 14 DSA problems from the existing corpus;
- 15 learner/teacher exchanges per problem;
- 210 learner messages + 210 teacher responses;
- 420 visible messages total;
- JSONL + readable Markdown transcript;
- no automated score, pass/fail, violation report, or repair during generation.

After the raw transcript exists, bring it back for comparison against the calibration dataset and historical teaching examples. Only then decide what needs to change in prompts, schema-driven generation, problem decomposition, canonical teaching assets, or deterministic control.

Do **not** assume OpenCode is part of the user's Luna runtime. `tools/replay_opencode_adapter.py` is experimental branch code from an earlier assumption and is not evidence that the user's local Luna exists inside OpenCode. The new `tools/run_dual_luna_transcript.py` deliberately accepts runtime-agnostic student and teacher commands.

Do **not** give either Luna the corpus answer key. The student receives only the problem, recent conversation, and a coarse behavioral signal such as clarification / plausible wrong attempt / recovery. The teacher receives the problem, learner message, and recent conversation and must use the normal Study OS product path.

PR #77 remains draft. Do not claim the 210-exchange two-Luna run happened until the actual local Luna student and actual Study OS teacher runtime have produced and saved the transcript.

## Current phase

**P4 — deterministic learning controller + versioned representation engine + operational improvement loop.**

## Latest evidence-bearing change

PR #77 now includes `tools/run_dual_luna_transcript.py`, a runtime-agnostic orchestration harness for the requested two-Luna experiment, plus tests and `docs/DUAL_LUNA_RAW_TRANSCRIPT.md`.

The branch also contains earlier replay/controller work, including a deterministic Two Sum asset and stateful replay experiments. Those are supporting implementation history, not substitutes for the requested raw two-Luna transcript.

The full existing DSA corpus is 14 problems / 210 scripted learner turns. Its problem statements and coarse learner-signal pattern are reused to guide the student role, but its expected output assertions, stage labels, forbidden terms, and grading rubric are not sent to either Luna in the dual-Luna run.

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
2. `docs/DUAL_LUNA_RAW_TRANSCRIPT.md` for the immediate PR #77 experiment
3. `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`
4. `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`
5. `docs/ADR-0016-deterministic-learning-control.md`
6. `docs/ROADMAP.md`
7. `docs/CURRENT_STATE.md`
8. latest accepted `docs/DECISIONS.md`
9. supporting P3 durability/reconciliation docs as needed

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

## Prior Luna architecture audit

The previous architecture/schema audit found that the P3/P2 durable substrate is healthy, while several P4 semantic objects remained design targets. That work remains historical context, but it does not supersede the immediate request to observe the actual teaching conversation first.

Initial operation concepts remain:

- `try_unaided`
- `rename_terms`
- `smaller_step`
- `show_trace`
- `give_hint`
- `restore_original`

Do not expand these merely because they exist in design docs. Use the raw transcript to determine which mechanisms are actually needed.

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
