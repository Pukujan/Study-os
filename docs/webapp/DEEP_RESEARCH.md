> Imported into Study OS on 2026-09-24 for SOS-0003 (#83). The companion deep-research report was prepared by a separate research task. Edits: two learner-identifying phrases and local machine paths were removed; everything else is verbatim. The adopted decisions and how they map onto the web-app spec are in [RESEARCH.md §0](RESEARCH.md#0-adopted-decisions-from-the-deep-research-report).

# Study-os: Deep Research Report

**Prepared for:** Alex (GitHub `Pukujan`), project `Pukujan/Study-os`
**Date:** 2026-09-24 (America/New_York)
**Scope:** learner analytics and UX, learning science, production and open-source edtech architectures, curriculum-to-graph compilation, cost at scale, a cheap self-hosted **decision layer** (Jev and Jev-compatible models, measured in `Pukujan/eval-lab`), and concrete recommendations.
**Read-only inputs:** public web sources; `Pukujan/Study-os` (README, `docs/MEASUREMENT_MODEL.md`); `Pukujan/eval-lab` (GitHub `main` @ `51256cb`). `Pukujan/private-study-log` was **not** used.

> Prices and model names below come from vendor pages fetched on 2026-09-24. They change often, so re-check them before budgeting.

---

## 0. Executive summary

**The framing question: is this a UX problem, a model-behavior problem, or a coding problem?**
It is **mainly a measurement-and-control problem, which makes it a coding problem first.** UX comes second, and model behavior comes last.

1. **Coding (the controller, the graph and the evidence log) sets the ceiling.** The best results in the literature come from systems where deterministic code owns progression and evidence:
   - Step-based intelligent tutoring systems (ITS) reach an effect size of about d≈0.76, close to human tutoring (VanLehn 2011).
   - Math Academy's knowledge graph and FIRe scheduler.
   - Duolingo's Session Generator, which serves precompiled course data in 14 ms.
   - Bastani et al. (PNAS 2025) show the reverse case: an unguarded GPT tutor *raised* practice scores but *lowered* unassisted exam scores by 17%. A guarded tutor that used teacher-written hints avoided the harm. "Help removed" verification lives in code, not in the model.
2. **UX decides whether distracted learners stay long enough to learn.** Two examples:
   - Duolingo's streak work: making the streak visible raised DAU by 3% and D14 retention by 1%.
   - Boredom is the most persistent and most harmful affective state, and it predicts gaming the system (Baker, D'Mello et al. 2010).
   Tiny steps, fast feedback and low friction matter as much as correct pedagogy.
3. **Model behavior is a bounded, swappable component**, as long as the LLM is confined to interpreter duties (grading, diagnosing, rewriting) and every call is gated by confidence and logged. Harvard's RCT (Kestin et al. 2025) and Stanford's Tutor CoPilot RCT both worked because the pedagogy was engineered around the model, not left to it.

**Architecture verdict.** A precompiled PIR lesson graph, a deterministic controller and an interpreter cascade (rules → cheap decision model → frontier LLM on low confidence) is the right design. It matches what Duolingo (precompiled course data plus a learned difficulty model), Khan Academy (grounding in vetted content plus a calculator tool) and OATutor (JSON lesson graph plus BKT) actually do.

**Cost verdict (rough).**
- An LLM that writes every message costs about **$0.13–$0.66 per learner-hour** on mid-tier models (Gemini 3.8 Flash to Sonnet 5 or GPT-6 Sol). That is about **$3.3 per learner-hour** on a top frontier model.
- A precompiled graph with interpreter escalation costs about **$0.01–$0.04 per learner-hour**, and it falls as good generations are promoted into the graph.
- Hosted Jev at $0.042 per million input tokens (output free) makes the decision tier effectively free (~$0.002 per learner-hour). A self-hosted encoder is cheaper still at the margin.

**Decision-layer verdict (based on eval-lab measurements first).** eval-lab's frozen benchmark asks a model to judge a candidate answer against a rubric: single pass/fail and pairwise A/B/TIE, 760 blind records. That is almost exactly Study-os's answer-grading job. On it:
- **Hosted Jev: 89.87%** (EXP-022; 90.0% pinned in EXP-014).
- **Qwen Flash: 97.36%.**
- The best local Jev-style model, **Kev-4B, scored 64.34%**. It scored 93.5% on pairwise records but only 59.5% on pass/fail.
- **Laya-421M, Kev-0.8B and Verdict were at or near the 50.26% majority baseline.**

So the cheap pretrained models (Laya above all) are **cheap and easy to host**, but zero-shot they are **not yet good enough for answer grading**. Laya's own model card says the same: the base checkpoints are "near chance on typed-decisions zero-shot" and it is "a fast base to specialise". The data supports Alex's upgrade path, but in this order:
- **Day 1:** hosted Jev, or a cheap LLM route, handles grading and misconception decisions.
- **Laya or Verdict** handles only easy, low-stakes routing and affect signals, after per-question temperature calibration.
- Log everything.
- Fine-tune Laya/ModernBERT on Study-os's own labels once they exist. Laya's own fine-tune went from 0.362 to 0.766.
- Convert well-understood decisions into state-machine rules.

---

## 1. Learner behavior and UX analytics in production edtech

### 1.1 What the big platforms measure

| Platform | What they measure / optimize | Mechanism worth copying | Source |
|---|---|---|---|
| **Duolingo** | DAU, D1/D7/D14 retention, CURR (Current User Retention Rate), streak length, session completion; per-exercise P(correct) | Streak experiments: visible streak gave +3% DAU and +1% D14; post-lesson streak emphasis gave +1% DAU and +3% D14; two streak freezes beat one, and three did no better than two. Focus on getting users from 0 to a 7-day streak | Duolingo streak blog; Econsultancy summary; Lenny's podcast transcript (Jackson Shuttleworth) |
| **Duolingo Birdbrain** | P(learner answers exercise correctly), learner ability, exercise difficulty | V1 was Elo/IRT-style logistic regression. V2 is an LSTM that compresses history into a 40-dimensional knowledge vector. Feeds the Session Generator to hit the "right difficulty" | Duolingo blog; IEEE Spectrum |
| **Duolingo HLR** | Recall probability over time (half-life) | Half-life regression: MAE 0.128 vs 0.235 for Leitner; +12% daily engagement in an operational A/B test | Settles & Meeder, ACL 2016 |
| **Khan Academy** | Skill mastery levels (Attempted / Familiar / Proficient / Mastered), mastery points, course mastery %; Khanmigo conversation quality and error rates | Mastery moves up *and down*. Assessments propagate to prerequisite skills ("mastery movement") | Khan help center; Khan blog (Khanmigo math updates) |
| **Coursera** | Long-horizon completion (e.g., 8-week course completion), progression, grades, persistence | In-house experimentation platform (400+ A/B tests in year 1); instructor-run A/B tests. Adding formative practice raised completion of the first graded assessment by over 50% in some courses | Coursera Engineering (Medium); Coursera blog |
| **Quizlet** | Predicted recall per term | Logistic regression on correctness, elapsed time and spacing, later a recurrent power-law memory model; "Memory Score" scheduling | Quizlet blog; Tech @ Quizlet (Medium); arXiv 1803.00111 |
| **ASSISTments** | Per-problem correctness, hint requests, bottom-out hints, attempts, time | E-TRIALS lets researchers run RCTs inside the product. Maine RCT: g=0.18 overall and g=0.29 for lower-prior students (Roschelle et al. 2016) | etrialstestbed.org; AERA Open |
| **Math Academy** | Per-topic spaced-repetition count, learning efficiency, XP | Knowledge graph of ~2,800 topics and ~10k prerequisite edges; FIRe implicit-repetition credit | mathacademy.com/how-our-ai-works; justinmath.com |

### 1.2 Behavioral constructs Study-os should detect

- **Wheel-spinning.** At least 10 practice opportunities on a skill without reaching mastery (often defined as 3 correct in a row). This happened in about 31% of Cognitive Tutor and 38% of ASSISTments student-skill pairs (Beck & Gong 2013). Early detection uses response time, rapid guessing, prior correctness and bottom-out hints. Missing prerequisites drive both wheel-spinning and gaming. *Study-os action:* after N failed attempts, stop drilling and route to a prerequisite probe. Do not drill harder.
- **Gaming the system.** Rapid hint-abuse to reach the bottom-out answer, or systematic guessing. Baker's detectors use timing and hint-sequence features. Boredom predicts gaming.
- **Affect.** Across AutoTutor, The Incredible Machine and Aplusix, **boredom** was the most persistent state and the one most linked to poor learning. **Confusion** helps when it resolves back into engaged concentration and hurts when it persists. **Frustration** was less persistent and less harmful ("better frustrated than bored"). *Action:* detect persistent confusion (repeated wrong answers plus slowing) and boredom (fast, disengaged answers, idle gaps, tab-away). These are separate interventions.
- **Hint dependence.** Record correctness *and* the help level used. Study-os already has A0–A6 help levels. ASSISTments and Cognitive Tutor treat a bottom-out hint as incorrect for mastery purposes. Study-os should too: a pass at A5/A6 is not `pass_unaided`.
- **Time-on-step.** Use a distribution, not a mean. Very short times mean guessing or gaming. Very long times mean confusion or distraction. The HESI score-setting study itself excluded test-takers with any item under 5 seconds or over 20 minutes, which is a useful sanity band.

### 1.3 Experimentation practice

- Duolingo "tests everything". Birdbrain models are compared by A/B test on learning metrics, and they reworked their infrastructure so running two model arms at once cost 50% less than one used to (Duolingo engineering blog).
- Coursera pairs short-term proxies with **long-horizon outcomes** (8-week completion) so it does not overfit to clicks.
- ASSISTments E-TRIALS supports randomization at the student, class and school level with preregistered analyses.
- **Lesson for Study-os:** each experiment needs one primary *learning* metric (for example `pass_delayed` rate on the target capability), a UX guardrail (7-day return rate, session abandonment) and a cost guardrail ($ per learner-hour). For a small N (two learners), use **within-learner crossover designs and matched problems**, as Study-os's N1_METHOD already implies. Save between-user A/B tests for later.

### 1.4 Tooling

| Need | Recommended | Why / caveat |
|---|---|---|
| Product analytics, funnels, retention, flags, experiments | **PostHog** (cloud free tier: 1M events/month and 1M flag requests/month; anonymous events from $0.00005 each) | All-in-one with feature flags plus experiments. Self-hosting via Docker exists but PostHog says it is unsupported and heavy. Amplitude and Mixpanel are equivalent SaaS options; pricing was not re-verified in this pass |
| Learning-record standard | **xAPI** statements (actor-verb-object-result-context) with an LRS; **1EdTech Caliper** if you need LMS interop | xAPI is flexible, and Caliper uses fixed metric profiles; they complement each other. **Learning Locker** (GPL-3.0) is still available, but the main repo's last update was May 2024 (maintenance mode) |
| Warehouse and BI | Your own SQLite → DuckDB/Postgres, then **Metabase** or **Apache Superset** | Both are open source and SQL-first, and fine for cohort and retention dashboards |
| Power BI + DAX | Fine for **aggregate** reporting (retention tables, mastery by topic) | Weak for event-sequence analysis (wheel-spinning runs, time between attempts, help-level trajectories); do those in SQL or Python first and feed Power BI the aggregates. Windows/Microsoft licensing is a plus only if Alex already lives in that ecosystem |

**Recommendation:** keep Study-os's own event log (SQLite plus the private evidence store) as the source of truth, with xAPI-shaped events (schema in §7.3). Mirror non-PII UX events to PostHog for funnels, flags and experiments. Push learning metrics to Metabase.

---

## 2. Learning science: concrete mechanisms

| Mechanism | Evidence | Concrete implementation in Study-os |
|---|---|---|
| **Step-based tutoring** | VanLehn 2011: step-based ITS d≈0.76, human tutors d≈0.79, answer-only systems d≈0.31 | PIR steps are the unit of feedback. Grade each step, not only final answers |
| **Cognitive Tutor / CTAT** | Cognitive Tutor Algebra RCT (Pane et al. 2014, RAND): no effect in year 1, +0.20 SD in high school in year 2. CTAT example-tracing tutors are built from behavior graphs without programming (Aleven et al. 2009) | A PIR step graph *is* an example-tracing behavior graph: expected correct paths plus anticipated buggy paths, each with feedback. Expect that deployments need time to pay off |
| **Knowledge tracing** | BKT (4 parameters per skill: prior, learn, guess, slip); PFA (logistic on prior successes and failures); DKT (LSTM). Khajah et al. 2016 ("How deep is knowledge tracing?"): BKT with forgetting and ability terms matches DKT. Later JEDM studies say results depend on the dataset | Start with **pyBKT** per capability dimension (recognition, state_prediction, implementation…). It is interpretable and fits in milliseconds. Consider DKT-style models only with thousands of learners |
| **Spaced repetition** | FSRS (difficulty, stability, retrievability model) beats SM-2 on 99.6% of 10k Anki collections by log loss (with caveats). HLR (Duolingo). Math Academy FIRe: implicit repetitions trickle down *encompassing* edges with fractional weights | Use FSRS (open source, `open-spaced-repetition`) for delayed probes (`pass_delayed`). Add FIRe-style fractional credit: passing "implement BFS on a grid" gives partial review credit to "queue operations" |
| **Mastery learning** | Khan: mastery moves up and down, and assessments propagate to prerequisites. Math Academy: mastery gates on the knowledge graph | Advancement only from `pass_unaided` (A0–A1) plus `pass_transfer`. Allow demotion |
| **Worked-example fading** | Renkl & Atkinson backward fading (remove the last steps first) improves near transfer; self-explanation prompts add far transfer. Expertise reversal (Kalyuga): full worked examples hurt experts | Map fading directly onto A6→A0: complete solution → worked example → partial scaffold → structural hint → cue → none. The controller fades per learner per capability |
| **Retrieval practice** | Adesope et al. 2017 meta-analysis: g≈0.61 overall and +0.51 vs restudy | Every lesson ends with retrieval, and delayed probes open with retrieval *before* re-showing the lesson (Study-os "Delayed" window) |
| **Interleaving** | Rohrer et al. 2020 cluster RCT (787 students): 61% vs 38% on a delayed test, d=0.83 | In DSA, interleave problem *types* (two-pointer vs sliding window vs BFS) after initial blocked practice. Choosing the strategy is the skill |
| **Affect-aware tutoring** | AutoTutor: ~0.8 SD vs textbook. Affect-sensitive AutoTutor helped low-knowledge learners (~0.71 SD in later sessions) | Detect confusion, frustration and boredom (§6). Respond with supportive messages or a shorter step for low-knowledge learners, and a challenge for bored high-knowledge learners |
| **Gamification** | Sailer & Homner 2020 meta-analysis: cognitive g=0.49, motivational g=0.36, behavioral g=0.25. Heterogeneous; only the cognitive effect was robust in rigorous studies | Use streaks, progress, and "mastered" badges tied to *verified* capability. Avoid points for activity alone, which invite gaming. Avoid loss-aversion mechanics that push cramming |
| **LLM tutoring evidence** | Harvard PS2 Pal RCT (N=194): more learning in less time vs active learning, with a heavily engineered pedagogical prompt. Tutor CoPilot RCT (900 tutors, 1,800 students): +4 pp mastery (+9 pp for weaker tutors) at ~$20 per tutor per year. Bastani et al. PNAS 2025: GPT Base −17% on unassisted exams; a guarded GPT Tutor removed the harm. Pardos & Bhandari 2023: human-written hints beat ChatGPT hints, and 30% of ChatGPT hints were rejected as incorrect | The LLM must never be the unverified source of truth for correctness or progression. Verify with the help removed |

---

## 3. Production and open-source architectures

- **Duolingo.**
  - The Session Generator was rewritten in Scala. Latency dropped from 750 ms to 14 ms by processing course data offline, serializing it to S3 and caching it in memory, then injecting per-user personalization at request time. *This is Study-os's precompiled PIR pattern.*
  - Birdbrain streams responses to estimate ability and difficulty.
  - Content generation: learning designers write "Mad Lib" prompts with fixed and variable rules. The LLM produces about 10 candidates; the human picks about 3 and edits them. "Teaching experts always have the final say."
  - DuoRadio uses LLM evaluators to filter scripts.
  - Duolingo Max (Roleplay, Video Call) uses GPT-4 for the open-ended surface only.
- **Khan Academy / Khanmigo.**
  - Socratic prompting with a 7-step prompt-engineering process.
  - Moderation guardrails that notify parents and teachers.
  - Grounding in vetted Khan content (standards, prerequisites, transcripts, expert-written hints).
  - Prompt chaining per lesson-plan section.
  - A **calculator tool** for arithmetic instead of relying on token prediction, plus benchmark conversations and manual review for math errors.
  - Cost: estimated operating cost fell from about $70 to $25–35 per user per year. The district price for computation was about $15 per student per year by late 2024.
- **ASSISTments.** Teacher-authored problems with hints and scaffolds, correctness logging, E-TRIALS for embedded RCTs.
- **OATutor (Berkeley, CHI 2023, MIT license).** React app. Content is JSON (course → lesson → problem → step → hints/scaffolds), and knowledge components (KCs) map in `skillModel.json`. BKT parameters are defined per skill (`bktParams.js`). Adaptive selection picks the lowest-mastery problem. It supports A/B testing of content variants, and was used for the ChatGPT-vs-human hints study. **The most copyable reference implementation** for a PIR step graph.
- **Oppia (Apache-2.0).** An exploration is a state graph. Each state has an interaction, answer groups (rules → feedback → destination) and a default outcome; misconceptions are linked to skills. *This is the closest open design to a PIR node with misconception branches.*
- **Open edX.** XBlocks plus an event-tracking log that feeds analytics. Useful as a precedent for an event schema, less so for adaptivity.
- **Anki.** Deck/note/card model with FSRS built in since 23.10. Its review log is the model for Study-os's delayed-probe log.
- **Math Academy.** An expert system over a hand-built knowledge graph (~2,800 topics), FIRe spaced repetition, diagnostic placement, and "spaced repetition compression" that picks tasks which knock out several due reviews at once. No LLM in the core loop.
- **Brilliant and Synthesis.** Interactive, problem-first lessons built from small steps. Their architectures are not publicly documented in primary sources; they are relevant here as UX precedents only.
- **LLM tutor research.**
  - **LearnLM** (Google, arXiv 2412.16429): "pedagogical instruction following". System instructions specify behaviors such as withholding answers, and experts preferred it to GPT-4o and Claude 3.5.
  - **Harvard PS2 Pal:** engineered prompts plus step-by-step structure.
  - **Tutor CoPilot:** LLM suggestions for *human* tutors.
  - Together these support "LLM as constrained interpreter inside a designed loop" over "LLM as the tutor".

---

## 4. Compiling a subject into a dependency graph of buildable steps

### 4.1 How the exemplars do it

- **rasbt/LLMs-from-scratch.** A strictly linear build path where each chapter produces a runnable artifact used by the next: Ch2 text data and dataloader → Ch3 attention → Ch4 GPT model (`gpt.py`) → Ch5 pretraining (`gpt_train.py`) → Ch6 classification fine-tune → Ch7 instruction fine-tune. Each chapter has a main notebook, a summary `.py` and exercise solutions. Principle: **every node produces a working artifact that later nodes import.**
- **Khan Academy.** Course → unit → lesson → skill (exercise). Prerequisite links let assessments propagate mastery.
- **Math Academy.** A topic knowledge graph with two edge types, *prerequisite* and *encompassing*, the latter with fractional weights. An example from Frank Hecker's summary: integration by parts encompasses polynomial integration at 1.0, exponential at 0.5 and trig at 0.2.
- **roadmap.sh (`developer-roadmap`).** A JSON graph (`nodes` with id/type/label, `edges` with source and target) plus a Markdown content file per node (`content/{slug}@{nodeId}.md`). Good for *coverage maps*, too coarse for steps.

### 4.2 Proposed PIR compilation pipeline for Study-os

1. **Concept graph (coarse, like roadmap.sh or Math Academy).** Nodes are concepts. Edges are `prerequisite` or `encompasses(weight)`.
2. **Capability matrix per concept.** Use Study-os's existing dimensions (recognition, mental_model, state_prediction, invariant_reasoning, procedure, pseudocode, implementation, debugging, transfer, retention, ai_oversight). Each (concept, capability) cell is a knowledge component (KC) with its own BKT or FSRS state.
3. **Step graph per KC (like CTAT, OATutor or Oppia).** Ordered micro-steps, each with:
   - a prompt at every help level A0…A6, precompiled;
   - expected answers: exact, pattern-based, or a rubric for free text;
   - anticipated misconceptions, each with a detector (rule or decision-model question) and remediation steps;
   - a transfer variant (changed surface) and a delayed probe item.
4. **Build artifacts, LLMs-from-scratch style (DSA).** Each concept ends with a runnable artifact the learner reuses. For example: `Stack` class → balanced-parentheses checker → iterative DFS with an explicit stack → topological sort.
5. **Offline LLM authoring with human review (the Duolingo pattern).** An LLM drafts steps, distractors, misconceptions and variants from a template. Deterministic validators check them (code tests pass, answer keys consistent, reading level). A human approves. Every node records provenance and version (Study-os already has `VERSIONING.md` and a PIR mutation gate).

**DSA example slice.**
`array indexing → two pointers (encompasses indexing 1.0) → sliding window (encompasses two pointers 0.7) → hash map counting → "longest substring without repeats" (encompasses sliding window 1.0, hash map 0.8)`.
- Capability steps for sliding window: recognition ("which of these problems is a window problem?") → state_prediction (trace l, r and the map on an input) → invariant ("what stays true about s[l..r]?") → pseudocode → implementation (unit-tested) → debugging (a planted off-by-one error) → transfer (min window over a *stream*) → delayed probe after 3 and 10 days via FSRS.

**HESI example slice.**
- HESI Exit (RN): ~150 NCLEX-style items across Nursing Process, Client Needs and Specialty areas. HESI A2 sections: reading, vocabulary, grammar, math, biology, anatomy and physiology, chemistry, physics.
- Graph example: `fluid & electrolytes → potassium physiology → hyperkalemia signs (ECG peaked T) → prioritization: which client first?` (encompasses assessment and physiology).
- Capability mapping for nursing: recognition (cue identification), mental_model (pathophysiology explanation), state_prediction ("what happens next if untreated?"), procedure (intervention order), transfer (a novel client scenario), retention (FSRS on high-yield facts such as lab ranges and drug classes).
- Item types: multiple choice, select-all-that-apply and ordered response. These are **deterministically gradable**, so HESI needs the LLM interpreter even less than DSA does. Use it mainly for "explain your rationale" free text and for misconception diagnosis.
- **Risk:** clinical content accuracy. Require a source citation and human (nurse) review for every promoted node.

---

## 5. Cost model at scale

### 5.1 Model prices used (per 1M tokens, standard tier, fetched 2026-09-24)

| Model | Input | Cached input | Output | Source |
|---|---:|---:|---:|---|
| OpenAI gpt-6-astra (top frontier) | $10.00 | $1.00 | $50.00 | platform.openai.com/docs/pricing |
| OpenAI gpt-6-sol | $2.00 | $0.20 | $10.00 | same |
| OpenAI gpt-6-luna (small) | $0.10 | $0.01 | $0.50 | same |
| Anthropic Sonnet 5 | $2.00 | $0.20 (read) | $10.00 | anthropic.com/pricing |
| Anthropic Haiku 4.5 | $1.00 | $0.10 | $5.00 | same |
| Google Gemini 3.8 Flash (promo to 2026-12-31) | $0.75 | $0.075 | $3.75 | ai.google.dev/gemini-api/docs/pricing |
| Google Gemini 2.5 Flash-Lite | $0.10 | $0.01 | $0.40 | same |
| **TypeSafe Jev** (decision model, no text) | **$0.042** | – | **free** | typesafe.ai launch blog |

Batch or flex tiers are about 50% cheaper and suit offline authoring and graph compilation.

### 5.2 Per-learner-hour estimate (assumptions stated)

Assume a distracted learner does about 60 micro-steps per hour (one per minute), of which about 40% (24) need free-text interpretation.

**A. LLM writes every message:** 60 turns × (4,000 input tokens of system prompt, lesson context and history + 300 output tokens) = 240k input + 18k output per hour.

| Model | No caching | ~75% of input cached |
|---|---:|---:|
| gpt-6-astra | $3.30 | ~$1.50 |
| Sonnet 5 / gpt-6-sol | $0.66 | ~$0.34 |
| Gemini 3.8 Flash | $0.25 | ~$0.13 |
| gpt-6-luna | $0.033 | ~$0.02 (quality risk for tutoring) |

**B. Precompiled graph plus interpreter cascade:**
- 60 steps served from the graph cost $0.
- 24 interpretations: about half resolved by rules or deterministic checkers (exact match, unit tests, MCQ keys) at $0. The rest go to the decision tier.
- Decision tier via hosted Jev: 24 × ~1.5k tokens = 36k tokens → **$0.0015/hour**. Self-hosted: effectively $0 marginal (hardware in §6.6).
- Frontier escalation on low confidence: about 20% of interpretations, so ~5 calls/hour × (2k input + 200 output) on Sonnet 5 or GPT-6 Sol → **~$0.03**.
- Step rewrites when a precompiled step failed: ~1/hour × (3k input + 500 output) → **~$0.011**.
- **Total ≈ $0.04 per learner-hour**, falling toward **~$0.01** as rewrites are promoted into the graph and escalations drop to about 5%.

**At scale (1M learners × 1 hour/day × 30 days = 30M learner-hours/month):**

| Design | Monthly cost |
|---|---:|
| A on Sonnet 5 with caching | ≈ $10M |
| A on Gemini Flash with caching | ≈ $3.8M |
| B | ≈ $1.2M → $0.3M |

For comparison, Khanmigo's computation cost is about $15 per student per year, and Tutor CoPilot's is about $20 per tutor per year.

### 5.3 Cost controls

- **Prompt caching.** Put the stable PIR node, rubric and misconception list first so they are cached.
- **Structured, short outputs.** Interpreter calls return JSON or labels, not prose.
- **Batch APIs** for offline graph compilation.
- **Promotion loop.** A good rewrite becomes a new precompiled variant, so the next learner costs $0.
- **Semantic cache of free-text answers.** Embed each answer with a small sentence-transformer. When a new answer is near-duplicate of an already-graded one for the same step, reuse the label. Mark such labels as `cached`.
- **Escalation policy.** Escalate only when:
  - the decision confidence is below the per-question threshold;
  - the question is novel (no rubric match); or
  - the stakes are high (a mastery gate).

---

## 6. The decision layer: Jev, Jev-compatible models, and alternatives

### 6.1 What Jev is

- **Jev** (TypeSafe AI, announced 2026-09-15) is a "System One" **typed decision model**.
- Endpoint: `POST https://api.typesafe.ai/v1/systemone` with `{model, state, questions}`.
- Question types:
  - **`choice`**: up to 255 labelled options;
  - **`noul`**: probability of true/yes;
  - **`score`**: ordered 2–10 levels.
- It returns calibrated probabilities in one parallel pass. It generates no text, and TypeSafe says it cannot make type errors.
- Claimed latency is 70–500 ms. Price is $0.042 per million input tokens with output free. The current version is `jev-1.13.0` (pin it when tuning thresholds).
- Access is a closed API from a waitlist, also offered through Vercel AI Gateway (`typesafe-ai/jev`). **No self-hosted weights.**
- This shape fits Study-os's interpreter duties well: "is this answer correct under rubric R?", "which misconception fits?", "how frustrated is the learner (0–3)?", "should we escalate?".

### 6.2 Measured results from eval-lab (primary evidence)

**Benchmark.** Frozen EXP-015 typed-judgment pool (fingerprint `b7edd612…`). Each record is a question, a candidate answer, a rubric and a closed label set. Single records are `pass`/`fail`; pairwise records are `A`/`B`/`TIE`. Gold labels come from answer keys or deterministic verifiers. There are 648 public-selection records and **760 blind records (primary)**. The majority baseline on blind is **50.26%**.

**Why this matters for Study-os.** This is essentially **free-text answer grading against a rubric**.

**Blind results, same 760 records:**

| System | Type / hosting | Coverage | Blind accuracy | p50 latency | Source (eval-lab path) |
|---|---|---:|---:|---:|---|
| Qwen3.8 Flash (InferHub) | hosted LLM | 100% | **99.21%** | – | `experiments/EXP-20260922-024-inferhub-recommendation-wave/RESULTS.md` |
| Qwen Flash (direct) | hosted LLM | 99.87% | **97.36%** | – | `experiments/EXP-20260922-022-fast-provider-wave/runs/blind-comparison-20260922/report.md` |
| **Jev (hosted, pinned)** | hosted decision model | 100% | **89.87%** (EXP-022); 90.0% (EXP-014) | p95 380 ms (EXP-014) | same; `experiments/EXP-20260921-014-independent-jev-benchmark/report.md` |
| **Kev-4B** (`jaredpalmer/kev-4b`, LoRA + pointer head on Qwen3.5-4B-Base, Apache-2.0) | local, M1 16 GB, MLX BF16 | 100% | **64.34%** (pairwise 93.52%, single 59.51%) | 1,047 ms | `experiments/EXP-20260924-027-local-decision-bakeoff/report.md` |
| SemIf (Qwen3.5-4B, SemIf-OpenJev runtime) | local, MLX BF16 | 100% | 54.74% | 1,322 ms | same |
| Verdict 1.4 (`heman10x/rlcd-modernbert-151m`, Apache-2.0) | local, **ONNX CPU** | 74.87% (abstains) | 51.49% | 133 ms | same |
| Verdict pre-v1.4 | local, ONNX CPU | 69.21% | 50.38% | 71 ms | same |
| Kev-0.8B | local, MLX | 100% | 50.26% | 177 ms | same |
| **Laya-421M** (`convaiinnovations/laya`, ModernBERT-large, Apache-2.0) | local, PyTorch MPS | 98.42% | **48.53%** | **141 ms** | same |
| Local Qwen3-0.6B student (TASK-0009) | local | 85.8% | 50.77% | – | `experiments/EXP-20260921-014-independent-jev-benchmark/report.md` |
| Grok 4.6 / 4.7 Build | hosted LLM | ~96–100% | ~43.5% (protocol-specific failure) | – | `paper/benchmark_comparison_study.md` §4 |
| Bespoke Nimble-9B, Kev-9B | – | **not run** (do not fit a 16 GB M1) | – | – | `experiments/EXP-20260924-027-local-decision-bakeoff/model-revisions.json` |

**LegalBench Hearsay (EXP-028, 94 items, always-"No" baseline 56.38%):**

| Model | Accuracy |
|---|---:|
| Kev-4B | **72.34%** (the only model clearly above baseline) |
| Laya | 61.70% (interval includes baseline) |
| Kev-0.8B | 54.26% |
| SemIf | 48.94% |
| Verdict (answered "Yes" on all 94) | 43.62% |

Source: `experiments/EXP-20260924-028-legalbench-hearsay/report.md`.

**Calibration (raw, no temperature fit).**
- Kev-4B pairwise: ECE 0.089, Brier 0.136. Kev-4B single pass/fail: ECE 0.259 (poorly calibrated).
- Laya's upstream runtime warns some temperatures are invalid and uncalibrated.
- Split-safe temperature scaling fixed a local Qwen 4B's ECE from 0.341 to 0.078 without changing accuracy (EXP-019).
- **Lesson:** always fit per-question-type temperatures on your own public split.

Sources: `paper/benchmark_comparison_study.md` §5; `experiments/EXP-20260921-019-calibrated-judge-study/report.md`.

**Method notes (from eval-lab).**
- Pinned model and runtime revisions.
- Sequential runs on one host (MacBookPro17,1, Apple M1, 16 GiB).
- Blind holdout is primary, and nothing was fit on it.
- Unresolved records (abstentions, context-limit skips, provider errors) are *statuses*, not counted as wrong.
- Brier, NLL and ECE are computed separately per label space.

Sources: `tasks/TASK-0053-local-decision-models.md`, `checkpoints/CURRENT.md`, `experiments/EXP-20260924-027-local-decision-bakeoff/{experiment.yaml,hardware-and-runtime.json,model-revisions.json}`.

**Plain reading.**
- For **rubric-based answer grading**, the only systems eval-lab has measured as good enough are hosted: Qwen Flash at about 97–99% and Jev at about 90%.
- The cheap local models are either near chance on pass/fail judgments (Laya, Kev-0.8B, Verdict) or only moderate (Kev-4B at 64%, which is strong only on pairwise comparisons).
- These are zero-shot results on one pool. Study-os's own grading items may be easier (short DSA traces, MCQ rationales), but **that has to be measured, not assumed.**

### 6.3 Laya specifically (the pretrained, cheap-to-host candidate)

**What it is.**
- `pip install laya`. Checkpoints:
  - `laya` (ModernBERT-large, 421M parameters, 512-token context);
  - `laya-multilingual` (mmBERT-base, 322M, 1k context, up to 8k);
  - `laya-typed-decisions` (fine-tuned).
- Training: RLCD with proper scoring rules. Apache-2.0.
- Runs on CPU or ONNX: 193–464 ms per request on CPU, about 33–40 ms on a T4 GPU.
- `laya-serve` exposes a **Jev-compatible `/v1/systemone`**. It binds 0.0.0.0 with no authentication unless `LAYA_API_KEY` is set, so set it.

**Its own published claims (vendor-reported; Jev numbers are third-party).**

| Benchmark | Laya | Jev | Note |
|---|---:|---:|---|
| AG News | 0.95 | 0.91 | |
| DAIR Emotion | 0.595 | 0.48 | |
| typed-decisions | 0.766 | 0.727 | Laya's figure is **the fine-tuned checkpoint** |
| Banking77 (>20 options) | 0.425 | 0.870 | |
| ECE (after temperature fitting) | 0.081 | – | |

**Its own "honest limits".**
- Base checkpoints are near chance zero-shot on typed-decisions (0.362 vs a 0.461 majority baseline).
- `noul` can follow the option labels instead of the state; the workaround is a two-option `choice`.
- Ordinal `score` questions are its weakest type.
- It ships over-confident (ECE 0.466 → 0.081 after per-type temperatures).
- `act_probability` is unusable; gate on `confidence` instead (AUROC 0.77).

**Fit for Study-os.**
- **Excellent** as a cheap, CPU-hostable **fine-tuning base** and for **coarse routing and affect questions** (intent, "is the learner asking for the answer?", frustration and emotion), where its card shows strength on topic and emotion tasks.
- **Not yet trustworthy for answer grading or misconception classification zero-shot.** eval-lab measured it at 48.5% on rubric judging.

### 6.4 Other Jev-compatible options found (web; mostly not yet measured in eval-lab)

| Model | Size / base | License | Hardware | Vendor claims |
|---|---|---|---|---|
| **OpenJev** (`openjev/openjev`) | ~27B-class Qwen (bf16 ~54 GB; FP8 29 GB; GGUF Q4_K_M 16.5 GB) | **CC BY-NC 4.0: non-commercial** | H100 (FP8) or a 24 GB GPU with Q4 GGUF | 84.0% vs hosted Jev 85.4% on 10k text questions; ~80 ms short decisions on H100. **The license rules it out for a commercial Study-os** |
| **TinyJev** (`AnkitAI/tinyjev-0.6b`) | Qwen3-0.6B + pointer head, 1.2 GB | MIT | CPU/PyTorch or MLX; `tinyjev serve` on port 8077 | ~110 ms per 3-question ticket on M1; transfer test 0.663, ECE 0.082 ("not 4B-class") |
| **Jeff-1** (`GestaltLabs/Jeff-1`) | LoRA on Qwen3-4B-Instruct | Apache-2.0 | 4B base (GPU or MPS); port 8079 | Fact-checking: 81.8% vs Jev 82.8%, lower ECE (0.081 vs 0.093) |
| **Bosun v3.1** (`Hanno-Labs/bosun-v3.1-0.6b` / `-1.7b`, GGUF available) | Qwen3 0.6B / 1.7B LoRA plus decision tokens | Apache-2.0 | CPU-feasible (GGUF) | DecisionBench: 1.7B 84.9% vs Jev 72.0% on *seen task families* (their own benchmark) |
| **Kev** family (0.5B/0.6B/0.8B/4B/8B/9B) | Qwen LoRA + pointer head | Apache-2.0 | 4B ≈ 9–10 GB; 9B needs 32 GB Mac | Vendor: 4B transfer test 0.838; **eval-lab measured 64.34% on rubric grading** |
| **Verdict** (`heman10x/rlcd-modernbert-151m`) | 151M ModernBERT (GLiClass base) | Apache-2.0 | ONNX CPU, ~70–130 ms | Abstains explicitly (`__insufficient_evidence__`); eval-lab: ~50% on accepted predictions |
| **MoritzLaurer/ModernBERT-large-zeroshot-v2.0** / **deberta-v3-large-zeroshot-v2.0** | 395M / 435M NLI zero-shot classifiers | Apache-2.0 / MIT | CPU OK | Universal NLI "entailment" classifier; baseline to beat is `facebook/bart-large-mnli` |

**Runtimes.**
- **`jev-compatible-server`** (Hanno-Labs): one `/v1/systemone` over Transformers or llama.cpp GGUF, with a registry of about 45 open models including Kev, Bosun and Laya.
- **`llm2jev`**: turns *any* chat model (vLLM, SGLang, Transformers, MLX) into a Jev-compatible service by reading option-label logprobs in one prefill.
- Both let Study-os code against **one interface** and swap hosted Jev ↔ Laya ↔ Kev ↔ a fine-tuned ModernBERT without changing controller code.

**Correction to the earlier "JEV" hypothesis:** "Jev" is TypeSafe's decision model, not JEPA. JEPA (V-JEPA 2, VL-JEPA) is an unrelated vision and world-model line and is dropped here.

### 6.5 Secondary option: plain encoders, NLI and affect classifiers

| Task | Model | Notes |
|---|---|---|
| Semantic similarity to reference answers; answer cache | sentence-transformers (bge / e5 / gte / nomic / jina families; `all-mpnet-base-v2`) | CPU, a few ms per sentence batch. Nearest reference answer plus threshold gives a first-pass grade |
| Zero-shot entailment ("the answer states that the window shrinks when a duplicate appears") | `MoritzLaurer/deberta-v3-large-zeroshot-v2.0`, `ModernBERT-large-zeroshot-v2.0`, `facebook/bart-large-mnli` | Rubric-point checking as NLI: one hypothesis per rubric point |
| Few-shot custom classifier | **SetFit** | ~8 labelled examples per class is competitive (CR 88.5%). Good for misconception labels once you have a few dozen examples |
| Sentiment | `cardiffnlp/twitter-roberta-base-sentiment-latest` | 3-class; tweet domain |
| Emotion (frustration proxies: annoyance, anger, confusion, disappointment) | `SamLowe/roberta-base-go_emotions` (28 labels, ONNX INT8 version available) | Multi-label; calibrate thresholds on Study-os data |
| Fine-tuning backbone | `answerdotai/ModernBERT-base` (149M) / `-large` (395M), Apache-2.0, 8k context, code in pretraining | Upgrade path (a) |

**Text-only affect is weak on its own.** Combine it with behavioral signals: time-on-step, attempt runs, hint escalations, idle gaps, rapid guessing. That combination is how Baker and D'Mello style detectors work.

### 6.6 Serving and hardware on one Linux box ("gravebuster", hardware unknown)

| Box | What fits | Expected latency |
|---|---|---|
| **CPU only** (8+ cores, 16–32 GB RAM) | Laya or Verdict via ONNX Runtime; sentence-transformers; NLI DeBERTa; TinyJev or Bosun-0.6B via PyTorch or llama.cpp GGUF | Laya 0.2–0.46 s; Verdict ~0.1 s; embeddings ms |
| **Small GPU** (8–12 GB, e.g. RTX 3060/4060) | The above plus Kev-4B or Jeff-1 in 4–8-bit, Qwen3/Gemma small models via vLLM or llama.cpp; HF **TEI** for embeddings and rerankers | Laya ~35 ms; 4B decision model ~100–300 ms |
| **24 GB GPU** (3090/4090) | OpenJev Q4 GGUF (non-commercial only), 9B decision models (Kev-9B, Nimble-9B) | ~0.2–1 s |

Serving tools: Hugging Face TEI (encoders), vLLM (prefix caching; used by OpenJev and llm2jev), llama.cpp/GGUF, Ollama (easy local serving), ONNX Runtime (CPU).

**Throughput math.** At ~24 decisions per learner-hour, one T4-class GPU running Laya at ~100 questions/s serves on the order of **10,000+ concurrent learner-hours**. A CPU-only box running Laya at ~3 questions/s serves ~450. Local inference is not the bottleneck; accuracy is.

### 6.7 Decision engines for next-step selection

1. **Rules / state machine (always first).** Deterministic PIR transitions:
   - wrong ×2 at A2 → A3;
   - `pass_unaided` → transfer probe;
   - N=10 attempts without mastery → prerequisite probe (wheel-spinning).
2. **Knowledge tracing.** pyBKT (MIT; supports forgetting, per-item guess/slip and per-student priors) per KC decides *when* a KC is mastered. FSRS decides *when* to re-probe.
3. **Contextual bandits (later).** Vowpal Wabbit `--cb_explore_adf` picks among *equally valid* pedagogical actions: which representation, which hint style, which variant. Context is learner state plus step features. Reward is the next unaided success or `pass_delayed`. Only use it once you have volume; log propensities from day one so off-policy evaluation is possible.
4. **The cascade for interpretation:**

```
learner input
  → deterministic checks (MCQ key, unit tests, exact/regex, trace equality)       [$0, ~ms]
  → decision model /v1/systemone (choice/noul/score, calibrated)                   [~$0, 30–400 ms]
       act if confidence ≥ τ(question_type) and stakes ≤ gate
  → frontier LLM interpreter (grade + diagnose + optional rewrite, JSON output)    [$0.005–0.01/call]
  → (mastery gates only) second opinion or human review queue
```

### 6.8 Recommended decision-layer plan (built on eval-lab evidence)

| Study-os decision | Day-1 route | Why |
|---|---|---|
| Answer grading (free text vs rubric) | Deterministic checks → **hosted Jev** (`noul` per rubric point, `choice` pass/partial/fail) → frontier LLM when Jev confidence < τ | Jev 89.87% on eval-lab's rubric-judging pool at ~$0.04/M tokens. Local models were ≤64% |
| Misconception classification | Hosted Jev `choice` over the node's precompiled misconception list plus `none_of_these` → LLM when low confidence or `none_of_these` | Closed label sets suit Jev. `none_of_these` feeds new-misconception discovery and promotion |
| Frustration / affect / "wants the answer" | **Laya (self-hosted, CPU)** `score` or `choice`, plus behavioral features; go_emotions as a cross-check | Low stakes, fast, private. Fit temperatures first; use `choice` instead of `noul` (Laya issue #156) |
| Sentiment of self-reports | Laya or cardiffnlp sentiment | Low stakes |
| Next-step selection | Rules + pyBKT + FSRS; bandit later | Deterministic and auditable; the LLM never picks progression |
| Step rewrite (precompiled step failed twice) | Frontier LLM (Sonnet 5 / GPT-6 Sol / Gemini 3.8 Flash) with PIR constraints → validators → candidate variant (not live-promoted until it passes review and A/B) | The only true generation duty |

**Thresholds (τ).** Pick τ per question type on Study-os's *own* labelled public split, targeting, for example, ≥95% precision on auto-accepted grades. Keep the blind split untouched, as eval-lab does. Re-fit τ when pinning a new model version (e.g. `jev-1.13.0`).

**Privacy.** Hosted Jev and frontier LLMs receive learner text. Send only the step context and the answer: no names, no IDs, no free-form personal notes. For HESI rationales this is usually fine. Laya on the box keeps affect data local.

---

## 7. Direct answer and concrete recommendations

### 7.1 UX vs model behavior vs code

- **Code (≈50% of the outcome).** Controller, PIR graph, evidence semantics, help-level fading, verification with help removed, mastery and delayed gates. Without these, even a perfect model produces the Bastani failure mode: practice looks great and learning doesn't happen.
- **UX (≈35%).** Tiny steps, a single clear action per screen, fast feedback, streaks tied to verified progress, gentle re-entry after gaps, affect-aware pacing. Distracted learners churn before learning science can act.
- **Model behavior (≈15%).** A bounded interpreter with measurable accuracy and calibration. It is swappable (Jev ↔ Laya ↔ fine-tuned ModernBERT ↔ LLM) because the interface is typed.

These percentages are a judgment call, not a measurement.

### 7.2 What to borrow

| From | Borrow |
|---|---|
| Duolingo | Precompiled course data plus per-user injection; human-in-the-loop LLM authoring; test-everything culture; streaks tied to effort |
| Khan Academy | Mastery levels that can drop; prerequisite propagation; grounding plus a tool for computation (for DSA, **run the code**) |
| Math Academy | Knowledge graph with encompassing weights; FIRe-style implicit review; diagnostic placement |
| OATutor / Oppia / CTAT | JSON step graph with hints and misconception branches; BKT per KC; content A/B variants |
| ASSISTments | Bottom-out hint = not mastered; wheel-spinning detection; embedded RCTs |
| Anki / FSRS | Delayed probes scheduled by retrievability |
| Harvard PS2 Pal / LearnLM | Pedagogical instruction constraints on any generative call |
| eval-lab | Frozen splits, blind holdout, statuses ≠ wrong, per-label-space calibration, pinned versions. Reuse this discipline for Study-os's interpreter |

### 7.3 Analytics event schema (no PII)

Use one append-only `learning_event` table with xAPI-shaped fields. Keep a pseudonymous learner key and **no names, emails or free-form personal data** in analytics mirrors. Keep raw free-text answers only in the private evidence store, with hashes in analytics.

```yaml
learning_event:
  event_id: uuid
  ts_utc: timestamp
  learner_key: pseudonymous-hash         # never email/name
  session_id: uuid
  subject: dsa | hesi
  pir_version: semver
  node_id / kc_id / step_id: string
  capability: recognition|mental_model|state_prediction|invariant_reasoning|procedure|pseudocode|implementation|debugging|transfer|retention|ai_oversight
  outcome_window: immediate|faded|transfer|delayed
  event_type: step_shown|answer_submitted|hint_requested|help_level_changed|step_skipped|step_rewritten|session_start|session_end|idle|tab_hidden|tab_visible|self_report|probe_scheduled|probe_taken|mastery_changed
  help_level: A0..A6
  attempt_no: int
  latency_ms: int                         # time on step until submit
  idle_ms: int
  answer_hash: sha256                     # raw text only in private store
  grade: fail|partial|pass
  capability_state_after: not_tested|fail|partial|pass_supported|pass_unaided|pass_transfer|pass_delayed
  interpreter:
    route: rule|decision_model|frontier_llm|human|cache
    model_id: e.g. jev-1.13.0 | laya@55cf4c4 | gpt-6-sol
    question_type: choice|noul|score
    label: string
    probabilities: {label: p}
    confidence: float
    threshold_used: float
    escalated: bool
    tokens_in / tokens_out / cost_usd: numbers
    latency_ms: int
  misconception: {label, confidence, alternatives[]}   # Study-os diagnosis-as-hypothesis
  affect: {frustration_score, boredom_flag, confusion_persistent, source: behavior|laya|self_report}
  self_report: {confidence, difficulty, clarity, overload}   # never overwrites behavior
  experiment: {id, arm, assignment_unit, propensity}
  learner_correction: {disputes_grade: bool, corrected_label, note_hash}
  reviewer_label: {label, reviewer_role, ts}             # gold for training/eval
```

**Metrics.**
- **Learning:**
  - `pass_unaided` rate per capability;
  - faded-transfer gap (supported pass vs unaided pass);
  - `pass_delayed` at 3, 10 and 30 days;
  - hints per mastered KC;
  - time to first unaided correct;
  - wheel-spinning incidence;
  - retention per minute studied.
- **UX:**
  - D1/D7/D30 return;
  - session length distribution;
  - steps per session;
  - abandonment step (where sessions die);
  - re-entry success after a gap longer than 3 days;
  - streak distribution.
- **Affect:**
  - persistent-confusion episodes;
  - boredom flags;
  - frustration trajectory after interventions.
- **Interpreter quality:**
  - accuracy vs reviewer labels, per route and model;
  - ECE and Brier per question type;
  - escalation rate;
  - learner-dispute rate;
  - $ per learner-hour;
  - p95 latency.

### 7.4 Experiment loop

1. **Hypothesis** from Study-os findings (a repeated subject finding → a lesson hypothesis, as in `MEASUREMENT_MODEL.md` promotion thresholds).
2. **Preregister** a primary learning metric plus UX and cost guardrails. Write down the analysis before looking.
3. **Assign** within learner (crossover over matched KCs) at small N, and between learner (PostHog flags) at scale. Log arm and propensity.
4. **Run** until the preregistered N or duration is reached. Keep delayed-probe windows. Don't stop on day-one clicks.
5. **Decide:** promote a variant into PIR, drop it, or iterate. Record the decision in `DECISIONS.md` with evidence IDs.
6. **Interpreter evals** follow the eval-lab protocol: a frozen Study-os grading set (public for tuning, blind for decisions); rerun on every model or threshold change.

### 7.5 Upgrade path for the decision layer (Alex's plan, with switch criteria)

**Start (weeks 0–N).**
- Deploy the Jev-compatible interface: hosted Jev for grading and misconceptions, Laya self-hosted for affect and routing, rules first, frontier LLM on low confidence.
- **Log from day one:** every decision request (state hash plus the full question schema), the model version, the full probability distribution, confidence, threshold, route, escalation outcome, the eventual **ground truth** (reviewer label, later learner performance, learner dispute), and latency and cost.
- Randomly send about 5% of *high-confidence* decisions to the LLM or a human for audit. Without this you cannot measure precision in the auto-accept region.

Then choose among three paths per decision type.

**(a) Replace with a fine-tuned ModernBERT or Laya trained on Study-os's multi-source labels.**
- *Data needed:* for each decision type, ≥300–1,000 labelled examples (SetFit can start at ~8–16 per class). Label sources: reviewer (Alex, a nurse for HESI), frontier-LLM adjudication (flagged as silver), deterministic verifiers (gold), and learner outcomes (for example, a grade of "pass" followed by unaided success on the transfer probe confirms it).
- Keep label provenance so you can train on gold and silver and evaluate on gold only.
- *Switch when:* on a frozen blind Study-os set, the fine-tuned model matches the incumbent (Jev) within about 2 percentage points **and** has ECE ≤ 0.05 after temperature scaling **and** keeps precision ≥ τ-target in the auto-accept band. Also expect lower cost and latency or a privacy gain.
- *Evidence this can work:* Laya's typed-decisions fine-tune went from 0.362 to 0.766 (vendor), and the Kev skills delta went from 0.540 to 0.803 on its hard suite (vendor).

**(b) Improve the harness instead of the model.**
- Better question decomposition (one `noul` per rubric point rather than one holistic pass/fail), neutral option keys, a `none_of_these` option, context trimming to the step, per-type temperatures, and multi-question consistency checks.
- *Data needed:* the same decision logs plus error analysis tags (why it was wrong).
- *Switch when:* error analysis shows errors cluster in prompt or schema causes, not capability. For example, eval-lab found Kev-4B at 93.5% on pairwise vs 59.5% on single judgments, which suggests reframing single grades as comparisons against a reference answer.
- *Acceptance:* the harness change improves blind accuracy or ECE with no coverage loss.

**(c) Convert well-understood decisions into state-machine rules.**
- *Data needed:* decision logs showing that a decision is determined by a few observable features. For example, "answer matches misconception M3" is almost always predicted by a regex or trace pattern. Or "frustrated" ≈ (3+ fails in a row ∧ latency rising ∧ help ≥ A3).
- *Switch when:* a rule reproduces the model's labels on ≥98% of logged cases with reviewer-confirmed correctness, and it covers enough traffic to matter.
- Rules are free, instant and auditable, and they become PIR transitions. This is the "promotion into the graph" idea applied to decisions.

**Standing rule.** Nothing is promoted on one session's evidence. Use Study-os's existing subject → repeated → lesson → cross-subject thresholds.

### 7.6 Risks

1. **Grading false positives.** Auto-passing a wrong answer corrupts mastery. *Mitigation:* confidence gates, audit sampling, stricter thresholds on mastery gates.
2. **Calibration drift** when vendors update aliases (`jev-latest`). *Mitigation:* pin versions and re-fit τ.
3. **Licensing.** OpenJev is CC BY-NC (non-commercial). Laya, Kev, Bosun, Jeff-1 and Verdict are Apache-2.0; TinyJev is MIT. Jev is a closed API on a waitlist, which is a vendor dependency.
4. **Clinical accuracy (HESI).** Every promoted node needs a source and nurse review; the LLM must not invent clinical facts.
5. **Over-gamification.** Streaks can reward showing up rather than learning. Tie rewards to verified capability states.
6. **Affect mis-detection.** Text-only emotion models are domain-shifted (tweets, Reddit). Combine them with behavior and never gate progression on affect alone.
7. **Small-N inference.** With two learners, prefer within-learner designs and treat results as hypotheses, not policy.
8. **Privacy.** Hosted models see learner text. Minimize payloads, keep PII out of analytics, and keep raw text in the private store.
9. **Vendor benchmark optimism.** Most decision-model scores are self-reported. eval-lab showed large gaps: Kev-4B vendor transfer 0.838 vs eval-lab 0.643; Laya's zero-shot result on rubric judging was near chance. Trust only your own frozen evals.

---

## Sources

**Study-os / eval-lab (read-only).** Paths are in the `Pukujan/eval-lab` repository.
- Study-os: `README.md`, `docs/MEASUREMENT_MODEL.md` (github.com/Pukujan/Study-os)
- eval-lab: `checkpoints/CURRENT.md`; `RESULTS.md`; `paper/benchmark_comparison_study.md`; `tasks/TASK-0053-local-decision-models.md`; `experiments/EXP-20260924-027-local-decision-bakeoff/{report.md,results.json,model-revisions.json,hardware-and-runtime.json}`; `experiments/EXP-20260924-028-legalbench-hearsay/report.md`; `experiments/EXP-20260921-014-independent-jev-benchmark/report.md`; `experiments/EXP-20260922-022-fast-provider-wave/runs/blind-comparison-20260922/report.md`; `experiments/EXP-20260922-024-inferhub-recommendation-wave/RESULTS.md`; `experiments/EXP-20260921-019-calibrated-judge-study/report.md`

**Edtech analytics and architecture**
- https://blog.duolingo.com/learning-how-to-help-you-learn-introducing-birdbrain/
- https://spectrum.ieee.org/duolingo
- https://blog.duolingo.com/unique-engineering-problems/
- https://blog.duolingo.com/rewriting-duolingos-engine-in-scala/
- https://blog.duolingo.com/large-language-model-duolingo-lessons/
- https://blog.duolingo.com/duolingo-max/
- https://blog.duolingo.com/scaling-duoradio/
- https://blog.duolingo.com/how-duolingo-streak-builds-habit/
- https://econsultancy.com/six-a-b-tests-used-by-duolingo-to-tap-into-habit-forming-behaviour/
- https://github.com/ChatPRD/lennys-podcast-transcripts/blob/main/episodes/jackson-shuttleworth/transcript.md
- https://aclanthology.org/P16-1174.pdf ; https://github.com/duolingo/halflife-regression
- https://blog.khanacademy.org/khan-academys-7-step-approach-to-prompt-engineering-for-khanmigo/
- https://blog.khanacademy.org/prompt-engineering-using-ai-for-effective-lesson-planning/
- https://blog.khanacademy.org/khanmigo-math-computation-and-tutoring-updates/
- https://blog.khanacademy.org/how-we-built-ai-tutoring-tools/
- https://khanmigo.ai/pricing
- https://denver-frederick.com/2024/05/02/empowering-learning-through-ai-the-impact-of-khan-academys-khanmigo/
- https://www.edweek.org/technology/khan-academy-plans-to-shake-up-writing-instruction-with-ai-tool/2023/11
- https://support.khanacademy.org/hc/en-us/articles/5548760867853--How-do-Khan-Academy-s-Mastery-levels-work
- https://support.khanacademy.org/hc/en-us/articles/115002552631-What-are-Course-and-Unit-Mastery
- https://support.khanacademy.org/hc/en-us/articles/360032987591-How-can-I-understand-my-progress-in-Khan-Academy
- https://medium.com/coursera-engineering/analytics-at-coursera-three-years-later-36ba911e407b
- https://medium.com/coursera-engineering/how-a-b-testing-powers-pedagogy-on-coursera-2cd10ed8365e
- https://blog.coursera.org/using-data-transform-learning-experience/
- https://quizlet.com/blog/spaced-repetition-for-all-cognitive-science-meets-big-data-in-a-procrastinating-world
- https://medium.com/tech-quizlet/improving-learn-ing-quizlets-new-memory-model-3c2271e5eaf4
- https://www.etrialstestbed.org/home ; https://journals.sagepub.com/doi/10.1177/2332858416673968
- https://mathacademy.com/how-our-ai-works
- https://justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/
- https://frankhecker.com/2025/02/14/math-academy-part-7/
- https://www.annastokke.com/ep-42-transcript
- https://github.com/CAHLR/OATutor ; https://dl.acm.org/doi/10.1145/3544548.3581574
- https://github.com/oppia/oppia ; https://oppia-user-guide.readthedocs.io/en/latest/admins/guide.html
- https://github.com/nilbuild/developer-roadmap
- https://github.com/rasbt/LLMs-from-scratch

**Analytics tooling**
- https://posthog.com/pricing ; https://posthog.com/docs/self-host
- https://github.com/LearningLocker/learninglocker ; http://www.imsglobal.org/initial-xapicaliper-comparison

**Learning science**
- https://doi.org/10.1080/00461520.2011.611369 (VanLehn 2011)
- https://www.rand.org/pubs/external_publications/EP50410.html (Pane et al. 2014)
- https://www.cs.cmu.edu/~bmclaren/pubs/AlevenEtAl-ExampleTracingTutors-IJAIED2009.pdf
- https://arxiv.org/abs/1604.02416 (How deep is knowledge tracing?)
- https://jedm.educationaldatamining.org/index.php/JEDM/article/view/451
- https://github.com/CAHLR/pyBKT ; https://arxiv.org/abs/2105.00385
- https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler ; https://github.com/open-spaced-repetition/srs-benchmark ; https://expertium.github.io/Benchmark.html
- https://www.educationaldatamining.org/EDM2015/uploads/papers/paper_84.pdf ; https://doi.org/10.1007/978-3-642-39112-5_44 (wheel-spinning)
- https://learninganalytics.upenn.edu/ryanbaker/BDRG-IJHCS-Final.pdf (Better to be frustrated than bored)
- https://doi.org/10.1007/s40593-014-0029-5 (AutoTutor review)
- https://escholarship.org/uc/item/81b9j9hs ; https://doi.org/10.1037/0022-0663.95.4.774 (fading)
- https://gwern.net/doc/psychology/spaced-repetition/2017-adesope.pdf (retrieval practice)
- https://eric.ed.gov/?id=EJ1237752 (Rohrer 2020 interleaving)
- https://link.springer.com/article/10.1007/s10648-019-09498-w (gamification meta-analysis)

**LLM tutoring research**
- https://www.nature.com/articles/s41598-025-97652-6 (Harvard AI tutor RCT)
- https://arxiv.org/abs/2410.03017 (Tutor CoPilot)
- https://arxiv.org/abs/2412.16429 (LearnLM)
- https://www.pnas.org/doi/10.1073/pnas.2422633122 ; https://github.com/obastani/GenAICanHarmLearning (Bastani et al.)
- https://arxiv.org/abs/2302.06871 (ChatGPT vs human hints)

**HESI**
- https://www.incrediblehealth.com/blog/hesi-exam/ ; https://leveluprn.com/pages/exam/hesi
- https://assets.ctfassets.net/zlnfaxb2lcqx/Vg60BOWlgmbL3nwDjmlnZ/9b739c91d725aa03bb4d9a468dadbaf7/HESI-RN-Integrated-Exams-Score-Setting-Study.pdf
- https://www.chamberlain.edu/resources/academics/hesi-admission-assessment-exam-faqs

**Model pricing (fetched 2026-09-24)**
- https://platform.openai.com/docs/pricing ; https://www.anthropic.com/pricing ; https://ai.google.dev/gemini-api/docs/pricing

**Decision models (Jev and alternatives)**
- https://typesafe.ai/blog/introducing-system-one-models-and-jev ; https://www.jevtypesafeai.com/how-to-use ; https://typesafe-api.hexdocs.pm/system_one.html ; https://systemonemodels.org/guides/jev-explained/ ; https://flaviocopes.com/jev/
- https://huggingface.co/convaiinnovations/laya ; https://github.com/NandhaKishorM/laya ; https://huggingface.co/convaiinnovations/laya-typed-decisions
- https://huggingface.co/jaredpalmer/kev-4b ; https://huggingface.co/jaredpalmer/kev-0.8b ; https://github.com/jaredpalmer/kev
- https://huggingface.co/heman10x/rlcd-modernbert-151m ; https://github.com/Heman10x-NGU/Verdict-open-jev
- https://github.com/TheoLeeCJ/SemIf-OpenJev ; https://github.com/bespokelabsai/nimble
- https://huggingface.co/openjev/openjev
- https://huggingface.co/AnkitAI/tinyjev-0.6b ; https://pypi.org/project/tinyjev/
- https://huggingface.co/GestaltLabs/Jeff-1 ; https://github.com/Gestalt-Lab/jeff
- https://huggingface.co/Hanno-Labs/bosun-v3.1-1.7b ; https://huggingface.co/Hanno-Labs/bosun-v3.1-0.6b
- https://github.com/Hanno-Labs/jev-compatible-server (docs/MODELS.md) ; https://pypi.org/project/jev-compatible-server/
- https://github.com/tic-top/llm2jev ; https://pypi.org/project/llm2jev/

**Encoders, classifiers, runtimes**
- https://www.answer.ai/posts/2024-12-19-modernbert.html ; https://huggingface.co/answerdotai/ModernBERT-base
- https://huggingface.co/MoritzLaurer/deberta-v3-large-zeroshot-v2.0 ; https://huggingface.co/MoritzLaurer/ModernBERT-large-zeroshot-v2.0 ; https://huggingface.co/facebook/bart-large-mnli
- https://arxiv.org/abs/2209.11055 ; https://huggingface.co/blog/setfit (SetFit)
- https://huggingface.co/SamLowe/roberta-base-go_emotions ; https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest
- https://vowpalwabbit.org/docs/vowpal_wabbit/python/latest/tutorials/python_Contextual_bandits_and_Vowpal_Wabbit.html
- https://github.com/huggingface/text-embeddings-inference ; https://docs.vllm.ai ; https://github.com/ggml-org/llama.cpp ; https://ollama.com ; https://onnxruntime.ai
