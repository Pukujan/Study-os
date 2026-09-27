# TeachRenderBox (PresentationIsland)

**Refs:** [#126](https://github.com/Pukujan/Study-os/issues/126)

## What

ChatGPT-style **visual island** for lesson frames. Teach diagrams mount inside
`TeachRenderBox` so **global app CSS cannot stretch / restyle** tables, `pre`,
or SVG inside the island.

## Isolation approach

**Open Shadow DOM** (preferred) + **CSS modules** injected into the shadow root.

| Layer | Role |
| --- | --- |
| Shadow DOM | True isolation from document stylesheets (element selectors like `table { width:100% }` do not pierce) |
| `TeachRenderBox.module.css` | Island-owned layout (compact growth table, code block, workers/curve chrome) |
| Light-DOM fallback | SSR / no-`attachShadow`: same module classes on a `data-isolation="css-module"` host |

Host attributes: `data-testid="teach-render-box"`, `data-teach-render=<kind>`,
`data-isolation=shadow-dom|css-module`.

## Built-in render types

| Kind | Notes |
| --- | --- |
| `code_block` | Monospace `pre` (ASCII / short code) |
| `mermaid` / `mermaid_flow` | Mermaid diagram (`mermaid` is an alias) |
| `growth_workers` | Stick-figure workers + boxes |
| `growth_curve` | SVG growth lines |
| `growth_table` | Compact scoreboard **inside the island only** |
| `fraction_bar`, `box_index`, `code_tree` | Existing frames, also island-mounted |
| `sticks_boxes_complexity` / `interactive_ops_boxes` | Interactive sticks-and-boxes Big O (#185) |

## How to register a new render type

1. Add a Frame union member in `web/src/api.ts`.
2. Implement the view component (keep styles in the island module or a child module you inject).
3. Call at module load:

```ts
import { registerTeachRender } from "./TeachRenderBox";

registerTeachRender({
  types: ["my_kind"],           // aliases allowed
  describe: (frame) => "...",
  render: (frame) => <MyView frame={frame} />,
});
```

4. Optionally teach `render_text.frame_to_text` for tutor grounding.
5. Author lesson JSON with `"type": "my_kind"` and wire explain indices so
   **Explain again / Worked example** can select a *different* type.

`Frame.tsx` always dispatches through `TeachRenderBox` — no per-type chrome outside the island.

## Explain again / Worked example

- **Explain again** → `POST .../adapt` `kind=reexplain` picks alternate authored
  frame indices (`teach_visual.alternate_indices`) so the **frame type on screen
  changes** (e.g. Big O `growth_workers` ↔ `growth_curve`). Tutor regenerate is fallback.
- **Worked example** → authored `worked_example` / `_alt` (or explain-frame pool)
  with a different type than the teach card.

## Related

- Flagged metaphors: `docs/ops/TEACH_VISUAL_V1.md`
- Files: `web/src/visuals/TeachRenderBox.tsx`, `teachRenderRegistry.ts`, `TeachRenderBox.module.css`
