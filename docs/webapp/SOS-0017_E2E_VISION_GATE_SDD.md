# SOS-0017 E2E + cheap-vision gate: system design (A9a)

Status: design only, issue #126. Requirements in `docs/webapp/SOS-0017_E2E_VISION_GATE_PDD.md`; evidence and URLs in `docs/webapp/SOS-0017_E2E_VISION_GATE_RESEARCH.md`. A9a ships docs plus a RED Python contract; the Playwright paths below are the A9-exec write set.

## Component map

```
web/
  playwright.config.ts            A9-exec  (projects: mobile 390x844, desktop 1440x900; webServer)
  e2e/
    player-vision-gate.spec.ts    A9-exec  (deterministic + metamorphic cases)
    fixtures/review-holdout.json  A9-exec  (blank/off-target holdout descriptors)
  e2e/vision/
    judge.ts                      A9-exec  (InferHub cheap-vision client; codes; retry; model id)
    prompt.ts                     A9-exec  (frozen prompt text + closed code set)
    receipt.ts                    A9-exec  (receipt JSON writer)
  src/                            A9-exec  (data-testid anchors only; no behavior change)
tests/
  test_e2e_vision_gate_contract.py  A9a    (RED: asserts paths, markers, codes, holdout wiring)
docs/webapp/SOS-0017_E2E_VISION_GATE_*.md  A9a
```

Nothing under `src/` (Python runtime) changes. The judge is a test-side tool, not product code: a vision verdict must never influence what a learner sees.

## Config shape (A9-exec)

