# SOS-0014 — mascot locomotion evidence

Captured against the branch-local build (`web/dist` served by `web/e2e/server.mjs`),
desktop 1440×900, headless Chromium. The harness steps the *live* sprite element
through the same `background-position` formula `Sprite` uses, so these prove the
sheet divides cleanly into N distinct frames with no bleed from a neighbouring cell.

| File | Sheet | Cell | Sheet size | Frames |
|---|---|---|---|---|
| `walk-frames.png` | `/mascot/pet-walk.webp` | 105×128 (at 128px render height) | 315×256 | 6 (3 cols × 2 rows) |
| `turn-frames.png` | `/mascot/pet-turn.webp` | 105×128 | 210×256 | 4 (2 cols × 2 rows) |

## What these show

- **Walk** — a real 6-frame leg cycle; the character is authored facing **right**,
  which is why `Pet` mirrors the sprite when `facing === "left"`. Legs alternate
  f0→f5; the pet is no longer sliding on the idle sheet.
- **Turn** — a 4-frame right → front → left sequence. Because the sheet already
  covers right-to-left, `Pet` mirrors it only when the *pre-turn* facing was left.

## Reproduce

```sh
cd web && npm run build
# branch-local server against a throwaway Postgres
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/postgres \
  E2E_PYTHON=.venv-ci/Scripts/python.exe node web/e2e/server.mjs &
node artifacts/a13-repro/sprite-contact-sheet.cjs http://127.0.0.1:4173
```

Raw per-frame captures from a live walk (`data-pet-activity="walk"` sampling) land
in `artifacts/a13-repro/pet-walk/`. Those are scratch, not committed.

## Not covered here

Live-site verification at 390×844 and 1440×900 is still required by the goal-level
DoD; these are local-build captures. The frame-index sweeps (100 seeds × 200 events,
`M-P1`–`M-P3`) are the automated guards in `web/src/mascot/locomotion.test.ts`.
