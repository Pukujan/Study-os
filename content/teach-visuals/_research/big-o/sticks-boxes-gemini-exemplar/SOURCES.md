# Sticks-and-boxes Big O — Gemini UX-class exemplar

**Issue:** [#185](https://github.com/Pukujan/Study-os/issues/185)  
**Parents:** [#126](https://github.com/Pukujan/Study-os/issues/126) · research [#161](https://github.com/Pukujan/Study-os/issues/161)

## Provenance

Per #161, invent-first metaphors need external grounding. Cold invent of
"stick workers" remains forbidden on the default Big O path.

**Exception (user-validated):** Alex (2026-09-27) rated a Gemini-built
interactive sticks-and-boxes game **VERY VERY GOOD** as an exemplar of this
**interactive UX class** (not perfect; not a pixel clone of Gemini chrome).
Study-os implements an equivalent learner-as-computer teach visual grounded
on this exemplar + existing research (OpenDSA AAVs / multi-class growth chart
family).

Default static teach remains the curated multi-class growth curve (#161).
This interactive game is a **complementary** representation.

## Captured states (screenshots in this folder)

| File | State |
| --- | --- |
| `8fed1840-…png` | O(1) finished — n=2, Sticks 1/1, Total Work 1 ops |
| `1e1d0dd0-…png` | O(n) mid — n=2, Sticks 1/2, Box 1 active |
| `0f0e7189-…png` | O(n) finished — n=2, Sticks 2/2 |
| `87fb2d77-…png` | O(n²) step 2 — Cross-Pairing Box 0 × Box 1, Sticks 1/4 |
| `e911b8dc-…png` | O(n²) step 3 — Cross-Pairing Box 1 × Box 0, Sticks 2/4 |
| `7b77f108-…png` | O(n²) step 4 — Cross-Pairing Box 1 × Box 1, Sticks 3/4 |

Dropdown copy from exemplar:

- `O(1) Constant — Put 1 stick in first box`
- `O(n) Linear — Put 1 stick in each box`
- `O(n²) Quadratic — Cross-pair every box with every box`

## Study-os type

`sticks_boxes_complexity` (alias `interactive_ops_boxes`) under
`web/src/visuals/SticksBoxesComplexity.tsx`.

## Study-os learner wording (#193)

The Gemini exemplar chrome says `Total Work` / `ops`. Study-os learner-facing copy uses **Steps** / **steps** (plain glossary: work = how many steps the computer takes). Screenshot rows above describe the exemplar, not live Study-os chrome.
