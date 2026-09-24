# Phased build plan

Principle: ship a **thin, private, useful** slice fast, then add intelligence. Every slice keeps all PROPERTIES invariants that apply to it. Each implementation task gets its own PCM task file and branch (`task/SOS-XXXX-*`), a leaf issue, and a PR body with `Refs #N`.

## Slice 0 — specs and issue log (this PR, #83)

Docs only.

## Slice 1 — "private beta, one DSA lesson + a HESI deck" (target: live within about 1–2 weeks of D016 acceptance)

Goal: both learners can log in at `design-bakery.com/study-os` and study every day. All learning and UX events are captured, and the tutor never leaks answers or claims mastery.

| Deliverable | Issue | Thin version |
|---|---|---|
| Hosting skeleton | #94 | Compose (`api`, `postgres`, `cloudflared`) on gravebuster; tunnel `study-api.design-bakery.com`; `study-os-web` Vercel project; design-bakery rewrite PR; nightly `pg_dump` |
| Auth | #86 | Admin CLI creates invite codes; handle + passphrase; cookie sessions (no passkeys yet) |
| DB | #87 | `auth`, `learn`, `ux` schemas; append-only triggers; schema allowlist test |
| Privacy | #95 | Scrubber on free text; no IP/UA; PII canary test |
| Controller | #90 | Web session states `START → PRESENT_STEP → AWAIT_ATTEMPT → GRADE → FEEDBACK → RETRY_DIFFERENT/CHECK → ADVANCE → SESSION_DONE` over the existing PIR sliding-window asset (the SOS-0002 rebuild once merged); a simple `REVIEW_DUE` using FSRS for HESI items |
| API | #85 | Sessions, attempts (idempotent), reactions, progress; SSE turns |
| Frontend | #84 | Login, home (two tiles: DSA lesson, HESI practice), lesson player with the persistent SVG box chart, MCQ player, reaction buttons, summary |
| HESI deck | #91 | 30–50 original/Open RN-derived MCQ + prioritization items on 3–4 KCs, rationales after the attempt, deterministic grading |
| Interpreter (minimal) | #89 | Only two operations: `grade_free_text` (unresolved text answers) and `rewrite_failed_step` (after 2 fails). Validator + fallback + telemetry + spend cap. Primary `cb/glm-5.3`, fallback `cb/deepseek-v4.1-flash` |
| Evals T0 | #92 | Detectors for P-CTL-1/2/3/5/6, P-LLM-2, P-SYS-1; 5 personas; in CI |

Explicitly **not** in slice 1: learner memory, Metabase, passkeys, the game layer beyond a simple daily streak and a progress bar, BKT, the promotion admin UI (generations are stored and marked `candidate` by a query, but promotion stays manual).

## Slice 2 — "the tutor learns what works"

- #88 learner memory v1 (allowlisted kinds, `learner.md` in interpreter context, view/delete UI).
- #89 `diagnose_misconception`, `propose_memory`. Promotion queue + admin review view.
- #92 T1 nightly on live routes; `CUE_TOO_STRONG`; the full persona set.
- #93 `analytics.*` views + Metabase (tailnet-only): progress, friction, operation effect, tutor quality/cost.

## Slice 3 — "long-running quiz game"

- Delayed checks and transfer items per KC (`pass_transfer`, `pass_delayed`), holdout pools, the mastery evidence rule shown as a "strong evidence" badge.
- Game layer: quest map over the KC graph, daily goal, streak with grace days, XP for effortful attempts and delayed-check passes, "boss rounds" = mixed delayed review. No leaderboards.
- Passkeys. Learner export/delete.
- HESI pack expansion: SATA, ordering, dosage-calculation generator.

## Slice 4 — "scale cheaply"

- BKT (pyBKT) derived estimates for next-item selection. Tutor MCP-style phase ranking (see donor audit).
- A/B-assignable operation variants (ASSISTments-style) with the `analytics.v_operation_effect` comparison.
- More subjects via packs. Invite-only beta users once invariants have held for 4+ weeks.

## Decisions and credentials needed from Alex

| # | Item | Why | Blocking |
|---|---|---|---|
| 1 | **Accept D016** (promote a private web-app track; narrowly relaxes the deferral of production UI/auth/deploy for an invite-only 2-learner beta) | `AGENTS.md` defers these until R0 | All implementation merges |
| 2 | **Vercel access**: create a `study-os-web` project from `Pukujan/Study-os` (root `web/`), or grant an agent a scoped token; approve the design-bakery `vercel.json` rewrite PR | Frontend hosting | Slice 1 frontend go-live |
| 3 | **Cloudflare**: run `cloudflared tunnel login` on gravebuster (browser auth to the design-bakery.com zone), or create the tunnel in the dashboard and give gravebuster the token; pick the hostname (proposed `study-api.design-bakery.com`) | Public API | Slice 1 go-live |
| 4 | **gravebuster access for agents**: this agent box has no Tailscale/SSH route to gravebuster (inventory was read through `ssh gravebuster` on Teresa-Pujan). Either allow deploys through Teresa-Pujan's SSH or add a deploy user/key for a pull-based deployer | Deploys | Slice 1 go-live |
| 5 | **InferHub key on gravebuster**: place `INFERHUB_API_KEY` in `/srv/study-os/.env` (mode 600) yourself; agents must not copy it off Teresa-Pujan | Interpreter | Slice 1 interpreter |
| 6 | The second learner's consent, and her pseudonym/handle choice; confirm the HESI exam type (A2 entrance vs Exit/NCLEX-style) and target month | Content scope | HESI deck |
| 7 | Spend cap (proposed US$5/month; raise freely) | P-LLM-5 | No |
| 8 | Whether Metabase may also be exposed through Cloudflare Access (email login at Cloudflare) or stays tailnet-only (default) | Analytics access from phone | No |

## Dependencies

- #80 (SOS-0002 sliding-window lesson rebuild) supplies the golden-conformant DSA lesson and the conformance evaluator that slice 1 reuses. Slice 1 can start on hosting/auth/DB/HESI in parallel.
- `study-os-benchmarker` pinned commit for detector parity (#92).
