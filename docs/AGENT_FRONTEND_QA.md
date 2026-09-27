# AGENT_FRONTEND_QA — Mandatory frontend QA (Ultrafast-first, then Playwright)

Status: **MANDATORY** for every agent working on Study-os frontend / UI  
Parent: #126  
Date: 2026-09-27  
Clarification (Alex): **Ultrafast runs FIRST for agents/local FE claims — NOT in GitHub Actions CI.** CI stays Playwright + vision only.  
Related: [`docs/PDD_UX_DEFECT_EXPLORATION.md`](PDD_UX_DEFECT_EXPLORATION.md), [`docs/UX_DEFECT_LOCAL_AND_CI.md`](UX_DEFECT_LOCAL_AND_CI.md), [`docs/webapp/SOS-0017_E2E_VISION_GATE_PDD.md`](webapp/SOS-0017_E2E_VISION_GATE_PDD.md), [`docs/benchmarks/ux-defect-jev-ultrafast/README.md`](benchmarks/ux-defect-jev-ultrafast/README.md), [`docs/webapp/DESIGN_SYSTEM.md`](webapp/DESIGN_SYSTEM.md) (#165)

## Mandate (Alex)

Before claiming a frontend change works, or opening/merging a PR that touches UI as “FE done”:

1. **FIRST — local Ultrafast scout** against live `https://study.design-bakery.com` **or** the PR preview. Gate with `python tools/gate_ux_defect_report.py <summary.json>` (exit 0 = no P0/P1).
2. **THEN — Playwright UX + vision** (deterministic + vision gate) against live, PR preview, or the local preview stack.
3. **CI** on that PR must run **Playwright + vision only**. Ultrafast is **not** a required Actions job — do **not** add Ultrafast to `.github/workflows/`.

Do not treat green unit/jsdom tests alone as FE proof. **Never claim FE done without an Ultrafast pass.**

This applies to **all agents** (Grok, Claude Code, InferHub workers, humans driving agents). No exceptions for “small” UI diffs.

## Pass / fail rules

| Rule | Requirement |
| --- | --- |
| Order | Ultrafast **first** (local/scout), then Playwright. CI does not substitute for Ultrafast. |
| P0 / P1 | Any **P0 or P1** → claim **fails** regardless of confidence. Fix it, or file a tracked defect and **block** merge / “works” claims until resolved or explicitly waived by the arbiter with a linked issue. |
| Confidence | Record confidence (and model/receipt ids) on the issue/PR. Confidence **does not waive** P0/P1. Low confidence → manually re-check why; do **not** skip or re-label as pass. |
| Ultrafast reliability | **Ultrafast is reliable.** Do not call Ultrafast flaky. OpenRouter Decisions misconfig, missing `OPENROUTER_API_KEY`, or Decisions HTTP 4xx is **config/env**, not an Ultrafast flake — fix the key/route and re-run the scout. |
| Defect schema | Prefer `docs/schemas/ux-defect-report.v1.json` (`summary.json` + `report.md` with `## Defects`). See PDD UX defect exploration. |

Oracle (product truth): click → observable change within 3s, else defect. Blank root / uncaught throw → **P0**. Details in [`docs/PDD_UX_DEFECT_EXPLORATION.md`](PDD_UX_DEFECT_EXPLORATION.md) §2–3.

## Jev / OpenRouter Decisions — QA harness only

- **Do not** call Jev or OpenRouter Decisions from **product / learner-facing code**.
- **Ultrafast** (and any Jev Decisions use for UX scouting) is a **QA harness only**, using OpenRouter Decisions against the exploratory agent — not an in-app tutor path.
- Product LLM routing stays on InferHub / IRE as documented in [`docs/webapp/LLM_ROUTE.md`](webapp/LLM_ROUTE.md). Hosted Jev in product grading (if any) is a separate, already-documented tier — it is **not** permission to wire Ultrafast into the player or into GitHub Actions.

## Runners (how-to)

### 1) Ultrafast scout (local — required for FE claims)

**Not a CI job.** Agents run this on Teresa-Pujan (Windows) or a box with `JEV_ULTRAFAST_ROOT` + `OPENROUTER_API_KEY`.

Windows / **Teresa-Pujan** (preferred):

```powershell
# Default Ultrafast checkout: D:\claude\jev-ultrafast (or $env:JEV_ULTRAFAST_ROOT)
# Requires OPENROUTER_API_KEY for OpenRouter Decisions (typesafe/jev-1.13)
powershell -File tools/ux-defect/Run-UltrafastScout.ps1
# Optional: -BaseUrl http://127.0.0.1:4173   /   -BaseUrl <PR preview URL>
```

Linux / agent box / Git Bash:

```bash
# From Study-os repo root
export JEV_ULTRAFAST_ROOT="${JEV_ULTRAFAST_ROOT:-../jev-ultrafast}"   # or /workspace/jev-ultrafast
./tools/frontend_qa/run_ultrafast_scout.sh https://study.design-bakery.com
# or against a PR preview URL:
./tools/frontend_qa/run_ultrafast_scout.sh "$PREVIEW_URL"
python tools/gate_ux_defect_report.py artifacts/ux-defect-ultrafast/<stamp>/summary.json
```

Checkout: **[`Pukujan/jev-ultrafast`](https://github.com/Pukujan/jev-ultrafast)** — Teresa-Pujan default `D:\claude\jev-ultrafast`. Script resolves `JEV_ULTRAFAST_ROOT`, then sibling `../jev-ultrafast`, `/workspace/jev-ultrafast`, or `D:/claude/jev-ultrafast`.

Artifacts land under `artifacts/ux-defect-ultrafast/<stamp>/` (`summary.json`, `report.md`, …). Durable crawl copies go in `docs/benchmarks/ux-defect-jev-ultrafast/<date>/` per the benchmark README.

If Decisions fails (missing key / HTTP 400): **fix OpenRouter config** and re-run — that is not an Ultrafast reliability failure.

### 2) Playwright UX + vision pass (local + CI)

Windows live defect pass:

```powershell
powershell -File tools/ux-defect/Run-PlaywrightDefectPass.ps1
```

Specs live under `web/e2e/` (SOS-0017 vision gate: `web/e2e/player-vision-gate.spec.ts`). npm script: `web` → `npm run test:e2e`.

```bash
# From Study-os repo root:
./tools/frontend_qa/run_playwright_ux.sh
PLAYWRIGHT_BASE_URL="$PREVIEW_URL" ./tools/frontend_qa/run_playwright_ux.sh
```

Requires Postgres/`TEST_DATABASE_URL` semantics for the local API stack (same as CI). Vision needs `INFERHUB_API_KEY`; without it the gate records `VISION_NOT_RUN` — that is **not** a green claim for perceptual coverage.

### P0/P1 summary gate (after Ultrafast or Playwright arms)

```bash
python tools/gate_ux_defect_report.py path/to/summary.json
```

Fails the process on **any** P0/P1. Confidence is printed for investigation and never soft-skips a blocker.

### CI (GitHub Actions)

- **Required for UI PRs:** `.github/workflows/ci.yml` job `playwright` (`npx playwright test` in `web/` after build) — Playwright + vision.
- **Ultrafast is NOT a required CI job.** Do **not** land WIP that adds `ultrafast-ux` (or any native Jev crawl) to Actions. Agent FE claims still owe a **local** Ultrafast scout receipt on the issue/PR before claiming FE works.

## Agent checklist (copy onto PR / issue)

- [ ] **Ultrafast FIRST** — local scout run (URL + artifact path + defect counts); `gate_ux_defect_report.py` exits 0
- [ ] Then local Playwright UX/vision pass (receipt path; note `VISION_NOT_RUN` if applicable)
- [ ] CI Playwright + vision green on this PR
- [ ] **No** Ultrafast GitHub Actions job required or added
- [ ] No open P0/P1 left unfixed / unfiled — P0/P1 fails the claim **regardless of confidence**
- [ ] Confidence recorded; low confidence → manual re-check notes posted
- [ ] Did **not** call Ultrafast “flaky”; OpenRouter/env failures diagnosed as config
- [ ] No new product-code Jev/OpenRouter Decisions usage

## Coordination

Prefer the existing `tools/frontend_qa/*` and `tools/ux-defect/*` entrypoints. Do **not** stack or reopen PRs that wire Ultrafast into GitHub Actions (e.g. historical `task/SOS-ultrafast-ci-gate-*` / PR #152) — Alex clarified Ultrafast is local/scout-only for FE claims.
