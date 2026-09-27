# Sticks-and-boxes Big O interactive teach visual

**Refs:** [#185](https://github.com/Pukujan/Study-os/issues/185) · [#126](https://github.com/Pukujan/Study-os/issues/126) · [#161](https://github.com/Pukujan/Study-os/issues/161)

## Intent

Learner **is** the computer. Feeling “4 steps for n=2 under O(n²)” vs “2 steps under O(n)” vs “1 step under O(1)” is the learning event. Pair with the curated multi-class growth curve so the curve family is not orphaned.

## UX class (not invent-cold)

User-validated Gemini exemplar screenshots live under
`content/teach-visuals/_research/big-o/sticks-boxes-gemini-exemplar/` with provenance in `SOURCES.md`.
Study-os matches the validated control grammar; it is not a pixel clone of Gemini chrome.

| Control | Behavior |
| --- | --- |
| Complexity dropdown | O(1) / O(n) / O(n²) rules |
| n slider | Box count 2–8; recomputes stick budget |
| Put Next Stick | One op; dispenser → active box; stats tick |
| Finished! | When sticks placed == target |
| Reset | Clears sticks / step cue; keeps n + complexity |
| Stats | Complexity · Sticks Placed x/y · Steps |

## Integration

- Frame type: `sticks_boxes_complexity` (alias `interactive_ops_boxes`)
- Component: `web/src/visuals/SticksBoxesComplexity.tsx`
- Lesson `big-o-growth-families`: default teach stays `growth_curve`; **Explain again** on `why_care` and `on2_quadratic` opens the interactive

## Plain-language glossary (#193)

| Term | Meaning on first screens |
| --- | --- |
| **n** | how big the problem is (how many items) |
| **work / steps** | how many steps the computer takes |

Do not lead with `ops` or `Work (ops)`. Prefer **steps** / **how much work**. Stats label is **Steps**.



## Surround + in-game copy density (#195) — memory-worthy

Golden tutor density applies to **text around and inside** the interactive, not only the lesson wall:

| Surface | Rule |
| --- | --- |
| Default Why teach.md | 1–2 short sentences (motivation). No “Explain again opens…” meta. |
| Explain / interactive teach | **`explain_md`**: one short line (or empty). Interactive fills the step. |
| n / work glossary | Prior middle-frame captions **or** one collapsed expandable — never stacked with the game. |
| Frame caption on sticks | Omit (UI already shows controls). |
| In-component intro | **None** — do not restate “You are the computer…” inside the island. |
| Dropdown options | Short labels (`O(1)` / `O(n)` / `O(n²)`); rules via `title`, not essay options. |
| Stats / field labels | Minimal (`Rule`, `Sticks`, `Steps`, `n`). No “Algorithm Complexity” / “Number of Boxes (n)” essays. |
| Step cue | Short (`Box i × Box j`), not “Step k: Cross-Pairing…”. |

Anti-pattern: teach paragraphs + expandable + intro + caption + long dropdowns all visible with the game.

## Non-goals

O(log n) interactive mode, auto-play demos, replacing the #161 growth-curve default.
