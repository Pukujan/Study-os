# Research-backed teach visuals (agent brief)

**Refs:** [#161](https://github.com/Pukujan/Study-os/issues/161) · parent [#126](https://github.com/Pukujan/Study-os/issues/126)

## Policy (non-negotiable)

1. **Invent forbidden.** No stick-figure metaphors or CSS doodles without an external research/OSS source.
2. **Research first.** Map every teach/explain/worked step in `content/teach-visuals/step-visual-map.v1.json` + `provenance.v1.json`.
3. **Big O teach default = four classes only** — O(1) / O(log n) / O(n) / O(n²) via `big-o.growth-simple-4class`.
   **Alex 2026-09-27:** full multi-class charts with n! / 2ⁿ / √n clutter are **TOO COMPLEX** for teach — **optional reference only**.
4. **Fractions are number-line-first** (Hamdan & Gunderson; Fuchs; IES Toolkit Module 1).
5. **Constructivist graph probes** cite Moore & Thompson (2015) + Farghally/OpenDSA AAVs — see `docs/research/teach-visuals/papers-constructivist-and-fractions.v1.json`.
6. InferHub vision verifies against curated reference — never generates diagrams.

## Defaults

- Big O → `/teach-visuals/big-o/growth-simple-4class.svg`
- Fractions → `/teach-visuals/fractions/` number-line assets
- Full Cmglee/cheatsheet → optional_reference (`comparison-computational-complexity.svg`, `_research/.../reference-full-cheatsheets`)

## Box mirror

`/workspace/study-os-visual-research/` — full Wikimedia/IES/paper PDFs + `provenance/research-assets.v1.json` + `catalog/SUMMARY.json`
