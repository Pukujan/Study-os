# SOS-0017 E2E + cheap-vision gate: research (A9a)

Status: planning/research only for issue #126, branch `task/SOS-frontend-lesson-ship-2026-09-25`. No product UI/API change is proposed here. Every claim below carries a URL. A9a is docs + RED harness only; A9-exec (InferHub) implements.

## Question

Can an automated browser gate decide whether the learner-facing player still *renders a usable step-review surface* after the 1-5 + Submit work of SOS-0016, using only cheap hosted vision (no OCR pipeline), and can it do so without passing a blank or broken canvas?

Three sub-questions:

1. Which viewport/project matrix is defensible and reproducible in CI?
2. What vision judge contract gives a machine-checkable verdict with explicit pass/fail codes?
3. What false-positive and metamorphic controls keep the judge honest when the page is empty or has been re-rendered?

## Evidence and citations

### Browser automation and device emulation

Playwright's browser contexts isolate state per test and can emulate devices, viewports, color schemes and locales, so a mobile and desktop project can share one spec: https://playwright.dev/docs/browser-contexts and https://playwright.dev/docs/emulate. Playwright ships device descriptors such as `iPhone 12`/`iPhone 13` at 390x844 with `deviceScaleFactor: 3` and a mobile UA: https://playwright.dev/docs/emulate#devices. Projects let one config run the same tests over multiple device/viewport configurations, including in CI: https://playwright.dev/docs/test-projects.

The 390x844 mobile target and 1440x900 desktop target used here are therefore both expressible: mobile via `devices["iPhone 12"]` (or an explicit `viewport: { width: 390, height: 844 }`), desktop via an explicit viewport. Playwright's default viewport when unspecified is 1280x720, so the desktop number must be stated explicitly rather than assumed: https://playwright.dev/docs/api/class-page#page-set-viewport-size and https://playwright.dev/docs/api/class-testoptions#test-options-viewport.

### Screenshots and trace artifacts

Playwright captures element, page and full-page screenshots and can attach them to the test report; a screenshot is a file path, not a promise about pixels: https://playwright.dev/docs/api/class-page#page-screenshot. Full-page capture stitches beyond the viewport and is the right mode for a "is the review surface present anywhere on the page" question: https://playwright.dev/docs/api/class-page#page-screenshot (option `fullPage`). Traces record DOM snapshots, network and screenshots for later replay, which is what makes a vision verdict auditable: https://playwright.dev/docs/trace-viewer. CI integration, including installing browsers and uploading traces/screenshots as artifacts, is documented: https://playwright.dev/docs/ci-intro and https://playwright.dev/docs/ci. A web-server project (`webServer`) starts the app before tests and can reuse a running dev server locally: https://playwright.dev/docs/api/class-testconfig#test-config-web-server.

### Vision as a judge

VLM-as-a-judge is an established pattern: WebVoyager uses a GPT-4V-based auto-evaluator to score web-agent trajectories and reports agreement with human evaluation, while noting the judge can be wrong on ambiguous UI: https://arxiv.org/abs/2401.13919. Prometheus-Vision trains a vision-language evaluator against fine-grained, score-wise rubrics and shows rubric-conditioned scoring is more reliable than free-form judgement: https://arxiv.org/abs/2401.06591. The LLM-as-a-judge literature documents position, verbosity and self-enhancement biases and recommends structured rubrics over open-ended "is this good?" prompts: https://arxiv.org/abs/2306.05685.

### The blank-canvas false positive

A judge that has not actually looked can still produce confident scores. "When Vision-Language Models Judge Without Seeing: Exposing Informativeness Bias" shows VLM judges exhibit informativeness bias: scoring can be driven by how informative the *prompt text* looks rather than by the image, so a detailed, plausible-looking rubric can earn a pass even when the image is blank or irrelevant: https://arxiv.org/abs/2604.17768. This is the single largest risk for a screenshot gate, and it is why a holdout is mandatory rather than optional. The rubric-artifact literature reaches the same conclusion from the text side: rubric wording itself shifts scores: https://arxiv.org/abs/2609.02942.

Mitigations adopted here:

- Negative holdout control: judge a deliberately blank/off-target image with the *same* prompt and require a fail code. If the blank control passes, the whole gate run is invalid, not merely "noisy".
- Code-constrained output: the judge must emit one of a fixed set of verdict codes plus a locator, never a free-text blessing.
- Corroboration: a vision PASS is a *supplement* to deterministic DOM/testid assertions, never a replacement. Deterministic assertions own correctness; vision owns "did a human-shaped surface actually paint".

### Metamorphic relations

Metamorphic testing defines expected relations between outputs of related executions rather than a single oracle; systematic surveys describe its use where a test oracle is hard to specify, which is exactly the "does this UI look right" case: https://arxiv.org/abs/2605.13898. Relations used here: presentation regeneration must not delete the review surface; viewport swap must not delete controls; a submitted review must remain visible as a receipt.

## Cheap-vision provider constraint

Only InferHub cheap vision, no OCR. Probe result carried into this plan (not re-run in A9a): primary `ali/qwen3.8-flash`, fallback `cb/deepseek-v4.1-flash`. `zai/glm-4.6v` timed out and `zai/glm-5.3-flash` returned HTTP 402, so both are excluded from the gate path. The judge must record the model id it actually used so a fallback does not silently change gate semantics.

## What this research does not establish

No measurement of learner outcomes is implied. A green vision gate is derived, tool-produced evidence about rendering, not `observed` learner behavior, and not mastery evidence. It says nothing about whether the step review is pedagogically effective. Under the repository's evidence hierarchy it sits below deterministic correctness and unaided behavior. The live A2A golden roleplay gate (SOS-0018) is named as the next atomic in `SOS-0017_E2E_VISION_GATE_TDD.md` and is deferred to A9b.
