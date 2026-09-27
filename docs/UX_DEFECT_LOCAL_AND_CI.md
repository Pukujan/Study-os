# UX defect passes: local Ultrafast scout vs CI Playwright gate

Refs #126. Mandate: [AGENT_FRONTEND_QA.md](./AGENT_FRONTEND_QA.md). Contract: [PDD_UX_DEFECT_EXPLORATION.md](./PDD_UX_DEFECT_EXPLORATION.md), schema [schemas/ux-defect-report.v1.json](./schemas/ux-defect-report.v1.json).

**Alex clarification:** Ultrafast runs **FIRST** for agents/local FE claims. It is **not** a required GitHub Actions job. CI stays **Playwright + vision only**.

## Roles

| Surface | Role | Fails on |
| --- | --- | --- |
| **Local Ultrafast scout** (`tools/ux-defect/Run-UltrafastScout.ps1`, `tools/frontend_qa/run_ultrafast_scout.sh`) | **First** FE claim gate — exploratory guest crawl vs live `https://study.design-bakery.com` (or `E2E_BASE_URL` / `BASE_URL` / PR preview) | Any **P0/P1** in `summary.json` (**regardless of confidence**) |
| **Local Playwright scout** (`tools/ux-defect/Run-PlaywrightDefectPass.ps1`) | Deterministic live follow-up after Ultrafast | Any **P0/P1** in `summary.json` |
| **CI merge gate** (`web/e2e/ux-defect-controls.spec.ts` + vision gate) | Blocks merge on stub-server asserts for Ultrafast-found P0/P1 controls + vision | Hard Playwright assert failures |

**Ultrafast is reliable.** Do not label Ultrafast flaky. OpenRouter Decisions misconfig / missing key / Decisions HTTP 4xx ≠ Ultrafast — fix env and re-run. Low-confidence Decisions rows and live-only notes (e.g. OS speech pending) stay in `summary.detail.json` or test `pending` annotations — **agents re-check those manually** on live; do not invent a green. Confidence never soft-skips P0/P1.

**Do not add Ultrafast to Actions.** No `ultrafast-ux` (or similar) workflow job. Historical WIP that added Ultrafast to CI is superseded by this policy.

## One-liners (Windows / Teresa-Pujan)

From the Study-os repo root on **Teresa-Pujan** (default Ultrafast path `D:\claude\jev-ultrafast`):

```powershell
# 1) Jev Ultrafast exploratory live scout FIRST (needs OPENROUTER_API_KEY)
powershell -File tools/ux-defect/Run-UltrafastScout.ps1

# 2) Playwright deterministic live scout
powershell -File tools/ux-defect/Run-PlaywrightDefectPass.ps1
```

Optional: `-BaseUrl http://127.0.0.1:4173`, `-Headed`, `$env:JEV_ULTRAFAST_ROOT`, `$env:MAX_ACTIONS`.

Artifacts: `artifacts/ux-defect-ultrafast/<stamp>/` and `artifacts/ux-defect-playwright/<stamp>/` (`summary.json` schema-shaped, plus `report.md`, screenshots, detail JSON).

## CI asserts (stub server) — Playwright only

`web/e2e/ux-defect-controls.spec.ts` locks:

- **Worked example** changes surface on HESI fractions (hero Try → `fractions-compare`)
- **Exit/Back** (brand / `nav.home`) leaves `/play/`
- **Companion Message + Send** shows tutor/system/thinking ack within 20s
- **Read aloud / Voice input / Open Message** affordances present; companion speaker toggles `aria-label`; OS speech marked **pending** (Refs #126) for live re-check
- **player.back** after worked example must not blank the shell

Same e2e stub server as `player-vision-gate.spec.ts` (`web/e2e/server.mjs`).

## Related wrappers

Bash entrypoints (also used from AGENTS mandate) — Ultrafast first:

```bash
./tools/frontend_qa/run_ultrafast_scout.sh https://study.design-bakery.com
python tools/gate_ux_defect_report.py artifacts/ux-defect-ultrafast/<stamp>/summary.json
./tools/frontend_qa/run_playwright_ux.sh
# Live PW defect harness:
PLAYWRIGHT_UX_DEFECT_PASS=1 ./tools/frontend_qa/run_playwright_ux.sh
```
