# Current State

Date: 2026-09-07
Status: P4 deterministic learning controller + known-PIR integration; PAM A passed
Primary trackers: #63 (product authority), #66 (known-PIR integration)

## Current product reality

Study OS is a deterministic learning-control system with a learner-facing GPT surface and a local canonical learner/evidence store.

Canonical live learner state/evidence remains local:

```text
/root/.study-os
SQLite + private evidence store
```

GitHub remains the public-safe architecture/spec/contracts/tests/evidence-lineage repository, not the live learner database.

P3 durability, cross-chat continuity, backup/restore, integrity checks, and historical reconciliation remain supporting infrastructure. The supplied historical transcript recovery is complete to the limit of that source; see `docs/HISTORICAL_TRANSCRIPT_RECOVERY_RECEIPT.md`. Do not reopen that recovery without genuinely new/stronger source evidence.

## Accepted known-PIR integration state

The first reviewed known-problem PIR integration slice is implemented and repo-side assurance is complete.

Accepted evidence:

- PR #71 merged;
- merge revision: `151c819e3457ae41fa1810b5060d0101f91bc12a`;
- exact tested PR head: `0ccfc9245cc86acdd68587f4bf72158d18ac2070`;
- normal CI passed on that exact head;
- PIR Mutation Gate passed on that exact head;
- total mutants: 1268;
- killed: 1064;
- survived: 204, all source-pinned/audited;
- unresolved non-equivalent semantic survivors: 0;
- timeout/other failure statuses: 0.

PAM status:

```text
PAM A — repo/design/executable verification: PASSED
PAM B — local deployment + restart/resume: NOT YET PASSED; NEXT LOCAL
PAM C — real Study OS GPT dogfood: NOT YET PASSED; NEXT LIVE AFTER LOCAL VALIDATION
```

Do not reopen PR #71 mutation assurance unless new evidence invalidates the pinned facts above.

## Current architecture authority

Read in this order:

1. Issue #63 — deterministic learning controller / representation engine;
2. `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`;
3. `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`;
4. `docs/ADR-0016-deterministic-learning-control.md`;
5. Issue #66 — subordinate known-PIR integration tracker;
6. `docs/P4_PIR_GPT_INTEGRATION_PDD.md`;
7. `docs/P4_PIR_GPT_INTEGRATION_SDD.md`;
8. `docs/P4_PIR_GPT_INTEGRATION_TDD.md`;
9. `docs/ROADMAP.md` and `docs/HANDOFF.md`.

Issue #63 remains the product architecture authority. Do not create a parallel controller, prerequisite system, diagnosis model, representation engine, or provenance model for PIR-specific follow-up work.

## Authority boundary

Study OS code/state controls:

- canonical course/problem/node identity and version;
- prerequisite satisfaction and progression blocking;
- learner-control/problem-run state;
- allowed pedagogical operations;
- assistance ceiling;
- advancement/mastery claims;
- assessment authority where deterministic grading exists;
- evidence semantics;
- module-version provenance.

AI may:

- propose diagnosis hypotheses;
- propose semantic decomposition/prerequisite candidates where policy allows;
- realize an explicitly authorized pedagogical operation;
- generate a representation under bounded semantic constraints.

AI may not silently advance curriculum, satisfy prerequisites, declare mastery, increase assistance beyond policy, or mutate canonical learner state.

## New operational product evidence

A mutation-testing dogfood trajectory failed before any canonical mutation-testing answer was submitted.

Observed pattern:

- code-first presentation was not understood;
- repeating the same parent-node explanation did not resolve the difficulty;
- a visual/concrete representation was requested;
- a concrete capacity/boundary scenario substantially improved intelligibility;
- no canonical parent response was submitted.

Classification:

> **system/pedagogical routing failure, not learner assessment failure**

Consequences:

- canonical parent attempt count remains unchanged;
- no parent `incorrect` outcome should be fabricated;
- learner-facing difficulty evidence remains durable;
- diagnosis remains a hypothesis;
- the controller should be able to block the parent, resolve/probe a prerequisite, authorize a smaller-step/representation operation, collect micro-evidence, and return deterministically.

This failure exercises existing #63 concepts including `missing_prerequisite`, `representation_interference`, `decomposition_too_coarse`, `smaller_step`, `change_representation`, `show_trace`, assistance ceilings, and representation lineage.

Focused design delta: `docs/P4_PREREQUISITE_SENSITIVE_TRAVERSAL_DELTA.md` (PR #74).

## Current implementation gap

The known-PIR runtime correctly provides a narrow deterministic canonical path and non-advancing expansion requests. Its current representation contract is intentionally simple (`learner_visible_markdown` plus visible components).

That is sufficient for the proven known-problem slice, but it does not yet express:

- a persistent prerequisite detour/return state;
- diagnosis-linked parent blocking;
- prerequisite micro-evidence;
- semantic representation intent such as family, roles, relationships, required boundary state, forbidden complexity, and restorable mapping.

The correct next product delta is to extend the existing P4/PIR control boundary, not to replace it.

## Unfamiliar-problem boundary

Arbitrary learner-facing raw-problem → PIR compilation remains unimplemented and must not be marked complete.

The eventual architecture should be:

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

For unfamiliar/no-dataset problems, uncertain prerequisite hypotheses must remain explicit, with confidence/unresolved state, cheap diagnostic probes where allowed, and fail-closed progression when unresolved prerequisites are required.

## Current sequencing

```text
PROVEN
  known PIR integration + PAM A

NEXT LOCAL
  PAM B local deployment / restart-resume validation
  deploy exact merge 151c819e3457ae41fa1810b5060d0101f91bc12a

NEXT LIVE
  PAM C real Study OS GPT known-PIR dogfood

PRODUCT-DESIGN FOLLOW-UP
  prerequisite-sensitive traversal + semantic representation adaptation
  implement only in a new reviewed revision

LATER
  general unfamiliar raw-problem compilation in the learner-facing product
```

PAM B must not contain local-only semantic repairs. A reusable product defect returns to GitHub review.

## Operational improvement loop

Real learning remains the product-development data stream:

```text
real trajectory
→ immutable source evidence
→ normalized operation/outcome
→ identify controller/representation failure
→ explicit module version N+1
→ offline replay / contract testing
→ prospective dogfood
→ keep/promote/revert
```

Replay is counterfactual system evaluation, never historical learner evidence.

## Immediate priorities

1. Review/merge the planning reconciliation and prerequisite-sensitive design delta if accepted.
2. Execute PAM B on the unchanged PR #71 merge revision; capture local runtime/tool/schema/backup state before deployment.
3. Validate full local tests, doctor/health, MCP compatibility, known sliding-window smoke behavior, restart/resume, and retry/idempotency.
4. Run PAM C against the validated local deployment and record discrepancies as regressions.
5. Implement the accepted prerequisite-sensitive traversal delta as a separate reviewed revision; do not patch it locally during PAM B.
6. Keep generic unfamiliar-problem compilation behind its separate validation gate.

## Long-horizon direction

Preserve module interfaces so stable high-volume functions can later be fulfilled by deterministic transforms, parsers/ASTs, traces, templates, retrieval, small classifiers/models, or other specialized components. The deterministic controller remains authority regardless of which implementation realizes a representation or diagnosis proposal.
