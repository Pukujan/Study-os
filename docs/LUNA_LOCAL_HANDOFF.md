# Luna Local Implementation Handoff — P3.0 Durable Evidence Repair

Date: 2026-09-03

This file is intended to be handed directly to the learner's local coding agent ("Luna") running in WSL.

## Mission

Repair the real GPT -> local Study OS evidence-capture path so learner interactions are **durable-or-recoverable**.

Primary invariant:

> No silent learner-evidence loss.

Do not treat the task as a generic 502 bug fix. The required outcome is that Study OS can prove what was committed, safely resolve uncertain results, and identify/reconcile evidence that never reached the local runtime.

## Read first — current authority

Read in this order before changing runtime behavior:

1. `AGENTS.md`
2. `docs/HANDOFF.md`
3. `docs/ROADMAP.md`
4. `docs/CURRENT_STATE.md`
5. `docs/DECISIONS.md` — latest accepted decisions, especially D010/D012/D014
6. `docs/P3_DURABLE_EVIDENCE_CAPTURE_PDD.md`
7. `docs/P3_DURABLE_EVIDENCE_CAPTURE_SDD.md`
8. `docs/P3_DURABLE_EVIDENCE_CAPTURE_TDD.md`
9. `docs/ERROR_IDEMPOTENCY_CONTRACT.md`
10. `docs/DATABASE_CONTRACT.md`
11. `docs/LOCAL_RUNTIME_ARCHITECTURE.md`
12. `contracts/study-os-mcp-tools.v0.1.json`
13. Issue #52

Historical P0/P1/P2 issue checklists are lineage, not current execution authority.

## Architecture to preserve

```text
GPT learner-facing app
        ↓
secure/private Study OS transport
        ↓
Study OS application/runtime semantics
        ↓
local SQLite + private evidence store
```

Runtime ownership remains:

- local SQLite + private evidence store = canonical live learner state/evidence;
- GitHub = source/spec/research/CI/curated public artifacts;
- FOSSIL = optional/downstream lineage/research, never required for normal capture/resume;
- GPT = current learner-facing surface.

Implementation code may be replaced/refactored if needed. Persistent evidence identity, provenance, idempotency, migrations, acknowledgement/recovery semantics are the assets that must survive.

## Do not build as part of this repair

Do not spend this cycle on:

- dedicated web/mobile frontend;
- HTTP expansion unrelated to the real failure;
- generated video/audio/image systems;
- Postgres;
- microservices;
- FOSSIL runtime dependency;
- broad adaptive-policy promotion;
- broad mutation/formal/chaos programs;
- wholesale runtime refactor for aesthetics;
- general platform hardening unrelated to the durability incident.

## Step 0 — protect local learner data before risky work

Before any migration/destructive diagnostic on the real runtime:

1. identify the actual configured Study OS root;
2. run current `doctor`/health checks;
3. make/verify a backup using the existing supported backup path;
4. use a disposable copied runtime or synthetic temp root for failure injection whenever possible;
5. do not expose raw private learner content in logs, issue comments, PR fixtures, or screenshots.

If the current backup cannot be verified, fix/establish a safe backup before a destructive migration.

## Step 1 — reproduce and localize the 502

Before changing production code, reproduce the current failure or gather enough local diagnostics to classify it.

For one attempted write, determine:

```text
A. request reached tunnel/edge?
B. local MCP/transport received it?
C. application/runtime handler entered?
D. idempotency lookup happened?
E. DB transaction began?
F. commit happened?
G. result was constructed?
H. response failed after commit?
```

Classify as one of:

- `pre_local_receipt`
- `transport_or_handler_before_commit`
- `persistence_before_commit`
- `post_commit_response_failure`
- `multiple_or_unresolved`

Use correlation IDs and stable categories where available. Do not log raw learner text merely to prove the request path.

If the failure is upstream of the local service, do not pretend local code can make the network infallible. Implement only the local durable/reconciliation requirements that remain relevant and report the upstream boundary.

## Step 2 — test first

Follow `docs/P3_DURABLE_EVIDENCE_CAPTURE_TDD.md`.

The repository already has useful regression coverage, especially in:

- `tests/test_local_runtime.py`
- `tests/test_application_*_conformance.py`
- MCP conformance/runtime tests

Existing behavior already includes idempotent event retry, conflict rejection, checkpoint rollback, restart continuity, DB busy handling, evidence hash checks, backup/restore, and contract conformance.

Do not rebuild these blindly.

Add/select a failing test for the actual missing failure class first.

The key P3 additions are expected to cover:

- post-commit response loss / unknown caller result;
- source/raw capture independent of later semantic failure where applicable;
- explicit reconciliation/backfill for pre-receipt missing turns;
- idempotent reconciliation rerun;
- ambiguous reconciliation fail-closed;
- `doctor` visibility for unresolved capture/reconciliation states;
- backup/restore of any new durable capture/reconciliation semantics.

## Step 3 — smallest implementation change

After the failing test exists, make the smallest change that satisfies the PDD/SDD invariant.

Do not widen architecture unnecessarily.

Prefer preserving the current application/MCP contract unless evidence shows the contract itself cannot represent a required durable state.

If a schema change is necessary:

- write a forward migration;
- preserve all historical records;
- do not reuse old fields with changed meaning;
- test migration from the current schema;
- backup valuable local state first;
- include migration/restore evidence in the PR.

## Required semantics

### Durable acknowledgement

Do not return/claim durable success until the required local transaction/durability boundary commits.

### Exact retry

