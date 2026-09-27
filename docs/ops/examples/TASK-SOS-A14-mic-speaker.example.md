# TASK-SOS-A14 — Mic / speaker controls (EXAMPLE CLAIM CARD)

> Promote to `tasks/TASK-SOS-NNNN-*.md` when `grok-bot@study-os` accepts.

<!-- continuity:task {"acceptance":["Read aloud / speaker click yields visible state change within 3s (speaking/on/off/muted/unavailable label) or control is hidden when speechSynthesis unavailable","Voice input / mic click yields visible state change within 3s (listening/error/unsupported) or control is hidden when SpeechRecognition unavailable","CompanionPanel mic/speaker match the same contract (no unlabeled emoji-only dead controls)","Ultrafast scout + Playwright pass with no new P0/P1 on mic-speaker; gate_ux_defect_report exits 0 for this class","PR Refs https://github.com/Pukujan/Study-os/issues/126 ; CI green; coord:receipt posted"],"depends_on":[],"goal":"Make player + Study-buddy voice controls honest: working with labeled state, or hidden until supported","id":"SOS-00XX-A14","issue_url":"https://github.com/Pukujan/Study-os/issues/126","next_action":"Worker: coord:proposal → arbiter accept → claim branch → implement write-first","owner":"unassigned","priority":"P1","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"queued","why":"Ultrafast 2026-09-27: D005 Read aloud no-op; D008/D009 Voice input no-op. Human-test A14: TTS/mic dead or unclear in player + Study buddy."} -->

- Status: queued (example)
- Owner: unassigned → claim after arbiter `coord:verdict decision=accepted`
- Priority: **P1** (Ultrafast)
- Depends on: none (parallel OK; **do not** share another atomic’s worktree)

## Goal

Voice affordances must either **work with an observable state change ≤3s** or be **hidden/disabled with a clear label**. No silent no-ops.

## Why

- #126 human-test A14: speaker/TTS no-op; mic weird/unlabeled; same in Study buddy.
- Ultrafast crawl `docs/benchmarks/ux-defect-jev-ultrafast/2026-09-27/`: D005, D008, D009.
- Product truth: `docs/PDD_UX_DEFECT_EXPLORATION.md` — Mic / speaker row.

## Write-first brief (implementer)

1. **Inventory** `web/src/player/VoiceControls.tsx` and companion mic/speaker in `CompanionPanel.tsx` — today speak/mic can return early with **no DOM change** (Ultrafast fail).
2. **Prefer wire over remove:** on click set `aria-pressed` / status text (`Speaking…` / `Listening…` / `Voice unavailable in this browser`) within 3s; clear on end/error.
3. If API missing: **do not render** the button (or render disabled + “Unavailable”) — never a dead emoji.
4. Optional: short Playwright asserting label/state toggle; Ultrafast scout must not re-hit D005/D008/D009 as P1.
5. Out of scope: new cloud STT/TTS vendors; product Jev wiring.

## Allowed files (suggested)

- `web/src/player/VoiceControls.tsx`, `CompanionPanel.tsx`, related CSS
- Focused tests under `web/src/player/` or `web/e2e/`
- No private transcripts; no InferHub product-path changes unless needed for labels only

## Branch hint

- `task/SOS-player-mic-speaker-2026-09-27`

## Claim markers

```markdown
<!-- coord:claim issue=126 agent=claude-code@teresa-inferhub
     branch=task/SOS-player-mic-speaker-2026-09-27 sha=pending state=active atomic=A14 -->
## Claim — A14 mic/speaker honesty
```
