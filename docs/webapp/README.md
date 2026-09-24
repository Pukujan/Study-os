# Study OS web app — spec index (SOS-0003)

Status: **proposed spec**. Owner-requested on 2026-09-24. Implementation is gated on decision [D016](../DECISIONS.md#d016--owner-promotes-a-private-hosted-web-app-track-proposed).
Leaf issue: #83. Parent epic: #82. Children: #84–#95.

## What this is

A plan to turn Study OS into a hosted web app that two real learners use every day:

- **Alex**, learning DSA. This continues the sliding-window / PIR work.
- **A second learner**, learning any subject. Right now that is the HESI nursing exam.

The design keeps the Study OS architecture. Lessons are precompiled into deterministic step graphs (PIR), and the controller serves those graphs with **no LLM call**. The LLM is only an **interpreter**. It grades free-text answers, diagnoses misconceptions, and rewrites a step that failed for this learner. Good generations are reviewed and **promoted back into the graph**, so cost falls as usage grows.

## Documents

| File | Contents |
|---|---|
| [RESEARCH.md](RESEARCH.md) | Research summary and sources: tutoring systems to borrow from, hosting, auth, memory, analytics (includes the Power BI answer) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Components, request flow, LLM-as-interpreter and graph promotion, hosting topology, auth design |
| [PROPERTIES.md](PROPERTIES.md) | Property-driven specs: invariants per component, and success/fail conditions for sessions and for the product |
| [DATA_MODEL.md](DATA_MODEL.md) | Postgres schemas, learning events, UX signals, learner-memory schema and scope rules, retention |
| [LLM_ROUTE.md](LLM_ROUTE.md) | IRE/InferHub route choice, price snapshot, live probe results, spend policy |
| [AGENT_EVAL.md](AGENT_EVAL.md) | Agent-vs-agent eval harness: personas, detectors, tiers, budgets |
| [BUILD_PLAN.md](BUILD_PLAN.md) | Phased plan, the thin first slice, issue map, and decisions or credentials needed from Alex |

## Recommendations at a glance

| Area | Recommendation |
|---|---|
| Frontend | Vite + React + TypeScript in `Study-os/web/`, deployed as its own Vercel project with `base: '/study-os/'`. `design-bakery.com/study-os` is served through a rewrite in design-bakery's `vercel.json`, the same pattern already used for `/ai-for-good`. |
| Backend | FastAPI (Python 3.11+) in `src/study_os/web/`. It reuses `study_os.pir` and the runtime services. Turns are delivered over SSE. |
| Hosting | Docker Compose on `gravebuster` (Ubuntu 24.04, 16 cores, 30 GB RAM) runs `api`, `postgres`, `metabase`, and `cloudflared`. A Cloudflare named tunnel publishes `study-api.design-bakery.com` (the zone is already on Cloudflare). Tailscale stays the admin-only path. Tailscale Funnel is a dev fallback only. |
| Auth | App-managed, invite-only, pseudonymous handle + passphrase (argon2id). Server-side session cookie, passkeys in phase 2. No email is stored and there is no third-party identity provider. Admin tools stay on the tailnet. |
| DB | Postgres 16 with append-only event tables. `account_id` and `subject_id` are separated so learning data is pseudonymous. |
| Learner memory | Typed, allowlisted records with provenance, plus a rendered read-only `learner.md`. The LLM proposes and the deterministic validator commits. mem0-style free-form memory is **not** adopted. |
| LLM | Interpreter-only. Primary route **`cb/glm-5.3`** (Top-20 rank 19, eligible, "top" tier, family effective ≈ $0.267/1M; route floor $0.0378 in / $0.1188 out per 1M). Fallback route **`cb/deepseek-v4.1-flash`** (rank 1, ≈ $0.022/1M, effectively free), which is also used for simulated learners. Live probes on 2026-09-24: 12/12 calls to these two routes succeeded with streaming + forced tool calls and no answer leaks, at about $0.00001–0.00002 per call. |
| Analytics | SQL views in the `analytics` schema, plus **Metabase OSS** on gravebuster (tailnet-only). DuckDB for ad-hoc work. No PostHog at first (first-party UX events are enough). **Power BI is not recommended** as the primary tool (see RESEARCH.md §5). |
| Evals | Agent-vs-agent harness in three tiers: T0 offline in CI (recorded fixtures, free), T1 nightly on live cheap routes, T2 pre-release. Deterministic detectors mirror `study-os-benchmarker` violation codes. |

## Governance boundary

`AGENTS.md` → "Explicitly deferred" lists production UI, CD/deployment, and production auth until R0. D014 already says frontend surfaces start when the owner promotes them. D016 records that promotion as **proposed**. It narrowly covers an invite-only private beta for two learners and relaxes no evidence invariant. This PR is docs-only and changes no guardrail.
