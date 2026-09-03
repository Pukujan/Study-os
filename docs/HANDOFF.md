# Agent Handoff

Last updated: 2026-09-03

## Current phase

**P3 operational dogfooding + durable evidence + structured curriculum acquisition.**

Study OS is already being used by Subject 001 through the GPT app for real learning. That usage is a primary product-development and evidence-generation loop.

The immediate execution priority is to repair the GPT -> local Study OS evidence path so real learning does not silently lose data. Broad frontend work and broad code hardening are deferred.

## Planning authority

Read in this order:

1. `docs/ROADMAP.md`
2. `docs/CURRENT_STATE.md`
3. latest accepted entries in `docs/DECISIONS.md`
4. Issue #52
5. current task-specific PDD/SDD/TDD

Git/issues preserve history. Superseded issue checklists do not override the current roadmap.

## P3.0 local Luna repair — read first

The current local-runtime repair is fully specified by:

1. `docs/P3_DURABLE_EVIDENCE_CAPTURE_PDD.md` — product guarantee and durable asset hierarchy;
2. `docs/P3_DURABLE_EVIDENCE_CAPTURE_SDD.md` — durability boundary, capture/reconciliation architecture and failure semantics;
3. `docs/P3_DURABLE_EVIDENCE_CAPTURE_TDD.md` — exact test-first implementation/verification plan;
4. `docs/LUNA_LOCAL_HANDOFF.md` — local WSL execution instructions.

**Luna must read all four before changing runtime behavior.**

### P3.0 invariant

> No silent learner-evidence loss.

A learner interaction must be either:

- durably committed and safely retryable; or
- explicitly known to be missing/uncertain and recoverable through reconciliation/backfill.

The desired guarantee is **durable-or-recoverable**, not “networks never fail.”

## First task for local Luna

Do not begin with a broad refactor.

First reproduce/localize the real HTTP 502/write failure and determine whether the failure occurs:

1. before local Study OS receipt;
2. during transport/request handling;
3. during persistence before commit; or
4. after durable commit while returning the result.

Use sanitized correlation/diagnostic data. Do not commit private learner content or tunnel credentials.

Then make the smallest architecture/code change required by the PDD/SDD and drive the repair using the TDD.

## Existing runtime foundations to preserve

The repository already contains useful implementation/tests for:

- local SQLite canonical learner state;
- private evidence hashing;
- idempotency keys and conflicting-key rejection;
- transaction rollback;
- checkpoint/current-pointer atomicity;
- restart/resume continuity;
- DB busy/locked errors;
- backup/restore;
- `doctor` integrity checks;
- application/MCP conformance.

P3.0 should extend these foundations, not replace them merely for code aesthetics.

Implementation code remains replaceable; persistent semantics are the durable assets.

## Runtime ownership

- Canonical live learner state: local SQLite + private evidence store.
- GPT app: current learner-facing surface.
- GitHub: source/spec/research/issue history/CI and curated public evidence.
- FOSSIL: optional/downstream durable lineage and research artifacts; not live learner persistence.

Accepted local-first architecture lineage is Issue #4.

## Durable evidence hierarchy

Protect this ordering:

```text
RAW / SOURCE EVIDENCE
        ↓
NORMALIZED OPERATIONAL RECORDS
        ↓
DERIVED LEARNER + SYSTEM STATE
```

Raw/source evidence must not be destroyed because later semantic processing, grading, or diagnosis fails.

Derived learner/system state must retain evidence provenance and may be replaced/recomputed without rewriting source history.

## Current reliability requirements

Protect at minimum:

- commit-before-success acknowledgement;
- exact retry idempotency;
- conflicting idempotency reuse rejection;
- no duplicate durable evidence;
- correlation/operation identities for diagnosis;
- explicit unknown/failed/reconciliation-required states;
- committed evidence survives restart;
- source/raw capture survives semantic-processing failure where captured;
- transcript reconciliation for turns that failed before local receipt;
- ambiguity fails closed rather than guessing;
- `doctor` exposes relevant integrity/attention states;
- backup/restore covers DB + private evidence + durable capture semantics;
- raw/private evidence provenance remains immutable/reviewable.

## TDD acceptance emphasis

The most important missing/explicit P3 tests are:

