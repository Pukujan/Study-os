# TASK-SOS-0004 — First Slice

<!-- continuity:task {"acceptance": ["D017 accepted (recorded on Alex's behalf) and D018 amendment recorded in docs/DECISIONS.md and docs/webapp/D018_AMENDMENT.md", "FastAPI backend on Postgres 16 with append-only learning/UX/decision tables, schema allowlist test, PII canary test", "Google OIDC (state+PKCE+nonce) open signup plus local email/passphrase argon2id fallback, server-side sessions (30d absolute/7d idle), CSRF, login throttling, rate limits, per-user and global daily model caps", "Web session controller serves the SOS-0002 sliding-window PIR asset and HESI A2 topic assets through the same PIR controller; FSRS review", "HESI A2 topic graph with prerequisites and checkpoints; original cited items, LLM-reviewed, all marked unreviewed", "Decision layer v1: rules then hosted Jev typesafe/jev-1.13 via OpenRouter Decisions API; every decision logged with confidence; minimal InferHub rewrite path cb/glm-5.3 -> cb/deepseek-v4.1-flash with validator, fallback and cache", "First-party tracker to POST /api/events and Metabase-ready SQL views; no PostHog", "Agent-vs-agent T0 evals offline in CI and live behind a flag, checked with src/study_os/pir/conformance.py", "React frontend built and served from gravebuster; api+postgres+cloudflared running there with health verified; tunnel/DNS for study.design-bakery.com via Cloudflare API", "Required CI green; existing tests green; PR uses Refs #N; receipts on #99"], "depends_on": [], "goal": "Build and deploy the first slice of the Study OS web app (slice 1 of docs/webapp/BUILD_PLAN.md as amended by D018): backend, auth, controller over PIR, HESI A2 topic program, decision layer, minimal LLM rewrite path, first-party analytics, agent-vs-agent evals, React frontend, all on gravebuster at study.design-bakery.com.", "id": "SOS-0004", "issue_url": "https://github.com/Pukujan/Study-os/issues/99", "next_action": "None for this task. Follow-ups: Google OAuth keys, human review of HESI items, #98 rrweb, #88 memory", "owner": "Pukujan (GitHub assignee); primary writer: Grok Bot executor on task/SOS-0004-first-slice", "priority": "P1", "protocol_version": "0.1.0-draft", "schema": "project-continuity.task.v1", "status": "completed", "why": "Alex and his wife need to study daily on a hosted app; D017 was accepted and amended by D018, so slice 1 can ship."} -->

- Status: completed
- Owner: Pukujan (GitHub assignee); primary writer: Grok Bot executor on task/SOS-0004-first-slice
- Priority: P1
- Depends on: none
- Branch: `task/SOS-0004-first-slice`
- GitHub issue (leaf): #99 — parent: #82 (web-app epic) — covers #84 #85 #86 #87 #89 #90 #91 #92 #93 #94 #95 #97; dependencies: none

## Goal

Build and deploy the first slice of the Study OS web app (slice 1 of docs/webapp/BUILD_PLAN.md as amended by D018): backend, auth, controller over PIR, HESI A2 topic program, decision layer, minimal LLM rewrite path, first-party analytics, agent-vs-agent evals, React frontend, all on gravebuster at study.design-bakery.com.

## Why

Alex and his wife need to study daily on a hosted app; D017 was accepted and amended by D018, so slice 1 can ship.

## Allowed files

- `src/study_os/web/**`, `web/**`, `deploy/**`, `tests/test_web_*.py`, `tools/web_*.py`, `tools/run_agent_evals.py`
- `pyproject.toml`, `requirements-dev.txt`, `requirements-dev.lock`, `.github/workflows/**`, `.gitignore` (build artifacts), `tools/verify_built_package.py` (web package data)
- `docs/DECISIONS.md` (D017 status, D018), `docs/webapp/**`, `docs/HANDOFF.md`, `PROJECT_MANIFEST.yaml` (web track note), `tasks/TASK-SOS-0004-first-slice.md`

## Human outcome

