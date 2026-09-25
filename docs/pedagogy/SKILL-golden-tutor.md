---
name: study-os-golden-tutor
description: >-
  Use this when writing or reviewing Study OS tutor/coding-agent lesson steps,
  sliding-window (or DSA) micro-teaching, PIR step text, agent-vs-agent tutor
  evals, or any prompt that must follow Alex's calibrated pedagogy. Prefer the
  machine-readable golden dataset over the short golden markdown alone.
---

# Study OS golden tutor skill

## When to use

Use this skill whenever you:

- author or rewrite a tutor step, probe, or repair
- build agent-vs-agent tutor evals
- draft a system prompt for a lesson/coding tutor agent
- check whether a lesson still matches the 2026-09-04 calibration

Do **not** assume the short files under `domains/dsa/sliding-window/golden/*.md` are enough by themselves. The durable pattern lives in the long transcript extract:

`domains/dsa/sliding-window/golden/dataset/`

## Read these files (in order)

1. `dataset/moat.md` — why multi-representation + stepwise goals is the moat
2. `dataset/representation_playbook.md` — which representation for which moment
3. `dataset/anti_patterns.json` — things Alex rejected (with transcript citations)
4. `dataset/moves.jsonl` — one teaching move per line (goal, prompt, on_correct/on_wrong, arrow rules, citations, `jev_scores`)
5. `dataset/diagrams.json` — intro vs exercise vs correction diagram variants
6. `dataset/rankings.md` / `jev_rank` fields — relative quality signals (not ground truth)
7. `dataset/manifest.json` — versions, source hashes, Jev spend

Also keep the two short goldens and `conformance-oracle.v0.1.json` as fixtures the PIR already compiles.

## Checklist before writing a lesson step

- [ ] Exactly **one** new concept/relation
- [ ] Same representation family as the surrounding steps (default: box/index ASCII)
- [ ] Intro/correction may use arrows/circles; **exercise must not leak the answer**
- [ ] Prompt asks a tiny, checkable question
- [ ] `on_correct`: brief confirm + show why on the **same** chart
- [ ] `on_wrong`: give right answer + show why on same chart + reassure + **different** retry + verify again before advance
- [ ] Partial answers keep the correct part and ask only for the missing piece
- [ ] No mastery claim; stop at assembled-but-unproven when you hit the golden boundary
- [ ] Not in `anti_patterns.json` (no mermaid step dumps, no text walls, no premature formulas, no removing the box early, no advancing after one post-error correct)

## Eval against moves.jsonl

For each authored step, find the nearest `moves.jsonl` row by `concept` and check:

1. goal text is a subset of that move's goal (not a bundle of later goals)
2. diagram id is an intro/exercise/correction variant from `diagrams.json` with matching `when`
3. `arrows_circles_allowed` matches the move
4. expected answer patterns do not appear inside the exercise diagram
5. Jev rank is a hint only — **transcript citations win** if scores disagree

## Repeated system prompt (copy-paste)

Paste the block below into tutor / coding-agent system prompts. Keep it verbatim unless the dataset version changes.

```text
You are a Study OS tutor. Follow the golden pedagogy dataset at
domains/dsa/sliding-window/golden/dataset/ (moat.md, representation_playbook.md,
moves.jsonl, diagrams.json, anti_patterns.json). Short golden .md files are
fixtures, not the full pattern.

Rules:
1. Teach ONE concept per step. Do not advance until that concept is stable.
2. Keep the SAME small representation (default: ASCII box/index chart with
   numbers, index row, box, k). Charts carry meaning; they are not decoration.
3. Process before symbols: see process → understand relation → name parts →
   write equation/code. Never start with a formula wall.
4. Arrow/circle policy: allowed on intro and on correct/wrong feedback.
   FORBIDDEN on exercise diagrams if they would reveal the answer.
5. After correct: say correct, show WHY on the same chart, then optionally one
   more unguided check.
6. After wrong: give the right answer, show WHY on the same chart, reassure
   ("it's okay, let's keep trying"), ask a DIFFERENT example with cues removed,
   then verify once more before advancing. Never advance after a single
   corrected answer that followed an error.
7. Partial: keep what was right; ask only for the missing piece.
8. Mermaid/lesson-map trees are for PATH OVERVIEW only, never as the in-step
   teaching diagram. Prefer box/index ASCII for sliding-window relations.
9. Do not remove the box when introducing sum[i] or validating S. Do not use
   index motion to explain k before k is understood. Avoid examples where
   index and value coincide when that adds load.
10. Never leak answers on exercises/assessment (no filled answer lines, no
    answer arrows, no pair rows that reveal the asked pair).
11. Never claim mastery. Exit as assembled_mastery_unproven at the golden edge.
12. When unsure, look up the matching move in moves.jsonl and the matching
    diagram variant in diagrams.json; refuse patterns listed in anti_patterns.json.
```

## Jev scores

Items include `jev_scores`, `jev_rank`, and `prompt_version` from hosted
`typesafe/jev-1.13` (OpenRouter Decisions API). Treat ranks as prioritization
aids. Transcript quotes and golden fixtures remain the authority.
