# SOS-0017 E2E + cheap-vision gate: test design (A9a)

Status: RED contract only, issue #126. A9a adds docs plus `tests/test_e2e_vision_gate_contract.py`, which fails until A9-exec lands the Playwright config, the spec, the vision judge and the `data-testid` anchors. Requirements: `docs/webapp/SOS-0017_E2E_VISION_GATE_PDD.md`. Design: `docs/webapp/SOS-0017_E2E_VISION_GATE_SDD.md`. Evidence: `docs/webapp/SOS-0017_E2E_VISION_GATE_RESEARCH.md`.

## Why a Python RED contract and not a browser run

`.github/workflows/ci.yml` has three jobs: `validate`, `python311` (Python + Postgres service) and `web` (Node 24: `npm run typecheck`, `npm test`, `npx vite build`). None installs Playwright browsers, and the `web` job has no Postgres. A TypeScript spec that cannot run is invisible to CI: it would neither fail nor protect anything. So A9a asserts the gate's *shape* from Python, inside the existing unittest discovery that `validate` already runs, with no browser and no network. This mirrors A8, where `tests/test_player_step_review_contract.py` was the RED contract that flipped green only when the executor implemented.

Consequence, stated plainly: **A9a CI is expected RED.** That is the deliverable, not a defect. Do not delete, skip or weaken the contract to make CI green; the fix is A9-exec implementation.

## What the contract asserts

| Test | Asserts | Fails today because |
| --- | --- | --- |
| `test_required_gate_paths_exist` | `web/playwright.config.ts`, `web/e2e/player-vision-gate.spec.ts`, `web/e2e/vision/judge.ts`, `web/e2e/vision/prompt.ts`, `web/e2e/vision/receipt.ts`, `web/e2e/fixtures/review-holdout.json` all exist | no `web/e2e/` and no config on this branch |
| `test_playwright_config_declares_viewport_matrix` | config declares `testDir` `./e2e`, `projects`, `webServer`, and the literal viewports 390x844 and 1440x900 | config absent |
| `test_package_json_declares_playwright_and_e2e_script` | `@playwright/test` in `devDependencies` and a `test:e2e` script | dependency absent |
| `test_spec_targets_required_testids` | spec references all seven anchor families | no `data-testid` in `web/src` and no spec |
| `test_spec_declares_metamorphic_relations` | spec declares `M-regen`, `M-viewport`, `M-submit`, `M-noop` | spec absent |
| `test_vision_prompt_declares_closed_code_set` | `prompt.ts` declares all ten verdict codes | judge absent |
| `test_vision_judge_pins_cheap_models_and_records_model` | judge pins `ali/qwen3.8-flash` primary and `cb/deepseek-v4.1-flash` fallback, and records the model used | judge absent |
| `test_holdout_is_wired_and_fails_closed` | holdout fixture exists, is referenced by the spec or judge, and `VISION_HOLDOUT_BROKEN` appears in the gate path | fixture absent |
| `test_receipt_marker_path_and_schema_are_declared` | `receipt.ts` declares schema `study_os.e2e.vision_gate_receipt/v0.1` and marker path `web/e2e/.artifacts/vision-gate-receipt.json` | receipt module absent |
| `test_docs_present` | the four SOS-0017 docs exist | passes as of A9a |

The receipt test asserts a *declared path constant*, never an artifact on disk. Committing a synthetic receipt would be fabricated evidence and is forbidden.

## Gate cases the spec must cover (A9-exec)

Deterministic, both projects:

1. D1 panel present: `player.review.panel` visible after lesson load.
2. D2 five ratings: `player.review.score-1`..`-5` all visible and enabled; selecting 3 marks it.
3. D3 why required: Submit is disabled or rejects while `player.review.why` is empty; enabled after non-whitespace text.
4. D4 submit posts once: Submit yields `player.review.submitted` and exactly one `ux.feedback` row for the bound step (corroborated by the existing A8 API contract, not re-implemented here).
5. D5 full-page screenshot captured per checkpoint and written to the artifact directory.

Vision, both projects:

6. V1 the initial review panel screenshot returns `VISION_PASS`.
7. V2 the post-submit receipt screenshot returns `VISION_PASS`.
8. V3 each blank/off-target holdout image returns a fail code; a `VISION_PASS` on holdout aborts the run with `VISION_HOLDOUT_BROKEN`.

Metamorphic:

| Id | Transformation | Required observation |
| --- | --- | --- |
| M-regen | Fire `regenerate_presentation` via `player.step.regen-*` | Panel, all five ratings, why, Submit still present and enabled; `player.review.submitted` absent unless a review was submitted before regeneration |
| M-viewport | Desktop 1440x900 -> mobile 390x844 mid-flow | Same control set present, none off-canvas, Submit reachable by tap target |
| M-submit | Rate 3, fill why, Submit | Receipt appears; panel persists; lesson phase and step progress unchanged |
| M-noop | Load, idle, reload | Control set identical; no receipt; no extra `ux.feedback` row |

M-regen is the load-bearing relation and pairs with the A8 render-invariance property in `docs/webapp/SOS-0016_STEP_REVIEW_TDD.md`. M-viewport is the relation that catches "works on my 1440px screen".

## Holdout (development adversary, not hidden)

`web/e2e/fixtures/review-holdout.json` lists three images: a solid blank canvas, the player with the review panel removed, and an unrelated screen. Judged with the identical prompt and model as real checkpoints. All must fail. This is committed and visible; it is never described as a hidden holdout. A separate withheld suite, if any, stays outside the public branch under the same commitment discipline A8 used.

## Commands

Local, after A9-exec:

```powershell
cd web
npm install
npx playwright install chromium
npm run test:e2e
```

Repository checks, unchanged and browser-free:

```powershell
python -m compileall tools tests
python tools/validate_repo.py
python -m unittest tests.test_e2e_vision_gate_contract -v
python -m unittest discover -s tests -v
```

## Gate interpretation

- Contract RED: expected on the A9a base. The gate does not exist yet.
- Contract GREEN but no receipt: `NOT_RUN`, never green. Vision absence must be reported as `VISION_NOT_RUN`.
- Deterministic PASS + vision `VISION_PROVIDER_ERROR`: report `NOT_RUN` for the perceptual half; do not launder a provider failure into a pass.
- Deterministic FAIL + vision PASS: RED. Vision never overrides a deterministic failure.
- Holdout passes: `VISION_HOLDOUT_BROKEN`; the entire run is void and must be re-run, not partially credited.
- Flaky pass on retry: report the flake. Do not raise retries to hide it.

## Next atomic

A9b: live A2A golden roleplay gate specs (SOS-0018) - PDD/SDD/TDD plus RED harness, same style; out of scope for A9a.
