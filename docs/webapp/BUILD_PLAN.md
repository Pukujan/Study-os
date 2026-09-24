# Phased build plan

Principle: ship a **thin, private, useful** slice fast, then add intelligence. Every slice keeps all PROPERTIES invariants that apply to it. Each implementation task gets its own PCM task file and branch (`task/SOS-XXXX-*`), a leaf issue, and a PR body with `Refs #N`.

## Slice 0 — specs and issue log (this PR, #83)

Docs only.

## Slice 1 — "private beta, one DSA lesson + a HESI deck" (target: live within about 1–2 weeks of D017 acceptance)

Goal: both learners can log in at `design-bakery.com/study-os` and study every day. All learning and UX events are captured, and the tutor never leaks answers or claims mastery.

| Deliverable | Issue | Thin version |
|---|---|---|
| Hosting skeleton | #94 | Compose (`api`, `postgres`, `cloudflared`) on gravebuster; tunnel `study-api.design-bakery.com`; `study-os-web` Vercel project; design-bakery rewrite PR; nightly `pg_dump` |
| Auth | #86 | Admin CLI creates invite codes; handle + passphrase; cookie sessions (no passkeys yet) |
| DB | #87 | `auth`, `learn`, `ux` schemas; append-only triggers; schema allowlist test |
| Privacy | #95 | Scrubber on free text; no IP/UA; PII canary test |
| Controller | #90 | Web session states `START → PRESENT_STEP → AWAIT_ATTEMPT → GRADE → FEEDBACK → RETRY_DIFFERENT/CHECK → ADVANCE → SESSION_DONE` over the golden-conformant PIR sliding-window asset (SOS-0002, merged in PR #81); a simple `REVIEW_DUE` using FSRS for HESI items |
| API | #85 | Sessions, attempts (idempotent), reactions, progress; SSE turns |
| Frontend | #84 | Login, home (two tiles: DSA lesson, HESI practice), lesson player with the persistent SVG box chart, MCQ player, reaction buttons, summary |
| HESI deck | #91 | 30–50 original/Open RN-derived MCQ + prioritization items on 3–4 KCs, rationales after the attempt, deterministic grading |
| Decision layer v1 | #97 | Rules first. `/v1/systemone` client with hosted Jev (if a key is available) for grading and misconception choice. **Day-one `learn.decision` logging** with 5% audit sampling. Conservative τ. No Laya yet |
| LLM interpreter (minimal) | #89 | Tier 3 only: `grade_free_text` on low confidence/no Jev, and `rewrite_failed_step` (after 2 fails). Validator + fallback + telemetry + spend cap. Primary `cb/glm-5.3`, fallback `cb/deepseek-v4.1-flash` |
| Analytics (minimal) | #93 | xAPI-shaped `analytics.v_learning_event` view. Server-side PostHog mirror of allowlisted UX events. Metabase can wait for slice 2 |
| Evals T0 | #92 | Detectors for P-CTL-1/2/3/5/6, P-LLM-2, P-SYS-1; 5 personas; in CI |

Explicitly **not** in slice 1: learner memory, Metabase dashboards, Laya, passkeys, the game layer beyond a simple daily streak and a progress bar, BKT, the promotion admin UI (generations are stored and marked `candidate` by a query, but promotion stays manual).

## Slice 2 — "the tutor learns what works"

- #88 learner memory v1 (allowlisted kinds, `learner.md` in interpreter context, view/delete UI).
- #89 `diagnose_misconception`, `propose_memory`. Promotion queue + admin review view.
- #92 T1 nightly on live routes; `CUE_TOO_STRONG`; the full persona set.
- #93 `analytics.*` views + Metabase (tailnet-only): progress, friction, operation effect, interpreter quality (accuracy vs reviewer labels, ECE/Brier, escalation rate, dispute rate, cost per learner-hour). PostHog funnels and retention.
- #97 Laya-421M on gravebuster for frustration / wants-answer / sentiment, **after** per-type temperature calibration on Study OS labels. Reviewer-label UI for decisions (gold labels). First τ fit on a public split, with a blind split held back.

## Slice 3 — "long-running quiz game"

- Delayed checks and transfer items per KC (`pass_transfer`, `pass_delayed`), holdout pools, the mastery evidence rule shown as a "strong evidence" badge.
- Game layer: quest map over the KC graph, daily goal, streak with grace days, XP for effortful attempts and delayed-check passes, "boss rounds" = mixed delayed review. No leaderboards.
- Passkeys. Learner export/delete.
- HESI pack expansion: SATA, ordering, dosage-calculation generator.

## Slice 4 — "scale cheaply"

