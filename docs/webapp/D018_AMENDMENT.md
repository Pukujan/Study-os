# D018 — owner amendment to the web-app spec (2026-09-24)

Accepted by Alex (owner), relayed by his assistant, recorded in SOS-0004 (#99). This file overrides the conflicting parts of the other `docs/webapp/` documents. Where they disagree, this file wins.

| Area | Was (SOS-0003 spec) | Now (D018) |
|---|---|---|
| Frontend hosting | Vercel project `study-os-web`, rewrite from `design-bakery.com/study-os` | Built static assets served from gravebuster by the API container at `https://study.design-bakery.com/` (Vite `base: '/'`) |
| API origin | `study-api.design-bakery.com`, CORS with credentials | Same origin: `/api/*` on `study.design-bakery.com`; no CORS |
| Edge | Cloudflare tunnel after `cloudflared tunnel login` by Alex | Named tunnel, remotely managed ingress, and proxied CNAME created through the Cloudflare API with Alex's tokens; `cloudflared` runs in Compose with its token in `/srv/study-os` (mode 600) |
| Accounts | Invite-only, pseudonymous handle + passphrase, no email | Open signup. Google sign-in primary (OIDC code + state + PKCE + nonce); local email/passphrase (argon2id) fallback. Minimal profile in `auth.*` only: Google `sub`, email, display name, handle |
| Sessions | 30-day sliding | 30-day absolute, 7-day idle; CSRF token header + Origin check on mutations |
| Abuse limits | Login 5/min per handle | Local login: 5 failures / 15 min per account, 20 / 15 min per IP (HMAC, purged daily), exponential backoff; per-IP and per-user request rate limits; per-user daily model-call cap; global daily spend cap |
| Analytics | Postgres + PostHog UX mirror + Metabase | Postgres only. First-party tracker → `POST /api/events` → `ux.event`; Metabase-ready views (`analytics.v_daily_active_learners`, `v_step_funnel`, `v_drop_off`, `v_hint_rate`, `v_accuracy_by_concept`, `v_time_on_step`, `v_learning_event`, `v_decision`). rrweb replay later (#98) |
| Caching | not specified | Lesson graphs compiled once per process; `cache.model_response` keyed by sha256(model, template, input); `/assets/*` immutable |
| HESI | 30–50 item Exit-style deck | Topic graph for HESI A2 (math, reading, vocabulary, grammar, A&P, biology, chemistry) with prerequisites and section checkpoints; Exit content areas scaffolded. Each topic compiles to a PIR asset (intro → probe → why / fix → different-example retry → extra check) served by the same controller and checked by the conformance evaluator. Original items citing OpenStax / Open RN / CDC, LLM-reviewed, all `unreviewed` until Alex reviews them |

## Privacy boundary after D018

- P-SYS-1 is narrowed for `auth.account` (email, display name) and `auth.identity` (Google subject). Nothing else may hold them.
- P-SYS-2 still holds: `learn.*` and `ux.*` never reference `auth.*`; the only bridge is `auth.account_subject`.
- Free text is scrubbed before storage or model calls. No IP address or user agent is stored. Throttling keeps only an HMAC of the IP for up to a day.

## Decision-layer note

The OpenRouter Decisions API accepts `criteria` as an **object** `{label: description}` for `choice` questions and requires an **ordered array** for `score` questions (re-probed on 2026-09-24: an array for `choice` returns HTTP 400). The implementation sends ordered arrays wherever the API allows them (score) and ordered-key objects for choice. Label order is fixed in code and logged with every decision.
