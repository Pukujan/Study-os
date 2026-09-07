# P4 Planning-State Reconciliation — 2026-09-07

Repository verified before this audit:

- `main`: `151c819e3457ae41fa1810b5060d0101f91bc12a`
- PR #71 exact tested head: `0ccfc9245cc86acdd68587f4bf72158d18ac2070`
- no newer accepted `main` commit existed at audit time

## Planning audit result

### Issue #63

Still the correct product authority. It already defines the concepts exercised by the failed mutation-testing learner trajectory: prerequisite control, diagnosis hypotheses, bounded operations, representation lineage, assistance ceilings, provenance, replay, and future modular routing.

Do not create a parallel controller/representation architecture.

A 2026-09-07 reconciliation comment now records the mutation-testing failure as a #63 product-design follow-up and pins the PAM/product sequence.

### Issue #66

Still the correct tracker for the first known-problem PIR integration slice. Its explicit non-goal excluding arbitrary live raw-problem compilation remains valid.

Checkpoint state:

- PAM A: PASSED
- PAM B: NOT YET PASSED / next local checkpoint
- PAM C: NOT YET PASSED / next live checkpoint after local validation

A 2026-09-07 reconciliation comment now makes that checkpoint state explicit without rewriting the historical issue body.

### P4 PDD / SDD / ADR-0016

Architecturally consistent with the new failure evidence. They need extension, not replacement. The concrete missing design is deterministic prerequisite detours plus a stronger semantic representation contract.

The focused extension is `docs/P4_PREREQUISITE_SENSITIVE_TRAVERSAL_DELTA.md`.

### `docs/ROADMAP.md`

Was stale in its execution order, which still described freezing/auditing/implementing the first real vertical slice as future work.

**Converged in this PR.** It now distinguishes:

- known PIR + PAM A as proven;
- PAM B as next local;
- PAM C as next live;
- prerequisite-sensitive traversal/representation adaptation as the product-design follow-up;
- arbitrary learner-facing compilation as later work.

### `docs/CURRENT_STATE.md`

Was materially stale and predated the known PIR implementation/PAM A.

**Converged in this PR.** It now records the exact PR #71 evidence, the current checkpoint states, the mutation-testing routing failure, the runtime/design gap, and the current sequence.

### `docs/HANDOFF.md`

Was materially stale and still described the pre-PIR Phase-2 vertical slice as next work.

**Converged in this PR.** It now gives the exact PAM-B local handoff, PAM-C live boundary, the prerequisite-sensitive product follow-up, and the persistent-local-executor authority boundary.

### `PROJECT_MANIFEST.yaml`

Mostly current. Its `next_milestone` already correctly keeps known PIR deployment/restart/live validation before arbitrary learner-facing compilation.

**No semantic change is required in this PR.** The manifest can later gain explicit machine-readable PAM checkpoint/product-follow-up fields if that is useful, but rewriting a mostly-current manifest is not required to resolve the present sequencing conflict.

### PIR PDD / SDD / TDD

Consistent with the narrow first slice. The current `request_problem_expansion` contract is intentionally non-advancing and is not a substitute for a prerequisite detour. The current `RepresentationSpec` (`learner_visible_markdown` + `visible_components`) is adequate for the proven known slice but not rich enough to express adaptive semantic representation intent.

## Exact stale/conflicting authority found

1. `docs/ROADMAP.md` — old execution order. **Fixed in this PR.**
2. `docs/CURRENT_STATE.md` — pre-PIR implementation/current-priority language. **Fixed in this PR.**
3. `docs/HANDOFF.md` — pre-PIR Phase-2/Luna handoff language. **Fixed in this PR.**
4. Issue #63 checklist/body — unchecked P4.0/P4.1 items do not cleanly distinguish the broad P4 architecture from the narrow known-PIR implementation now proven. **Reconciled by current issue comment; body left as historical tracker text.**
5. Issue #66 checklist/body — body remains mostly unchecked despite PAM A having passed. **Reconciled by PAM-A receipt plus current issue comment; body left as historical acceptance ledger.**
6. `PROJECT_MANIFEST.yaml` — correct sequencing milestone but no explicit PAM A/B/C status/product-follow-up fields. **Not a blocking conflict; no change required now.**

## Current converged sequence

```text
PROVEN:
known PIR integration + PAM A

NEXT LOCAL:
PAM B local deployment / restart-resume validation

NEXT LIVE:
PAM C real GPT dogfood

PRODUCT-DESIGN FOLLOW-UP:
prerequisite-sensitive traversal + semantic representation adaptation

LATER:
general unfamiliar raw-problem compilation in learner-facing product
```

Do not mark general compilation complete or imply the failed learner trajectory invalidates PAM A.

## Repo changes in this PR

- planning-state reconciliation record;
- prerequisite-sensitive PDD/SDD/TDD delta;
- public-safe mutation-testing prerequisite-routing regression fixture;
- implementation/executor handoff boundary;
- focused review checklist;
- converged `ROADMAP.md`;
- converged `CURRENT_STATE.md`;
- converged `HANDOFF.md`.

No runtime, MCP contract, schema, migration, canonical PIR asset, or mastery-policy code is changed.
