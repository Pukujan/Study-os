# Plain-human rewrite (mandatory post-gen)

**Status:** wired on generation/regen + serve paths  
**Refs:** [#126](https://github.com/Pukujan/Study-os/issues/126)  
**Module:** `src/study_os/web/player/human_rewrite.py` (`REWRITE_VERSION = study-os.human-rewrite.v1`)

## Why

HESI math intros and DSA teach/explain cards were reading as machine prose: long walls, AI-blog tells (`delve`, `showcasing`, `furthermore`, participle tails), hard to scan. Golden-tutor structure wants numbered short sentences; human-sounding-writing wants concrete, short, no filler.

## What it does

Deterministic post-process (no extra LLM call):

1. Scrub AI-tell words / participle tails (CGM human-sounding-writing).
2. Split walls into short sentences (≤28 words).
3. Number as `1) …` `2) …`.
4. For `teach` / `decomposition`, prefer a grounding sentence as `#1` when one already exists in the text (problem / goal / what you will practice). Never invent facts.
5. Trim to a kind-specific word budget. Never grow content-word count vs input.

## Where it hooks (live after CD)

| Surface | Hook |
| --- | --- |
| Player teach card (authored + overlay) | `presentation.effective` |
| Explain again / chat regen `teach_md` | `presentation.validate_proposal` (before validate) |
| Feedback explain / correct | `engine._learner_explain` / `_learner_correct` (attempt, confused, miss) |
| Worked example card | `engine._worked_example_payload` + `_public_worked_example` |
| HESI / pack intro + why/fix | `packs.intro_markdown`, `why_markdown`, `fix_markdown` |
| HESI pack rebuild | `tools/web_build_hesi_pack.py` (intro + rationale) |

Tutor prompt `tutor.v3.md` also asks the model for numbered grounded sentences so gen is cleaner before the pass.

## Done-when tests

```bash
PYTHONPATH=src python -m unittest tests.test_human_rewrite -v
```

Covers scrub + numbering, teach grounding preference, idempotence, presentation/engine/pack hooks.

## Skills / refs

- `/home/box/agent-data/workflows/study-os-golden-tutor/SKILL.md`
- `/home/box/agent-data/workflows/human-sounding-writing-and-plain-charts/SKILL.md`
- CGM `docs/HUMAN_SOUNDING_WRITING.md` / `human-sounding-rules.json`
