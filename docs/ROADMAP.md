# Study OS Roadmap

Date: 2026-09-08
Status: canonical execution roadmap
Primary tracker: #63
PIR integration tracker: #66

## Product direction

Study OS is a deterministic learning-control layer between course/source material and a longitudinal learner record.

The core product problem is the **learner ↔ course representation mismatch**. AI should reduce unnecessary representation difficulty while preserving the target skill. Deterministic code/state controls curriculum progression, assistance, fading, restoration, evidence semantics, and module versions.

```text
COURSE / SOURCE MATERIAL
        ↓
COURSE GRAPH + NODE VERSION
        ↓
DETERMINISTIC COURSE STATE
        ↓
DETERMINISTIC LEARNING CONTROLLER
        ↓ authorized operation
VERSIONED REPRESENTATION ENGINE
        ↓
GPT LEARNER SURFACE
        ↓
DURABLE OPERATIONAL EVIDENCE
        ↓
LEARNER + CONTROLLER STATE
        ↺
```

## Durable assets

The project treats these as durable:

- architecture and authority boundaries;
- persistent data semantics/migrations;
- raw evidence integrity/provenance;
- course-node/prerequisite/progression contracts;
- learner-control state semantics;
- pedagogical-operation definitions;
- representation lineage and structural constraints;
- diagnosis/prompt/schema provenance;
- learner/system evaluation semantics;
- module-version provenance;
- replay/evaluation lineage;
- explicit invariants, PDD/SDD/ADR/decision records.

Implementation code and model providers are replaceable.

## Current phase — P4

**Deterministic learning controller + versioned representation engine + operational improvement loop.**

P3 durability/continuity remains supporting infrastructure.

The core reconstructable loop is:

```text
course state
+ learner-control state
+ source evidence
→ deterministic authorization
→ versioned operation / representation
→ bounded AI realization
→ learner outcome
→ deterministic state transition
```

## Accepted recent progress — known PIR

The first known sliding-window canonical PIR has passed PAM Checkpoints A and B.

PAM A:

```text
PR #71 merged
verified head: 0ccfc9245cc86acdd68587f4bf72158d18ac2070
merge/deployment baseline: 151c819e3457ae41fa1810b5060d0101f91bc12a
normal CI: PASS
PIR Mutation Gate: PASS
unresolved non-equivalent semantic survivors: 0
```

PAM B accepted local deployment evidence:

```text
deployed baseline: 151c819e3457ae41fa1810b5060d0101f91bc12a
schema: 2
local tests: 342 / 342 PASS
MCP/private transport: healthy
semantic tools: 20, including five PIR tools
known sliding-window smoke: PASS
restart/resume: PASS
retry/idempotency: PASS
local_only_changes: []
```

Current #66 checkpoint state:

```text
PAM A — PASSED
PAM B — PASSED
PAM C — NEXT / NOT YET CLAIMED
```

A later stale planning comment that regressed PAM B to “not yet passed” is superseded by the 2026-09-08 ledger correction in #66.

## P4.0 — Canonical contracts

Continue stabilizing machine-readable/versioned contracts for:

- course node/version;
- prerequisites and progression policy;
- learner-control state;
- assistance ceilings and transitions;
- pedagogical-operation registry;
- representation/version/reversible mapping;
- diagnosis hypotheses;
- decision/provenance records;
- outcome records;
- replay records.

Design authority:

- `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`
- `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`
- `docs/ADR-0016-deterministic-learning-control.md`

## P4.1 — Real bounded teaching loops

Do not build a generic framework first. Extend from real learner trajectories.

Already validated/implemented foundations include:

- versioned learner snapshot and decision proposals;
- deterministic prerequisite gates in adaptive selection;
- evidence-gated scaffold controller;
- contextual representation policy;
- known canonical PIR traversal/assessment integration;
- durable source evidence and restart/resume substrate.

Current focused delta:

### Prerequisite-sensitive remediation

A real mutation-study dogfood failure showed that the learner could not parse the code-first representation and never reached a valid canonical parent-task attempt.

Required route:

```text
source difficulty evidence
→ versioned schema-constrained diagnosis proposal
→ deterministic prerequisite-sensitive routing
→ block parent progression
→ select canonical missing prerequisite only when justified
→ authorize bounded smaller-step / representation operations
→ structured representation constraints
→ behavioral micro-probe
→ controller-authorized parent re-entry
```

Canonical implementation/review PR:

- `#75 — Add prerequisite-sensitive remediation control`

Focused specs:

- `docs/P4_PREREQUISITE_REMEDIATION_PDD.md`
- `docs/P4_PREREQUISITE_REMEDIATION_SDD.md`
- `docs/P4_PREREQUISITE_REMEDIATION_TDD.md`
- `docs/P4_PREREQUISITE_REMEDIATION_DEFERRED_LIVE_REQUIREMENTS.md`

