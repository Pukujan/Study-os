# TASK-SOS-0003 — Web app research, specs, and issue log

<!-- continuity:task {"acceptance":["docs/webapp/ covers research with sources, architecture, property-driven specs, session and product success/fail conditions, data model, learner memory scope, auth, hosting, analytics (plain Power BI answer), LLM route with price snapshot and live probe, agent-vs-agent test design, and a phased plan with a thin first slice","every component spec lists invariants that tests can check","epic #82 and children #84-#95 exist and are linked from docs/webapp/BUILD_PLAN.md","validate_repo.py, the unittest suite, and pinned PCM preflight stay green; required CI passes; auto-merge enabled","no private-repository content and no secrets are included"],"depends_on":[],"goal":"Research and specify the hosted Study OS web app (React at design-bakery.com/study-os, backend and DB on gravebuster, LLM interpreter via IRE/InferHub under the deterministic controller) and file its issue log.","id":"SOS-0003","issue_url":"https://github.com/Pukujan/Study-os/issues/83","next_action":"Open the docs-only PR with Refs #83, enable auto-merge, and post the push receipt on #83 with a parent update on #82.","owner":"Pukujan (GitHub assignee); primary writer: Grok Bot executor session on task/SOS-0003-webapp-specs","priority":"P2","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"active","why":"Alex promoted a hosted web app for two real learners. Without researched, testable specs, the web surface would drift from ADR-0016 deterministic control and from the no-personal-data rule."} -->

- Status: active
- Owner: Pukujan (GitHub assignee)
- Priority: P2
- Depends on: none
- Branch: `task/SOS-0003-webapp-specs`
- GitHub issue (leaf): #83 — parent: #82 (web-app epic) — dependencies: none

## Goal

Research and specify the hosted Study OS web app (React at design-bakery.com/study-os, backend and DB on gravebuster, LLM interpreter via IRE/InferHub under the deterministic controller) and file its issue log.

## Why

Alex promoted a hosted web app for two real learners. Without researched, testable specs, the web surface would drift from ADR-0016 deterministic control and from the no-personal-data rule.

## Human outcome

Alex can decide in one read: the stack, auth, DB, memory, analytics (including whether Power BI fits), LLM route and price, hosting, and the smallest slice that can go live. Agents implementing any child issue have checkable invariants and success/fail conditions to test against.

## Allowed files

- `docs/webapp/**` (new)
- `docs/DECISIONS.md` (D016 only)
- `docs/HANDOFF.md` (the `continuity:current` marker and one short web-app section)
- `tasks/TASK-SOS-0003-webapp-specs.md`

## Scope and boundaries

- In scope: research, specs, the issue log (#82 epic; #84–#95 children, linked as GitHub sub-issues), a proposed decision D016, and small live probe calls to IRE/InferHub routes (owner pre-approved on 2026-09-24).
- Out of scope: app code, deploys, infrastructure changes on gravebuster/Vercel/Cloudflare, branch `task/SOS-0002-*` (concurrent task, #80), and any private-repository content.
- Dependencies/uncertainty: D016 needs Alex's explicit acceptance before implementation PRs merge. The companion deep-research report did not exist when this PR was opened; a placeholder is in `docs/webapp/RESEARCH.md`.
- Task id note: `continuity task new` would compute SOS-0002 on this branch because SOS-0002's task file lives on its unmerged branch. This file uses SOS-0003 to avoid colliding with #80.

## Acceptance criteria

- [x] `docs/webapp/` covers every required section, with sources.
- [x] Per-component invariants are testable (`docs/webapp/PROPERTIES.md`).
- [x] Issue log exists and is linked from `docs/webapp/BUILD_PLAN.md`.
- [ ] Local checks and required CI green; auto-merge enabled (see PR).
- [x] No private-repository content or secrets.

## Evidence and sources

- Starting revision: Study OS `main` @ `b227f51d93451aa688bd3c5a707f11f5df39cbf2`.
- design-bakery `main` @ `7fdd80c` (`vercel.json` `/ai-for-good` external-rewrite pattern); DNS on Cloudflare nameservers (checked via DNS-over-HTTPS on 2026-09-24).
- gravebuster: read-only inventory over `ssh gravebuster` from Teresa-Pujan (Ubuntu 24.04.4, 16 cores, 30 GB RAM, Docker and Tailscale present; no Postgres or cloudflared).
- IRE: `docs/INFERHUB-API-SETUP.md` (local `641a7f9`), Top-20 snapshot sha256 `8e2b1b32…570e7c` (generated 2026-09-22T17:10:44Z); live probe results in `docs/webapp/LLM_ROUTE.md`.
- study-os-benchmarker @ `d438988fda12e9df902caabbcb6a639834452d5d` (violation codes).
- External sources are cited inline in `docs/webapp/RESEARCH.md`.

## Related records

- Leaf #83; parent #82; dependencies none. Sibling children: #84 frontend, #85 API, #86 auth, #87 DB, #88 memory, #89 LLM, #90 controller, #91 subjects/HESI, #92 evals, #93 analytics, #94 hosting, #95 privacy.
- Primary writer / branch: Grok Bot executor session / `task/SOS-0003-webapp-specs`; as-of status: active.
- PR/CI evidence and push receipt: posted on #83 after push.

## Checkpoint log

No checkpoints yet.

## Handoff

Read PROJECT → CURRENT → this task → `docs/webapp/README.md`. Checkpoint before stopping.
