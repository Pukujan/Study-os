# Study-os UX defect crawl — 2026-09-27 (Jev Ultrafast)

Durable record of the live guest UX defect crawl. Refs #126 #147.

| Field | Value |
| --- | --- |
| **Date (ET)** | 2026-09-27 ~01:48–01:50 ET (UTC 05:48–05:50) |
| **Live URL** | https://study.design-bakery.com |
| **Agent** | jev-ultrafast (OpenRouter Decisions, model `typesafe/jev-1.13`; no TypeSafe key) |
| **Actions** | 75 (cap 140) |
| **Decisions** | 103 (OpenRouter Decisions OK) |
| **Defects** | 11 (1×P0, 8×P1, 2×P2) |
| **P0** | **D004** — Dead/no-op control: Worked example (fractions play `/play/62028e19-…`) |
| **Duration** | 36.42s |
| **Source artifact id** | `20260927-054810` |

## Product truth / schema

- PDD: [docs/PDD_UX_DEFECT_EXPLORATION.md](../../../PDD_UX_DEFECT_EXPLORATION.md) (lands via #147 / PR #148)
- Schema: [docs/schemas/ux-defect-report.v1.json](../../../schemas/ux-defect-report.v1.json)

## Artifacts in this folder

| File | Role |
| --- | --- |
| [report.md](./report.md) | Human summary with `## Defects` |
| [summary.json](./summary.json) | Machine summary (defect list + phases) |
| [actions.jsonl](./actions.jsonl) | One JSON object per action |
| [decisions.jsonl](./decisions.jsonl) | One JSON object per OpenRouter decision |
| [run.log](./run.log) | Harness log (local paths scrubbed; no secrets) |

**Not included:** screenshots / binaries (optional; prior Windows IPC screenshot timeout — D001). Playwright results: **placeholder for later add**.

## Defect highlights

1. **P0 D004** — Worked example no-op on fractions lesson
2. **P1** — Missing Back/exit on play (D002/D007/D010); dead Read aloud / Open Message / Voice input / Open Your answer
3. **P2** — Screenshot IPC timeout (harness); possible teach/probe spoil (D003)

## Method (short)

Pass/fail: after each non-wait action, require URL/text/fingerprint change within ~3s; else DEFECT. Multi-phase goals with action cap 140. See PDD §3.