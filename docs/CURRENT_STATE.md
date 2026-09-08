# Current State

Date: 2026-09-08
Status: P4 deterministic learning controller + versioned representation engine
Primary tracker: #63
PIR integration tracker: #66

## Current product reality

Study OS is actively used through the GPT app for real learning.

P3 durability/cross-chat continuity is supporting infrastructure. Canonical live learner state remains local in SQLite/private evidence storage; GitHub contains public-safe architecture, contracts, tests, schemas, curated fixtures, and reproducibility evidence.

## Known PIR integration state

The first canonical sliding-window PIR integration has completed PAM Checkpoints A and B.

Accepted PAM-A evidence:

```text
PR #71: merged
verified head: 0ccfc9245cc86acdd68587f4bf72158d18ac2070
merge/deployment baseline: 151c819e3457ae41fa1810b5060d0101f91bc12a
normal CI: PASS
PIR Mutation Gate: PASS
mutation totals: 1268 total / 1064 killed / 204 classified survivors
unresolved non-equivalent semantic survivors: 0
timeouts/other mutation failures: 0
```

Accepted PAM-B evidence from Issue #66:

```text
deployed revision: 151c819e3457ae41fa1810b5060d0101f91bc12a
schema: 2
local tests: 342 / 342 PASS
MCP/private transport: healthy
semantic tool inventory: 20, including 5 PIR tools
generic capabilities: none
known sliding-window resolution: PASS
restart/resume: PASS
retry/idempotency: PASS
local_only_changes: []
```

The initial Windows CRLF audit mismatch was accepted as environment/repository-byte normalization rather than a semantic local repair.

Current #66 checkpoint state is:

```text
PAM A — PASSED
PAM B — PASSED
PAM C — NEXT / NOT YET CLAIMED
```

A later planning comment accidentally regressed PAM B to “not yet passed” without invalidating the accepted local receipt. The 2026-09-08 #66 ledger correction supersedes that stale status.

Do not treat raw mutation survivor count as an unresolved blocker when the enforced semantic classification gate is satisfied, and do not reopen A/B without new invalidating evidence.

## Product thesis

Study OS addresses the mismatch between the target concept and the representation chosen by a course/source/tutor.

Difficulty may come from:

- the target concept itself;
- a missing prerequisite;
- terminology/identifier interference;
- notation/source wording;
- code/control-flow representation;
- amount of information/context;
- task decomposition/granularity;
- assistance level.

The product architecture remains:

```text
course/source
→ deterministic course state
→ deterministic learning controller
→ authorized pedagogical operation
→ versioned representation engine
→ GPT learner surface
→ durable learner response
→ deterministic outcome/state transition
```

AI generates hypotheses/representations inside a bounded envelope. It does not own curriculum progression or mastery.

## New operational regression evidence

A mutation-testing study session produced a useful P4 failure trajectory before any canonical learner response was submitted.

Observed/public-safe summary:

- the code-first representation was not understandable enough to attempt the task;
- repeated same-target explanation did not resolve the barrier;
- the learner requested a chart/visual representation;
- a later concrete capacity/ticket framing was more intuitive;
- canonical learner attempts remained zero.

Interpretation:

```text
observed:
  representation confusion + explicit visual request + no canonical task answer

derived/proposed:
  possible missing prerequisite and representation interference

not proven:
  one specific analogy/visual caused better learning
```

This is a controller/representation routing failure, not evidence that the learner failed the mutation-testing concept.

## Focused P4 implementation delta

Canonical development/review PR:

`#75 — Add prerequisite-sensitive remediation control`

Branch:

`codex/p4-prerequisite-sensitive-remediation`

Superseded planning PRs #73 and #74 are closed. #74's unique deferred live-authority requirements are preserved in:

- `docs/P4_PREREQUISITE_REMEDIATION_DEFERRED_LIVE_REQUIREMENTS.md`.

The focused path is:

