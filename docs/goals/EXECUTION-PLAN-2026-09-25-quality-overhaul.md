# Execution Plan — Quality Overhaul 2026-09-25 (integration owner merge of 3 planner passes)

Inputs: `local://plan-sdd.md` (SDD Spec Planner-2), `local://plan-property.md` (Property Plan Planner), `local://plan-red.md` (RED Test Planner-2), repo map (scout `Repo Map`). Parent goal: `GOAL-2026-09-25-quality-overhaul.md`. Disagreements resolved below; **this file + the slice plans are the binding merge**; spec wins over vote.

## Resolved decisions (integration owner)

| # | Question | Decision | Why |
|---|---|---|---|
| R1 | Branch names (SDD used `task/SOS-0011-*`, RED reconciled to continuity projections) | `task/SOS-0012-decomposer-rebuild` (#118), `task/SOS-0013-regen-api` + `task/SOS-0013b-regen-review-ui` (#120), `task/SOS-0014-mascot-locomotion` (#121), `task/SOS-0015-frontend-viewport` (#119) | Matches `tasks/TASK-SOS-0012..0015` headers (issue authority) |
| R2 | Idempotency: SDD proposed `Idempotency-Key` **header**; RED/property noted existing **body-field** convention (`service.py:342-357`, `api.py:93,122`) | Body field `idempotency_key` is primary; header accepted as fallback on the two new endpoints only; shared ledger table `learn.idempotency_keys` stores `{subject}:{key}` scoped rows with response JSON for verbatim replay; conflict payload ⇒ 409 `idempotency_conflict`; in-flight ⇒ 409 `idempotency_in_flight` | Don't break the frozen existing convention; new endpoints get stronger replay (SDD §2.4 semantics) |
| R3 | Migration name | `0003_player_regen_review.sql` (single new file, additive, `IF NOT EXISTS` + guarded DO blocks) | Sorts after the two 0002s (db.py sorted application); one owner = S2 |
| R4 | `ux.decomposer_review` table + ratings CHECK | **Keep table** (immutable captured evidence per AGENTS.md). Delete only the bespoke review **app** (mirror HTML/JS/data) and its routes. The new 1–5 signal goes to `learn.player_review`; no CHECK-widening in the decomposer table | Raw evidence immutability invariant |
| R5 | Regenerate without LLM keys | `player/regeneration.py` = deterministic template-bank fallback (seeded purely from lesson_id/step_id/slot/variant/module-version; no RNG, no wall clock) + injected `LLMTransport` seam with validate→repair-once→fallback (tutor.py precedent). Offline determinism is a property test, not a hope | Deterministic canonical state; spend caps |
| R6 | Presentation override storage | In `player_session.state.presentation_overrides` (canonical live state = local_database/PIR row per manifest) + mirror rows in `learn.player_step_variant` for analytics; view() merges over lesson JSON; step identity (step_id, kc) untouched | Engine state is the single canonical live state; Postgres = analytics only |
| R7 | Mascot frame source | Image-gen via CGM pipeline; if generation unavailable in a session: BLOCK and message orchestrator. Never CSS/SVG fakes; never fabricated provenance | Alex's explicit "no CSS hacks" + generative media not canonical algorithm state (FSM is testable, art is swappable) |
| R8 | styles.css ownership | S3 owns `:root` tokens + player/review classes; S4 must NOT touch styles.css (Sprite already injects scoped <style>; mascot layout uses existing `.robot-visit`-class floats + inline vars); S5 owns the rest of the overhaul after S3/S4 merge | One writer per file window |
| R9 | Holdout (S6) | Private data only under `~/.study-os/holdout/decomposer-v2/` (`problems.jsonl` + `goldens/*.json`, `schemas/holdout-problem.v1.json`-validated). CI: loud-skip when absent (`HOLDOUT-SKIP`, exit 0 under CI=true), exit 2 locally. Public fixtures = trivial synthetic. P5_NO_PRIVATE repo-tree guard test. Baseline: candidate aggregate ≥ 0.80 hard floor AND ≥ `docs/goldens/decomposer/BASELINE.json` | Goal method + data boundary |
| R10 | Scorer | ONE canonical implementation `tools/score_decomposition.py`: 0.4·concept-set Jaccard + 0.5·step-graph F1 + 0.1·coverage; topological-validity hard gate = zero; deterministic, no model calls. Metamorphic tests and holdout import it | "never reimplement" per property plan |
| R11 | Empty-frame rule | Per-frame opaque-pixel count (alpha ≥ 16) ≥ class threshold (pet ≥ 1200, duo ≥ 2400, robot ≥ 1000); enforced in generator + manifest `empty_frame_check`; sha256 per sheet in `web/public/mascot/manifest.json` | Byte-size checks miss the bug class |
| R12 | Merge order | S1 → S2 → S3 (S3 rebases on merged S2 contract) ; S4 parallel (no shared files with S1–S3); S5 last; then per-slice deploy+live-verify | Goal order + R8 file windows |

## Frozen interfaces (specs land as first commit of their slice branch)

1. `schemas/decomposition.v2.schema.json` — full field spec in plan-sdd §1.1 (strategy, concept_dag nodes/edges, learning_order, steps with presentation slots question/example/visual, provenance, revision `*.v2`). Cross-field DAG rules enforced in `src/study_os/decomposer/order.py` + property tests (P1_ACYCLIC/ORDER/COVERAGE, M1–M3).
2. `schemas/holdout-problem.v1.schema.json` — plan-property §3.
3. Player API contract — plan-sdd §2 as amended by R2/R5/R6: `POST /api/player/sessions/{id}/regenerate` `{slot, idempotency_key}` → full PlayerView (+`_replayed` when replayed); `POST /api/player/review` `{session_id, step_id, variant, slot?, rating 1-5, why?≤1000, idempotency_key}` → `{ok, review_id}`. Errors `{"error": code}`; CSRF+header+rate guard unchanged.
4. `src/study_os/web/migrations/0003_player_regen_review.sql` — DDL in plan-sdd §3 + R3/R4.
5. `schemas/mascot-sprite-manifest.v1.schema.json` — plan-sdd §4.1 verbatim; manifest at `web/public/mascot/manifest.json`.
6. Layout + testid contract — plan-sdd §5.1–5.3 (tokens `--player-main-max/--player-side-w/--review-panel-w/--regen-btn-min-h/--mascot-size-*/--layout-gap`; breakpoints 1023/1024; `data-testid` names `player.step.regen-{question,example,visual}`, `player.review.panel/score-N/why/submit/submitted`, `mascot.pet/sprite/hide`). Playwright matrix asserts exactly these.
7. Canonical storage decision (S1): decompositions package data `src/study_os/decomposer/decompositions/<id>.v2.json`; lesson emit to existing `web/player/lessons/` via `emit.to_lesson_v1()` self-checked by `engine.check_lesson`.

## Test contract (from plan-property; RED-first per plan-red §3)

Property: P1_ACYCLIC/ORDER/COVERAGE, P2_WEB_CONTROL/PLAYER_ENGINE (+regen determinism), P3_NOMUTATE/NOMUTATE_SRC/RERATE_NEWROW, P4_ONCE/BODY_SAME/CONFLICT, M-P1..P3 (FSM), A1 (manifest/sha256/opaque-pixels), P5_HARNESS/NO_PRIVATE.
Metamorphic: M1 paraphrase, M2 concept-reorder, M3 re-render preservation; regen-keeps-step-identity (S2 RED). All pytest files are `unittest.TestCase` (CI runs `python -m unittest discover -s tests`); hypothesis pinned in requirements-dev.

## Ownership map (single writer per file)

| Slice | Owner agent | May touch | Never touches |
|---|---|---|---|
| S1 | S1 Decomposer | `schemas/decomposition.v2.schema.json`, `schemas/holdout-problem.v1.schema.json`, `src/study_os/decomposer/**`, `tools/run_decomposer.py`, `tools/score_decomposition.py`, `tools/eval_decomposer_holdout.py`, `tools/holdout_pack.py`, decomposer tests, deletions (static mirror, CSP test), api.py **decomposer routes only**, service.py `record_decomposer_reviews` only, docs/goldens/decomposer/**, docs/research pointers | web/src, player/**, mascot/**, migrations 0003 |
| S2 | S2 Regen API | api.py player-route region, `player/{service,engine,regeneration}.py`, migration 0003, `tests/test_web_regen_review.py` | decomposer routes (S1 deleting), web/src |
| S3 | S3 Regen Review UI | `web/src/{api.ts,pages/Player.tsx,player/**,styles.css}` + colocated vitest | src/study_os/** |
| S4 | S4 Mascot | `web/src/mascot/**`, `web/public/mascot/**`, `schemas/mascot-sprite-manifest.v1.schema.json`, `tools/generate_mascot_frames.py`, `tests/test_mascot_*.py` | styles.css, Player.tsx |
| S5 | S5 Frontend | styles.css (post S3/S4 merge), pages, `.github/workflows/ci.yml` e2e job, `web/e2e/**`, `web/playwright.config.ts`, package.json devDeps (playwright) | src/study_os/**, decomposer |
| All | Orchestrator (integration owner) | merge conflicts, PROJECT_MANIFEST.yaml, docs/HANDOFF.md, tasks/*.md, receipts, deploy, PCM checkpoints, holdout staging | implementation files |

## Sequencing and verification

Per slice: RED (draft PR) → impl → green locally (`python -m compileall tools tests && python tools/validate_repo.py && python -m unittest discover -s tests`; `cd web && npm ci && npm run typecheck && npm test`; ruff + pyright on changed Python; Playwright chromium for S5) → PR ready → orchestrator review → squash merge → deploy to gravebuster (`/srv/study-os`, `docker compose up -d --build`, health checks per deploy/README.md) → live verify at 390×844 + 1440×900 with captures logged in the task file → receipt on leaf issue + InferHub/OpenRouter spend JSON.
Goal-level DoD unchanged from `GOAL-2026-09-25-quality-overhaul.md`.

## Deviations recorded

- SDD proposed a header-first idempotency and a new `learn.idempotency_keys` design; kept with R2 body-field-primary amendment (existing convention compatibility).
- SDD proposed `0003_player_review.sql`; renamed `0003_player_regen_review.sql` (covers both new surfaces; R3).
- SDD §5.2 z-index note self-corrected in-line; frozen: sheet z-index 60, mascot hidden while sheet open on ≤1023px (S3 may hide via `hidden` attribute, no stacking hacks).

## Workspace isolation (post-incident, binding)

Every slice works ONLY in its own git worktree; the primary checkout `D:/claude/study-os` is orchestrator-owned; no agent ever `git checkout` outside its worktree:

| Slice | Worktree | Branch |
|---|---|---|
| S1 | `D:/claude/study-os-s1` | `task/SOS-0012-decomposer-rebuild` |
| S2 | `D:/claude/study-os-s2` | `task/SOS-0013-regen-api` |
| S3 | `D:/claude/study-os-s3` | `task/SOS-0013b-regen-review-ui` |
| S4 | `D:/claude/study-os-s4` | `task/SOS-0014-mascot-locomotion` |
| S5 | after S1–S4 merge | `task/SOS-0015-frontend-viewport` |

Local verification environment: `.venv-ci/Scripts/python` (full dev deps incl. psycopg) + `TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/postgres` (docker `sos-test-pg`). Known pre-existing LOCAL-only failures at baseline (env-specific, CI green — ignore, never "fix"): `test_helper_adoption.test_protocol_schemas_are_exact_pinned_copy` (local PCM clone drift), `test_pir_golden_conformance.test_oracle_pins_goldens_and_benchmarker`, `test_pir_mutation_gate_contract.test_checker_accepts_audited_equivalent_survivor` (CRLF hash drift).
