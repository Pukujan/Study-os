# Agent Handoff

Last updated: 2026-09-14
Primary tracker: #63

## Immediate execution authority — Contains Duplicate model-tutoring pilot v0.2

The 14-problem / 210-exchange raw dual-Luna evidence run is complete. Its key result was that only Two Sum and Sliding Window reached real teaching; 12 problems repeatedly exposed `needs_compilation` / reviewed-asset state.

The immediate product proof is now the bounded model/schema-driven `contains-duplicate-set` pilot described in:

1. `docs/MODEL_TUTORING_PILOT_HANDOFF.md`
2. `contracts/model-tutoring-trace.v0.2.schema.json`
3. `tools/check_model_tutoring_acceptance.py`
4. latest evidence/pilot update in Issue #63

The first 15-turn model-tutoring artifact (v0.1) is **not current acceptance evidence**. Manual review found two holes: progression was authorized by the corpus's scripted `learner_signal` rather than the actual learner response, and the conversation never established the no-duplicate `return False` case.

Current required path:

```text
real learner message
      ↓
Luna diagnosis + learner outcome
      ↓
verbatim evidence_quote bound to learner message
      ↓
deterministic controller: stay / advance at most one concept
      ↓
Luna bounded learner-visible generation
      ↓
deterministic presentation validation
      ↓
learner
```

The corpus `learner_signal` may guide Student Luna only. It is never progression evidence.

Fresh acceptance requires:

- 15 new Contains Duplicate exchanges from current HEAD;
- transcript schema `study-os.model-tutoring-exchange.v0.2`;
- trace schema `study-os.model-tutoring-trace.v0.2`;
- every `demonstrated` outcome tied to a verbatim learner-message evidence quote;
- no advancement for `not_yet` / `uncertain`;
- no concept skip or backwards transition;
- A0-A2 assistance ceiling;
- calibrated variables/visual/question/output constraints;
- no learner-visible compilation/asset jargon;
- final loop turn explicitly establishes `return False` when the scan ends without a duplicate;
- acceptance runner exits 0;
- manual transcript + trace review after the run.

Run locally with a fresh pilot:

```bash
python tools/run_model_tutoring_contains_duplicate.py --fresh
python tools/check_model_tutoring_acceptance.py \
  --transcript artifacts/model-tutoring-contains-duplicate.jsonl \
  --trace artifacts/model-tutoring-contains-duplicate-trace.jsonl \
  --scenario contains-duplicate-set \
  --report artifacts/model-tutoring-contains-duplicate-acceptance.json
```

Do **not** run another 210-turn corpus replay now. Do **not** expand to the other unsupported DSA problems until this bounded v0.2 pilot is accepted.

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

## Deprioritized

- another full 210-turn rerun before the v0.2 pilot passes;
- broad frontend work;
- video infrastructure;
- generic multimodal platform work;
- production multi-user auth;
- deep FOSSIL integration;
- premature inference-cost optimization;
- broad hardening unrelated to control/data/evidence integrity.
