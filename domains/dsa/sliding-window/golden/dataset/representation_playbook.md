# Representation playbook (sliding-window / DSA tutor)

Use this when choosing what to show on a lesson step. Grounded in the 2026-09-04 transcript + goldens + PROJECT_BOUNDARY.

| Representation | When to use | When NOT to use |
|---|---|---|
| **Box/index ASCII** (numbers + index + optional position + box + k) | Default for teaching any window relation: position, index, k, box start, sum[i], successive sums, recurrence bridge | Do not abandon mid-concept; do not replace with prose-only |
| **Guided vs unguided chart** | Guided (arrows/circles/box highlights) on intro + correct/wrong feedback; unguided on exercises | Never leave answer arrows on an exercise/probe |
| **Mermaid / lesson-map tree** | Meta overview of the concept path (problem→…→append→loop); agent/controller docs | Not as the primary teaching diagram for a single relation (Alex: "terrible") |
| **Enumerate column tree** | Teaching `enumerate(a)` pairing index‖number‖pair | Omit pair row on exercises if it reveals the asked pair |
| **Code tree / side-by-side** | append conversion, else-bridge, loop assembly — code beside the same box chart | Do not show full final loop before bridges exist; do not leak answer lines on assessment |
| **Worked equivalence** | Brief: `7+2+6=15` same as `13-4+6=15` after successive sums understood | Not a multi-paragraph formula lecture before the chart process |
| **Companion talk** | 1–3 short sentences naming the one relation | Text walls; renaming vocabulary casually; "improve" wording that changes the representation |

## Arrow / circle policy

- **Introducing** a concept → show arrows/circles.
- **Correcting / showing why** → show arrows/circles on the same chart.
- **Exercise** → same rows/structure, **no** answer-revealing arrows/circles/highlights/pair rows.

## Help fading

intro (cues on) → exercise (cues off) → on error: cues on for why → retry cues off → verify cues off → advance.

## Cross-check with oracle

`conformance-oracle.v0.1.json` encodes representation_rules, probe glyph forbids, max_new_concepts_per_step=1, feedback/why/partial requirements.
