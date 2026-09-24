# TASK-SOS-0003 — Web app research, specs, and issue log

<!-- continuity:task {"acceptance":["docs/webapp/ covers research with sources, architecture, property-driven specs, session and product success/fail conditions, data model, learner memory scope, auth, hosting, analytics (plain Power BI answer), LLM route with price snapshot and live probe, agent-vs-agent test design, and a phased plan with a thin first slice","every component spec lists invariants that tests can check","epic #82 and children #84-#95 and #97 exist and are linked from docs/webapp/BUILD_PLAN.md","validate_repo.py, the unittest suite, and pinned PCM preflight stay green; required CI passes; auto-merge enabled","no private-repository content and no secrets are included","the companion deep-research report is incorporated (docs/webapp/DEEP_RESEARCH.md) and its adopted decisions are reflected in RESEARCH §0, ARCHITECTURE §4, DATA_MODEL, PROPERTIES P-DEC, and BUILD_PLAN"],"depends_on":[],"goal":"Research and specify the hosted Study OS web app (React at design-bakery.com/study-os, backend and DB on gravebuster, LLM interpreter via IRE/InferHub under the deterministic controller) and file its issue log.","id":"SOS-0003","issue_url":"https://github.com/Pukujan/Study-os/issues/83","next_action":"None for SOS-0003. Verify PR #96 merged with required checks and post the merge receipt on #83; implementation starts with separate issue-backed tasks for #82 children after Alex accepts D017.","owner":"Pukujan (GitHub assignee); primary writer: Grok Bot executor session on task/SOS-0003-webapp-specs","priority":"P2","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"completed","why":"Alex promoted a hosted web app for two real learners. Without researched, testable specs, the web surface would drift from ADR-0016 deterministic control and from the no-personal-data rule."} -->

- Status: completed
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

- `docs/webapp/**` (new, including the imported `DEEP_RESEARCH.md`)
- `docs/DECISIONS.md` (D017 only)
- `docs/HANDOFF.md` (the `continuity:current` marker and one short web-app section)
- `tasks/TASK-SOS-0003-webapp-specs.md`

## Scope and boundaries

- In scope: research, specs, the issue log (#82 epic; #84–#95 children, linked as GitHub sub-issues), a proposed decision D017, and small live probe calls to IRE/InferHub routes (owner pre-approved on 2026-09-24).
- Out of scope: app code, deploys, infrastructure changes on gravebuster/Vercel/Cloudflare, branch `task/SOS-0002-*` (concurrent task, #80), and any private-repository content.
- Dependencies/uncertainty: D017 needs Alex's explicit acceptance before implementation PRs merge. The companion deep-research report arrived after the PR opened. It is imported as `docs/webapp/DEEP_RESEARCH.md` (learner-identifying phrase and local paths removed), and its decisions are adopted in `docs/webapp/RESEARCH.md` §0.
- Task id note: `continuity task new` would compute SOS-0002 on this branch because SOS-0002's task file lives on its unmerged branch. This file uses SOS-0003 to avoid colliding with #80.

## Acceptance criteria

- [x] `docs/webapp/` covers every required section, with sources.
- [x] Per-component invariants are testable (`docs/webapp/PROPERTIES.md`).
- [x] Issue log exists and is linked from `docs/webapp/BUILD_PLAN.md`.
- [x] Local checks green; PR #96 opened with auto-merge enabled. Required CI and the merge result are recorded live on #83.
- [x] No private-repository content or secrets.

## Evidence and sources

- Starting revision: Study OS `main` @ `b227f51d93451aa688bd3c5a707f11f5df39cbf2`.
- design-bakery `main` @ `7fdd80c` (`vercel.json` `/ai-for-good` external-rewrite pattern); DNS on Cloudflare nameservers (checked via DNS-over-HTTPS on 2026-09-24).
- gravebuster: read-only inventory over `ssh gravebuster` from Teresa-Pujan (Ubuntu 24.04.4, 16 cores, 30 GB RAM, Docker and Tailscale present; no Postgres or cloudflared).
- IRE: `docs/INFERHUB-API-SETUP.md` (local `641a7f9`), Top-20 snapshot sha256 `8e2b1b32…570e7c` (generated 2026-09-22T17:10:44Z); live probe results in `docs/webapp/LLM_ROUTE.md`.
- study-os-benchmarker @ `d438988fda12e9df902caabbcb6a639834452d5d` (violation codes).
- External sources are cited inline in `docs/webapp/RESEARCH.md`.

- Decision number: proposed as D016 in the first checkpoints; renumbered to **D017** after SOS-0002 (#81) merged its own D016 into `main`.

## Related records

- Leaf #83; parent #82; dependencies none. Sibling children: #84 frontend, #85 API, #86 auth, #87 DB, #88 memory, #89 LLM, #90 controller, #91 subjects/HESI, #92 evals, #93 analytics, #94 hosting, #95 privacy, #97 decision layer.
- Primary writer / branch: Grok Bot executor session / `task/SOS-0003-webapp-specs`; as-of status: completed at this commit; PR #96 merge pending (live result on #83).
- PR/CI evidence and push receipt: posted on #83 after push.

## Checkpoint log

No checkpoints yet.

### 2026-09-24 21:46:57 UTC — Grok Bot executor (for Pukujan)

<!-- continuity:checkpoint {"agent":"Grok Bot executor (for Pukujan)","blocked":["Companion deep-research report not yet present; placeholder in docs/webapp/RESEARCH.md","Go-live needs Alex: D016 acceptance, Vercel project, Cloudflare tunnel login, gravebuster deploy access, InferHub key on gravebuster"],"changed":["docs/webapp/**","docs/DECISIONS.md","docs/HANDOFF.md","tasks/TASK-SOS-0003-webapp-specs.md"],"completed":["Created epic #82 and children #84-#95 (linked as sub-issues) plus leaf #83","Wrote docs/webapp/ (README, RESEARCH, ARCHITECTURE, PROPERTIES, DATA_MODEL, LLM_ROUTE, AGENT_EVAL, BUILD_PLAN), proposed D016, HANDOFF web-app note","Ran 12 small live IRE/InferHub probe calls (owner pre-approved): cb/glm-5.3 6/6 and cb/deepseek-v4.1-flash 4/4 clean streamed forced tool calls; cbcn GLM routes 503"],"decisions":["Task id SOS-0003 set manually because SOS-0002 (#80) lives on an unmerged concurrent branch","LLM is an interpreter only; primary route cb/glm-5.3 (priced, above the 0.10 threshold, owner-approved quality over cost), fallback cb/deepseek-v4.1-flash","Implementation merges gated on Alex accepting D016; docs-only PR changes no guardrail"],"evidence":["Product commit 7d0da9835f27a36a3fcac993d19f4d6190c33e46 on task/SOS-0003-webapp-specs from main b227f51","Local: validate_repo.py passed; unittest 350 tests OK; pinned PCM preflight MODE: TARGET_VALID","IRE Top-20 snapshot sha256 8e2b1b323cf9438b1274f321c309729d60f133ef14915895265ca76758570e7c (2026-09-22T17:10:44Z)"],"next_action":"Open the PR with Refs #83, enable auto-merge, post receipts on #83 and #82; then close out SOS-0003","protocol_version":"0.1.0-draft","schema":"project-continuity.checkpoint.v1","task_id":"SOS-0003","timestamp":"2026-09-24T21:46:57Z"} -->
<!-- continuity:checkpoint-operation {"payload_sha256":"33bbfb7eedef1a28844c5d5cfa8779f0a74671e8b4ea3b7249ed1997441ed068","request_id":"sos-0003-cp1-20260924","schema":"project-continuity.checkpoint-operation.v1","task_id":"SOS-0003"} -->

Completed:
- Created epic #82 and children #84-#95 (linked as sub-issues) plus leaf #83
- Wrote docs/webapp/ (README, RESEARCH, ARCHITECTURE, PROPERTIES, DATA_MODEL, LLM_ROUTE, AGENT_EVAL, BUILD_PLAN), proposed D016, HANDOFF web-app note
- Ran 12 small live IRE/InferHub probe calls (owner pre-approved): cb/glm-5.3 6/6 and cb/deepseek-v4.1-flash 4/4 clean streamed forced tool calls; cbcn GLM routes 503

Evidence:
- Product commit 7d0da9835f27a36a3fcac993d19f4d6190c33e46 on task/SOS-0003-webapp-specs from main b227f51
- Local: validate_repo.py passed; unittest 350 tests OK; pinned PCM preflight MODE: TARGET_VALID
- IRE Top-20 snapshot sha256 8e2b1b323cf9438b1274f321c309729d60f133ef14915895265ca76758570e7c (2026-09-22T17:10:44Z)

Decisions:
- Task id SOS-0003 set manually because SOS-0002 (#80) lives on an unmerged concurrent branch
- LLM is an interpreter only; primary route cb/glm-5.3 (priced, above the 0.10 threshold, owner-approved quality over cost), fallback cb/deepseek-v4.1-flash
- Implementation merges gated on Alex accepting D016; docs-only PR changes no guardrail

Changed:
- docs/webapp/**
- docs/DECISIONS.md
- docs/HANDOFF.md
- tasks/TASK-SOS-0003-webapp-specs.md

Blocked/uncertain:
- Companion deep-research report not yet present; placeholder in docs/webapp/RESEARCH.md
- Go-live needs Alex: D016 acceptance, Vercel project, Cloudflare tunnel login, gravebuster deploy access, InferHub key on gravebuster

Next:
- Open the PR with Refs #83, enable auto-merge, post receipts on #83 and #82; then close out SOS-0003

### 2026-09-24 21:47:14 UTC — Grok Bot executor (for Pukujan)

<!-- continuity:checkpoint {"agent":"Grok Bot executor (for Pukujan)","blocked":["Implementation needs Alex: D016 acceptance, Vercel project, Cloudflare tunnel login, gravebuster deploy access, InferHub key on gravebuster"],"changed":["tasks/TASK-SOS-0003-webapp-specs.md","docs/HANDOFF.md"],"completed":["Opened PR #96 (Refs #83) and closed out SOS-0003: task completed, continuity:current cleared"],"decisions":["Close out in-PR like SOS-0001 so the HANDOFF marker diff against main is zero and does not conflict with the concurrent SOS-0002 branch"],"evidence":["Closeout commit 9265155226743f7afc364508f45bfb678ea84a03; PCM preflight TARGET_VALID; validate_repo passed"],"next_action":"Confirm PR #96 merged with required checks and post the merge receipt on #83; no further SOS-0003 work","protocol_version":"0.1.0-draft","schema":"project-continuity.checkpoint.v1","task_id":"SOS-0003","timestamp":"2026-09-24T21:47:14Z"} -->
<!-- continuity:checkpoint-operation {"payload_sha256":"dd21d780ce0b14897f7263040c8969dba10f7e3e09e0c70d532b1e33bf78f00e","request_id":"sos-0003-cp2-20260924","schema":"project-continuity.checkpoint-operation.v1","task_id":"SOS-0003"} -->

Completed:
- Opened PR #96 (Refs #83) and closed out SOS-0003: task completed, continuity:current cleared

Evidence:
- Closeout commit 9265155226743f7afc364508f45bfb678ea84a03; PCM preflight TARGET_VALID; validate_repo passed

Decisions:
- Close out in-PR like SOS-0001 so the HANDOFF marker diff against main is zero and does not conflict with the concurrent SOS-0002 branch

Changed:
- tasks/TASK-SOS-0003-webapp-specs.md
- docs/HANDOFF.md

Blocked/uncertain:
- Implementation needs Alex: D016 acceptance, Vercel project, Cloudflare tunnel login, gravebuster deploy access, InferHub key on gravebuster

Next:
- Confirm PR #96 merged with required checks and post the merge receipt on #83; no further SOS-0003 work

### 2026-09-24 21:51:38 UTC — Grok Bot executor (for Pukujan)

<!-- continuity:checkpoint {"agent":"Grok Bot executor (for Pukujan)","blocked":["Implementation needs Alex: D017 acceptance, Vercel project, Cloudflare tunnel login, gravebuster deploy access, InferHub/TypeSafe/PostHog keys on gravebuster"],"changed":["docs/webapp/**","tasks/TASK-SOS-0003-webapp-specs.md","docs/HANDOFF.md"],"completed":["Imported the companion deep-research report as docs/webapp/DEEP_RESEARCH.md (learner-identifying phrase and local paths removed)","Adopted: rules first; hosted Jev for grading and misconception choice; Laya-421M on gravebuster only for calibrated low-stakes affect signals; frontier LLM (IRE cb/glm-5.3) only on low confidence and for rewrites; deterministic next step (rules + pyBKT + FSRS, bandit later); xAPI-shaped events + Metabase + PostHog UX mirror, Power BI for aggregates only; day-one decision logging, 5% audit sampling, and section 7.5 switch criteria","Created decision-layer child issue #97 and linked it under epic #82"],"decisions":["Jev not probed live: no key available to this agent; tier 3 covers tier-2 duties until Alex provides TYPESAFE_API_KEY"],"evidence":["Commit de63020868bbaa016e957d712531f44eb6705f45; PCM preflight TARGET_VALID; validate_repo passed"],"next_action":"Re-enable auto-merge on PR #96; after merge, post the merge receipt on #83; no further SOS-0003 work","protocol_version":"0.1.0-draft","schema":"project-continuity.checkpoint.v1","task_id":"SOS-0003","timestamp":"2026-09-24T21:51:38Z"} -->
<!-- continuity:checkpoint-operation {"payload_sha256":"5600f4fd110f421639176b9bce0480858c23c61ba28d0c1149a42bc2c7e99e0a","request_id":"sos-0003-cp3-20260924","schema":"project-continuity.checkpoint-operation.v1","task_id":"SOS-0003"} -->

Completed:
- Imported the companion deep-research report as docs/webapp/DEEP_RESEARCH.md (learner-identifying phrase and local paths removed)
- Adopted: rules first; hosted Jev for grading and misconception choice; Laya-421M on gravebuster only for calibrated low-stakes affect signals; frontier LLM (IRE cb/glm-5.3) only on low confidence and for rewrites; deterministic next step (rules + pyBKT + FSRS, bandit later); xAPI-shaped events + Metabase + PostHog UX mirror, Power BI for aggregates only; day-one decision logging, 5% audit sampling, and section 7.5 switch criteria
- Created decision-layer child issue #97 and linked it under epic #82

Evidence:
- Commit de63020868bbaa016e957d712531f44eb6705f45; PCM preflight TARGET_VALID; validate_repo passed

Decisions:
- Jev not probed live: no key available to this agent; tier 3 covers tier-2 duties until Alex provides TYPESAFE_API_KEY

Changed:
- docs/webapp/**
- tasks/TASK-SOS-0003-webapp-specs.md
- docs/HANDOFF.md

Blocked/uncertain:
- Implementation needs Alex: D017 acceptance, Vercel project, Cloudflare tunnel login, gravebuster deploy access, InferHub/TypeSafe/PostHog keys on gravebuster

Next:
- Re-enable auto-merge on PR #96; after merge, post the merge receipt on #83; no further SOS-0003 work

### 2026-09-24 21:53:31 UTC — Grok Bot executor (for Pukujan)

<!-- continuity:checkpoint {"agent":"Grok Bot executor (for Pukujan)","blocked":["Go-live needs Alex: D017 acceptance, Vercel project, Cloudflare tunnel login, gravebuster deploy access, INFERHUB/OPENROUTER/PostHog keys in gravebuster /srv/study-os/.env"],"changed":["docs/webapp/**"],"completed":["Recorded the owner-chosen tier-2 route: OpenRouter Decisions API, pinned typesafe/jev-1.13 (never ~typesafe/jev-latest in production), OPENROUTER_API_KEY, reference adapter typesafe-ai/system-one-adapter-python","Live Jev probe: 4 calls (one HTTP 400 because score criteria must be an ordered array; fixed) plus a 12-item mini grading set scoring 11/12, with all confidence>=0.9 predictions correct, 0.16-0.26 s per call"],"decisions":["Only the env var name is referenced in specs; the key was loaded in-process from the approved box env file and never printed or committed"],"evidence":["Commit ddc0707f0ae98cb897f4b00939a72faba5081fd6; PCM preflight TARGET_VALID; validate_repo passed"],"next_action":"Re-enable auto-merge on PR #96; after merge, post the merge receipt on #83","protocol_version":"0.1.0-draft","schema":"project-continuity.checkpoint.v1","task_id":"SOS-0003","timestamp":"2026-09-24T21:53:31Z"} -->
<!-- continuity:checkpoint-operation {"payload_sha256":"b9010d01ba8d032eccadd1592615d7dfdccc74f2e721f524f84e2078e822cc87","request_id":"sos-0003-cp4-20260924","schema":"project-continuity.checkpoint-operation.v1","task_id":"SOS-0003"} -->

Completed:
- Recorded the owner-chosen tier-2 route: OpenRouter Decisions API, pinned typesafe/jev-1.13 (never ~typesafe/jev-latest in production), OPENROUTER_API_KEY, reference adapter typesafe-ai/system-one-adapter-python
- Live Jev probe: 4 calls (one HTTP 400 because score criteria must be an ordered array; fixed) plus a 12-item mini grading set scoring 11/12, with all confidence>=0.9 predictions correct, 0.16-0.26 s per call

Evidence:
- Commit ddc0707f0ae98cb897f4b00939a72faba5081fd6; PCM preflight TARGET_VALID; validate_repo passed

Decisions:
- Only the env var name is referenced in specs; the key was loaded in-process from the approved box env file and never printed or committed

Changed:
- docs/webapp/**

Blocked/uncertain:
- Go-live needs Alex: D017 acceptance, Vercel project, Cloudflare tunnel login, gravebuster deploy access, INFERHUB/OPENROUTER/PostHog keys in gravebuster /srv/study-os/.env

Next:
- Re-enable auto-merge on PR #96; after merge, post the merge receipt on #83

## Handoff

Read PROJECT → CURRENT → this task → `docs/webapp/README.md`. Checkpoint before stopping.
