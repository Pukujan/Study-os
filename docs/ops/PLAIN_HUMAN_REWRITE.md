# Plain-human rewrite (mandatory post-gen)

**Status:** wired on generation/regen + serve paths  
**Refs:** [#126](https://github.com/Pukujan/Study-os/issues/126)  
**Module:** `src/study_os/web/player/human_rewrite.py` (`REWRITE_VERSION = study-os.human-rewrite.v2`)

## Why

Digit-prefixed `1) 2) 3)` teach lists were **more distracting than helpful** (Alex live). v2 emits 2–3 short plain sentences.

## What

Scrub AI tells → short sentences → plain prose (no digit lists) → teach ≤3 sentences / ~42 words. Grounding sentence first when present. Never invent facts / never grow word count.

## A19

Bars / TeachRenderBox lead. Explain again + Worked must swap/alter the diagram.

```bash
PYTHONPATH=src python -m unittest tests.test_human_rewrite -v
```

## Interactive-filled steps (#195)

When an interactive teach visual (e.g. sticks-and-boxes) **fills** the Explain card, authored `explain_md` should be **one short line or empty** — do not stack glossary paragraphs, captions that restate the UI, or in-component intro essays on top of the game. Surround copy must match golden density.

