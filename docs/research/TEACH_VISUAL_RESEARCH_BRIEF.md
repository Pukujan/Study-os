# Teach visual research brief (curated, not invented)

**Issue:** [#161](https://github.com/Pukujan/Study-os/issues/161) (parent [#126](https://github.com/Pukujan/Study-os/issues/126))  
**Updated:** 2026-09-27  
**Policy:** research-first. Inventing stick-figure metaphors without a source is forbidden.

## Finding

Alex live feedback (2026-09-27): **growth curves beat invented stick workers**; a two-line “slow vs fast” chart undersells Big O. Course cheatsheets and Wikimedia complexity plots show **O(1), O(log n), O(n), O(n²)** on shared axes. Fraction magnitude teaching is grounded in **number-line** representations, not area bars alone.

## External sources used

| Domain | Artifact | License | Why |
| --- | --- | --- | --- |
| Big O | [Comparison_computational_complexity.svg](https://commons.wikimedia.org/wiki/File:Comparison_computational_complexity.svg) (Cmglee) | CC BY-SA 4.0 | Canonical multi-class ops-vs-n chart matching the bigocheatsheet / bigochart family |
| Big O | [Big-O-notation.png](https://commons.wikimedia.org/wiki/File:Big-O-notation.png) | Public domain | Asymptotic bound sketch |
| Fractions | [Fraccion_propia_en_la_recta.png](https://commons.wikimedia.org/wiki/File:Fraccion_propia_en_la_recta.png) | CC BY-SA 4.0 | Fractions placed on number lines |
| Fractions | [Number-line.svg](https://commons.wikimedia.org/wiki/File:Number-line.svg) | CC0 | Clean number-line chrome |
| Fractions | [3_4_fraction.svg](https://commons.wikimedia.org/wiki/File:3_4_fraction.svg) | Public domain | Area model companion |
| Pedagogy | Farghally et al. / OpenDSA AAVs | MIT courseware + papers | Algorithm *analysis* visualizations (growth/runtime) outperform prose-only AA |
| Pedagogy | Siegler et al. 2011 (Cog Psych) | peer-reviewed | Fractions as magnitudes on a mental number line |
| Pedagogy | Hamdan & Gunderson; Fuchs; IES REL Fractions Toolkit | peer-reviewed / IES | Number-line interventions improve fraction magnitude |

Program / donor pointers (not copied binaries): OpenDSA AlgAnal growth modules (MIT), bigocheatsheet / bigochart *family* as the visual grammar Study OS matches (we ship Commons-licensed figures + deterministic series, not a proprietary scrape).

## Inventory (player lessons)

See `content/teach-visuals/step-visual-map.v1.json` (19 step entries).

| Lesson | Steps | Primary visual | Status |
| --- | --- | --- | --- |
| `big-o-growth-families` | 7 | multi-class `growth_curve` + curated Commons SVG | **landed** |
| `fractions-compare` | 6 | `fraction_bar` **with number_line** + curated number-line PNG | **landed** |
| `sliding-window-box` | 6 | deterministic `box_index` (OpenDSA/JSAV-style) | **queued** (no invent; golden arrow rules stay authority) |

## Vision role

InferHub cheap vision **verifies** that the live TeachRenderBox render matches the curated reference (`asset_id` / public `src`). Vision must **not** generate diagrams.

## Agent rule

Before drawing anything new: open the step map → pick `visual_type` + `asset_ids` → cite provenance. If missing, queue an asset with an issue link — do not invent.
