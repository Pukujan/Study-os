# Study OS web app — spec index (SOS-0003)

Status: **proposed spec**. Owner-requested on 2026-09-24. Implementation is gated on decision [D017](../DECISIONS.md#d017--owner-promotes-a-private-hosted-web-app-track-proposed).
Leaf issue: #83. Parent epic: #82. Children: #84–#95, #97.

## What this is

A plan to turn Study OS into a hosted web app that two real learners use every day:

- **Alex**, learning DSA. This continues the sliding-window / PIR work.
- **A second learner**, learning any subject. Right now that is the HESI nursing exam.

The design keeps the Study OS architecture. Lessons are precompiled into deterministic step graphs (PIR), and the controller serves those graphs with **no model call**. Interpretation runs as a cascade:
1. **rules first**;
2. then a cheap typed decision model: **hosted Jev** for grading and misconception choice, and **Laya-421M on gravebuster** for low-stakes affect signals once calibrated;
3. then a **frontier LLM** via IRE, only on low confidence or to rewrite a failed step.

Good generations are reviewed and **promoted back into the graph**. Well-understood decisions become state-machine rules. Both make cost fall as usage grows.

## Documents

| File | Contents |
|---|---|
| [RESEARCH.md](RESEARCH.md) | Research summary and sources: tutoring systems to borrow from, hosting, auth, memory, analytics (includes the Power BI answer) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Components, request flow, LLM-as-interpreter and graph promotion, hosting topology, auth design |
| [PROPERTIES.md](PROPERTIES.md) | Property-driven specs: invariants per component, and success/fail conditions for sessions and for the product |
| [DATA_MODEL.md](DATA_MODEL.md) | Postgres schemas, learning events, UX signals, learner-memory schema and scope rules, retention |
| [LLM_ROUTE.md](LLM_ROUTE.md) | IRE/InferHub route choice, price snapshot, live probe results, spend policy |
| [AGENT_EVAL.md](AGENT_EVAL.md) | Agent-vs-agent eval harness: personas, detectors, tiers, budgets |
| [BUILD_PLAN.md](BUILD_PLAN.md) | Phased plan, the thin first slice, decision-layer switch criteria, issue map, and decisions or credentials needed from Alex |
| [DEEP_RESEARCH.md](DEEP_RESEARCH.md) | Companion deep-research report (imported): UX analytics, learning science, architectures, cost model, Jev/Laya decision layer (eval-lab evidence) |

## Recommendations at a glance

| Area | Recommendation |
|---|---|
| Frontend | Vite + React + TypeScript in `Study-os/web/`, deployed as its own Vercel project with `base: '/study-os/'`. `design-bakery.com/study-os` is served through a rewrite in design-bakery's `vercel.json`, the same pattern already used for `/ai-for-good`. |
| Backend | FastAPI (Python 3.11+) in `src/study_os/web/`. It reuses `study_os.pir` and the runtime services. Turns are delivered over SSE. |
| Hosting | Docker Compose on `gravebuster` (Ubuntu 24.04, 16 cores, 30 GB RAM) runs `api`, `postgres`, `metabase`, and `cloudflared`. A Cloudflare named tunnel publishes `study-api.design-bakery.com` (the zone is already on Cloudflare). Tailscale stays the admin-only path. Tailscale Funnel is a dev fallback only. |
| Auth | App-managed, invite-only, pseudonymous handle + passphrase (argon2id). Server-side session cookie, passkeys in phase 2. No email is stored and there is no third-party identity provider. Admin tools stay on the tailnet. |
| DB | Postgres 16 with append-only event tables. `account_id` and `subject_id` are separated so learning data is pseudonymous. |
| Learner memory | Typed, allowlisted records with provenance, plus a rendered read-only `learner.md`. The LLM proposes and the deterministic validator commits. mem0-style free-form memory is **not** adopted. |
| Decision layer | Rules → hosted **Jev via OpenRouter** (pinned `typesafe/jev-1.13`, Decisions API, `OPENROUTER_API_KEY`; live probe 3/3 valid calls after one schema fix plus an 11/12 mini grading set, 0.16–0.26 s per call; grading `noul`/`choice`, misconception `choice` + `none_of_these`; eval-lab blind 89.87%; about $0.042/1M input) → frontier LLM on low confidence. **Laya-421M** self-hosted only for frustration/wants-answer/sentiment after calibration, never for grading. Next step is deterministic (rules + pyBKT + FSRS; bandit later). Day-one decision logging, 5% audit sampling, and switch criteria (fine-tune / harness / rule) come from DEEP_RESEARCH §7.5. |
| LLM (tier 3) | Low-confidence escalation and failed-step rewrites only. Primary route **`cb/glm-5.3`** (Top-20 rank 19, eligible, "top" tier, family effective ≈ $0.267/1M; route floor $0.0378 in / $0.1188 out per 1M). Fallback route **`cb/deepseek-v4.1-flash`** (rank 1, ≈ $0.022/1M, effectively free), which is also used for simulated learners. Live probes on 2026-09-24: 12/12 calls to these two routes succeeded with streaming + forced tool calls and no answer leaks, at about $0.00001–0.00002 per call. |
| Analytics | Postgres append-only log with **xAPI-shaped events** as the source of truth. **Metabase OSS** (tailnet-only) for learning metrics. **PostHog Cloud** receives a server-side mirror of allowlisted non-PII UX events for funnels, retention, flags, and experiments. DuckDB for ad-hoc work. **Power BI only for aggregates** (RESEARCH.md §5). |
| Evals | Agent-vs-agent harness in three tiers: T0 offline in CI (recorded fixtures, free), T1 nightly on live cheap routes, T2 pre-release. Deterministic detectors mirror `study-os-benchmarker` violation codes. |

## Governance boundary

`AGENTS.md` → "Explicitly deferred" lists production UI, CD/deployment, and production auth until R0. D014 already says frontend surfaces start when the owner promotes them. D017 records that promotion as **proposed**. It narrowly covers an invite-only private beta for two learners and relaxes no evidence invariant. This PR is docs-only and changes no guardrail.
