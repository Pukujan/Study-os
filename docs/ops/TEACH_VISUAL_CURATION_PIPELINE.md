# Teach visual curation pipeline

**Refs:** [#161](https://github.com/Pukujan/Study-os/issues/161) [#126](https://github.com/Pukujan/Study-os/issues/126)

## Flow

```text
external research / OSS figure
    → download + sha256 + license record
    → content/teach-visuals/** + provenance.v1.json
    → mirror to web/public/teach-visuals/**
    → lesson frame references asset_id / curated_diagram src
    → TeachRenderBox consumes frame
    → InferHub vision verifies screenshot ↔ reference (match only)
```

## Paths

| Path | Role |
| --- | --- |
| `content/teach-visuals/provenance.v1.json` | Asset pack + licenses + sha256 |
| `content/teach-visuals/step-visual-map.v1.json` | lesson × step → visual type + assets |
| `content/teach-visuals/{big-o,fractions}/` | Canonical binaries (DB/content pack) |
| `web/public/teach-visuals/` | Runtime URLs for `curated_diagram` |
| `docs/research/TEACH_VISUAL_RESEARCH_BRIEF.md` | Research brief |

## Frame types

| Type | Use |
| --- | --- |
| `growth_curve` | Deterministic multi-class series (`y_scale: log`, optional `highlight_label`, `asset_id`) |
| `curated_diagram` | `<img>` of a provenance-backed OSS/PD figure |
| `fraction_bar` + `number_line` | Fraction magnitude (research default) |
| `box_index` | Sliding-window array (queued for external stills; keep deterministic) |

**Removed from default Big O path:** invent-first `growth_workers` stick metaphors.

## Captions

No numbered `1. 2. 3.` caption spam (A19 / plain-human rewrite). Captions are optional plain sentences.

## Vision verify

Use InferHub vision against Playwright screenshots with the curated reference `src` named in the prompt. Fail codes: wrong family count, missing number line, stick-worker-only Big O Why, numbered caption chrome.

## Checklist for a new step visual

1. Add/choose asset in `provenance.v1.json` (license OK?).
2. Map the step in `step-visual-map.v1.json`.
3. Author lesson frames with `asset_id` / `curated_diagram`.
4. Register any new render type via `registerTeachRender`.
5. Unit + vitest + (when key present) vision gate.
6. PR Refs #161 and #126.
