# TASK-SOS-A18 — Blank play / worked-example crash (EXAMPLE CLAIM CARD)

> Example only for the multi-agent port. Promote to `tasks/TASK-SOS-NNNN-*.md` with a real SOS id when Grok Bot accepts the queue.

<!-- continuity:task {"acceptance":["Chat or chip Show a worked example does not unmount the React root or blank the app","Browser back from play never leaves an empty lavender shell without recovery UI","Resume of the same session shows real content or ErrorBoundary Retry/Go home — never a permanent blank /play/{id}","Public worked_example view shape exposes md (and/or safe steps) so Player cannot throw on missing stripped solution_md","PR opened Refs https://github.com/Pukujan/Study-os/issues/126 ; CI green; coord:receipt posted"],"depends_on":[],"goal":"Eliminate P0 blank-play crash class: worked-example adapt + back/Resume remount whitescreen","id":"SOS-00XX","issue_url":"https://github.com/Pukujan/Study-os/issues/126","next_action":"Worker: reserve branch, marker push, coord:claim, implement on A18 worktree, open PR","owner":"unassigned","priority":"P0","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"queued","why":"#126 human-test: worked example and Resume blank the play page; needs InferHub claimable atomic under Grok Bot authority"} -->

- Status: queued (example)
- Owner: unassigned → claim via `coord:claim` after arbiter accept
- Priority: P0
- Depends on: none (parallel with A12; **do not** share A12 worktree)

## Goal

Stop blank play: worked-example path and Resume/back must never whitescreen the player.

## Why

#126 ops feedback: “Show a worked example” and Resume at `/play/{session}` produced an empty shell; root cause class is stripped `solution_md` vs UI expecting `md`/`steps_md`, missing ErrorBoundary, and remount keeping `card_mode=worked_example`.

## Allowed files (suggested)

- `src/study_os/web/player/` (engine view / adapt public shape)
- `web/src/player/Player.tsx`, worked-example card, ErrorBoundary wiring on `main`/`App`/`Player`
- `web/src/player/CompanionPanel.tsx` (adapt example path only as needed)
- Focused tests under `tests/` + any existing player unit tests
- No private transcripts; no product task-board UI

## Branch / worktree hints

- Branch: `task/SOS-player-blank-play-2026-09-26`
- Worktree hint (Teresa): `D:\claude\_workspace\study-os-A18`
- Model hint: InferHub `cb/deepseek-v4.1-flash` (BYOK) — executor only

## Claim markers (worker posts after arbiter accept)

```markdown
<!-- coord:claim issue=126 agent=claude-code@teresa-inferhub
     branch=task/SOS-player-blank-play-2026-09-26 sha=pending state=active -->
## Claim — A18 blank play / worked-example crash
```

Arbiter accept shape:

```markdown
<!-- coord:verdict on=P-126-A18 by=grok-bot@study-os decision=accepted -->
**Primary writer:** claude-code@teresa-inferhub  
**Branch:** task/SOS-player-blank-play-2026-09-26
```

## Acceptance criteria

- [ ] Worked example chip does not blank the app
- [ ] Back navigation does not leave a dead empty root
- [ ] Resume shows content or bounded error UI
- [ ] Public worked_example shape is render-safe
- [ ] PR Refs #126; CI green; receipt posted

## Out of scope

- A12 arrow/explain work on the other worktree
- A19–A24 curriculum/pet/homepage items
- Product UI for the agent task board
- Copying private notes into the public repo

## Handoff

Grok Bot owns verdict/review. Worker claims → implements → PR → receipt. If A18 already merged as follow-up PR, mark this example `completed` and cut a new leaf for remaining blank-play regressions only.