Superseded planning PRs #73 and #74 are closed. Broader #73 ideas are candidate #63 backlog, not accepted scope; #74's unique future-live requirements were retained in the deferred-requirements document above.

This path remains shadow-only until separately promoted and was not part of the accepted PAM-B deployment receipt.

## P4.2 — Operational improvement loop

Normal learning is the primary system-development dataset.

For meaningful trajectories preserve:

```text
course node/version
learner-control state before
source representation
learner attempt or pre-attempt difficulty evidence
diagnosis hypothesis + schema/prompt/model versions
authorized operation(s)/version
representation version + structural constraints
assistance level
next learner behavior
fade/restoration outcome
transfer/retention when applicable
module version set
```

Version independently where useful:

- course graph;
- controller/policy;
- operation taxonomy;
- diagnosis schema/prompt/model adapter;
- representation engine/prompt;
- retrieval/ranking;
- assessment;
- learner-state derivation.

Development loop:

```text
real trajectory
→ identify failure
→ propose module version N+1
→ deterministic contract tests
→ offline replay where valid
→ prospective real dogfood
→ keep/promote/revert
```

Replay output never becomes historical learner outcome evidence.

## P4.3 — Increasing task complexity

Use Study OS through the actual learning path:

```text
Python / DSA foundations
→ arrays / dictionaries / common patterns
→ LeetCode-style problems
→ complex DSA
→ system design
→ AI-system reasoning/debugging
```

Increasing complexity should expose failures in:

- actual concept understanding;
- prerequisite assumptions;
- terminology/representation;
- information amount;
- decomposition granularity;
- assistance dependence;
- restoration to authentic/source representations.

## Unfamiliar problems / no-dataset path

Versioned prompt engineering + schema-constrained outputs are the intended mechanism for proposing structure when no curated lesson dataset exists.

But learner-facing arbitrary raw-problem compilation is **not current live scope**.

Later pipeline:

```text
raw unfamiliar problem
→ versioned semantic/decomposition compiler prompt
→ schema-constrained candidate concept/prerequisite graph
→ deterministic validation
→ accepted canonical graph version
→ deterministic teaching controller
```

An LLM-generated graph remains a candidate until validation accepts it.

When learner state is unknown, use explicit diagnostic probes rather than fabricated mastery/prerequisite claims.

Candidate future modules retained in Issue #63 from superseded PR #73 include typed targeted-turn specs, operation-scoped information budgets, exercise contracts, output-contract validation, offline automated authoring/evaluation, and Luna/Sol matched-state differential calibration. These are not prerequisites for PAM C or #75.

## Supporting P3 work

Keep protecting:

- durable source-turn capture;
- idempotency/retry safety;
- cross-chat continuity;
- backup/restore;
- doctor/integrity checks;
- historical reconciliation when genuinely new source evidence exists;
- structured curriculum provenance.

Core invariant:

> No silent learner-evidence loss.

## Later beta/authenticated users

Do not prioritize production multi-user architecture until longitudinal dogfooding has produced repeated stable trajectories on harder material and the controller/representation contracts are auditable.

Subject 001 remains a design participant, not a population proxy.

## Much later — inference-cost/distribution optimization

Preserve interfaces that later allow high-volume functions to route through cheaper components:

- deterministic rules/state machines;
- parser/AST/compiler transforms;
- deterministic traces/static analysis;
- terminology rewriting;
- validated templates;
- retrieval/cached representations;
- embeddings/small classifiers/task-specific models;
- constrained LLM fallback.

Cost optimization follows validated product behavior, not the reverse.

## Current execution order

1. **Run PAM C next** on the exact PAM-B deployment baseline `151c819e3457ae41fa1810b5060d0101f91bc12a`; preserve the live receipt before changing that baseline.
2. Keep PR #75 green/reviewable and shadow-only; do not reinterpret it as part of PAM B/C baseline evidence.
3. Capture PAM-C discrepancies as durable product evidence, especially renderer/progression/free-language failures.
4. Review/merge #75 as a separate product-controller revision, then give any live promotion its own repo/local/live verification chain.
5. Add persistent prerequisite-detour/return state, representation lineage/restoration, and live evidence-chain support before bounded live authority.
6. Continue dogfooding through harder DSA/system-design tasks and version modules from observed failures.
7. Only after the known-problem live gate and separate compiler validation, consider arbitrary raw-problem → canonical graph compilation in the learner-facing product.
8. Consider beta/multi-user architecture only after repeated stable within-subject trajectories.

## Roadmap governance

`docs/ROADMAP.md`, `docs/CURRENT_STATE.md`, `docs/HANDOFF.md`, `PROJECT_MANIFEST.yaml`, `docs/DECISIONS.md`, the accepted P4 specs, Issue #63, and Issue #66 for the pinned PIR checkpoint evidence are current planning authority.

Historical issues, superseded PRs, stale comments, and unchecked items remain lineage. They do not override newer accepted implementation/evidence.
