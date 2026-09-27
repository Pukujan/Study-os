# AGENT_FRONTEND_QA — Mandatory frontend QA (Ultrafast + Playwright)

Status: **MANDATORY** for every agent working on Study-os frontend / UI  
Parent: #126  
Date: 2026-09-27  
Related: [`docs/PDD_UX_DEFECT_EXPLORATION.md`](PDD_UX_DEFECT_EXPLORATION.md), [`docs/webapp/SOS-0017_E2E_VISION_GATE_PDD.md`](webapp/SOS-0017_E2E_VISION_GATE_PDD.md), [`docs/benchmarks/ux-defect-jev-ultrafast/README.md`](benchmarks/ux-defect-jev-ultrafast/README.md), [`docs/webapp/DESIGN_SYSTEM.md`](webapp/DESIGN_SYSTEM.md) (#165)

## Mandate (Alex)

Before claiming a frontend change works, or opening/merging a PR that touches UI:

1. Run a **local Ultrafast scout** against live `https://study.design-bakery.com` **or** the PR preview.
2. Run a **Playwright UX defect pass** (deterministic + vision gate) against live or the PR preview / local preview stack.
3. **CI** on that PR must also run **Playwright + vision** and an **Ultrafast crawl** (see runners below). Do not treat green unit/jsdom tests alone as FE proof.

This applies to **all agents** (Grok, Claude Code, InferHub workers, humans driving agents). No exceptions for “small” UI diffs.

## Pass / fail rules

| Rule | Requirement |
| --- | --- |
| P0 / P1 | Any **P0 or P1** fail → do **not** claim green. Fix it, or file a tracked defect and **block** merge / “works” claims until resolved or explicitly waived by the arbiter with a linked issue. |
| Low confidence | Agent **must manually re-check** why confidence is low. Do **not** skip the gate or re-label as pass. |
| Confidence recorded | Record confidence (and model/receipt ids) on the issue/PR. Confidence **does not waive** P0/P1. |
| Defect schema | Prefer `docs/schemas/ux-defect-report.v1.json` (`summary.json` + `report.md` with `## Defects`). See PDD UX defect exploration. |

Oracle (product truth): click → observable change within 3s, else defect. Blank root / uncaught throw → **P0**. Details in [`docs/PDD_UX_DEFECT_EXPLORATION.md`](PDD_UX_DEFECT_EXPLORATION.md) §2–3.

## Jev / OpenRouter Decisions — QA harness only

- **Do not** call Jev or OpenRouter Decisions from **product / learner-facing code**.
- **Ultrafast** (and any Jev Decisions use for UX scouting) is a **QA harness only**, using OpenRouter Decisions against the exploratory agent — not an in-app tutor path.
- Product LLM routing stays on InferHub / IRE as documented in [`docs/webapp/LLM_ROUTE.md`](webapp/LLM_ROUTE.md). Hosted Jev in product grading (if any) is a separate, already-documented tier — it is **not** permission to wire Ultrafast into the player.

## Runners (how-to)

### Ultrafast scout (local)

Windows (preferred on Teresa-Pujan):

```powershell
powershell -File tools/ux-defect/Run-UltrafastScout.ps1
```


Checkout / install: **[`Pukujan/jev-ultrafast`](https://github.com/Pukujan/jev-ultrafast)** — on Alex’s Windows box typically `D:\claude\jev-ultrafast`.

```bash
# From Study-os repo root (Linux/box or Git Bash):
./tools/frontend_qa/run_ultrafast_scout.sh https://study.design-bakery.com
# or against a PR preview URL:
./tools/frontend_qa/run_ultrafast_scout.sh "$PREVIEW_URL"
```

Stub resolves `JEV_ULTRAFAST_ROOT` (default: sibling `../jev-ultrafast`, or `D:/claude/jev-ultrafast` when present) and prints the one-line invocation expected by that harness. Artifacts should land under Ultrafast’s `artifacts/` **and** (when recording a durable crawl) be copied into `docs/benchmarks/ux-defect-jev-ultrafast/<date>/` per the benchmark README.

### Playwright UX + vision pass (local)

Windows live defect pass:

```powershell
powershell -File tools/ux-defect/Run-PlaywrightDefectPass.ps1
```


Specs live under `web/e2e/` (SOS-0017 vision gate: `web/e2e/player-vision-gate.spec.ts`). npm script: `web` → `npm run test:e2e`.

```bash
# From Study-os repo root:
./tools/frontend_qa/run_playwright_ux.sh
# Optional: point at an already-running preview (see script env notes)
PLAYWRIGHT_BASE_URL="$PREVIEW_URL" ./tools/frontend_qa/run_playwright_ux.sh
```

Requires Postgres/`TEST_DATABASE_URL` semantics for the local API stack (same as CI). Vision needs `INFERHUB_API_KEY`; without it the gate records `VISION_NOT_RUN` — that is **not** a green claim for perceptual coverage.

### P0/P1 summary gate

```bash
python tools/gate_ux_defect_report.py path/to/summary.json
```

Fails the process on **any** P0/P1. Confidence is printed for investigation and never soft-skips a blocker. Use after Ultrafast or Playwright arms emit `summary.json`.

### CI

- **Playwright + vision:** `.github/workflows/ci.yml` job `playwright` (`npx playwright test` in `web/` after build). Required for UI PRs.
- **Ultrafast crawl:** wire via the Ultrafast harness in CI (follow-on / stack with any Ultrafast-CI or local-runner PR). Until that job is green on the PR, agents still owe a **local** Ultrafast scout receipt on the issue before claiming FE works.

## Agent checklist (copy onto PR / issue)

- [ ] Local Ultrafast scout run (URL + artifact path + defect counts)
- [ ] Local Playwright UX/vision pass (receipt path; note `VISION_NOT_RUN` if applicable)
- [ ] CI Playwright + vision green on this PR
- [ ] CI Ultrafast crawl green **or** tracked blocker + local scout receipt linked
- [ ] `python tools/gate_ux_defect_report.py <summary.json>` exits 0 (no P0/P1)
- [ ] No open P0/P1 left unfixed / unfiled
- [ ] Confidence recorded; low confidence → manual re-check notes posted
- [ ] No new product-code Jev/OpenRouter Decisions usage

## Coordination

If an open PR already lands Ultrafast-CI wiring or a local-runner package, **stack or rebase** this policy PR onto that work rather than duplicating harness entrypoints. Prefer extending `tools/frontend_qa/*` stubs over inventing a second runner path.

## Coordination with Ultrafast-CI / local-runner

A parallel agent branch `task/SOS-ultrafast-ci-gate-2026-09-27` (and any follow-on PR) is expected to land:

- `tools/run_jev_ultrafast_ux_crawl.py` — full guest Ultrafast crawl → `summary.json`
- `tools/ux-defect/ux-defect-pass.cjs` — Playwright live UX defect pass
- CI job(s) invoking those + `tools/gate_ux_defect_report.py`

Until that merges, agents still owe a **local** Ultrafast scout (from [`Pukujan/jev-ultrafast`](https://github.com/Pukujan/jev-ultrafast) / `D:\claude\jev-ultrafast`) plus Playwright via `./tools/frontend_qa/run_playwright_ux.sh`, and must not claim FE green without receipts. Prefer **stacking/rebasing** onto that CI PR rather than inventing a second runner path; the stubs above already prefer the in-repo scripts when present.
