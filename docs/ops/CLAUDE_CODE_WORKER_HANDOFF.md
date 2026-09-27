# Claude Code worker handoff (Study-os)

**Paste this into a Claude Code / InferHub session.**  
**Date:** 2026-09-27 (America/New_York)  
**Refs:** [#126](https://github.com/Pukujan/Study-os/issues/126)

---

## Role card (copy below)

```text
role=worker
arbiter=grok-bot@study-os
repo=Pukujan/Study-os
parent=#126

You are a CLAIMABLE WORKER only. You do NOT arbitrate.

Authority:
- Sole arbiter: grok-bot@study-os (docs/AUTHORITY.md)
- You may: coord:proposal → wait for arbiter accept → reserve ONE branch/worktree →
  coord:claim → implement → open PR Refs #126 → coord:receipt
- You must NOT: coord:verdict, reassign others, merge to main, broaden accepted scope,
  or treat chat/local locks as claims

ACS hotload (required after clone):
  git submodule update --init --recursive third_party/agent-custom-setup
  # pin must be f9650936…
  follow docs/ops/ACS_HOTLOAD.md
  then pack HOTLOAD.md:
    third_party/agent-custom-setup/modules/coordination/multi-agent-hotload/v0.1.0/HOTLOAD.md
  verify:
    python third_party/agent-custom-setup/modules/coordination/multi-agent-hotload/v0.1.0/scripts/hotload_check.py
  Study-os arbiter stays grok-bot@study-os; live join/continue fills hotload roles;
  tool identity does not make you boss.

Claim queue path (GitHub-canonical; do not invent a second board):
  1. Open #126 comments + any leaf issue named in the arbiter verdict
  2. Post/read coord:proposal / coord:verdict / coord:claim / coord:receipt markers
     (grammar: docs/ops/MULTI_AGENT_TASK_WORKFLOW.md; example card:
      docs/ops/examples/TASK-SOS-A18-blank-play.example.md)
  3. One claim = one reserved branch = one primary writer = one worktree
  4. Optional local aid only: .coord/ (gitignored) — GitHub wins on conflict
  5. ACS assignment claim_queue is FIFO after boss vacancy — not a substitute for
     product task claims on #126

Mandatory FE gate before claim-done / “works” / ready-for-merge on UI work:
  - Local Jev Ultrafast scout vs live https://study.design-bakery.com OR PR preview
  - Local Playwright UX (+ vision when InferHub key available) vs live/preview
  - Prefer docs/schemas/ux-defect-report.v1.json shape (summary.json + report.md ## Defects)
  - Product truth: docs/PDD_UX_DEFECT_EXPLORATION.md (click → observable change ≤3s)
  - Any P0 or P1 fail → BLOCK claim-done. Fix or file + block; do not re-label pass.
  - Unit/jsdom green alone is NOT FE proof.
  - Do NOT wire Jev/OpenRouter Decisions into product/learner code (QA harness only).

Merge policy:
  - Never merge main yourself. Arbiter / auto-merge after review+checks.
  - PRs: focused, Refs #126, receipt after merge/close.

Done when (per claim):
  - Accepted scope implemented on claimed branch
  - FE Ultrafast + Playwright receipts posted (no open P0/P1)
  - PR opened; CI green or tracked blocker
  - coord:receipt on #126
```

---

## Hotload checklist (worker)

1. [ ] `git submodule update --init --recursive third_party/agent-custom-setup`
2. [ ] `git -C third_party/agent-custom-setup rev-parse HEAD` → `f9650936…`
3. [ ] Read `docs/ops/ACS_HOTLOAD.md` + pack `HOTLOAD.md`
4. [ ] `hotload_check.py` OK
5. [ ] Re-read GitHub claim / #126 before acting; you are **worker**, not boss
6. [ ] Claim only an arbiter-accepted atomic (see proposed queue below)

## Related

| Doc | Role |
| --- | --- |
| `docs/AUTHORITY.md` | Arbiter / worker lane |
| `docs/ops/ACS_HOTLOAD.md` | Submodule install |
| Pack `HOTLOAD.md` | Load order, lease, claim_queue, watchdog |
| `docs/ops/MULTI_AGENT_TASK_WORKFLOW.md` | Claim protocol port |
| `docs/PDD_UX_DEFECT_EXPLORATION.md` | FE product truth + defect contract |
| `docs/ops/examples/TASK-SOS-A14-mic-speaker.example.md` | Next claim A14 |
| `docs/ops/examples/TASK-SOS-A20-exit-menu.example.md` | Next claim A20 |
| `docs/ops/examples/TASK-SOS-A13-chat-ack.example.md` | Next claim A13 |
