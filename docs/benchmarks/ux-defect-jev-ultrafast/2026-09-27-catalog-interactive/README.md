# Ultrafast scout receipt — 2026-09-27 (catalog interactive / #161)

**Target:** https://study.design-bakery.com

## Result

Local Ultrafast scout **blocked on harness deps** in this box (`browser_harness` missing after cloning `jev-ultrafast`). Tracked blocker — not a soft-skip.

## Companion FE proof

- `PYTHONPATH=src` unittest: `test_interactive_exercise` + `test_teach_visual` green
- `web` typecheck + vitest (markdown, TeachRenderBox, InteractiveVisual, visuals) green
- Playwright UX defect desktop controls green earlier in session (`E2E_PYTHON=/workspace/venv311/bin/python3`)
- CI `playwright` job required on this PR
