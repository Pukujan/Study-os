# UX defect local scouts

Local UX defect scouts live under `tools/ux-defect/` (PowerShell) and `tools/frontend_qa/` (bash).

**Order:** Ultrafast first (agent FE claims), then Playwright. Ultrafast is **not** a GitHub Actions job.

```powershell
# Teresa-Pujan: D:\claude\jev-ultrafast + OPENROUTER_API_KEY
powershell -File tools/ux-defect/Run-UltrafastScout.ps1
powershell -File tools/ux-defect/Run-PlaywrightDefectPass.ps1
```

See `docs/UX_DEFECT_LOCAL_AND_CI.md` and `docs/AGENT_FRONTEND_QA.md`.
