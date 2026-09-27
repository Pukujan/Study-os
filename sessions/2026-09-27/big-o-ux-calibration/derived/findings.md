# Findings — big-o-ux-calibration (2026-09-27)

Self-reported product UX calibration from author **Pukujan** (not "Alex" in attribution). Not mastery evidence.

## Teach visuals (Big O + catalog)

1. **No numbered teach chrome** — digit-prefixed `1) 2) 3)` lists distract; prefer plain sentences + the diagram (A19 / plain-human rewrite).
2. **Prefer graphs over invent-first sticks** — multi-class growth curves beat slow-vs-fast-only and stick-worker / "number-box workers" metaphors.
3. **Simpler teach charts** — live teach frame = simple O(1)/O(log n)/O(n)/O(n²); dense cheatsheets stay reference-only.
4. **Catalog-wide** — every lesson/step, not one hardcoded Big O slide; sliding-window keeps golden `box_index` (no invent).
5. **Research-first interactives** — pick-which-curve / draw-dots / number-line tasks are literature + external-program research topics for a catalog-wide pipeline, not chat vibes or one locked probe.
6. **Hikers + empty table** is not enough for Why — need real multi-class growth visuals on the teach card.
7. **Worked example ≠ teach** — must visibly change content (not duplicate numbered prose).

## Crashes / defects

8. **Explain again ×2 crash** — `undefined` `.type` ErrorBoundary (#163).
9. **Pet jitter** — idle animation while "walking" = shaking in place; needs real walk/turn frames (#121).
10. **Tutor latency** — 18–60s+ on live; ack makes it survivable, not fast (#160).

## Fractions / navigation

11. **Number-line-first** where research requires (IES Toolkit / Hamdan & Gunderson / Fuchs); bar models as supporting frames.
12. **Step-1 probe gap** (human-test): teach question without `probe` → only 1–5 Submit; no Back/LessonMap jump; blocked from Step 2 (later unblocked — keep as calibration).

## Theme / identity

13. **Prefer dark** — hates bright lavender; dark mode for player + teach; charts readable on dark (#165).
14. **Design system** — CSS tokens + theme switcher (not one-off dark CSS); later full customization (palettes, typography, mood presets). Theme skins chrome/UI only for now (not curated teach stills / pet art).
15. **Author name** — attribute critiques as **Pukujan**.

Canonical entries: `content/human-feedback/feedback.jsonl` (full this-session corpus).  
Live in-app reviews stay in `ux.feedback`; decomposer ratings in `ux.decomposer_review`.
