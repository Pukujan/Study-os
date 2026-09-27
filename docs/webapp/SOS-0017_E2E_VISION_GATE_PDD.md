# SOS-0017 E2E + cheap-vision gate: product definition (A9a)

Status: product/requirement definition only, issue #126. Research basis and URLs live in `docs/webapp/SOS-0017_E2E_VISION_GATE_RESEARCH.md`. A9a delivers docs + a RED harness; A9-exec delivers the implementation.

## Problem

SOS-0016 shipped a learner step review (1-5 rating + why + Submit) verified by API, DB and jsdom contract tests. None of those prove the surface actually paints in a real browser, at a real viewport, after a presentation regeneration. Today the only way to know is a human clicking the preview. That is slow, unrecorded, and it cannot catch a regression that only appears on a 390px-wide canvas.

## Goal

A branch-local automated gate that answers two questions per run, with artifacts:

1. Deterministic: are the required review controls present and usable in a real browser at both viewports?
2. Perceptual: does a cheap vision judge confirm a human would see a rendered, non-blank review surface?

## Non-goals

- No OCR pipeline, no pixel-diff golden images, no visual-regression baseline service.
- No production UI, no deployment, no CD. The live site changes only after merge to `main`.
- No new API surface, no schema change, no evidence-class change. `ux.feedback` semantics stay exactly as SOS-0016 defined them.
- No learner-outcome claim. A green gate is derived tool evidence about rendering, not mastery evidence.
- No live A2A golden roleplay (SOS-0018); deferred to A9b.

## Users and triggers

- Contributor / CI: runs the gate on a branch or PR before asking a human to test.
- Reviewer: reads the gate receipt to see whether the pass was deterministic-only or corroborated by vision, and which vision model produced it.
- Watchdog agent: treats RED as "not done" and GREEN as "eligible for human verification".

## Requirements

R1. One spec file drives both viewport projects; no copy-pasted mobile/desktop specs.
R2. Viewport matrix is exactly mobile 390x844 and desktop 1440x900. Mobile maps to Playwright's `iPhone 12`/`iPhone 13` descriptor (390x844); desktop is set explicitly because Playwright's default is 1280x720.
R3. Required `data-testid` anchors exist: `player.review.panel`, `player.review.score-N` (N in 1..5), `player.review.why`, `player.review.submit`, `player.review.submitted`, and the regeneration control family `player.step.regen-*`. These are named in the SOS-0016 execution plan S5 and are A9-exec product work; until they land the gate is RED by design.
R4. The judge emits a fixed verdict code from a closed set, plus a locator and the model id. Free-text-only verdicts are rejected as `VISION_MALFORMED`.
R5. A blank/off-target negative holdout image is judged with the same prompt in the same run. If the holdout returns a pass code, the run is `VISION_HOLDOUT_BROKEN` and no PASS may be recorded.
R6. Metamorphic relations must hold: after `regenerate_presentation`, the 1-5 + Submit surface is still present; a viewport swap mid-flow keeps all controls; after Submit the `player.review.submitted` receipt is present.
R7. Every run writes a machine-readable receipt (JSON) and attaches screenshots, including the holdout image, so a verdict is auditable after the fact.
R8. The gate runs against a branch-local or preview app with `TEST_DATABASE_URL` semantics; it never points at the live site.
R9. Vision is optional-but-recorded: if no vision key is configured the run reports `VISION_NOT_RUN` and the deterministic result still stands alone. `VISION_NOT_RUN` is not green.
R10. The gate must fail loudly when anchors, config or receipts are missing. Silent skip is forbidden.

## Done-when (A9-exec)

1. `web/playwright.config.ts` defines `mobile` (390x844) and `desktop` (1440x900) projects plus a `webServer` block; `@playwright/test` is in `web/package.json` devDependencies and `web/package-lock.json` is updated by `npm install`, not hand-edited.
2. The R3 `data-testid` anchors exist in `web/src` (product work; A9a does not add them).
3. `web/e2e/player-vision-gate.spec.ts` passes deterministically on both projects against a locally served build.
4. A vision judge module calls `ali/qwen3.8-flash` with fallback `cb/deepseek-v4.1-flash`, returns a code from the closed set, and records the model actually used.
5. The blank-canvas holdout runs in the same execution and returns a fail code; a passing holdout aborts the run.
6. Metamorphic cases R6 pass on both viewports.
7. A receipt JSON plus screenshots (including the holdout) are written to the artifact directory and uploaded in CI.
8. The A9a Python RED contract `tests/test_e2e_vision_gate_contract.py` flips green without being weakened, and `python -m compileall tools tests`, `python tools/validate_repo.py`, `python -m unittest discover -s tests` all pass.
9. CI gains a Playwright job (browsers installed, artifacts uploaded) without slowing the existing `validate`, `python311`, `web` jobs below their current timeouts.

## Acceptance evidence classes

| Claim | Evidence class | Source |
| --- | --- | --- |
| Controls present and clickable at both viewports | derived (tool) | Playwright assertions + trace |
| A human-shaped surface actually painted | derived (tool, model-mediated) | vision judge code + screenshot + model id |
| Judge not trivially satisfiable | derived (tool) | blank holdout fail code |
| Review still works after regeneration | derived (tool) | metamorphic spec result |
| Learner understood the step | not claimed | no evidence; out of scope |

## Risks

- Vision false positive on blank/near-blank canvases (informativeness bias). Control: R5 holdout, closed code set, vision never overrides a deterministic failure.
- Model churn: a cheap model is deprecated or repriced and the gate silently changes meaning. Control: model id in receipt; fallback logged, not hidden.
- Flakiness from animation, fonts, or dev-server warmup. Control: explicit waits on testids, `webServer` reuse, retry policy with flake reported rather than masked.
- Anchor drift: someone renames a testid and only the vision layer notices. Control: deterministic assertions are the primary oracle.
- Cost/time blowup in CI. Control: one screenshot per checkpoint, capped resolution, small model, no per-frame capture.

## Next atomic

A9b: live A2A golden roleplay specs (SOS-0018), PDD/SDD/TDD plus RED harness, same style as this set.