```text
learner/source difficulty evidence
→ versioned schema-constrained DiagnosisProposal
→ deterministic prerequisite-sensitive remediation router
→ parent progression blocked
→ canonical prerequisite selected only when justified
→ bounded operation set
→ structured representation constraints
→ behavioral micro-probe
→ later controller-authorized parent re-entry
```

New/updated artifacts include:

- `src/study_os/adaptive/diagnosis.py`;
- `src/study_os/adaptive/prerequisite_remediation.py`;
- richer `RepresentationCandidate` structural constraints;
- `schemas/p4-diagnosis-proposal.schema.json`;
- `prompts/p4/diagnosis-proposal.v0.1.md`;
- focused PDD/SDD/TDD;
- deferred live-authority requirements;
- public-safe regression fixture and tests.

This path remains **shadow authority** in this slice and was not part of the accepted PAM-B deployment receipt.

## Versioned prompt/schema strategy

For unfamiliar learner-evidence patterns, the LLM may propose diagnosis via a pinned prompt and strict structured output.

The deterministic runtime then decides what those hypotheses are permitted to change.

Version independently where relevant:

- diagnosis prompt/template;
- diagnosis schema;
- model/provider adapter;
- controller/policy;
- operation registry;
- representation candidate/version;
- representation rendering prompt;
- assessment/learner-state derivation.

Prompt changes must not silently rewrite the meaning of historical diagnosis evidence.

## Unfamiliar problems / no-dataset boundary

No curated dataset is required for the first safe architecture because uncertainty can remain explicit and diagnostic probes can gather evidence online.

However, arbitrary learner-facing raw-problem compilation is still deferred.

Future path:

```text
raw unfamiliar problem
→ versioned semantic/decomposition compiler prompt
→ schema-constrained candidate graph
→ deterministic graph validation
→ accepted canonical graph version
→ deterministic teaching controller
```

An LLM-generated prerequisite graph is not canonical merely because it is well-formed.

Broader candidate modules from superseded PR #73 — typed targeted-turn specs, information budgets, exercise contracts, output validation, offline automated authoring, and Luna/Sol differential calibration — are recorded as Issue #63 backlog rather than accepted current scope.

## Design authority

Current authority includes:

- Issue #63;
- Issue #66 for PIR/PAM evidence;
- `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`;
- `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`;
- `docs/ADR-0016-deterministic-learning-control.md`;
- `docs/P4_PREREQUISITE_REMEDIATION_PDD.md`;
- `docs/P4_PREREQUISITE_REMEDIATION_SDD.md`;
- `docs/P4_PREREQUISITE_REMEDIATION_TDD.md`;
- `docs/P4_PREREQUISITE_REMEDIATION_DEFERRED_LIVE_REQUIREMENTS.md`;
- `docs/ROADMAP.md`;
- `docs/HANDOFF.md`;
- `PROJECT_MANIFEST.yaml`;
- latest accepted `docs/DECISIONS.md` entries.

## Immediate execution priorities

1. Keep PR #75 reviewable/green and shadow-only; do not fold it into the historical PAM-B claim.
2. Run PAM C through the real Study OS GPT against exact deployed baseline `151c819e3457ae41fa1810b5060d0101f91bc12a`.
3. Capture renderer/progression/free-language discrepancies as durable operational evidence while preserving learner/assistant turns.
4. Close the PAM-C receipt before changing the deployed baseline.
5. Review/merge #75 as a separate product-controller revision and give any later live promotion its own repo/local/live evidence chain.
6. Feed real trajectories into versioned controller/representation improvements.
7. Do not enable arbitrary raw-problem compilation until its separate compiler validation gate is satisfied.

## Core invariants

- No silent learner-evidence loss.
- Transcript confusion alone is not mastery or task-failure evidence.
- Canonical prerequisites and progression are code/state controlled.
- AI diagnosis remains a hypothesis.
- Ambiguous prerequisite diagnosis fails closed.
- Representation adaptation must preserve the target skill.
- Assistance cannot exceed policy ceilings.
- Module/prompt/schema evolution is explicit and replayable.
- Accepted PAM receipts stay pinned to the exact revisions/evidence they attest.
- Subject-001 evidence does not imply population-level efficacy.
