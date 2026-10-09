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