`web/playwright.config.ts` declares two projects over one spec, an explicit desktop viewport (Playwright's default 1280x720 is not the required 1440x900), and a `webServer` that builds/serves the branch-local app. Mobile uses the `iPhone 12` descriptor, which is 390x844 at deviceScaleFactor 3; if a device descriptor is unavailable in the pinned Playwright version, an explicit `viewport: { width: 390, height: 844 }` plus `isMobile: true` and `hasTouch: true` is the equivalent and is acceptable, provided the receipt records which form was used.

Required config properties: `testDir: "./e2e"`, `fullyParallel: true`, `forbidOnly: !!process.env.CI`, `retries: process.env.CI ? 1 : 0`, `reporter` including `html` and `json`, `use.trace: "on-first-retry"`, `use.screenshot: "only-on-failure"` plus explicit full-page captures inside the spec, and `webServer` with `reuseExistingServer: !process.env.CI` and a `TEST_DATABASE_URL`-driven disposable database. The desktop project sets `viewport: { width: 1440, height: 900 }`; the mobile project sets `devices["iPhone 12"]`.

Playwright's `devices` registry and the `iPhone 12` 390x844 descriptor come from `@playwright/test`; the config must import it rather than re-typing UA strings.

## Deterministic anchors

The spec locates only by `data-testid`, never by visible text or CSS structure, so copy changes do not silently break the gate:

| Anchor | Meaning |
| --- | --- |
| `player.review.panel` | step-review container |
| `player.review.score-1` .. `player.review.score-5` | five rating controls |
| `player.review.why` | free-text why field |
| `player.review.submit` | Submit control |
| `player.review.submitted` | post-submit receipt |
| `player.step.regen-*` | presentation regeneration controls |

Until A9-exec adds these, `web/e2e/player-vision-gate.spec.ts` cannot pass and the A9a Python contract fails on the missing path. That is the intended RED state.

## Vision prompt contract

The prompt is frozen text in `web/e2e/vision/prompt.ts`. The judge receives exactly one image plus a short task line. The model must answer with a single code from the closed set on the first line and a locator on the second; anything else is `VISION_MALFORMED` and is treated as a failure, not retried into a pass.

Closed code set:

| Code | Meaning | Gate effect |
| --- | --- | --- |
| `VISION_PASS` | Review surface visibly rendered: five rating controls, a why field, and Submit are identifiable | Counts as corroboration only |
| `VISION_FAIL_BLANK` | Canvas is empty, all-white/near-uniform, or shows no UI | Fail |
| `VISION_FAIL_PARTIAL` | Some but not all required controls are identifiable | Fail |
| `VISION_FAIL_WRONG_TARGET` | A UI is rendered but it is not the step-review surface | Fail |
| `VISION_FAIL_UNREADABLE` | Rendering is present but clipped, overlapping, or off-canvas | Fail |
| `VISION_UNCERTAIN` | Judge cannot decide from the image | Fail-closed; never a pass |
| `VISION_MALFORMED` | Output did not match the required shape | Fail-closed |
| `VISION_PROVIDER_ERROR` | Transport/auth/quota failure (for example HTTP 402, timeout) | `not_run`; deterministic result still reported |
| `VISION_NOT_RUN` | No vision credential configured | `not_run`; explicitly not green |
| `VISION_HOLDOUT_BROKEN` | The blank/off-target holdout returned `VISION_PASS` | Aborts the run; every verdict in it is void |

Prompt rules the contract must encode:

1. Judge only what is visible in the image. Do not infer from the prompt wording that the UI is correct.
2. If the image is blank or you are unsure, output `VISION_FAIL_BLANK` or `VISION_UNCERTAIN`. A blank image can never be `VISION_PASS`.
3. Output exactly two lines: `<CODE>` then `<locator or NONE>`. No prose, no markdown, no confidence scale.
4. Do not grade pedagogy, wording quality, or aesthetics. This is a rendering check only.

Rule 1 and rule 2 exist because VLM judges have been shown to score from how informative the prompt looks rather than from the image (informativeness bias), so a detailed rubric can buy a pass on a blank canvas: https://arxiv.org/abs/2604.17768. Rubric-conditioned, score-wise evaluation is more reliable than free-form judgement, which is why the code set is closed rather than open: https://arxiv.org/abs/2401.06591. Structured rubrics are also the standard mitigation for judge bias: https://arxiv.org/abs/2306.05685. The WebVoyager auto-evaluator is the precedent for VLM-scored web UI with known disagreement against humans, so its verdict is treated as corroboration only: https://arxiv.org/abs/2401.13919.

## Model selection

Primary `ali/qwen3.8-flash`; fallback `cb/deepseek-v4.1-flash`. Excluded: `zai/glm-4.6v` (timed out in probe) and `zai/glm-5.3-flash` (HTTP 402). Fallback is allowed only on transport/auth failure, must be recorded, and must not be used to reinterpret an earlier verdict. A run that mixes models across checkpoints records each model per checkpoint.

## Receipt schema

`web/e2e/.artifacts/vision-gate-receipt.json` (path may be overridden by env var; the A9a contract accepts either the default or the env-named marker):

```json
{
  "schema": "study_os.e2e.vision_gate_receipt/v0.1",
  "run_id": "uuid",
  "git_sha": "9098439...",
  "started_at": "ISO-8601",
  "finished_at": "ISO-8601",
  "projects": ["mobile", "desktop"],
  "checkpoints": [
    {
      "id": "review.panel.initial",
      "project": "mobile",
      "viewport": {"width": 390, "height": 844},
      "screenshot": "relative/path.png",
      "deterministic": "PASS|FAIL",
      "vision_code": "VISION_PASS",
      "vision_locator": "center panel, five numbered controls",
      "vision_model": "ali/qwen3.8-flash",
      "vision_latency_ms": 1234
    }
  ],
  "holdout": {
    "image": "relative/path-blank.png",
    "vision_code": "VISION_FAIL_BLANK",
    "vision_model": "ali/qwen3.8-flash",
    "result": "OK|HOLDOUT_BROKEN"
  },
  "metamorphic": [
    {"id": "M-regen", "project": "desktop", "result": "PASS|FAIL"}
  ],
  "verdict": "GREEN|RED|NOT_RUN",
  "notes": ["fallback used for checkpoint X"]
}
```

`verdict` is `GREEN` only when every deterministic and metamorphic result is `PASS`, the holdout is `OK`, and at least one checkpoint carries `VISION_PASS`. If vision was unavailable, `verdict` is `NOT_RUN` even when deterministic checks pass; the receipt must say so plainly. Screenshots, including the holdout, are written beside the receipt and uploaded as CI artifacts so a verdict is replayable.

## Metamorphic design

Relations are stated as "transformation -> required observation" rather than as absolute oracles, which is the metamorphic-testing approach when no direct oracle exists: https://arxiv.org/abs/2605.13898.

| Id | Transformation | Required observation |
| --- | --- | --- |
| M-regen | Trigger `regenerate_presentation` via `player.step.regen-*` | `player.review.panel`, all five `player.review.score-N`, `player.review.why`, `player.review.submit` still present and enabled |
| M-viewport | Start desktop 1440x900, switch to mobile 390x844 mid-flow | Same control set present; none off-canvas; Submit still reachable |
| M-submit | Rate 3, fill why, Submit | `player.review.submitted` appears; panel does not vanish; phase/progress unchanged |
| M-noop | Load, wait, reload without interaction | Control set identical before and after; no spurious receipt |

M-regen is the highest-value relation: regeneration is the operation most likely to drop the review surface, and the A8 TDD already flags render invariance as a property (`docs/webapp/SOS-0016_STEP_REVIEW_TDD.md`).

## Holdout design

`web/e2e/fixtures/review-holdout.json` describes images that must never pass: a solid blank canvas, a page with the review panel removed, and an unrelated screen. The holdout is judged with the identical prompt and identical model as the real checkpoints, in the same run. A `VISION_PASS` on any holdout sets `holdout.result = "HOLDOUT_BROKEN"`, voids the run, and fails the gate. The holdout is a development adversary, not a hidden evaluation; it is committed and visible.

## CI shape

Add a `playwright` job (Node 24, matching the existing `web` job) that runs `npm ci`, `npx playwright install --with-deps chromium`, starts the API against a Postgres 16 service with `TEST_DATABASE_URL`, runs `npx playwright test`, and uploads `web/e2e/.artifacts` plus the HTML report on failure. Chromium-only keeps cost down; the viewport matrix, not the browser matrix, is what this gate is about. Browser-install and artifact-upload mechanics: https://playwright.dev/docs/ci-intro and https://playwright.dev/docs/ci. The existing `validate`, `python311`, and `web` jobs are unchanged; the A9a Python contract runs inside `validate`'s existing unittest discovery and needs no browser.

## Boundaries and invariants respected

- No raw/private learner transcript enters the receipt; only derived rendering evidence, screenshot paths, codes and model ids.
- `observed` vs `self_reported` vs `derived` stays distinct: every field here is `derived` (tool-produced).
- Screenshots of the app UI are not learner evidence and are not promoted to FOSSIL.
- Gate runs are branch-local/preview only; the live site changes after merge to `main`.
- No fixed "learning style" assumption is introduced; viewport choice is a rendering target, not a learner trait.
