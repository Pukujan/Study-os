# Decomposer human-eval (SOS-0011)

Open live: **https://study.design-bakery.com/review/decomposer**

Or open `index.html` via the Study OS static server (same-origin `/vendor` for Mermaid + KaTeX).

- `data/*.json` — pedagogical proposals (steps + renderable artifacts)
- `data/index.json` — problem/variant index
- Ratings: per-step Good / Prefer / Bad + optional comment → `POST /api/review/decomposer` → `ux.decomposer_review`
- Export JSON is secondary (localStorage draft + download button)

Representation palette (cheap render only): ASCII/SVG box-index, KaTeX/algebra, Mermaid graphs, geometry SVG, code trees, tables. No paid image models for teaching charts.
