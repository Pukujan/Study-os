# teach_visual_v1 (Big O / DSA teach panels)

**Refs:** [#126](https://github.com/Pukujan/Study-os/issues/126)  
**Flag:** `STUDY_OS_TEACH_VISUAL_V1` (default on; set `0`/`false`/`off` to restore `presentation_raw`)

## What

Reversible versioned teach visuals for DSA (starting with Big O `why_care`):

- Default metaphor: `growth_workers` (stick-figure code workers + number boxes)
- Alternate: `growth_curve` (SVG growth lines)
- Raw empty `growth_table` kept under `presentation_raw` for rollback

## Product fixes bundled here

1. **Worked example ≠ teach** — authored `worked_example` / `worked_example_alt` (or explain-frame fallback); never silent clone.
2. **Continue stays** on teach-only steps during Worked example / explain (`player.teach-continue`).

## Linguistic note

Prose stays simple numbered sentences (A19). No hard must-match-diagram rule; visuals are a separate upgrade. Prefer naming what is on screen when regenerating.

## Tests

```bash
PYTHONPATH=src python -m unittest tests.test_big_o_worked_example -v
cd web && npm test -- --run src/visuals/visuals.test.tsx
```
