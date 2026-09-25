# Goal — Resume: quality overhaul of Study OS web app (decomposer, player, mascot, frontend)

**Date opened:** 2026-09-25 · **Base:** `main` @ `3127eac` (after PR #116) · **Live:** https://study.design-bakery.com
**Supersedes:** "next steps" list in `docs/checkpoints/CHECKPOINT-2026-09-24-progress.md` (branch `codex/checkpoint/wip-20260924-progress`, PR #117).

## Problem statement (Alex, 2026-09-25)

1. The pedagogical decomposer is not working and was built badly — rebuild it **simpler**, do not extend it.
2. The lesson player must make **regenerating the current step's presentation** (question/example/visual) a first-class surface action; chat is ONLY a channel to the LLM, never the only way to change what is shown.
3. A **review panel** beside the lesson: rate each explanation **1–5**, optional "why", explicit **Submit** — the human preference signal feeding representation policy.
4. **Mascot**: bugs (empty one-shot frames live), no walking (it slides with idle animation = shaking in place), hover semantics unclear, mobile touch UX unclear. Needs generated walk/turn animation frames (vision + image-gen), not CSS hacks.
5. **Frontend**: many broken parts; needs a visual overhaul verified on **both mobile web and desktop**, live on study.design-bakery.com — not draft shots.

Durable evidence for each is filed as linked issues (created from this goal): decomposer rebuild, player regenerate+review, mascot locomotion, frontend viewport overhaul.

## Method (binding for this goal)

Spec-driven + property-driven + TDD, executed by parallel subagents, everything idempotent:

- **SDD first**: per slice, a spec delta (SDD/PDD/TDD docs like the existing `docs/P3_*` / `docs/P4_*` triplets) merged before implementation. Interfaces frozen in `schemas/` before any subagent codes against them.
- **RED tests first**: each slice lands failing tests (pytest + vitest) on a branch before implementation commits.
- **Property tests**: decomposition DAG acyclicity/order; player controller determinism (same seed + same history ⇒ same state); review rows append-only; idempotency-key replay ⇒ exactly-once effects.
- **Metamorphic tests**: decomposer output invariant under paraphrase of the problem statement, reordering of independent concepts, and representation re-render (strategy/concept set stable; steps remain topologically valid); player regenerate output keeps step identity and concept, changes presentation only.
- **Hidden holdout differential tests**: a private held-out set of DSA problems + golden-aligned reference decompositions (never in the repo public tree; stored per documented data path). A slice is not done until candidate decomposer output beats/matches the goldens on the holdout via the same deterministic scorer used in CI-adjacent tooling.
- **Multi-planner**: 3 independent planning passes (SDD planner, property/metamorphic planner, test/RED planner) produce plans; an integration owner merges them into one execution plan; disagreement resolved by spec, not vote.
- **Multiple subagents**: one owner per file-ownership slice (decomposer core; player API+controller; player UI+styles; mascot+assets; review panel; CI/viewport harness). Siblings coordinate only through frozen interfaces + issue comments. Shared files (`api.py` route table, `styles.css` tokens, migrations index) have exactly one integration owner.
- **Idempotent execution**: every migration, seed script, generator run, and deploy step is safe to re-run (idempotency keys on writes, checksum-guarded asset generation, declarative compose deploy). Agents that crash mid-slice re-run from checkpoint without duplicate side effects.
- **Checkpoint protocol unchanged**: PCM checkpoint markers in task files, `Refs #N` PRs (never `close #N`), CI green before auto-merge, gravebuster deploy + live verification per slice.

## Slices and ownership

| # | Slice | Branch | Primary files | Issue |
|---|-------|--------|---------------|-------|
| S0 | Merge #117 checkpoint (Sprite one-shot fix + CSP-safe review page) | existing | `web/src/mascot/Sprite.tsx` | #117 |
| S1 | Decomposer rebuild: schema + generator + tool + tests, delete static mirror | `task/SOS-0011-decomposer-rebuild` | `src/study_os/decomposer/`, `schemas/`, `tools/run_decomposer.py` | filed from this goal |
| S2 | Player API: `regenerate` endpoint + 1–5 review endpoint + controller state + decision logging | `task/SOS-0005-regen-api` | `src/study_os/web/*` | filed from this goal |
| S3 | Player UI: in-place step regeneration controls + side review panel (1–5, why, Submit) | `task/SOS-0005-regen-ui` | `web/src/pages/Player.tsx`, `web/src/player/*` | filed from this goal |
| S4 | Mascot: walk/turn sheets via image-gen (CGM, provenance) + locomotion state machine + touch UX | `task/SOS-0005-mascot-locomotion` | `web/src/mascot/*`, `web/public/mascot/*` | filed from this goal |
| S5 | Frontend viewport overhaul + Playwright 3-viewport CI + live verification | `task/SOS-0005-frontend-viewport` | `web/src/styles.css`, routes, `.github/workflows` | filed from this goal |
| S6 | Hidden holdout differential harness for decomposer | part of S1 | `tools/` + private data path | with S1 |

Order: S0 immediately; planning pass (SDD×3 planners) before S1–S5 code; S2 before S3 (API frozen first); S4 and S5 parallelizable after S3 layout tokens frozen; S6 with S1.

## Definition of done (goal-level)

- Every slice: merged to `main` with CI green, deployed to gravebuster, verified **live** at 390x844 and 1440x900 with captures recorded in the task file.
- Decomposer: one canonical data location, schema-validated output, holdout differential score ≥ golden baseline, static mirror deleted, bespoke review HTML removed.
- Player: regenerate works in-place on question/example/visual per step; review (1–5 + why + Submit) persisted append-only per step/variant.
- Mascot: real walk cycle with direction facing, no shaking, hover (desktop) + tap (mobile) both work, one-shot frames verified non-empty.
- Frontend: viewport matrix green in CI; no known-open visual break on live site.
- Receipts posted on all linked issues; InferHub/OpenRouter spend recorded per repo convention.

## Constraints

- No secrets in repo; private transcripts stay out; spend caps respected; rules → Jev (OpenRouter) → InferHub cascade unchanged; Postgres-only analytics; hosting stays gravebuster.
- AGENTS.md invariants unchanged; PROJECT_MANIFEST/HANDOFF updated when gates/scope change; PCM validator `MODE: TARGET_VALID` before checkpointing.
