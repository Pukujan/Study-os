# Study OS v2 — Big O vertical slice (unreleased)

**Refs:** [#204](https://github.com/Pukujan/Study-os/issues/204), [PR #205](https://github.com/Pukujan/Study-os/pull/205), [#185](https://github.com/Pukujan/Study-os/issues/185).  
**Status:** An isolated, experimental frontend preview. Not a deployed replacement, not a complete decomposer, and not a user-learning-efficacy result.

## Enable explicitly

- On a local frontend developer server: `cd web && VITE_STUDY_OS_V2=1 npm run dev`, then open `/v2`.
- On a production or ordinary CI build without `VITE_STUDY_OS_V2=1`, `/v2` shows an unavailable message; the standard learner UI remains unchanged.
- The Playwright CI job deliberately sets `VITE_STUDY_OS_V2=1` for its **throwaway test build only**. It runs the v2 learner flow at 390×844 and 1440×900 and attaches screenshots. It does not deploy that build.
- Tests: `cd web && npm run typecheck && npm test`. The dedicated real-browser test is `npx playwright test e2e/v2-big-o.spec.ts`, with the preview-enabled build and the existing E2E Postgres server.

## Current verified model

The accepted #185 sticks-and-boxes interactive remains the action surface. It now optionally reports its selected mode/input size and actual steps placed to the parent. The v2 equation, plotted current point, displayed work and transfer oracle all reuse `targetSticks(mode,n)`, the same deterministic rule that drives stick placement. The current example is initial `n=3`, `O(n)`, so the equation is `W(3)=3`; the O(n²) model at n=3 is `W(3)=3×3=9`.

**This is a pedagogical toy model.** `W(n)` means exact placements in the game, not a production CPU benchmark. `O(n²)` names a growth class, not an exact runtime equation. All vocabulary is explicitly visible before the game, and the learner must enter a prediction for a **different input size** to see feedback. The preview performs no AI calls and writes no learner data.

## What this does NOT solve yet

- Genuine backend-owned guest session → signup/link → durable resume/navigation, including data migration and auth edge cases.
- A canonical, reusable problem ontology with alias/prerequisite graph, versioned symbol scopes and automatic undefined-term rejection across arbitrary domains. Three Big O definitions are a first proof, **not** a general ontology.
- Verified problem solver/decomposer, held-out differential evaluation, or multi-problem algebra/graph/game generalization. The real #118 decomposition work remains open.
- Model-grounded alternate explanations, calibrated interventions, latency and consistency scoring on real problem text.
- Production-ready UI/accessibility acceptance. Passing tests and screenshot attachment are necessary but not proof of satisfactory pedagogy.

Next: owner/learner review of entry→game→explanation→prediction at desktop/mobile; revise according to observed confusion. Freeze the shared semantic contract, then test Two Sum, sliding window and fractions using it before migrating the existing routes.

The classic frontend, database, controller, ACS PR and live deployment are not modified by this preview.


## Automatic PR review pipeline (2026-10-09 UTC)

Each update to the draft PR automatically triggers [V2 interactive reviewer](../../.github/workflows/v2-review-preview.yml). The workflow runs `node scripts/build-v2-review.mjs` to emit a **single-file, offline** React preview containing inlined CSS and JavaScript (no requests to API, AI providers or analytics). It then opens that file in real Chromium at mobile **390×844** and desktop **1440×900**, exercises game→equation→prediction→back, rejects runtime errors and network requests, and uploads `review.html` and screenshots as the 30-day artifact `study-os-v2-offline-review`.

**How to review:** on [draft PR #205](https://github.com/Pukujan/Study-os/pull/205) open Checks → V2 interactive reviewer → latest successful run → Artifacts → `study-os-v2-offline-review`. Unzip, double-click `review.html`. On any desktop browser, no local server, login, credentials or install is necessary. This preview is a standalone copy of **only** the Big O v2 teaching surface. It is **not** a deploy of the complete app and cannot validate API login, actual learner progress/resume or LLM-driven explanation behavior.

Latest first green reviewer receipt: [run 37873051045](https://github.com/Pukujan/Study-os/actions/runs/37873051045) at `2c2993476a856b455be992421b3cbd9756eb17e6`. The earlier whole-app E2E CI [run 37872265819](https://github.com/Pukujan/Study-os/actions/runs/37872265819) passed 34 browser tests, including the v2 route. Reviewers must evaluate clarity and pedagogy manually; checks cannot prove the explanation is understandable.


## 2026-10-09 user review: hosted path and drag-game revision

Owner explicitly selected **https://study.design-bakery.com/v2** (same-origin React route, rather than a new subdomain). The v2 component is now *always available once the reviewed PR is merged and CD successfully deploys it*; no `VITE_STUDY_OS_V2` build flag is required. The entire original `/` route and legacy player stay as-is. **The URL will not become live until the arbiter authorizes merge/release and CD succeeds.** This is public beta content and does not write learner data or call the AI/backend.

The standalone game has been changed from choosing a Big O class and typing a numeric answer to five computer-authored missions. Users drag a stick onto a box or ordered pair; mobile users can tap the stick and target; keyboard users can focus and activate the same controls. Wrong/duplicate actions are checked immediately without recording a successful placement; each accepted placement increments a real-time graph next to the board. Completed boards alone count as historical measurements, and the mathematical name/equation appears only *after* the activity is completed. No production login, decomposer, or mastery model is affected.

Caveat: This is a narrow DSA toy puzzle, not an automated AI-generated curriculum and not a hidden assessment. Complexity families O(log n) and O(n log n) are **not implemented as visual games** until a truthful state model and suitable tasks are specified. Partial bar heights show steps already placed, not an exact algorithmic runtime prediction. The assistant must not claim learner comprehension merely because the test suite passes.

## 2026-10-09 teaching copy + small-screen follow-up (Refs #204)

After the first production learner feedback, `W(n)` was identified as an invented label that forced beginners to decode an extra symbol. The v2 player replaces it with literal counts (e.g. **3 boxes → 3 sticks**) and **does not name O(n), O(n²) or O(1) on the first round**. Two completed examples of the same growth family are needed before showing its Big O label. A second O(1) round was added so constant growth is actually compared across sizes.

At viewports <= 860px, the stick game gets a compact, sticky live work chart **above** the target board, in the same vertical viewport. The full graph remains below for comparison. Fixed 0–16 y-axis avoids exposing target counts before a round finishes. Pointer-event dragging displays a movable stick and highlights targets on touch/mouse; click/tap/keyboard fallback remains.

**Notation gate:** `src/study_os/web/notation_guard.py` rejects uppercase function and indexed symbols in tutor replies / regenerated presentation (`W(n)`, `S[i]`, `T(n)`) unless a trusted step explicitly defines and approves them via `teach.approved_notation: [{symbol,definition}]`. The unvalidated model cannot authorize its own symbols. The gate is fail-closed for the bounded syntax family; this is not yet an all-notation, all-generator ontology, and it does not replace pinned PIR lexical-register or benchmarker evaluation. Support for lowercase function notation, arbitrary math typography and code/text disambiguation will need a typed math AST and curated notation registry as a separate integration. New tests include rejection of `W(n)`.
