# Design system (switchable tokens) — Refs #165 / #126

Status: **chrome / UI only**. Out of scope: curated teach image assets and teacher pet/bot sprites.

## Axes

| Axis | Values | Storage / DOM |
| --- | --- | --- |
| Appearance | `light` \| `dark` \| `system` | `data-theme-appearance` resolves to light/dark |
| Palette | `lavender` \| `slate` \| `forest` \| `sunset` | `data-theme-palette` |
| Type | `sans` \| `serif` \| `mono` | `data-theme-type` → `--font-body` |
| Mood | `calm` \| `focus` \| `playful` | `data-theme-mood` → radius / line-height |
| Density | `comfortable` \| `compact` \| `spacious` | `data-theme-density` → `--space-unit` |

**Default:** dark + slate (Pukujan hates bright lavender). Persisted at `localStorage["sos.theme.v1"]`. Boot script in `web/index.html` applies datasets before React to avoid FOUC.

## Files

| Path | Role |
| --- | --- |
| `web/src/theme/tokens.ts` | Types, defaults, parse/apply helpers |
| `web/src/theme/tokens.css` | CSS custom properties per appearance×palette + type/mood/density |
| `web/src/theme/ThemeProvider.tsx` | Context + persistence + `prefer_dark` analytics |
| `web/src/theme/ThemeToggle.tsx` | Header chrome controls |
| `web/src/styles.css` | Components consume `var(--*)` only |

## Agent rules

1. **Do not** hardcode light lavender hex (`#F4F1FF`, `#111B4D`, `#8F7CFF`) in new chrome CSS — use tokens.
2. Charts / SVG teach **widgets** (BoxIndex, GrowthCurve, FractionBar, Mermaid) should use `var(--ink)`, `var(--primary)`, `var(--chart-1..4)`, etc. so dark mode stays readable.
3. **Do not** restyle curated teach **image** packs under `content/teach-visuals/` or `web/public/teach-visuals/`, and **do not** theme pet/robot sprite art in this change.
4. Shadow DOM teach islands inherit CSS variables from the host — prefer tokens over island-local hex.
5. When changing theme UX, run Ultrafast scout + Playwright (`docs/AGENT_FRONTEND_QA.md`).

## Analytics

Selecting / defaulting to dark logs `rating` with `control: prefer_dark` and `value_int: 1` (light → `0`) via first-party `/api/events`.

## Manual check

1. Load app → dark slate by default.
2. Header **Theme** panel: switch palette / type / mood / density; **Dark/Light** quick toggle.
3. Player chrome + chart SVGs remain readable; pet sprite and curated teach images unchanged.
