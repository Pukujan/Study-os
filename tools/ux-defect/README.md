# UX defect local runners

Ultrafast-first for agent FE claims; CI merge gate is Playwright + vision only.
See [docs/UX_DEFECT_LOCAL_AND_CI.md](../../docs/UX_DEFECT_LOCAL_AND_CI.md) and [docs/AGENT_FRONTEND_QA.md](../../docs/AGENT_FRONTEND_QA.md).

**Teresa-Pujan (Windows)** — Ultrafast checkout default `D:\claude\jev-ultrafast` (override with `$env:JEV_ULTRAFAST_ROOT`). Requires `OPENROUTER_API_KEY` for Decisions (config failures ≠ Ultrafast flake).

```powershell
# 1) Ultrafast FIRST
powershell -File tools/ux-defect/Run-UltrafastScout.ps1
# 2) Then Playwright
powershell -File tools/ux-defect/Run-PlaywrightDefectPass.ps1
```

Bash (Linux / box):

```bash
./tools/frontend_qa/run_ultrafast_scout.sh https://study.design-bakery.com
python tools/gate_ux_defect_report.py artifacts/ux-defect-ultrafast/<stamp>/summary.json
./tools/frontend_qa/run_playwright_ux.sh
```

Do **not** wire these into GitHub Actions as an Ultrafast job.
