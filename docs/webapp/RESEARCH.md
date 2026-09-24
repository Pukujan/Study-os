# Research summary and recommendations

Scope: what the hosted web app should borrow, and the infrastructure choices (hosting, auth, memory, analytics). This complements the existing [`docs/OSS_TUTORING_DONOR_AUDIT.md`](../OSS_TUTORING_DONOR_AUDIT.md) (Tutor MCP, ScaffoldLM, OATutor, Oppia, catsim, DeepTutor, pyBKT/pyKT, FSRS) and does not repeat it.

> **Companion deep-research report.** A separate report on edtech UX analytics, pedagogy, production architectures, and the LLM-as-interpreter cost model is being prepared (working path `/workspace/research/study-os-deep-research.md` on the shared agent box; it is not in this repo). It did not exist when this PR was opened. When it lands, fold its sources and findings into §1, §4, and §5 through a follow-up under #82. This file is deliberately lighter on those areas.

Evidence labels used below: **[E]** empirical research finding; **[P]** product practice (publicly described, efficacy not established); **[D]** design inference for Study OS.

## 1. Tutoring systems: what to borrow concretely

| System / idea | What it does | Borrow for Study OS web | Where it lands |
|---|---|---|---|
| **Cognitive Tutors / Carnegie Learning MATHia** (Anderson, Corbett, Koedinger, Pelletier 1995, *J. Learning Sciences* 4(2)) | Model tracing against a cognitive model of the steps. Each step gets immediate feedback, and a skill is mastered only after enough correct opportunities. | Step-level grading against the PIR step graph (the "cognitive model" is the golden). Each skill has its own knowledge component (KC) opportunity count. Mastery is gated per KC, never per session. **[E]** | #90, DATA_MODEL `learn.kc_opportunity` |
| **Knowledge tracing: BKT** (Corbett & Anderson 1995, *UMUAI* 4:253–278; [pyBKT](https://github.com/CAHLR/pyBKT)) | Four interpretable parameters (prior, learn, slip, guess) per KC. | Use as a **derived** estimate for "what to practise next". It never replaces the evidence-based capability states. Estimates are recorded as `derived`, with parameters versioned. **[E]/[D]** | slice 3, #88 |
| **DKT** (Piech et al. 2015, [arXiv:1506.05908](https://arxiv.org/abs/1506.05908)) | RNN knowledge tracing. | **Do not adopt.** Two learners means far too little data, and it is not interpretable. Revisit only as a pyKT benchmark if a beta grows. **[D]** | — |
| **FSRS / Anki** ([py-fsrs](https://github.com/open-spaced-repetition/py-fsrs), already a dependency; [FSRS wiki](https://github.com/open-spaced-repetition/fsrs4anki/wiki)) | Spaced-repetition scheduler with difficulty, stability, and retrievability. | Schedule **delayed checks** (`pass_delayed`) and HESI item review. Use the existing `adaptive/fsrs_adapter.py`. The rating comes from observed correctness plus assistance level, not self-report. **[E]** | #90, #91 |
| **Duolingo** (half-life regression: Settles & Meeder 2016, ACL; [Birdbrain](https://blog.duolingo.com/learning-how-to-help-you-learn-introducing-birdbrain/)) | Gamified short lessons, streaks, XP, a difficulty model aiming at about 80% success. | Borrow the **session shape**: short rounds, instant feedback, a visible path, a daily goal, a streak **with free grace days**. XP counts effortful attempts and delayed-check passes, not raw correctness. Avoid loss-aversion pressure and do not show leaderboards (only two learners, and it is a comparison-harm risk). **[P]** | #84 |
| **ASSISTments** (Heffernan & Heffernan 2014, *IJAIED* 24:470–497) | Problems with scaffolding sub-questions after a wrong answer. Also a platform for randomized A/B tests of hints. | A wrong answer on a hard step becomes **scaffold sub-questions**, which is the golden "retry with a smaller step". Borrow the **A/B test infrastructure** idea: operation variants are versioned modules that can be randomly assigned and whose outcomes are compared. **[E]** | #90, #93 |
| **AutoTutor** (Graesser et al.; Nye, Graesser & Hu 2014, *IJAIED* 24:427–469) | Expectation-misconception tailored dialogue: pump → hint → prompt → assertion. | Maps directly onto assistance levels A1→A6. The interpreter matches free text against **expected parts and known misconceptions** listed in the step graph. The LLM only classifies; it does not converse freely. **[E]** | #89 |
| **Assistance dilemma / fading** (Koedinger & Aleven 2007, *Ed. Psych. Review* 19:239–264; Renkl & Atkinson 2003) | Too much help hurts learning and too little stalls it. Fade worked examples over time. | Enforced by the controller: an assistance ceiling per step, and fade after correct answers (`FADE` state). Correct-at-A5 ≠ correct-at-A0. **[E]** | #90 |
| **Retrieval practice** (Roediger & Karpicke 2006, *Psych. Science* 17(3)) | Testing beats restudy for retention. | Every session opens with **due retrieval items** (`REVIEW_DUE`) before new material. **[E]** | #90 |
| **Tutoring efficacy** (VanLehn 2011, *Educational Psychologist* 46(4):197–221) | Step-based ITSs approach human-tutor effect sizes. Answer-based systems help less. | Keep grading **step-based**, not end-answer only. **[E]** | #90 |
| **Khanmigo** ([khanmigo.ai](https://www.khanmigo.ai/)) and **LearnLM** (Google 2024, [arXiv:2407.12687](https://arxiv.org/abs/2407.12687)) | Socratic LLM tutors that avoid giving answers, with pedagogy benchmarks. | Confirms the failure modes to test: answer leakage, over-helping, and false praise. Study OS goes further: the LLM never owns the dialogue policy (ADR-0016). Borrow LearnLM-style **pedagogy rubrics** for T2 evals. **[P]** | #92 |
| **OATutor / Oppia** (see donor audit) | Open-source step and hint content formats, and misconception-tagged answer groups. | The subject-pack item format: answer groups with misconception tags, hint ladders, and a license field per item. **[P]** | #91 |

**The main takeaway [D]:** the highest-leverage ideas are (a) step-level model tracing, (b) spaced retrieval, (c) scaffolding with fading, and (d) versioned A/B-able operations. Study OS already has the controller semantics for all four. The web app mostly needs to surface them and log them cleanly. Generative-AI tutoring products are useful mainly as a list of failure modes.

## 2. Hosting

Observed on 2026-09-24:

- `design-bakery.com` uses Cloudflare nameservers (`mack`/`raquel.ns.cloudflare.com`), is proxied, and is served by Vercel. The apex redirects (307) to `www`.
- The Pukujan/design-bakery `vercel.json` (on main at `7fdd80c`) already proxies `/ai-for-good/*` to a separate Vercel project (`ai-for-good-livid.vercel.app`) using external rewrites ordered **before** the SPA catch-all.
- `gravebuster` (checked read-only over SSH from Teresa-Pujan) runs Ubuntu 24.04.4 with a 6.8 kernel, 16 cores, 30 GB RAM (about 9 GB available), and 128 GB free on `/`. Docker and Tailscale 1.102.2 are installed. Postgres, cloudflared, node, and uv are not.

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Cloudflare Tunnel** (named, `cloudflared`), [docs](https://developers.cloudflare.com/tunnel/routing/) | Free. Custom hostname on the zone Alex already has. WAF/DDoS protection. No open ports. Optional Access (free up to 50 users). | One more daemon, and Cloudflare terminates TLS (acceptable for learning data). | **Recommended** for the public API |
| **Tailscale Funnel**, [docs](https://tailscale.com/docs/features/tailscale-funnel) | Already installed, one command. | Only `*.ts.net` names, only ports 443/8443/10000, non-configurable bandwidth limits, aimed at dev/sharing. | Dev/preview fallback only |
| Port-forward + Caddy | Full control. | Opens the home network and needs dynamic DNS. | No |

Vercel serving: external rewrites have a **120 s time-to-first-byte** proxy limit, and after that the stream continues as long as bytes keep arriving ([Vercel limits](https://vercel.com/docs/limits), [changelog](https://vercel.com/changelog/cdn-origin-timeout-increased-to-two-minutes)). This is fine for the static app. The API is called **directly** at `study-api.design-bakery.com`, which avoids the double proxy. Because it is the same site as `www.design-bakery.com`, SameSite=Lax cookies still work.

## 3. Auth

Constraints: two learners now, possibly a small beta later, **no personal data**, and the backend at home.

| Option | Personal data held | Verdict |
|---|---|---|
| **App-managed invite-only handle + passphrase (argon2id), server sessions; passkeys next** ([OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [OWASP sessions](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)) | None (the handle is pseudonymous) | **Recommended** |
| Supabase Auth (design-bakery already uses Supabase) | Email at Supabase | No: puts identity at a third party, and email is personal data |
| Cloudflare Access as the learner login | Email at Cloudflare | Use only for **admin** surfaces, if at all |
| Tailscale-only access | Device identity | Too much friction for the second learner's devices |

## 4. Learner memory

- **mem0** ([repo](https://github.com/mem0ai/mem0); [arXiv:2504.19413](https://arxiv.org/abs/2504.19413)) uses LLM-driven extraction of free-form "facts" with add/update/delete. That is a good *operation model*, but free-form extraction is exactly how off-scope personal facts leak in ("she mentioned her night shift"). **[D]**
- **Recommendation:** use typed, allowlisted memory kinds with provenance (DATA_MODEL §4). Keep mem0's add/update/delete/noop proposal shape, but have a deterministic validator commit. Render `learner.md` as a read-only projection for the LLM context window. This follows the existing Study OS rule that derived learner-state claims need provenance and uncertainty.

## 5. Analytics — and the Power BI question

**Plain answer: Power BI can do it, but it is the wrong primary tool here.** Power BI Desktop can connect to Postgres (Npgsql is bundled), and DAX is fine for measures. But:

- authoring is Windows-only;
- scheduled refresh from a home Postgres needs the **on-premises data gateway, which is Windows-only** ([Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/connect-data/refresh-scheduled-refresh)) and would run on Teresa-Pujan, not gravebuster;
- publishing and sharing needs a **Pro license**, with 8 refreshes/day on Pro;
- it adds a second metric language (DAX) next to SQL, for two users.

If Alex wants DAX practice for career reasons, Power BI Desktop can read the same read-only `analytics.*` views over Tailscale at no cost. It just should not be on the critical path.

| Tool | Fit |
|---|---|
| **Postgres views (`analytics.*`) + Metabase OSS** ([docs](https://www.metabase.com/docs/latest/)) | **Recommended.** One Docker container (about 1–2 GB RAM), SQL-native, good dashboards and alerts, runs on gravebuster, reached over the tailnet only. |
| DuckDB ([postgres extension](https://duckdb.org/docs/extensions/postgres)) | Recommended for ad-hoc and notebook analysis and for exports. No server. |
| Evidence.dev ([evidence.dev](https://evidence.dev)) | Optional: markdown+SQL reports in git, good for a weekly "what worked" report. |
| Grafana | Optional for ops metrics (latency, errors, LLM spend). Not needed for learning analytics. |
| Apache Superset | Capable but heavier than Metabase with no benefit at this scale. |
| PostHog | Not at first. Self-hosted hobby deploy wants 8–16 GB RAM ([docs](https://posthog.com/docs/self-host)), which exceeds gravebuster's free headroom. Cloud would send behavior data to a third party. First-party UX events (DATA_MODEL §3) cover sentiment and frustration. Revisit for session replay only if a beta grows. |

## 6. Content licensing for HESI

HESI exam content is proprietary (Elsevier). Subject packs must use original items, or openly licensed sources such as the **Open RN** nursing textbooks (CC BY 4.0, e.g. [Nursing Fundamentals](https://wtcs.pressbooks.pub/nursingfundamentals/)). Every item carries a `license` and `source` field (#91). Dosage-calculation items are generated deterministically.
