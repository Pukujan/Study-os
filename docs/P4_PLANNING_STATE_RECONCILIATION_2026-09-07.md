# P4 Planning-State Reconciliation — 2026-09-07

Repository verified before this audit:

- `main`: `151c819e3457ae41fa1810b5060d0101f91bc12a`
- PR #71 exact tested head: `0ccfc9245cc86acdd68587f4bf72158d18ac2070`
- no newer accepted `main` commit existed at audit time

## Planning audit result

### Issue #63

Still the correct product authority. It already defines the concepts exercised by the failed mutation-testing learner trajectory: prerequisite control, diagnosis hypotheses, bounded operations, representation lineage, assistance ceilings, provenance, replay, and future modular routing.

Do not create a parallel controller/representation architecture.

### Issue #66

Still the correct tracker for the first known-problem PIR integration slice. Its explicit non-goal excluding arbitrary live raw-problem compilation remains valid.

Checkpoint state:

- PAM A: PASSED
- PAM B: NOT STARTED / next local checkpoint
- PAM C: NOT STARTED / next live checkpoint after local validation

### P4 PDD / SDD / ADR-0016

Architecturally consistent with the new failure evidence. They need extension, not replacement. The concrete missing design is deterministic prerequisite detours plus a stronger semantic representation contract.

### `docs/ROADMAP.md`

Stale in its `Current execution order`: it still describes freezing/auditing/implementing the first real vertical slice as future work. The known PIR vertical slice now exists and has passed repo-side PAM A assurance. The roadmap should be updated after this delta is reviewed to distinguish baseline PIR deployment from the prerequisite-sensitive follow-up.

### `docs/CURRENT_STATE.md`

Materially stale. It predates the known PIR implementation and PAM A. Its immediate priorities still say to audit the runtime and implement the first deterministic course-node loop. Current state must instead recognize the merged known-PIR runtime and the PAM B/C sequence.

### `docs/HANDOFF.md`

Materially stale. It still says Phase 2 is the proposed smallest vertical slice and references the pre-PIR audit state. The next operational handoff is PAM B on the pinned PR #71 merge revision, while prerequisite-sensitive traversal is a reviewed product-design follow-up.

### `PROJECT_MANIFEST.yaml`

Mostly current. Its `next_milestone` correctly keeps known PIR deployment/restart/live validation before arbitrary learner-facing compilation. It should eventually gain explicit PAM checkpoint state and the prerequisite-sensitive design follow-up so planning state is machine-readable.

### PIR PDD / SDD / TDD

Consistent with the narrow first slice. The current `request_problem_expansion` contract is intentionally non-advancing and is not a substitute for a prerequisite detour. The current `RepresentationSpec` (`learner_visible_markdown` + `visible_components`) is adequate for the proven known slice but not rich enough to express adaptive semantic representation intent.

## Exact stale/conflicting authority to fix

1. `docs/ROADMAP.md` — old execution order.
2. `docs/CURRENT_STATE.md` — pre-PIR implementation/current-priority language.
3. `docs/HANDOFF.md` — pre-PIR Phase-2/Luna handoff language.
4. Issue #63 checklist — unchecked P4.0/P4.1 items no longer cleanly distinguish design authority from the narrow known-PIR implementation now proven.
5. Issue #66 checklist — body remains mostly unchecked despite PAM A having passed; issue comments contain the authoritative checkpoint receipt.
6. `PROJECT_MANIFEST.yaml` — correct milestone but no explicit PAM A/B/C status or product-design follow-up field.

This PR intentionally does not rewrite all historical planning files in the same change. It introduces the reviewed delta and regression oracle first so those status documents can converge on an accepted design rather than encode an unreviewed implementation shape.

## Recommended convergence after review

Update planning state to exactly distinguish:

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
