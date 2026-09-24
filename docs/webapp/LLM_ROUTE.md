# LLM route choice (IRE / InferHub)

## 1. Policy inputs

- The IRE runbook (`docs/INFERHUB-API-SETUP.md` in Pukujan/inference-recommendation-engine, local checkout on Teresa-Pujan at `641a7f9`) says: routes under **0.10 USDC per 1M tokens** count as effectively free; prefer recommendation-eligible Top 20/Top 20+ entries; verify live route, price, and tool/stream support; record snapshot and route.
- Owner direction on 2026-09-24: cheap calls through IRE routes are pre-approved. **Tutoring quality and reliability matter more than cost.** Cost must never block progress, but route and price must be recorded, and a pricier route is never picked silently.
- Architecture: the IRE route is **tier 3** of the interpretation cascade (ARCHITECTURE §4). Tier 1 is rules. Tier 2 is hosted Jev for grading and misconception choice, and Laya on gravebuster for low-stakes affect signals. The frontier LLM is called only when tier 2 is below its confidence threshold, for audit samples, and to rewrite failed steps. Volume is therefore low.

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

## 5a. Tier 2: hosted Jev via OpenRouter (owner decision 2026-09-24)

Jev is not an IRE/InferHub route. Alex chose to reach it through **his OpenRouter key**, following eval-lab `docs/TASK-0010-OPENROUTER-JEV.md` (public `Pukujan/eval-lab` @ `51256cb`):

| Field | Value |
|---|---|
| Endpoint | OpenRouter Decisions API `POST https://openrouter.ai/api/alpha/decisions` |
| Model | **`typesafe/jev-1.13`** (pinned; resolved to `typesafe/jev-1.13-20260917` in the probe). **Never** the rolling alias `~typesafe/jev-latest` in production; that alias is a canary arm only |
| Price | $0.042 per 1M input tokens, output free (eval-lab planning observation 2026-09-20; confirmed by the probe's usage `cost`: 432 input tokens → $0.0000181) |
| Context | 32K |
| Credential | env var **`OPENROUTER_API_KEY`**. On gravebuster it lives in `/srv/study-os/.env` (mode 600). It is never committed, printed, or sent to the browser |
| Request shape | `{model, state, questions: {<key>: {type: choice\|noul\|score, instructions, criteria}}}`. For `choice`, `criteria` is an object `{label: description}`. For `score`, `criteria` must be an **ordered array** of level descriptions (an object returns HTTP 400) |
| Response shape | `answers.<key>` → `{choice \| score, probabilities, confidence}` (plus `legend` for score), and `usage {input_tokens, output_tokens, cost}` |
| Reference adapter | `typesafe-ai/system-one-adapter-python` (differential reference only; the Study OS question spec stays repository-owned, as in eval-lab) |
| Benchmark evidence | eval-lab blind rubric judging: 89.87% (EXP-022; 760 records, 50.26% majority baseline) — see [DEEP_RESEARCH.md §6.2](DEEP_RESEARCH.md#62-measured-results-from-eval-lab-primary-evidence) |

**Live probe (2026-09-24 about 17:50 ET, from the agent box, 4 calls, total ≈ $0.00006):**

| Case | Questions | Result | Latency |
|---|---|---|---|
| DSA `sum[1]`, correct free-text answer ("its 1+5+1 so 7") | grade `choice` pass/partial/fail | `pass`, p=1.00, conf 1.00 | 0.26 s |
| DSA `sum[1]`, off-by-one answer ("1+5+1+3 = 10") | grade + misconception `choice` (4 labels incl. `none_of_these`) | grade `fail` p=0.93 (conf 0.89); misconception `window_too_long` p=0.93 (conf 0.91) | 0.25 s |
| HESI free text "ugh just tell me which one is right" | wants_answer `choice` + frustration `score` 0–3 | first attempt HTTP 400 (score criteria given as an object); retry: wants_answer `yes` p=1.00; frustration 2.37 (p: 2→0.55, 3→0.41), conf 0.55 | 0.24 s |

Reading: the shape fits Study OS grading and misconception choice well, with sub-300 ms latency. Frustration came back at confidence 0.55, which is below any sensible τ, so it would not be acted on. That matches the plan to keep affect low-stakes, with Laya after calibration. Four calls are **not** an accuracy estimate. τ must be fitted on a Study OS labelled split (#97).

**Mini grading set (same day, 12 hand-labelled items, 6 DSA sliding-window + 3 index + 3 HESI rationale, `choice` pass/partial/fail):** 11/12 correct. The miss: an unsummed expression "4+7+2" (gold `pass`) was graded `partial` at confidence 0.67. All 6 predictions with confidence ≥ 0.9 were correct. Every `partial` prediction had confidence ≤ 0.5. Latency was 0.16–0.25 s per call. This supports the cascade design: act at high confidence, and escalate partial or low-confidence grades to tier 3 or treat them as `unresolved`. At 12 items it is an illustration, not an accuracy estimate.

**Budget note:** the key's OpenRouter spending limit was low at the first probe (about $0.08 of $2.40). Alex raised it on 2026-09-24 and cleared Jev for free use. At ≈ $0.00002 per decision, cost is negligible. The spend guard (P-LLM-5) still treats a tier-2 402/limit error as "tier 2 unavailable" and escalates to tier 3 or `unresolved`. It never blocks learning.

Tier 3 grading alternative: eval-lab also measured `Qwen3.8 Flash` via InferHub at 99.21% on the same blind pool. It is a candidate for tier-3 **grading** specifically (not rewriting), to be confirmed on a Study OS grading set (#97).

## 6. Operating rules

- `INFERHUB_API_KEY` and `OPENROUTER_API_KEY` live only in `/srv/study-os/.env` on gravebuster (mode 600), loaded by the API process. They never go in the repo, the logs, the prompts, or CI for PR code.
- Before each route change, re-read the latest IRE snapshot, re-run the probe (the T1 harness includes it), and record a new `interpreter_route` module version with snapshot sha256.
- Emit prompt-free telemetry per call (route, tokens, cost, latency, validation result) in the IRE `AGENT-TELEMETRY.md` style, so IRE can learn route reliability from Study OS traffic.
- If the primary returns 503/timeout, fail over to the fallback within the same request and record both attempts. If both fail, serve deterministic content.
