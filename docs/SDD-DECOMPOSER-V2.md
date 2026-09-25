# SDD delta — Decomposer v2 (SOS-0012)

Refs #118 (leaf), #114, #111. Frozen planning inputs: `local://plan-sdd.md` §1,
`local://plan-property.md` §1–§3, `local://plan-red.md` §S1+S6.

## What changed and why

SOS-0011 (#114/#115) shipped the pedagogical decomposer as a **static human-eval
mirror**: curated/LLM JSON under `docs/research/decomposer-review/data/` +
`web/public/review/decomposer/data/`, a bespoke review HTML app (`index.html`,
`app.js`), and FastAPI routes persisting ratings to `ux.decomposer_review`.
That pipeline had no schema, no deterministic generator, and no differential
evaluation. SOS-0012 replaces it with a **deterministic, schema-validated
decomposer package** plus a **holdout differential harness**. The append-only
ratings evidence (`ux.decomposer_review`, migration
`0002_decomposer_review.sql`) is captured research evidence and stays.

Deleted in this slice (cutover):

- `docs/research/decomposer-review/` (data mirror, README, app.js, index.html;
  `spend.json` relocated to `docs/research/spend/sos-0011-spend.json` — spend
  history stays).
- `web/public/review/decomposer/` (public mirror of the same data).
- `tests/test_decomposer_review_csp.py` (asserts the deleted app exists).
- `api.py`: `DecomposerReviewBody`, `POST /api/review/decomposer`,
  `GET /api/review/decomposer/variants`, the `/review/decomposer` page handler,
  the `/review/decomposer/data` static mount and its SPA-catch-all guard.
- `service.py::record_decomposer_reviews` (dead after route removal).

Human review moves into the in-player review surface (S2/S3, #120); the table
stays so captured ratings remain queryable evidence.

## Modules (`src/study_os/decomposer/`)

| Module | Responsibility |
| --- | --- |
| `__init__.py` | Exports `decompose()`, `ProblemSpec`, `DecompositionError`, `validate_decomposition` |
| `contracts.py` | `Decomposition` dataclass family, dict serde, `validate_decomposition()` (jsonschema draft 2020-12 against `schemas/decomposition.v2.schema.json` + cross-field rules), canonical package-data loader |
| `concepts.py` | Problem-feature extraction (pure, keyword rules) + concept DAG construction |
| `order.py` | Kahn topological ordering; deterministic tie-break by concept id; raises `DecompositionError` on cycles (acyclicity lives here only) |
| `presentation.py` | Per-concept presentation builders (question/example/visual) + `render_visual`/`render_visual_as` renderer seam (M3) |
| `generator.py` | `decompose(problem) -> Decomposition`; deterministic template/rules path. Optional LLM seam: an injected transport argument, **unused by default** |
| `emit.py` | `to_json()` canonical writer (sorted keys, trailing newline), checksum-guarded idempotent writes, `to_lesson_v1()` adapter into player-lesson.v1 self-checked via `study_os.web.player.engine.check_lesson` |

Deliberately excluded: no LLM orchestration, no storage layer (CLI owns
writes), no HTTP, no RNG, no wall clock (provenance `created_at` is the frozen
module release stamp so identical inputs give byte-identical output).

## CLI contract

```
python tools/run_decomposer.py decompose   --problem problems/<id>.txt --out src/study_os/decomposer/decompositions/
python tools/run_decomposer.py emit-lesson --decomposition <id>.v2.json --out <lesson path>.v1.json
python tools/run_decomposer.py validate    [--all | PATH ...]
python tools/run_decomposer.py holdout     [--data-dir DIR] [...same flags as tools/eval_decomposer_holdout.py]
```

Exit codes: `0` success, `2` invalid (schema/acyclicity/lesson check).
`--seed` is accepted and must not change output (property-tested); `--force`
overwrites; every write is checksum-guarded (skip when sha256 unchanged), so
all subcommands are idempotent.

Supporting tools: `tools/score_decomposition.py` (deterministic scorer,
`--gate` threshold), `tools/eval_decomposer_holdout.py` (S6 harness, exit
`0`/`1`/`2`/`3`, `CI=true` loud-skip), `tools/holdout_pack.py` (stages private
data under `~/.study-os`, refuses repo paths, chmod 700).

## Scoring axes

Aggregate = `0.4 * concept-set Jaccard + 0.5 * step-graph F1 + 0.1 * coverage`
(4-decimal output). Step-graph F1 matches candidate/reference steps on
`(concept_id, kth occurrence, prerequisite-concept set)` signatures.
Topological validity is a hard gate: an invalid candidate scores 0 regardless
of the aggregate. Gate rule: pass iff validity holds **and** aggregate ≥
threshold; differential acceptance is aggregate ≥ `BASELINE.json` baseline
(hard floor 0.80). Baseline changes require a decision record.

## Canonical storage

`src/study_os/decomposer/decompositions/<problem_id>.v2.json` — package data
(loaded via `importlib.resources`, mirroring `web/player/lessons`), packaged
through `pyproject.toml` `package-data`. Player-facing lessons still land in
`src/study_os/web/player/lessons/` via `emit-lesson` (unchanged loader); this
slice does not add player lessons.

## Private data path

`~/.study-os/holdout/decomposer-v2/{problems.jsonl,goldens/<problem_id>.json}`
per `schemas/holdout-problem.v1.schema.json`. Never committed; `source_class:
private` must never appear under the repo tree (`P5_NO_PRIVATE` guard). Public
synthetic fixtures for harness tests live at
`tests/fixtures/holdout_public/` with `source_class: "public"`.

## Dependency note

`jsonschema>=4.23,<5` was dev-only; `contracts.py` validates at runtime, so it
is promoted to `project.dependencies` in `pyproject.toml` (already covered by
`requirements-dev.lock`; AGENTS.md "build/test expectations" updated). The
schema file itself is read from the repo `schemas/` directory; the installed
wheel does not include it, so wheel-level consumers validate via the repo
tree (documented limitation; `verify_built_package.py` scope unchanged).
