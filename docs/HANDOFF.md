# Agent Handoff

Last updated: 2026-09-15
Primary tracker: #63

### Qualification execution authority

The generic all-DSA run is regression evidence. The bounded next step is the
frozen-candidate qualification loop defined in
`docs/MODEL_TUTORING_DECOMPOSITION_RELIABILITY_QUALIFICATION_V1.md` and
implemented by `tools/run_model_tutoring_autonomous_loop.py`. Use `--resume` to
continue a checkpoint; do not mix evidence after a candidate fingerprint
change. A public epoch passing is not a hidden qualification claim.

## Immediate execution authority — all-DSA generic model tutoring

The one-problem Contains Duplicate pilot is no longer the completion target.

The next product proof is the full 14-problem / 210-exchange DSA corpus through one **generic** Luna + schema + deterministic-guardrail architecture.

Primary execution authority:

1. `docs/ALL_DSA_MODEL_TUTORING_HANDOFF.md`
2. `datasets/dsa-conversation-replay.v0.1.json`
3. latest model-tutoring evidence / semantic-gate updates in Issue #63
4. current model-tutoring schemas, prompt registry/versioning, runners, and acceptance code produced under that handoff

The historical one-problem files remain useful evidence:

- `docs/MODEL_TUTORING_PILOT_HANDOFF.md`
- `tools/run_model_tutoring_contains_duplicate.py`
- `tools/check_model_tutoring_acceptance.py`
- v0.1/v0.2 Contains Duplicate transcripts/traces

They are **not** the final architecture boundary.

### Full-corpus target

```text
14 DSA problems
× 15 exchanges
= 210 learner/teacher exchanges
= 420 learner-visible messages
```

All 14 problems must use the same generic model-generated teaching path. Do not add a hand-authored canonical lesson per problem and do not replace assets with scenario-specific controller code.

### Required architecture

```text
raw problem
    ↓
Luna problem decomposer
    ↓
versioned structured teaching spec
    - concepts / prerequisites
    - variables + semantic roles
    - representations
    - semantic invariants
    - completion/base conditions
    - assistance boundaries
    ↓
generic deterministic schema + semantic validation
    ↓
learner state
    ↓
actual learner message
    ↓
Luna diagnosis + learner-outcome assessment
    ↓
verbatim learner evidence
    ↓
generic deterministic controller authorizes one operation
    ↓
Luna learner-visible generation
    ↓
generic structural + semantic validation
    ↓
learner
```

Prompt, schema, and deterministic code have separate jobs:

- **prompt**: directs Luna's decomposition/diagnosis/generation behavior;
- **schema**: makes Luna externalize concepts, semantics, evidence, variables, and progression claims in machine-checkable form;
- **deterministic code**: validates generic invariants and owns state transitions; it does not author the lesson;
- **acceptance/calibration**: judges the generated teaching plan and visible conversation against trusted behavior without leaking hidden benchmark assertions to the teacher.

Prompt versioning and prompt evaluation are mandatory for this phase. Every plan/turn must record prompt/model/schema provenance, and candidate prompt versions must be evaluated across all 14 problems plus metamorphic variants rather than on one scenario.

### Local Luna authority

Local Luna owns the whole implementation/fix/test/rerun loop. It should not stop after one problem passes or ask for ordinary implementation decisions that can be resolved from repo evidence.

It should keep fixing the **general architecture** until all 14 pass individually.

### Terra

There is no Terra-specific repository integration today. If Terra is available locally, use it as an independent diagnostic critic of failed teaching plans/transcripts/traces. Terra is advisory only: it does not interact with measured learners, authorize progression, alter acceptance reports, or feed hidden calibration answers into the teacher.

Persist Terra diagnoses separately when used.

### Existing semantic regression that must remain fixed

Contains Duplicate exposed an important failure mode: structurally valid output silently changed the meaning of `box` from “earlier values already passed” into a boolean result. The current semantic correction must remain a regression test while the architecture is generalized.

### Completion boundary

Do not call the architecture proven until:

- all 14 problems are taught through the generic model/schema path;
- no problem falls back to learner-visible `needs_compilation`;
- no new per-problem canonical lessons are added;
- generated teaching plans and every turn have versioned provenance;
- prompt evaluation exists across the full corpus + metamorphic variants;
- TDD, differential, metamorphic, property/stateful, mutation, and prompt-regression gates pass;
- the 14×15 dual-Luna run passes acceptance for every problem;
- the final transcript/trace receive manual review.

Keep PR #77 draft until this boundary is met.

## Current phase

**P4 — deterministic learning control + bounded/versioned model representation engine + operational improvement loop.**

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

## Product thesis

The core moat is the learner ↔ course representation problem.

```text
COURSE / SOURCE
      ↓
DETERMINISTIC COURSE STATE
      ↓
DETERMINISTIC LEARNING CONTROLLER
      ↓ authorized pedagogical operation
VERSIONED MODEL / REPRESENTATION ENGINE
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

- current course/concept state;
- allowed next operations;
- evidence requirements for progression;
- assistance ceiling;
- progression/blocking;
- mastery semantics;
- evidence/provenance semantics;
- module versions.

AI may:

- propose problem decompositions and structured teaching plans;
- propose diagnosis hypotheses;
- assess the current learner reply under an explicit schema;
- quote learner evidence;
- generate an authorized explanation/representation operation;
- transform terminology, examples, traces, pseudocode, or code under explicit constraints.

AI may not silently advance curriculum or mark mastery.

## Non-negotiable invariants

1. No silent learner-evidence loss.
2. Corpus simulation labels never become learner evidence.
3. Advancement requires evidence from the actual learner message.
4. Course progression is controlled by code/state.
5. AI behavior is bounded by explicit authorized operations.
6. Transcript text alone never becomes mastery.
7. AI diagnosis remains a hypothesis.
8. Raw evidence survives module/model changes.
9. Historical learner outcomes are immutable.
10. Replay/counterfactual outputs never masquerade as experienced learner evidence.
11. Module evolution is explicit/versioned.
12. Future non-LLM components must be able to fulfill the same module contracts.
13. Generic SQL/shell/file MCP access remains prohibited.
14. Generated problem semantics cannot silently mutate within a run.
15. Prompt changes are explicitly versioned and evaluated before promotion.

## Deprioritized

- one-problem-only proof loops as the final acceptance target;
- broad frontend work;
- video infrastructure;
- generic multimodal platform work;
- production multi-user auth;
- deep FOSSIL integration;
- premature inference-cost optimization;
- broad hardening unrelated to control/data/evidence integrity.
