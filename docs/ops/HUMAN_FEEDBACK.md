# Human feedback — append before inventing UX

**Refs:** [#164](https://github.com/Pukujan/Study-os/issues/164) · parent [#126](https://github.com/Pukujan/Study-os/issues/126)  
**Pack:** [`content/human-feedback/`](../../content/human-feedback/)

## Author

Product critiques in this pack: **`author: Pukujan`** (not "Alex").

## Rule (non-negotiable)

Before inventing or “improving” learner-visible UX (diagrams, teach chrome, Explain/Worked flows, chat ack, etc.):

1. **Read** the latest `content/human-feedback/feedback.jsonl` entries (and any linked session).
2. **Append** new Alex critiques you just heard (text + screenshot when available) **before** coding a fix or new visual.
3. **Reuse** existing stores — never stand up a parallel feedback DB.

## Where each signal goes

| Kind | Write here | Do not |
| --- | --- | --- |
| In-player 1–5 step review / thumbs | `ux.feedback` via `POST /api/feedback` | Duplicate into a new table |
| Decomposer Good/Bad/Prefer + note | `ux.decomposer_review` via `POST /api/review/decomposer` | Widen that table for chat screenshots |
| Verbatim pedagogy calibration chat | `sessions/YYYY-MM-DD/<id>/` (see existing sliding-window calibration) | Paste private exports into git |
| Chat / issue / live screenshot product critique | **Append** `content/human-feedback/feedback.jsonl` (+ `assets/`) | Invent SQLite/analytics theater |

Schema: [`content/human-feedback/schema.v1.json`](../../content/human-feedback/schema.v1.json).  
Tags (also usable as `ux.feedback.reasons` if you later promote): `too_complex`, `crash`, `prefer_graph`, `no_bullets`, `simpler_charts`, `research_first`, `interactive`, `invent_forbidden`, `prefer_dark`, `design_system`, `pet_jitter`, `author_name`, `catalog_wide`, `navigation`, `probe_missing`, `latency`, `fractions`, `other`.

## Append helper

```bash
python tools/append_human_feedback.py \
  --text "Explain again ×2 crashes" \
  --tag crash \
  --lesson big-o-growth-families \
  --source live_player \
  --screenshot ./shot.png \
  --issue 163 --issue 164
```

Idempotent on screenshot sha256: re-running with the same asset hash + identical text is rejected.

## Seed (2026-09-27)

2026-09-27 session fully ingested (Big O / Explain-crash / simpler-charts / research-first interactives / catalog-wide / dark mode + design system / pet jitter / fractions probe+nav / author=Pukujan — Refs #161 #163 #164 #165 #160 #121). Session pointer: `sessions/2026-09-27/big-o-ux-calibration/`.

## Related surfaces

- Admin rollup of `ux.feedback`: `/admin/feedback` (`web/src/pages/AdminFeedback.tsx`)
- Learner bar: `web/src/player/FeedbackBar.tsx`
- Calibration session pattern: `sessions/2026-09-04/sliding-window-pedagogy-calibration/`
