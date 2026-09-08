# Current State

Date: 2026-09-07
Status: P4 deterministic learning controller + versioned representation engine
Primary tracker: #63
PIR integration tracker: #66

## Current product reality

Study OS is actively used through the GPT app for real learning.

P3 durability/cross-chat continuity is supporting infrastructure. Canonical live learner state remains local in SQLite/private evidence storage; GitHub contains public-safe architecture, contracts, tests, schemas, curated fixtures, and reproducibility evidence.

## Known PIR integration state

The first canonical sliding-window PIR integration has completed PAM Checkpoint A assurance.

Accepted exact evidence:

```text
PR #71: merged
verified head: 0ccfc9245cc86acdd68587f4bf72158d18ac2070
normal CI: PASS
PIR Mutation Gate: PASS
mutation totals: 1268 total / 1064 killed / 204 classified survivors
unresolved non-equivalent semantic survivors: 0
timeouts/other mutation failures: 0
```

The remaining #66 sequence is:

```text
PAM B — pinned local MCP deployment + restart/resume validation
PAM C — real Study OS GPT PIR dogfood receipt
```

Do not treat raw mutation survivor count as an unresolved blocker when the enforced semantic classification gate is satisfied.

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

Current development branch:

`codex/p4-prerequisite-sensitive-remediation`

Draft PR:

`#75 — Add prerequisite-sensitive remediation control`

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
- public-safe regression fixture and tests.

This path remains **shadow authority** in this slice.

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

## Design authority

Current authority includes:

- Issue #63;
- Issue #66 for PIR/PAM sequencing;
- `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`;
- `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`;
- `docs/ADR-0016-deterministic-learning-control.md`;
- `docs/P4_PREREQUISITE_REMEDIATION_PDD.md`;
- `docs/P4_PREREQUISITE_REMEDIATION_SDD.md`;
- `docs/P4_PREREQUISITE_REMEDIATION_TDD.md`;
- `docs/ROADMAP.md`;
- `docs/HANDOFF.md`;
- `PROJECT_MANIFEST.yaml`;
- latest accepted `docs/DECISIONS.md` entries.

## Immediate execution priorities

1. Finish PR #75 focused tests and clean CI.
2. Keep prerequisite-sensitive remediation shadow-only in this slice.
3. In a separate persistent-local lane, execute PAM B for the already-merged known PIR.
4. After PAM B, run PAM C through the real Study OS GPT and capture discrepancies as operational evidence.
5. Feed those real trajectories into versioned controller/representation improvements.
6. Do not enable arbitrary raw-problem compilation until the known-problem deployment/live gates and separate compiler validation are satisfied.

## Core invariants

- No silent learner-evidence loss.
- Transcript confusion alone is not mastery or task-failure evidence.
- Canonical prerequisites and progression are code/state controlled.
- AI diagnosis remains a hypothesis.
- Ambiguous prerequisite diagnosis fails closed.
- Representation adaptation must preserve the target skill.
- Assistance cannot exceed policy ceilings.
- Module/prompt/schema evolution is explicit and replayable.
- Subject-001 evidence does not imply population-level efficacy.