- commit succeeds but response is lost -> exact retry resolves original record with no duplicate;
- failure before commit -> no false ACK and clean retry;
- raw/source capture survives downstream semantic failure;
- missing pre-receipt turn can be backfilled from reviewed transcript provenance;
- reconciliation rerun is idempotent;
- ambiguous reconciliation refuses automatic merge;
- `doctor` surfaces unresolved evidence gaps;
- backup/restore preserves new capture/reconciliation semantics.

Existing `tests/test_local_runtime.py` and application/MCP conformance suites remain regression authority for already-covered invariants.

## Learning/evidence direction

Current operational evidence supports subject-level testing of:

- representation translation overhead;
- variable-name semantic interference;
- information overload / under-information;
- over-help / under-help;
- dynamic task decomposition/recomposition;
- assistance fading;
- source/original representation restoration.

Preserve where available:

```text
source task
 -> learner attempt
 -> failure/confusion evidence
 -> intervention/operation
 -> representation + assistance + information/granularity conditions
 -> learner response
 -> fade/original-format check
 -> transfer
 -> delayed retention
```

Learner evaluation and system/intervention evaluation remain separate.

Do not promote Subject 001 observations into population claims.

## Curriculum/data direction

Approved public/open curriculum sources may be sampled and structured in parallel with operational learning.

Preserve source provenance, source class, rights/license boundary, competency/prerequisite mapping, task version, authored representation, and learner outcome separately.

PR #50 remains the source-registry/planning work. PR #51 remains canonical operational evidence around Two Sum representation failures. PR #49 is retrospective methodology evidence; review each on its own evidence/privacy boundary.

## Issue state

Issue #52 is the canonical open P3 execution tracker.

Historical execution trackers have been closed as superseded/deferred so they do not compete with P3:

- #1/#2/#3 — bootstrap/research/mobile sequencing superseded;
- #4 — closed as accepted local-first architecture;
- #5 — old P0/P1 tracker superseded;
- #10 — old OSS-first P2 tracker superseded, implemented semantics retained;
- #21 — blanket SWE verification sequencing superseded, methods remain risk-driven tools;
- #26 — frontend/application-boundary work deferred;
- #27 — platform gaps before frontend not planned now;
- #42 — old curriculum sequencing superseded by P3.2.

Do not reopen them merely because old unchecked boxes remain.

## Engineering stance

Preserve:

- PDD/SDD/TDD and explicit invariants;
- persistent schemas/migrations/contracts;
- architecture ownership boundaries;
- evidence provenance/privacy;
- idempotency/recovery semantics;
- compatibility when persistent history requires it.

Implementation code is replaceable. Do not prioritize broad refactors, mutation score, formal methods, synthetic simulation, frontend tooling, or general platform hardening unless the current failure model requires them.

## Local repair completion evidence

Luna's implementation PR must include:

- reproduced/localized 502 boundary or explicit unresolved classification;
- exact tested commit SHA;
- exact test/validation commands and results;
- TDD T1–T14 applicability/results;
- migration status and backup result if schema changes;
- real local/MCP/GPT smoke result;
- known limitations/unreconciled historical evidence gaps;
- no private learner content/secrets in public artifacts.

## Immediate next work

1. Local Luna reads PDD + SDD + TDD + `LUNA_LOCAL_HANDOFF.md`.
2. Reproduce/localize the real 502 boundary.
3. Add/select the failing test for that exact failure class.
4. Repair the smallest required durability/reconciliation path.
5. Run focused + existing regression tests on disposable data.
6. Verify restart/retry/unknown-result/backup semantics.
7. Verify one real GPT smoke write and inspect local durability.
8. Resume normal Subject 001 learning and reconcile known missed sessions.
9. Continue structured curriculum sampling in parallel.

## Non-negotiable invariants

- Raw/private learning evidence is not committed publicly by default.
- Observed, self-reported, and derived evidence remain distinct.
- Derived learner/system state retains evidence provenance.
- Exact retry must not duplicate durable evidence.
- No acknowledged local durable write may disappear after restart.
- Remote failure before local receipt is recoverable only from actual source evidence; never invent missing turns.
- Reconciliation ambiguity fails closed.
- Hidden learning/evaluation answers remain protected.
- Adaptive components do not own canonical SQLite/checkpoint state directly.
- Representation policies are contextual interventions, not fixed learning-style labels.
- Public/source curriculum provenance remains distinct from learner outcomes.

## Handoff rule

Keep this file concise and current. Update it when P3.0 is completed, the reliability root cause changes the architecture, or the owner changes execution priority.
