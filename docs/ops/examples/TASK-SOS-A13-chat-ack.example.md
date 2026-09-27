# TASK-SOS-A13 — Study-buddy chat ack (EXAMPLE CLAIM CARD)

> Promote to `tasks/TASK-SOS-NNNN-*.md` when `grok-bot@study-os` accepts.

<!-- continuity:task {"acceptance":["On Send, UI shows immediate mechanical ack within 3s (pending bubble or hold-on/lemme-think copy) even before tutor tokens","If still waiting ~4s, visible nudge refreshes; then real reply replaces pending","No silent drop: error state shown on transport failure","Intermittent misses fixed under load (double-send / slow InferHub)","Ultrafast + Playwright: study-buddy chat ack class passes; no new P0/P1","PR Refs https://github.com/Pukujan/Study-os/issues/126 ; CI green; coord:receipt posted"],"depends_on":[],"goal":"Reliable chat acknowledgement: immediate mechanical ack, ~4s nudge, then real reply","id":"SOS-00XX-A13","issue_url":"https://github.com/Pukujan/Study-os/issues/126","next_action":"Worker: coord:proposal → arbiter accept → claim → implement write-first","owner":"unassigned","priority":"P1","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"queued","why":"#126 A13 deferred after A12: chat ack latency intermittent; Ultrafast checklist chat no ack exercised; product truth requires ack/pending/sent/error within 3s."} -->

- Status: queued (example)
- Owner: unassigned → claim after arbiter accept
- Priority: **P1** (intermittent; FE gate treats silent drop as ≥P1)
- Depends on: A12 path landed on main — OK to claim now

## Goal

Sending a Study-buddy message **always** shows feedback within 3s; never a silent drop.

## Why

- #126 A13: immediate mechanical ack (“hold on / lemme think…”), nudge ~4s if waiting, then real reply.
- `PDD_UX_DEFECT_EXPLORATION.md`: Study-buddy chat ack row.
- Companion already has a typing indicator — harden so it cannot miss under slow/error paths.

## Write-first brief

1. On submit: **optimistically** append user bubble + pending/ack tutor row **before** await `api.tutor` (or equivalent).
2. ~4s timer: if still pending, update ack copy (nudge); clear on reply/error.
3. On failure: pending → error chip + retry; never remove user bubble silently.
4. Guard double-submit while `busy`.
5. Playwright: Send → pending visible ≤3s; mock slow reply → nudge; mock fail → error.
6. Out of scope: A15 over-pivot tutor policy; regenerate_presentation changes.

## Allowed files (suggested)

- `web/src/player/CompanionPanel.tsx`, `TutorPanel.tsx` if shared
- Focused unit/e2e tests
- Avoid backend prompt rewrites unless required for ack-only copy

## Branch hint

- `task/SOS-player-chat-ack-2026-09-27`

## Claim markers

```markdown
<!-- coord:claim issue=126 agent=claude-code@teresa-inferhub
     branch=task/SOS-player-chat-ack-2026-09-27 sha=pending state=active atomic=A13 -->
## Claim — A13 study-buddy chat ack
```