- BKT (pyBKT) derived estimates for next-item selection. Tutor MCP-style phase ranking (see donor audit).
- A/B-assignable operation variants (ASSISTments-style) with the `analytics.v_operation_effect` comparison.
- More subjects via packs. Invite-only beta users once invariants have held for 4+ weeks.

## Decision-layer upgrade path and switch criteria

Adopted from [DEEP_RESEARCH.md §7.5](DEEP_RESEARCH.md#75-upgrade-path-for-the-decision-layer-alexs-plan-with-switch-criteria). Per decision type (grade, misconception, affect, intent), choose one path once the day-one logs support it:

| Path | Data needed | Switch when |
|---|---|---|
| **(a) Fine-tune ModernBERT or Laya** on Study OS multi-source labels | ≥300–1,000 labelled examples per decision type (SetFit can start at 8–16 per class). Label provenance: reviewer (gold), deterministic verifier (gold), LLM adjudication (silver), learner outcome (e.g. a graded pass followed by an unaided transfer pass) | On the frozen blind Study OS set: within about 2 pp of the incumbent (Jev) **and** ECE ≤ 0.05 after temperature scaling **and** precision ≥ the τ target in the auto-accept band; plus a cost, latency, or privacy gain |
| **(b) Improve the harness** | The same decision logs plus error-analysis tags | Errors cluster in prompt/schema causes rather than capability (e.g. switch holistic pass/fail to one `noul` per rubric point, or to comparison against a reference answer); accept when blind accuracy or ECE improves with no coverage loss |
| **(c) Convert to a state-machine rule** | Logs showing a few observable features determine the decision | The rule reproduces model labels on ≥98% of logged cases with reviewer-confirmed correctness, and it covers meaningful traffic. It then becomes a PIR/controller transition |

Standing rule: nothing is promoted on one session's evidence (Study OS subject → repeated → lesson → cross-subject thresholds).

## Decisions and credentials needed from Alex

| # | Item | Why | Blocking |
|---|---|---|---|
| 1 | **Accept D017** (promote a private web-app track; narrowly relaxes the deferral of production UI/auth/deploy for an invite-only 2-learner beta) | `AGENTS.md` defers these until R0 | All implementation merges |
| 2 | **Vercel access**: create a `study-os-web` project from `Pukujan/Study-os` (root `web/`), or grant an agent a scoped token; approve the design-bakery `vercel.json` rewrite PR | Frontend hosting | Slice 1 frontend go-live |
| 3 | **Cloudflare**: run `cloudflared tunnel login` on gravebuster (browser auth to the design-bakery.com zone), or create the tunnel in the dashboard and give gravebuster the token; pick the hostname (proposed `study-api.design-bakery.com`) | Public API | Slice 1 go-live |
| 4 | **gravebuster access for agents**: this agent box has no Tailscale/SSH route to gravebuster (inventory was read through `ssh gravebuster` on Teresa-Pujan). Either allow deploys through Teresa-Pujan's SSH or add a deploy user/key for a pull-based deployer | Deploys | Slice 1 go-live |
| 5 | **InferHub key on gravebuster**: place `INFERHUB_API_KEY` in `/srv/study-os/.env` (mode 600) yourself; agents must not copy it off Teresa-Pujan | Interpreter | Slice 1 interpreter |
| 6 | The second learner's consent, and her pseudonym/handle choice; confirm the HESI exam type (A2 entrance vs Exit/NCLEX-style) and target month | Content scope | HESI deck |
| 7 | Spend cap (proposed US$5/month; raise freely) | P-LLM-5 | No |
| 7a | **Hosted Jev access** (TypeSafe waitlist or Vercel AI Gateway `typesafe-ai/jev`): put `TYPESAFE_API_KEY` on gravebuster | Tier-2 grading and misconception decisions. Until then, tier 3 handles them | No (degrades to tier 3) |
| 7b | **PostHog Cloud project** (free tier) and project key on gravebuster; confirm the US or EU region | UX funnels, flags, experiments | No |
| 7c | A reviewer for HESI decision labels and promoted nursing content (clinical accuracy) | Gold labels, content safety | Before promoting HESI generations |
| 8 | Whether Metabase may also be exposed through Cloudflare Access (email login at Cloudflare) or stays tailnet-only (default) | Analytics access from phone | No |

## Dependencies

- #80 (SOS-0002 sliding-window lesson rebuild, merged in PR #81) supplies the golden-conformant DSA lesson (`sep4.sliding-window.golden-box-index-enumerate-append.v2`) and `src/study_os/pir/conformance.py`, which slice 1 reuses for detector parity.
- `study-os-benchmarker` pinned commit for detector parity (#92).
