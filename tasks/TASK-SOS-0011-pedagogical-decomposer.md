# TASK-SOS-0011 — Pedagogical decomposer (research + human-eval prototype)

<!-- continuity:task {"acceptance":["docs/research/pedagogical-decomposer.md with 30+ verified sources, verdict table, architecture, recovery test design","Human-eval review app at /review/decomposer with per-step Good/Bad/Prefer + optional comments on rendered artifacts","POST /api/review/decomposer append-only to ux.decomposer_review","3-4 DSA problems with multiple representation variants under docs/research/decomposer-review/","Task file + branch task/SOS-0011-pedagogical-decomposer; PR Refs #114 #111 #107 only","Deployed to gravebuster so Alex can review live","InferHub spend recorded"],"depends_on":[],"goal":"Research and prototype a Pedagogical Decomposer that turns a raw DSA problem into a golden-schema teaching sequence with renderable multi-representation artifacts, reviewed by Alex via a live HTML app backed by Postgres.","id":"SOS-0011","issue_url":"https://github.com/Pukujan/Study-os/issues/114","next_action":"Collect Alex per-step ratings; compute recovery Kendall tau; only then design production pipeline.","owner":"Pukujan (GitHub assignee); primary writer: Grok Bot executor on task/SOS-0011-pedagogical-decomposer","priority":"P1","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"active","why":"Golden dataset captures finished sequences, not how to invent them for new problems."} -->

- Status: active
- Owner: Pukujan (GitHub assignee)
- Priority: P1
- Depends on: none (related research: SOS-0010 golden dataset #111; SOS-0005 gate #107)
- Branch: `task/SOS-0011-pedagogical-decomposer`
- GitHub issue (leaf): #114 — parent: #82 — related: #111, #107

## Goal

Research-first Pedagogical Decomposer + live human-eval UI showing full proposals (not a lesson player) with rendered artifacts per step.

## Deliverables

1. `docs/research/pedagogical-decomposer.md`
2. `docs/research/decomposer-review/` (+ `web/public/review/decomposer/`)
3. Migration `0002_decomposer_review.sql` + `POST /api/review/decomposer`
4. Deploy to gravebuster
5. Receipt on #114

## Out of scope

- Production auto-authoring into the lesson player
- Merging UX draft PR #102
- Paid image-model teaching charts

## Acceptance

- [x] Research doc with verdicts + 30+ sources
- [x] Review HTML (document-style, per-step ratings, artifact render)
- [x] API + Postgres table
- [x] Live on study.design-bakery.com/review/decomposer
- [x] Receipt + InferHub spend on #114

## Checkpoint log

- 2026-09-24: Opened #114 under epic #82; research doc drafted (34 sources); curated + InferHub variants packaged; review UI + API deployed to gravebuster; PR #115.
