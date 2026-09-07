# Agent Handoff

Last updated: 2026-09-07
Primary product tracker: #63
Known-PIR integration tracker: #66

## Read first

1. Issue #63 — deterministic learning controller / representation engine.
2. Issue #66 — known canonical PIR GPT/MCP integration and PAM receipts.
3. `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`.
4. `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`.
5. `docs/ADR-0016-deterministic-learning-control.md`.
6. `docs/P4_PIR_GPT_INTEGRATION_PDD.md`.
7. `docs/P4_PIR_GPT_INTEGRATION_SDD.md`.
8. `docs/P4_PIR_GPT_INTEGRATION_TDD.md`.
9. `docs/ROADMAP.md`.
10. `docs/CURRENT_STATE.md`.
11. `PROJECT_MANIFEST.yaml`.
12. `docs/P4_PREREQUISITE_SENSITIVE_TRAVERSAL_DELTA.md` when working on the product follow-up.

## Current accepted baseline

Study OS uses the GPT surface with canonical learner/evidence state stored locally under `/root/.study-os` (SQLite + private evidence store). GitHub is architecture/spec/contracts/tests/public-safe lineage, not the live learner database.

P3 durability/continuity remains supporting infrastructure. Historical reconciliation of the supplied source is complete to the limit of that source; do not repeat it without genuinely new evidence.

## Known PIR — PAM A is complete

The first reviewed known-problem PIR integration slice is merged and repo-side assured.

Pinned evidence:

```text
PR: #71
exact tested head: 0ccfc9245cc86acdd68587f4bf72158d18ac2070
merge revision: 151c819e3457ae41fa1810b5060d0101f91bc12a
normal CI: PASS
PIR Mutation Gate: PASS
mutants total: 1268
killed: 1064
survived: 204 (source-pinned/audited)
unresolved non-equivalent semantic survivors: 0
timeout/other failure statuses: 0
```

Checkpoint state:

```text
PAM A: PASSED
PAM B: NOT YET PASSED — NEXT LOCAL
PAM C: NOT YET PASSED — NEXT LIVE AFTER LOCAL VALIDATION
```

Do not reopen mutation assurance unless new evidence invalidates these facts.

## Immediate execution — PAM B

The next local operator/persistent executor should validate the **unchanged** PR #71 merge revision:

`151c819e3457ae41fa1810b5060d0101f91bc12a`

Before changing the local machine, capture:

1. installed Study OS revision/runtime version;
2. DB schema version;
3. MCP contract/tool inventory;
4. doctor/health state;
5. configured GPT/MCP route identity where safely observable;
6. DB/private-runtime backup receipt.

Then:

1. install exact merge revision;
2. apply only reviewed migrations actually present;
3. run the full local test suite;
4. restart MCP/private transport;
5. run doctor/health;
6. verify prior MCP compatibility and PIR operations;
7. run the known sliding-window smoke path;
8. restart mid-run and verify the same ProblemRun, pinned PIR revisions, current step, and authorized next turn resume;
9. exercise retry/idempotency behavior;
10. return a sanitized PAM-B receipt with `local_only_changes: []` unless a reusable defect was returned to GitHub and reviewed.

Do not implement new prerequisite-sensitive pedagogy as a local-only fix during PAM B.

## Next live — PAM C

After PAM B passes, use the existing Study OS GPT against the validated deployment.

Require:

- known problem resolves to the pinned canonical PIR;
- first and subsequent TeachingTurns are backend-authorized;
- GPT does not independently advance the canonical graph;
- clarification/expansion cannot jump progression;
- learner/assistant source turns remain durable;
- restart/resume state remains deterministic;
- historical final frontier remains `assembled_mastery_unproven`;
- discrepancies are captured as regression/product evidence.

PAM C is product-integration validation, not learning-efficacy or population evidence.

## New product-design follow-up from mutation-testing dogfood

A mutation-testing learning trajectory failed **before a canonical parent answer was submitted**:

- code-first presentation was not understood;
- repeating the same explanation did not resolve the difficulty;
- visual/concrete representation was requested;
- a concrete capacity/boundary scenario made the prerequisite semantics substantially clearer;
- canonical parent attempts correctly remained zero.

Classification:

> SYSTEM/PEDAGOGICAL ROUTING FAILURE — not a learner assessment failure.

