# P4/PIR Threat Model — Study OS GPT Canonical PIR Integration

Date: 2026-09-05
Status: proposed threat/failure authority
Tracker: #66

## Scope

This threat model covers the first production-facing known-problem PIR teaching path through the existing Study OS GPT/MCP/application/runtime stack.

It focuses on pedagogical-control integrity, renderer/answer isolation, durable state, transport/application contract drift, and local-deployment contamination.

## Protected assets

- canonical problem/PIR identity and revision;
- legal transition graph;
- learner-visible representation state;
- controller-only assessment answers/predicates;
- problem-run current state/status;
- learner source evidence;
- derived learner-outcome evidence;
- existing Study OS session/checkpoint/retention state;
- private local transcript/evidence store;
- independent benchmark/holdout separation;
- exact module/revision provenance.

## Trust boundaries

```text
learner text
  ↓ untrusted/free language
Study OS GPT
  ↓ semi-trusted semantic client; not progression authority
MCP transport
  ↓ typed application boundary
ApplicationService
  ↓ trusted production contract
PIR controller/renderer
  ↓ trusted deterministic kernel
local persistence
```

The GPT may be capable and cooperative but is intentionally treated as non-authoritative for progression, mastery, hidden answers, and canonical graph mutation.

## Threats

### T-001 — unauthorized GPT advancement

Failure: GPT answers ahead, skips a bridge, or asks the backend for a future step without a valid learner outcome.

Controls:
- no public arbitrary `set_step` operation;
- current turn ID required for response submission;
- explicit outcome-edge authorization;
- expansion operations cannot advance;
- live GPT instructions bind it to semantic tools.

Tests: INV-002, INV-015.

### T-002 — answer/oracle leakage

Failure: expected answer or grading predicate appears in MCP response, error detail, chart, prompt or GPT-visible metadata.

Controls:
- separate `TeachingTurn` and controller-only assessment models;
- explicit forbidden fields;
- recursive safe-output tests;
- error detail redaction rules.

Tests: INV-004, INV-007.

### T-003 — representation drift

Failure: GPT or renderer drops the array/index/box, changes variable roles, renames symbols, increases chart complexity, or loses problem context during a required bridge.

Controls:
- machine-readable representation requirements;
- frozen/parameterized render contracts;
- correction mutation budget;
- GPT instructed not to rewrite critical renderer output.

Tests: INV-005, INV-006 plus data mutations.

### T-004 — semantic compression / skipped bridge

Failure: endpoints remain mathematically correct but a required learner-sized transformation is removed.

Controls:
- explicit canonical step ordering;
- historical replay assertions;
- data mutation suite for skipped/collapsed bridges;
- no runtime optimization that replaces graph traversal with endpoint equivalence.

Tests: historical replay and `SKIPPED_BRIDGE` / `UNDER_DECOMPOSITION` mutations.

### T-005 — PARTIAL collapse

Failure: partially correct learner work is treated as fully wrong or fully correct.

Controls:
- first-class outcome enum;
- assessment-specific partial predicates;
- historical regression fixture.

Tests: INV-003.

### T-006 — false mastery

Failure: final solution exposure, fatigue, self-report, or conversation completion marks mastery.

Controls:
- `assembled_mastery_unproven` terminal status;
- no mastery edge from meta/self-report;
- mastery claims require separately defined evidence.

Tests: INV-008.

### T-007 — stale/replayed request double advancement

Failure: retry or duplicate network delivery executes a transition twice.

Controls:
- idempotency ledger;
- current turn identity;
- input hash/conflict detection;
- atomic transaction.

Tests: INV-010, INV-011.

### T-008 — restart semantic drift

Failure: after restart, current run uses a different asset/controller revision or GPT reconstructs state from chat memory.

Controls:
- persisted pinned revisions/current step;
- deterministic re-render from durable state;
- fail closed if pinned asset missing.

Tests: INV-001, INV-012.

### T-009 — evidence/state split-brain

Failure: learner evidence commits but run transition does not, or run advances without durable evidence.

Controls:
- atomic write boundary where supported;
- failure injection tests;
- no success acknowledgement before commit.

Tests: INV-011, INV-014.

### T-010 — MCP/application contract drift

Failure: new tool names/fields differ between contract JSON, generated GPT actions, application operation inventory and server dispatch.

Controls:
- existing inventory/schema generation checks;
- new tools route through ApplicationService;
- versioned MCP contract.

Tests: INV-013.

### T-011 — hidden evaluator contamination

Failure: benchmark oracle/holdout answers enter production runtime or GPT context.

Controls:
- runtime depends only on reviewed production assets/controller assessment needs;
- benchmarker remains independent;
- sealed material never committed to public repo/runtime bundle.

Tests/review:
- dependency/import checks;
- local deployment receipt confirms no hidden material mounted/copied.

### T-012 — local Luna redesign

Failure: local deployment agent changes semantics, tests, schema or fixture to make integration pass.

Controls:
- Luna receives exact reviewed commit and bounded handoff;
- semantic changes require return to GitHub review;
- local receipt lists local-only modifications;
- requirement: none for accepted checkpoint unless separately reviewed.

### T-013 — unsafe public error details

Failure: private transcript, credentials, hidden answers or internal controller objects appear in application/MCP errors.

Controls:
- existing safe public detail validation;
- narrow error payloads;
- dedicated failure tests.

### T-014 — subject/run authorization mix-up

Failure: one subject can submit/get another subject's problem run.

Controls:
- subject ID matched on every run operation;
- not-found/conflict behavior avoids leaking unrelated private state.

Tests: subject mismatch rejection.

### T-015 — unsupported automatic compilation

Failure: unknown problem is silently compiled/accepted by GPT in the first slice, mixing compiler generalization with runtime validation.

Controls:
- resolver returns `needs_compilation` for unknown problems;
- no live compiler tool enabled in first slice.

### T-016 — failure hidden by plausible GPT prose

Failure: backend fails but GPT continues tutoring from its own model knowledge, making failure invisible.

Controls:
- GPT integration instructions require active PIR problem runs to use backend-authorized state;
- backend failures fail closed;
- live dogfood verifies no silent fallback advancement.

## Pedagogical failure taxonomy

These named failures are treated as testable regression categories where applicable:

- `REPRESENTATION_DROPPED`
- `VARIABLE_ROLE_CHANGED`
- `LANGUAGE_REGISTER_JUMP`
- `TOO_MANY_NEW_VARIABLES`
- `UNSUPPORTED_ADVANCE`
- `SKIPPED_BRIDGE`
- `OVER_DECOMPOSITION`
- `UNDER_DECOMPOSITION`
- `ANSWER_LEAKAGE`
- `CHART_COMPLEXITY_JUMP`
- `PROBLEM_CONTEXT_LOST`
- `CORRECTION_CHANGED_TOO_MUCH`
- `WRONG_ABSTRACTION_LEVEL`
- `SELF_REPORT_TREATED_AS_MASTERY`

## Claim boundary

Passing this threat/verification program supports only the claim that the known-problem PIR integration enforces its specified control/presentation invariants under tested conditions.

It does not prove:

- that the canonical decomposition is optimal for every learner;
- arbitrary-problem compiler generalization;
- population learning efficacy;
- long-term retention;
- sealed-holdout success.
