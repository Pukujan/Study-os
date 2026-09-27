# TASK-SOS-A20 — Exit lesson → home/menu (EXAMPLE CLAIM CARD)

> Promote to `tasks/TASK-SOS-NNNN-*.md` when `grok-bot@study-os` accepts.

<!-- continuity:task {"acceptance":["Play surface shows a visible Exit/Home/Leave lesson control (not only step-Back)","Activating it navigates to home/menu within 3s without blank /play/{id}","Step Back (adapt back) remains distinct from Exit","Resume of same session still shows content or ErrorBoundary — no A18 regression","Ultrafast + Playwright: D002/D007/D010 class cleared (no Missing Back/exit P1); no new P0","PR Refs https://github.com/Pukujan/Study-os/issues/126 ; CI green; coord:receipt posted"],"depends_on":[],"goal":"Add an explicit leave-lesson control to homepage/main menu without blank-play crash","id":"SOS-00XX-A20","issue_url":"https://github.com/Pukujan/Study-os/issues/126","next_action":"Worker: coord:proposal → arbiter accept → claim → implement write-first","owner":"unassigned","priority":"P1","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"queued","why":"Human-test A20 + Ultrafast D002/D007/D010: no Back/exit to main menu on play; companion Back is step-back only."} -->

- Status: queued (example) — **still needed** after A18/#150 (worked-example content fix ≠ exit control)
- Owner: unassigned → claim after arbiter accept
- Priority: **P1** (Ultrafast HIT)
- Depends on: none; do not reopen A18 blank-play unless this change regresses it

## Goal

Learner can **leave the lesson to home/menu** via a labeled control. Step-back ≠ exit.

## Why

- #126: “No Back/exit to main menu from the lesson player. Step back ≠ leave lesson.”
- Ultrafast 2026-09-27: D002/D007/D010 Missing Back/exit on play.
- Today companion **Back** calls `api.adapt(..., "back")` (prior step), not route home.

## Write-first brief

1. Add **Exit lesson** / **Home** (name per CGM HSW) on play chrome — header or companion footer — `data-track="player.exit"`.
2. On click: navigate to home route (`App` home/lanes); optionally `save progress` first if already wired; **never** leave empty lavender `/play/{id}`.
3. Keep step-Back as-is; aria-labels must distinguish Exit vs Back.
4. Regression: ErrorBoundary + Resume still bounded (A18 class).
5. Playwright: control visible on `/play/{id}`; click → home URL. Ultrafast must not re-HIT missing exit.

## Allowed files (suggested)

- `web/src/pages/Player.tsx`, `web/src/player/CompanionPanel.tsx`, `web/src/App.tsx` (routing only as needed)
- `web/e2e/` focused spec
- Avoid curriculum / tutor prompt churn

## Branch hint

- `task/SOS-player-exit-menu-2026-09-27`

## Claim markers

```markdown
<!-- coord:claim issue=126 agent=claude-code@teresa-inferhub
     branch=task/SOS-player-exit-menu-2026-09-27 sha=pending state=active atomic=A20 -->
## Claim — A20 exit lesson to menu
```
