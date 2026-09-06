# Next Session Handoff — PIR Mutation Gate

Date: 2026-09-06

## Purpose

This file is the authoritative next-session checkpoint for the current Study OS GPT/PIR integration work. Start the next session here; do not reconstruct the project from chat history.

## Stable merged baseline

- Repository: `Pukujan/Study-os`
- Main branch production integration commit: `61397ecaf9c8684497945bda205ee24bb4e93d5f`
- MCP contract: v0.4 / 20 semantic tools
- DB schema: v2
- Persistent ProblemRun runtime: merged
- Known September-4 sliding-window teaching asset: merged
- PARTIAL routing, expansion non-advance, idempotency, restart/resume, subject isolation, revision pinning, and `assembled_mastery_unproven`: covered by normal CI

Do not redesign or reimplement this merged slice while finishing the mutation gate.

## Active assurance branch

- PR: #71 — `Add PIR trust-kernel mutation gate`
- Branch: `codex/pir-implementation-mutation-gate`
- Current head at this checkpoint: `c7e3e58b3fb71d505fce37f5add3c31b8e4f7619`
- Base: `main` at `61397ecaf9c8684497945bda205ee24bb4e93d5f`

Latest head change: tests now verify typed stale-turn authority instead of classifying conflicts from controller exception text.

## Latest executable evidence

For head `c7e3e58b3fb71d505fce37f5add3c31b8e4f7619`:

### Normal CI

- Workflow run: `34032652099` / CI #272
- Result: **SUCCESS**

### PIR Mutation Gate

- Workflow run: `34032652160` / PIR Mutation Gate #42
- Result: **FAILURE**, because unresolved surviving mutants remain
- Artifact: `9989198675` (`pir-mutmut-report`)

Latest mutmut totals:

- total: **1268**
- killed: **980**
- survived: **288**
- no_tests: **0**
- skipped: **0**
- suspicious: **0**
- timeout: **0**
- segfault: **0**
- critical unresolved authority-function diffs exported: **160**

Important: the prior timeout has been eliminated. The current blocker is survivor classification/test strength, not runner instability.

## What has already been learned from mutation testing

Mutation testing has found real test/authority gaps and improved the code/tests. Examples already addressed include:

- post-restart terminal rendering coverage;
- exact persisted revision identity;
- expansion being renderer-only and non-advancing;
- stale response atomicity;
- exact idempotency/evidence persistence;
- direct terminal exit behavior;
- automatic traversal cycle detection;
- typed stale-turn boundary instead of granting conflict authority based on exception-message text.

Do not discard these gains or revert to a broad happy-path-only suite.

## Interpretation of the 288 survivors

`288 survived` does **not** mean 288 known production bugs. The broad three-file mutation target also creates mutations in diagnostic strings, schema/serialization details, SQLite spelling/case, mechanically equivalent expressions, and other non-authority behavior.

However, survivors in learner-authority functions are not to be waved away. The current export identifies 160 unresolved mutants in named authority functions. Each must be classified by semantic effect.

## Next executable work

1. Download/read mutation artifact `9989198675` from run `34032652160`.
2. Work from `pir-critical-survivor-diffs.txt` first.
3. Classify each remaining authority-function survivor into:
   - real semantic survivor;
   - equivalent mutation;
   - diagnostic/non-authority mutation.
4. For every real semantic survivor, add or strengthen a test that detects the changed behavior.
5. Do **not** weaken production contracts, validators, or learner-authority rules to make mutation results green.
6. Do **not** require zero survivors across irrelevant whole-file diagnostic/schema noise merely for ceremony; the blocking rule is zero unresolved **non-equivalent critical semantic** survivors.
7. Keep the broad totals as evidence even after defining the focused release policy.
8. Run normal CI and PIR Mutation Gate on the same exact head.
9. Merge PR #71 only when normal CI is green and the critical semantic mutation policy is satisfied with no unresolved non-equivalent critical survivors.
10. Record PAM Checkpoint A only after that merge/evidence is exact.
11. Only after PAM A, prepare the pinned Luna/local deployment handoff. Do not start local deployment before then.

## PAM state

- Checkpoint A — GitHub/design/executable verification: **NOT YET PASSED**
- Checkpoint B — Luna/local MCP deployment: **NOT STARTED**
- Checkpoint C — real Study OS GPT dogfood: **NOT STARTED**

Existing assurance protocol remains in:

`docs/P4_PIR_GPT_INTEGRATION_PAM_HANDOFF.md`

This next-session file is the current operational checkpoint layered on top of that protocol.

## Authority constraints to preserve

- LLM decides meaning; software decides vocabulary, step size, diagrams, variables, progression, and presentation.
- Personalization changes traversal/path, not the canonical problem map at runtime.
- Expansion must not advance pedagogical state.
- Exposure/assembly must not be promoted to mastery.
- Final historical status remains `assembled_mastery_unproven` unless independent evidence justifies something stronger.
- Pinned canonical/controller/renderer/assessment revisions fail closed on mismatch.
- Stale turns fail closed and must not write attempts/events/state transitions.
- Idempotent exact retries return the original semantic result; conflicting reuse fails.
- No sealed/hidden benchmark material enters runtime or public regression assets.

## Repositories / source authority

- Product/runtime: `Pukujan/Study-os`
- PIR research: `Pukujan/study-os-pedagogical-IR`
- Independent benchmarker: `Pukujan/study-os-benchmarker`
- Sept-4 PIR source revision currently pinned by production registry: `3abb6d08eceb53771fe5f4e6a87f7e0d99e3c009`

## Fast start for next session

The next assistant should begin with:

> Read `docs/NEXT_SESSION_HANDOFF_2026-09-06_PIR_MUTATION_GATE.md`, inspect PR #71 head and the latest mutation artifact, then continue survivor classification/testing immediately. Do not restate the roadmap and do not hand off to Luna until PAM A is actually passed.
