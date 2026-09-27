# Sticks-and-boxes Big O interactive teach visual

**Refs:** [#191](https://github.com/Pukujan/Study-os/issues/191) · [#185](https://github.com/Pukujan/Study-os/issues/185) · [#126](https://github.com/Pukujan/Study-os/issues/126) · [#161](https://github.com/Pukujan/Study-os/issues/161)

## Intent

Learner **is** the computer. Feeling “4 ops for n=2 under O(n²)” vs “2 ops under O(n)” vs “1 op under O(1)” is the learning event. Pair with the curated multi-class growth curve so the curve family is not orphaned.

## UX class (not invent-cold)

User-validated Gemini exemplar screenshots live under
`content/teach-visuals/_research/big-o/sticks-boxes-gemini-exemplar/` with provenance in `SOURCES.md`.
Study-os matches the validated control grammar; it is not a pixel clone of Gemini chrome.

| Control | Behavior |
| --- | --- |
| Complexity dropdown | O(1) / O(n) / O(n²) rules |
| n slider | Box count 2–8 (default **n = 3**); recomputes stick budget; compare O(n) at 3 vs 5 |
| Put Next Stick / click target box | One op; dispenser → active box; stats tick |
| Compare-next CTA | After a mode finishes: advance O(1)→O(n); after O(n) at n<5 offer try n=5; then O(n²); Finished only at end |
| Heat panel | Calm → warm → melting as Total Work climbs |
| Scale note | Copy-only n=3 vs n=1 billion — never render huge box counts |
| Finished! | When sticks placed == target |
| Reset | Clears sticks / step cue; keeps n + complexity |
| Stats | Complexity · Sticks Placed x/y · Total Work ops |

## Integration

- Frame type: `sticks_boxes_complexity` (alias `interactive_ops_boxes`)
- Component: `web/src/visuals/SticksBoxesComplexity.tsx`
- Lesson `big-o-growth-families`: default teach stays `growth_curve`; **Explain again** on `why_care` and `on2_quadratic` opens the interactive

## Non-goals

O(log n) interactive mode, auto-play demos, replacing the #161 growth-curve default.
