# UX defect passes: local scout vs CI merge gate

Refs #126. Mandate: [AGENT_FRONTEND_QA.md](./AGENT_FRONTEND_QA.md). Contract: [PDD_UX_DEFECT_EXPLORATION.md](./PDD_UX_DEFECT_EXPLORATION.md), schema [schemas/ux-defect-report.v1.json](./schemas/ux-defect-report.v1.json).

## Roles

| Surface | Role | Fails on |
| --- | --- | --- |
| **Local scout** (`tools/ux-defect/Run-*.ps1`) | Fast feedback while fixing against live `https://study.design-bakery.com` (or `E2E_BASE_URL` / `BASE_URL`) | Any **P0/P1** in `summary.json` |
| **CI merge gate** (`web/e2e/ux-defect-controls.spec.ts` + existing vision gate) | Blocks merge on stub-server asserts for Ultrafast P0/P1 controls | Hard Playwright assert failures |

Low-confidence / intermittent findings (info notes, flaky live chat, OS speech) stay in `summary.detail.json` or test `pending` annotations — **agents re-check those manually** on live; do not invent a green.

Ultrafast CI job (native Jev crawl in Actions) is owned by a separate PR — do not duplicate that workflow here.

## One-liners (Windows)

From the Study-os repo root:

```powershell
# Playwright deterministic live scout
powershell -File tools/ux-defect/Run-PlaywrightDefectPass.ps1

# Jev Ultrafast exploratory live scout (needs OPENROUTER_API_KEY; uses D:\claude\jev-ultrafast)
powershell -File tools/ux-defect/Run-UltrafastScout.ps1
```

Optional: `-BaseUrl http://127.0.0.1:4173`, `-Headed`, `$env:JEV_ULTRAFAST_ROOT`, `$env:MAX_ACTIONS`.

Artifacts: `artifacts/ux-defect-playwright/<stamp>/` and `artifacts/ux-defect-ultrafast/<stamp>/` (`summary.json` schema-shaped, plus `report.md`, screenshots, detail JSON).

## CI asserts (stub server)

`web/e2e/ux-defect-controls.spec.ts` locks:

- **Worked example** changes surface on HESI fractions (hero Try → `fractions-compare`)
- **Exit/Back** (brand / `nav.home`) leaves `/play/`
- **Companion Message + Send** shows tutor/system/thinking ack within 20s
- **Read aloud / Voice input / Open Message** affordances present; companion speaker toggles `aria-label`; OS speech marked **pending** (Refs #126) for live re-check
- **player.back** after worked example must not blank the shell

Same e2e stub server as `player-vision-gate.spec.ts` (`web/e2e/server.mjs`).

## Related wrappers

Bash entrypoints (also used from AGENTS mandate):

```bash
./tools/frontend_qa/run_ultrafast_scout.sh https://study.design-bakery.com
./tools/frontend_qa/run_playwright_ux.sh
# Live PW defect harness:
PLAYWRIGHT_UX_DEFECT_PASS=1 ./tools/frontend_qa/run_playwright_ux.sh
```

P0/P1 gate: `python tools/gate_ux_defect_report.py path/to/summary.json`.