```text
same idempotency identity + same fingerprint
    -> original durable result, no duplicate

same idempotency identity + different fingerprint
    -> explicit conflict
```

### Unknown result

If commit succeeds but the response is lost, retry/query must resolve the already committed operation safely.

### Raw/source evidence

Where a learner-facing turn is captured locally, optional normalization/diagnosis/system grading must not be able to erase it.

### Reconciliation

A turn that never reached local Study OS can only be recovered from actual source evidence such as a reviewed transcript/export.

Backfill must:

- preserve source provenance;
- distinguish live capture from reconciliation capture;
- deduplicate exact matches;
- preserve recovery time separately from source time;
- refuse automatic merge when identity is ambiguous.

Never invent a missing turn.

## `doctor` expectations

Extend `doctor` only as needed to surface the P3 durability state.

It should be able to identify applicable problems such as:

- DB/migration/integrity failure;
- missing/corrupt private evidence artifact;
- invalid idempotency state;
- durable receipt referencing missing record;
- semantic/derived record referencing missing source evidence;
- unresolved unknown-result/reconciliation-required item;
- ambiguous reconciliation item;
- backup/restore integrity status where available.

`doctor` reports; it must not silently rewrite learner history to make itself healthy.

## Backup/restore expectations

If P3 adds new persisted capture/reconciliation state, backup/restore must preserve it.

After restore verify:

- source/capture identities;
- hashes/private artifact references;
- idempotency identity/fingerprint semantics;
- reconciliation provenance/status;
- learner/system evidence links;
- retry behavior;
- `doctor` result.

A restore that recovers a checkpoint but loses underlying learner evidence is not acceptable.

## Public/private boundary

Use synthetic fixtures only in committed tests.

Do not commit:

- real raw learner transcript;
- tunnel URLs containing secrets/tokens;
- local credentials;
- private filesystem paths when avoidable;
- logs containing raw private learner content.

Prefer correlation IDs, hashes, status categories, and synthetic payloads.

## Focused verification before PR

Run the applicable P3 TDD tests and existing regressions.

Expected pattern if a new focused file is created:

```bash
python -m unittest tests.test_p3_durable_evidence_capture -v
python -m unittest tests.test_local_runtime -v
```

Then run the repository's canonical validation/test commands from the current checkout.

Record exact commands and pass/fail totals; do not summarize only as "tests passed."

## Disposable rollout sequence

Before real learner use:

1. disposable/synthetic runtime root;
2. durable write;
3. exact retry;
4. conflict retry;
5. injected before-commit failure;
6. injected post-commit response-loss case where feasible;
7. restart service;
8. `doctor`;
9. reconciliation/backfill fixture;
10. backup -> destroy disposable state -> restore;
11. MCP/local transport smoke.

Only then test the actual GPT path.

## Real GPT smoke

After lower layers pass:

1. start/verify the real local service and transport;
2. perform one small non-sensitive Study OS write through the GPT app;
3. inspect the local DB/evidence state using supported service/diagnostic methods;
4. verify the operation is durably present;
5. if caller result was uncertain, retry using the same logical identity and verify no duplicate;
6. run `doctor`.

Do not use a long valuable learning session as the first real smoke test.

## Historical missed sessions

The current repair does not retroactively prove that prior 502 turns were locally captured.

After the live path is trustworthy, reconcile known missed/uncertain sessions only from available actual source evidence.

Preserve whether each record was:

- captured live;
- already present despite caller uncertainty;
- recovered later by reconciliation;
- unresolved/ambiguous.

## Stop and report instead of improvising when

Stop and return diagnostics/proposal if:

- the real failure is entirely outside the local Study OS boundary;
- public MCP contract changes appear necessary;
- a destructive migration is required without verified backup;
- current local checkout/state conflicts materially with `main` specs;
- reconciliation identity is ambiguous;
- fixing the issue would require committing private credentials/config;
- a proposed shortcut would make derived state authoritative over raw evidence.

## Implementation PR requirements

Open a PR referencing Issue #52.

Include:

### Root-cause / boundary table

| Boundary | Observed? | Evidence |
|---|---|---|
| request reached local transport | yes/no/unknown | sanitized ref |
| application handler entered | yes/no/unknown | ref |
| transaction began | yes/no/unknown | ref |
| commit occurred | yes/no/unknown | ref |
| caller received result | yes/no/unknown | ref |

### Change summary

- failure class fixed;
- architecture/data semantics changed;
- code areas changed;
- migration version or explicitly `none`;
- compatibility implications;
- known limitations.

### TDD receipt

Report T1–T14 from `P3_DURABLE_EVIDENCE_CAPTURE_TDD.md` as:

- pass;
- not applicable + reason;
- unresolved blocker.

### Verification receipt

- exact head SHA;
- exact commands;
- pass/fail counts;
- backup/restore result;
- local transport/MCP smoke;
- real GPT smoke;
- unresolved historical evidence gaps.

## Definition of done

The local P3.0 repair is complete only when:

- the current 502 boundary is localized or explicitly documented as unresolved/upstream;
- no tested acknowledged durable write can disappear;
- exact retries cannot duplicate the affected evidence;
- commit-then-response-loss is recoverable safely;
- pre-receipt missing evidence has a tested provenance-preserving backfill path;
- ambiguous reconciliation never guesses;
- restart and backup/restore preserve durability semantics;
- existing checkpoint/evidence integrity remains green;
- one actual GPT smoke write is proven durable locally;
- the learner can resume normal Study OS learning without manually administering routine persistence.

The goal is not to preserve current code. The goal is to preserve trustworthy longitudinal learner evidence.
