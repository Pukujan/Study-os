# teach_visual_v1 (Big O / DSA teach panels)

**Refs:** [#161](https://github.com/Pukujan/Study-os/issues/161) [#126](https://github.com/Pukujan/Study-os/issues/126)  
**Flag:** `STUDY_OS_TEACH_VISUAL_V1` (default on; set `0`/`false`/`off` to restore `presentation_raw`)

## What

Versioned teach visuals for DSA, **research-backed**:

- **Default (Big O):** multi-class `growth_curve` — O(1), O(log n), O(n), O(n²) on shared axes (`y_scale: log`)
- **Explain again:** curated Wikimedia complexity chart (`curated_diagram`)
- **Fractions:** `fraction_bar` with **number_line** on the default teach card
- Raw empty `growth_table` kept under `presentation_raw` for rollback

See `docs/research/TEACH_VISUAL_RESEARCH_BRIEF.md` and `docs/ops/TEACH_VISUAL_CURATION_PIPELINE.md`.

## Product fixes bundled here

1. **Worked example ≠ teach** — authored `worked_example` / `worked_example_alt` (or explain-frame fallback); never silent clone.
2. **Continue stays** on teach-only steps during Worked example / explain (`player.teach-continue`).
3. **No invent-first stick workers** on the default Big O path.

## Linguistic note

Prose stays plain short sentences (A19). **Strip numbered captions.** Visuals follow the curated pack; InferHub vision only verifies match.

## Tests

```bash
PYTHONPATH=src python -m unittest tests.test_teach_visual tests.test_big_o_worked_example -v
cd web && npm test -- --run src/visuals/visuals.test.tsx
```

## Island isolation

Learner-visible frames mount through `TeachRenderBox` (Shadow DOM). See [`TEACH_RENDER_BOX.md`](TEACH_RENDER_BOX.md).