This exercises Issue #63 concepts already in authority:

- `missing_prerequisite`;
- `representation_interference`;
- `decomposition_too_coarse`;
- `smaller_step`;
- `change_representation`;
- `show_trace`;
- deterministic progression blocking;
- assistance ceilings;
- representation lineage/restoration;
- explicit module versions.

Do not create a parallel architecture.

Target behavior:

```text
parent concept
→ confusion/difficulty evidence
→ diagnosis hypothesis
→ prerequisite resolution/probe
→ deterministic block of parent assessment/progression
→ authorize bounded smaller-step/representation operation
→ versioned prerequisite representation
→ micro-evidence
→ deterministic return to parent
```

No parent `incorrect` outcome is recorded solely because the learner could not parse a prerequisite representation when no canonical parent response was submitted.

Design authority: `docs/P4_PREREQUISITE_SENSITIVE_TRAVERSAL_DELTA.md`.
Public-safe regression fixture: `tests/fixtures/pir/mutation_testing_prerequisite_routing.v1.json`.

## Representation requirement

Do not encode “use a theater” as policy.

Adaptive representation should be expressed by semantic constraints such as:

- representation family;
- semantic roles;
- required relationships;
- required boundary state;
- preserved semantics;
- forbidden complexity;
- code visibility;
- source/parent representation;
- restorable mapping;
- operation/rendering versions.

Candidate realization families can include decision tree, state flow, sequence trace, comparison view, table, source code, and concrete scenario.

## Unfamiliar-problem boundary

Arbitrary learner-facing raw-problem → PIR compilation remains later work.

Do not infer that PAM A or the mutation-testing failure authorizes a generic live compiler.

Future intended pipeline:

```text
raw unfamiliar task
→ versioned decomposition/compiler prompt
→ schema-constrained candidate concept/prerequisite graph
→ deterministic validation
→ versioned graph
→ deterministic runtime traversal
→ diagnosis/adaptation
→ bounded representation realization
```

The LLM may propose decomposition, prerequisite hypotheses, diagnosis hypotheses, and representation candidates. It may not own progression, mastery, prerequisite satisfaction, assistance escalation, or canonical learner-state mutation.

For no-dataset/unfamiliar tasks, preserve uncertainty explicitly: confidence/unresolved prerequisite hypotheses, cheap diagnostic probes, and fail-closed progression when required.

## Persistent local Luna / executor follow-up

Only after the design delta is accepted should persistent local execution implement it.

Allowed later work:

- additive controller/state persistence required by the reviewed design;
- extend the existing P4/PIR controller rather than creating a parallel controller;
- deterministic prerequisite detour/return semantics;
- semantic representation-contract validation;
- regression tests from the public fixture;
- focused pytest/property/mutation loops for new authority logic;
- reviewed migration rehearsal if persistence changes;
- restart/resume, idempotency, local MCP/service integration;
- exact candidate SHA + sanitized receipts.

Not allowed:

- redefining progression/mastery/prerequisite satisfaction;
- weakening tests, mutation scope, or gate thresholds;
- hard-coding a single analogy as representation policy;
- generic live raw-problem compilation;
- local-only semantic repairs;
- self-approval of the checkpoint.

## Sequencing summary

```text
PROVEN:
known PIR integration + PAM A

NEXT LOCAL:
PAM B on 151c819e3457ae41fa1810b5060d0101f91bc12a

NEXT LIVE:
PAM C known-PIR GPT dogfood

PRODUCT-DESIGN FOLLOW-UP:
prerequisite-sensitive traversal + semantic representation adaptation

LATER:
general unfamiliar raw-problem compilation
```

## Non-negotiable invariants

1. No silent learner-evidence loss.
2. Course/problem progression is controlled by code/state.
3. AI behavior is bounded by explicit authorized operations.
4. Transcript/self-report alone never becomes mastery or prerequisite satisfaction.
5. Diagnosis remains a hypothesis.
6. Multi-dimensional interventions remain multi-dimensional in data.
7. Source representations remain restorable where claimed.
8. Historical learner outcomes remain immutable.
9. Replay/counterfactual output never masquerades as experienced evidence.
10. Module evolution is explicit/versioned; no hidden prompt drift.
11. Same canonical controller inputs + policy version produce the same authorization.
12. Generic SQL/shell/file MCP access remains prohibited.
