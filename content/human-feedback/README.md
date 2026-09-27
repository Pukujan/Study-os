# Human feedback (calibration pack)

**Refs:** [#164](https://github.com/Pukujan/Study-os/issues/164) · parent [#126](https://github.com/Pukujan/Study-os/issues/126)

Lean, **append-only** git pack for **Pukujan’s** live critiques (text + screenshots + lesson/step + tags).

## Do not invent a second database

| Signal | Canonical store | This pack’s role |
| --- | --- | --- |
| Learner step review / thumbs | Postgres `ux.feedback` (`POST /api/feedback`) | Optional mirror / pointer only |
| Decomposer pedagogy Good/Bad/Prefer | Postgres `ux.decomposer_review` (`POST /api/review/decomposer`) | Optional mirror / pointer only |
| Verbatim pedagogy calibration chats | `sessions/YYYY-MM-DD/<id>/` | Link via `promotion.session_path` |
| Chat / issue / screenshot product UX critiques | **`feedback.jsonl` + `assets/`** | Primary home |

Agents must **reuse** those tables and session folders. Never add a parallel SQLite/Postgres “human feedback” schema.

## Layout

```text
content/human-feedback/
  schema.v1.json      # entry shape
  feedback.jsonl      # append-only
  assets/             # screenshots (sha256 in entry)
  README.md
```

Ops brief: [`docs/ops/HUMAN_FEEDBACK.md`](../../docs/ops/HUMAN_FEEDBACK.md).

Append helper:

```bash
python tools/append_human_feedback.py \
  --text "…" --tag too_complex --tag prefer_graph \
  --lesson big-o-growth-families --step why_care \
  --screenshot /path/to.png --issue 164
```

## Seed coverage (2026-09-27)

`feedback.jsonl` holds the full this-session corpus (not a thin 5-row sample): numbered teach chrome, stick-worker invent reject, slow-vs-fast undersell, simpler 4-curve vs cheatsheets, research-first / catalog-wide interactives, Explain-again crash, dark mode + design-system tokens, pet jitter, fractions probe/nav + number-line research, sliding-window keep `box_index`, tutor latency, author=Pukujan.
