# LLM route choice (IRE / InferHub)

## 1. Policy inputs

- The IRE runbook (`docs/INFERHUB-API-SETUP.md` in Pukujan/inference-recommendation-engine, local checkout on Teresa-Pujan at `641a7f9`) says: routes under **0.10 USDC per 1M tokens** count as effectively free; prefer recommendation-eligible Top 20/Top 20+ entries; verify live route, price, and tool/stream support; record snapshot and route.
- Owner direction on 2026-09-24: cheap calls through IRE routes are pre-approved. **Tutoring quality and reliability matter more than cost.** Cost must never block progress, but route and price must be recorded, and a pricier route is never picked silently.
- Architecture: the LLM is an **interpreter only** (ARCHITECTURE §4). Volume is therefore low: only unresolved free-text, diagnoses, and rewrites of failed steps.

## 2. Snapshot used

| Field | Value |
|---|---|
| Recommendation view | IRE InferHub research `TOP-20-RECOMMENDATIONS.md`, profile `daily-cheap-reliable-recent`, generated 2026-09-22T17:10:44Z (13:10 ET) |
| Snapshot file | `research_model_top20_recommendations.csv`, sha256 `8e2b1b323cf9438b1274f321c309729d60f133ef14915895265ca76758570e7c` |
| Route prices | `research_model_route_performance.csv` in the same snapshot (public status updated 2026-09-22T16:23Z) |
| Catalog check | IRE route audit observed `https://inferhub.dev/api/catalog` 200 at 2026-09-24T06:46Z (02:46 ET) |
| Live probe | 2026-09-24 about 17:38–17:41 ET, from Teresa-Pujan. Key loaded in-process from the approved `.env` and never printed. |

## 3. Candidates

| Top-20 rank | Model | Eligible | Tier | Family effective $/1M | Route tested | Route floor in/out $/1M |
|---:|---|:-:|---|---:|---|---|
| 1 | DeepSeek V4.1 Flash | yes | upper_mid | 0.0221 (effectively free) | `cb/deepseek-v4.1-flash` | 0.0001 / 0.0006 |
| 2 | GLM 5.3 Flash | yes | top | 0.0329 (effectively free) | `cbcn/glm-5.3-flash` | 0.0029 / 0.0095 |
| 18 | Qwen 3.8 Max | yes | top | 0.1696 (priced) | `ali/qwen3.8-max` | 0.012 / 0.036 |
| 19 | GLM 5.3 | yes | top | 0.2671 (priced) | `cb/glm-5.3`, `cbcn/glm-5.3` | 0.0378 / 0.1188 (cb); 0.021 / 0.066 (cbcn) |

GPT/OpenAI routes (Luna/Astra) are `not_routing_eligible` / research-only in the snapshot and were not considered.

## 4. Live probe design and results

Script: two cases per route. Both use `stream: true` with `stream_options.include_usage`, a **forced tool call** `emit_turn{operation, markdown, question, new_relations}`, temperature 0.2, and max_tokens 600.

- `dsa_hint`: authorize `give_hint` at A2 for `sum[1]` of `a=[2,1,5,1,3,2]`, `k=3`, after a wrong answer of 8. The hidden answer 7 must not appear, and the box chart must be kept.
- `hesi_retry`: authorize `retry_different_example` for ABC prioritization. Give a *different* 3-option scenario and do not say which option is correct.

Checks: streamed chunks > 0, tool called, args are valid JSON with all fields, `new_relations == 1`, exactly one `?`, no forbidden token (answer / "master"), word count.

| Route | Calls | Success | Tool + schema + 1 question + 1 relation | Answer leak | TTFT (s) | Total (s) | Cost / call (US$) |
|---|---:|---:|:-:|:-:|---|---|---|
| `cb/glm-5.3` | 6 | 6 | 6/6 | 0 | 3.4–5.1 | 4.3–6.1 | 0.0000100–0.0000185 |
| `cb/deepseek-v4.1-flash` | 4 | 4 | 4/4 | 0 | 2.1–3.6 (tool args arrive in a burst) | 2.4–3.8 | ≈0.00001 |
| `ali/qwen3.8-max` | 2 | 2 | 2/2 (finish_reason `stop`, not `tool_calls`) | 0 by the strict check | 1.6–1.8 | 3.3–3.8 | ≈0.000014 |
| `cbcn/glm-5.3-flash` | 2 | 0 | — | — | — | — | HTTP 503 `no_capacity` |
| `cbcn/glm-5.3` | 2 | 0 | — | — | — | — | HTTP 503 `no_capacity` |

Qualitative review of the outputs (by the spec author; small sample, not a benchmark):
- **GLM 5.3** had the best pedagogy. It kept the box chart, pointed at the window span without stating the sum, and gave a clean different HESI scenario with no rule that gave away the answer.
- **DeepSeek V4.1 Flash** was correct and fast. In the HESI retry it prefixed "scan for anything threatening breathing". That is a strong cue, arguably above the A2 ceiling.
- **Qwen 3.8 Max** listed all three window values ("add only these") and, in HESI, appended "airway patency always precedes pain", which **effectively reveals the answer**. It also ended tool calls with `finish_reason: stop`.

This is why the validator (P-LLM-2) must include a cue-strength check at T1/T2, not only exact-answer matching (#92).

## 5. Decision

| Use | Route | Price class | Why |
|---|---|---|---|
| **Tutor interpreter (primary)** | `cb/glm-5.3` | Priced: family effective ≈ $0.267/1M, above the $0.10 threshold (**recorded, owner-approved: quality over cost**) | Top tier, eligible, 6/6 clean streamed tool calls, best adherence to the teaching pattern in the probe |
| Tutor interpreter (fallback) | `cb/deepseek-v4.1-flash` | Effectively free (≈ $0.022/1M; rank 1) | Most runtime evidence in the snapshot (233/233 successes), fast, 4/4 clean |
| Simulated learners (agent evals T1) | `cb/deepseek-v4.1-flash` | Effectively free | Cheap, and diversity of learner behavior matters more than pedagogy |
| Eval judge (T2 rubric, optional) | `cb/glm-5.3` | Priced | Same family as the tutor. Consider a different family for judge independence once more routes are verified |
| Avoid for now | `cbcn/*` GLM routes; `ali/qwen3.8-max` for the tutor | — | 503 no-capacity at probe time; hint leakage and tool finish quirk |

Cost expectation: about $0.00001–0.00002 per interpretation. Even 2,000 interpretations/day is under $0.05/day. Spend cap: **US$5/month** (P-LLM-5 degrades to deterministic content; it never blocks learning). Raise it freely if quality needs it.

## 6. Operating rules

- `INFERHUB_API_KEY` lives only in `/srv/study-os/.env` on gravebuster (mode 600), loaded by the API process. It never goes in the repo, the logs, the prompts, or CI for PR code.
- Before each route change, re-read the latest IRE snapshot, re-run the probe (the T1 harness includes it), and record a new `interpreter_route` module version with snapshot sha256.
- Emit prompt-free telemetry per call (route, tokens, cost, latency, validation result) in the IRE `AGENT-TELEMETRY.md` style, so IRE can learn route reliability from Study OS traffic.
- If the primary returns 503/timeout, fail over to the fallback within the same request and record both attempts. If both fail, serve deterministic content.