Alex (DSA) and his wife (HESI A2) can sign up at study.design-bakery.com and study daily; every learning, UX, and model decision event is captured in Postgres for analysis.

## Scope and boundaries

- In scope: slice 1 per BUILD_PLAN as amended by D018 (see #99).
- Out of scope: learner memory (#88), rrweb replay (#98), Metabase deployment, Laya, passkeys.
- Dependencies/uncertainty: Google OAuth client keys not yet present (local fallback active until then); HESI content needs Alex's review.

## Acceptance criteria

- [x] D017 accepted (recorded on Alex's behalf) and D018 amendment recorded in docs/DECISIONS.md and docs/webapp/D018_AMENDMENT.md
- [x] FastAPI backend on Postgres 16 with append-only learning/UX/decision tables, schema allowlist test, PII canary test
- [x] Google OIDC (state+PKCE+nonce) open signup plus local email/passphrase argon2id fallback, server-side sessions (30d absolute/7d idle), CSRF, login throttling, rate limits, per-user and global daily model caps
- [x] Web session controller serves the SOS-0002 sliding-window PIR asset and HESI A2 topic assets through the same PIR controller; FSRS review
- [x] HESI A2 topic graph with prerequisites and checkpoints; original cited items, LLM-reviewed, all marked unreviewed
- [x] Decision layer v1: rules then hosted Jev typesafe/jev-1.13 via OpenRouter Decisions API; every decision logged with confidence; minimal InferHub rewrite path cb/glm-5.3 -> cb/deepseek-v4.1-flash with validator, fallback and cache
- [x] First-party tracker to POST /api/events and Metabase-ready SQL views; no PostHog
- [x] Agent-vs-agent T0 evals offline in CI and live behind a flag, checked with src/study_os/pir/conformance.py
- [x] React frontend built and served from gravebuster; api+postgres+cloudflared running there with health verified; tunnel/DNS for study.design-bakery.com via Cloudflare API
- [x] Required CI green; existing tests green; PR uses Refs #N; receipts on #99

## Evidence and sources

- Live: `curl https://study.design-bakery.com/api/health` → 200 `{"ok":true,"decision_model":true,"llm":true,"google":false}`; SPA served with immutable hashed assets.
- Tests: `TEST_DATABASE_URL=… python -m unittest discover -s tests` (web: units, controller/decision/packs, API+Postgres, eval harness); `cd web && npm test`.
- Evals: `python tools/run_agent_evals.py --seeds 2` → 0 violations, conformance passed (`docs/webapp/evals/scorecard-t0-stub.json`); live flag run with real Jev + InferHub → 0 violations (`scorecard-t0-live.json`).
- HESI pack v0: 38 topics / 303 items; 290 servable after an independent review (deepseek) and a second solve for key disagreements (glm: 52 of 62 agreed with the key); 13 held back; every item `unreviewed`.

## Reproduction details (only when needed)

Starting revision, material inputs/configuration, runtime, exact command or prompt, observed result, and limitations.

## Related records

- Leaf #99; parent #82; dependencies none. Related: #98 (rrweb, later), #88 (memory, slice 2).
- Primary writer: Grok Bot executor / `task/SOS-0004-first-slice` / from main `2268471` / completed
- Related PR/CI evidence and push receipt (request ID / SHA): PR #100; receipts on #99.

## Checkpoint log

Receipts are posted on #99 for each checkpoint.

1. `0913474` — task file, D017 accepted / D018 recorded, handoff marker.
2. `679b78a` — backend: auth, controller, decision layer, HESI packs, migrations.
3. `284508e` — web tests + CI Postgres service; controller exit fix.
4. `2192622` — React frontend + first-party tracker + web CI job.
5. `a36899f`, `778c0b6` — deploy bundle, Cloudflare tunnel/DNS via API, live on gravebuster; agent-vs-agent evals.
6. `bd88458`, `75070ab` — frontend polish from browser e2e; full HESI A2 pack; docs.

## Handoff

Read PROJECT → CURRENT → this task → minimum relevant spec. Checkpoint before stopping.
