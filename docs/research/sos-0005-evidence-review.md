# SOS-0005 research gate: evidence review before building

- Issue log: umbrella #107 (sub-issue of #82); related #101, #103, #104, #105, #106.
- Status: **durable research on `main`.** Hypotheses and verdicts below. Alex reviewed 2026-09-24; product decisions are recorded in [`decisions-2026-09-24.md`](./decisions-2026-09-24.md). Design/build remains on draft PR #102 (not merged here).
- Author: Grok Bot executor, 2026-09-24 (ET). Landed to main 2026-09-24 (docs-only).
- Method: web search plus direct fetches. Every DOI below was resolved against the Crossref API (title and authors matched). Every non-DOI URL was checked with an HTTP request from the box on 2026-09-24 and returned 200; the one exception is marked. Effect sizes come from the paper abstracts or publisher pages as found in search. **Full texts were not read for every paper**, so treat any number as "as reported in the abstract". No IRE/InferHub model was used to summarise in this pass (InferHub spend for the research phase: $0.00).
- Evidence grading: **[E-peer]** peer-reviewed study or meta-analysis · **[E-co]** company research or engineering data (not peer-reviewed) · **[E-ux]** UX research firm study (NN/g, Baymard) · **[O]** opinion, teardown or design essay · **[Std]** standard or spec.
- Verdict scale: **supported** / **weak** / **contradicted** / **unknown**, each with a confidence of low, medium or high. Verdicts are about *the hypothesis as stated*. Many are "supported with conditions", and the conditions matter more than the label.

## Verdict table

| # | Hypothesis | Verdict | Confidence | One-line reason |
|---|---|---|---|---|
| H1 | Micro-step lesson player, produce/predict before being told | **Supported** (with fading) | Medium-high | Retrieval practice g≈0.61, self-explanation g≈0.55, predicting and problem-first g≈0.36 conceptual. But expertise reversal means fixed micro-steps hurt learners who already know the step. |
| H2 | Interactive/animated visuals | **Supported for representational, learner-paced visuals; weak for decorative motion** | Medium | Representational animation d≈0.40 vs decorative d≈−0.05. Transient-information and segmenting effects require pausable, stepwise visuals. |
| H3 | LLM tutor chat that never leaks answers | **Supported, conditional on guardrails and grounding** | Medium | Harvard RCT: gains more than doubled. PNAS: an unguarded GPT cut exam scores by 17%, and the guarded tutor only removed the harm. 2023 ChatGPT hints had a 30% error rate. |
| H4 | Adaptive re-explanation in a *new representation* | **Weak** (a new *example* in the same representation is better supported) | Medium | Switching representations costs translation effort (DeFT). The goldens themselves keep one diagram and change the *example*. The assistance dilemma is unresolved. |
| H5 | Per-screen limits (one concept, word budget) | **Supported as a principle; unknown for specific numbers** | Medium | WM capacity is about 4 chunks. Coherence and segmenting principles hold. No source validates specific word or element counts, and choice-overload effects average about zero. |
| H6 | Motion spec plus reduced-motion support | **Supported** (accessibility); motion's *learning* value weak | High (a11y) / Medium (learning) | WCAG 2.3.3 and prefers-reduced-motion are standards. Decorative motion shows no learning gain. |
| H7 | Grown-up anime/sticker visual style | **Unknown** (lean weak) | Low | Kawaii and decorative-picture studies show mood gains and a neutral effect on learning. Seductive-detail risk exists but results are inconsistent. No study of anime style for adult learners. Needs user testing. |
| H8 | Onboarding in about 60s, signup deferred until after the first lesson | **Supported** for lesson-before-signup and no tutorial deck; **unknown** for "60s" | Medium | Duolingo gradual engagement; NN/g found tutorials don't improve task success. Headspace's quiz doubled starts but not active days. Brilliant does account + paywall first and still succeeds. |
| H9 | Netflix-style catalogue (rows/carousels) | **Weak** at the current catalogue size | Medium | Netflix rows depend on a huge catalogue plus personalisation. NN/g and Baymard find carousels are overlooked (about 1% click; 84% of clicks go to the first slide). Duolingo moved *toward* one clear path. |
| H10 | Multiple lanes visible on home | **Supported** (few lanes, one primary "continue") | Medium-low | Showing 4 lanes costs little: choice overload averages D≈0.02. "Only HESI shows" is a bug, not a hypothesis. Duolingo's single path cut confusion but drew backlash over lost choice, so keep both a primary action and browsing. |
| H11 | Voice learning agent | **Weak** for this product now | Medium-low | Modality effect d≈0.72, but it reverses under learner pacing (d≈−0.14) and drops to ≈0.20 after bias correction. ASR error doubles for some groups. Turn-taking expectation is about 200 ms. Voice is proven for *language speaking* (Duolingo, Speak), not for DSA or maths. InferHub has no STT/TTS routes. |
| H12 | LLM-first, then retrieval/caching of proven outputs | **Weak as ordered.** Grounding should come *first*; caching later is fine | Medium | Khan: accuracy rises when human-written steps are in context. RAG improves factuality. Ungrounded 2023 hints had a 30% error rate. Prompt caching cuts input cost by up to 90%. Logging everything from day one is well supported. |
| H13 | Goldens + oracle as the eval suite | **Supported as necessary, not sufficient** | Medium | Expert-authored references match the "human-authored hints" that beat 2023 LLM hints. But LLM judges show position and verbosity bias, and conformance is not learning. LearnLM and the RCTs use multi-method evals and learning outcomes. |
| H14 | Chibi pet companion on the lesson screen (tap to talk, reacts to answers; robot visits during idle) | **Weak-to-supported, conditional** — hypothesis to validate with Alex's like/dislike feedback | Medium-low | Pedagogical agents: small effect g≈0.19–0.20, smaller for post-secondary (g≈0.12); the benefit comes from interaction and words, not the image (no image effect). Decorative motion and irrelevant sounds carry a distraction risk. |
| H15 | One screen, one state: the question card stays visible and the companion panel opens beside it (side panel / half sheet); variants update the card in place | **Supported** (principle) — hypothesis for the specific UI | Medium | Split-attention/contiguity: integrating related information gives d≈0.85. Existing patterns: Khanmigo beside the exercise, Duolingo "Explain My Answer" inline. |

**Source count: 86 distinct external sources**: 45 peer-reviewed/academic (37 Crossref-verified DOIs, 5 arXiv papers, and 3 academic PDFs: Mayer, Schneider et al., WWC) and 41 company, UX-research, standards, teardown, news, working-paper or tool pages. H14/H15 were added 2026-09-24 after Alex's interaction-design notes. References are listed in the final section.

> **Product moat (Alex, 2026-09-24):** Study OS's main advantage is **multiple forms of information representation** plus **breaking hard problems into small stepwise pedagogical goals**. Recorded as decision D12 in [`decisions-2026-09-24.md`](./decisions-2026-09-24.md). Hypotheses H1, H2, H4, and H15 are the evidence gate for that moat; style/voice/home UI are secondary.


---

## H1: Micro-step lesson player, produce/predict first

**Claim under test:** lessons should be many small steps where the learner produces or predicts something *before* being told, one new idea per step.

**Evidence FOR**
- Practice testing beats restudy, g=0.61 over 272 effects [E-peer, R21].
- Prompting self-explanation, g=0.55 [E-peer, R9].
- Predicting before feedback improves learning, via surprise and error-driven updating [E-peer, R4].
- Problem solving *before* instruction beats instruction-first for conceptual knowledge and transfer, g=0.36 over 166 comparisons [E-peer, R25].
- ICAP: constructive and interactive engagement outperform active, which outperforms passive [E-peer, R17].
- Mayer's segmenting principle was positive in 7 of 7 tests [E-peer summary, R2].
- Step-based ITS reach d≈0.76, close to human tutors [E-peer, R24].
- Brilliant, as a design practice: "start with a problem at the edge of understanding, one small leap, name the technique afterwards" [O/E-co, R46].

**Evidence AGAINST / disconfirming**
- Expertise reversal: guidance that helps novices hurts more knowledgeable learners [E-peer, R8]. Fixed micro-steps for everyone is therefore contradicted.
- Productive failure shows **no** procedural-knowledge gain (g≈−0.03) [R25], so problem-first mainly helps conceptual goals.
- ITS gains shrink on standardised tests compared with local tests [E-peer, R1].
- No source shows that *more* granularity is always better. Over-segmentation risks fragmenting the concept (no direct study found, so **unknown**).

**Alternatives:** worked-example → faded-example sequences; adaptive step size (skip steps once mastery evidence exists); problem-first only for conceptual steps, direct instruction for procedures.

**Verdict:** supported, *with fading/adaptive granularity*. Confidence: medium-high.

## H2: Interactive / animated visuals

**Evidence FOR**
- Instructional animation beats static pictures, d=0.37; representational animation d=0.40 [E-peer, R6].
- The WWC fractions guide recommends number lines and visual models [E-peer/gov, R31].
- Rational-number interventions meta-analysis for students with difficulties [E-peer, R30]: large overall effects with heavy use of visual representations. This is an indirect link.
- Concreteness fading (concrete → abstract) supports transfer [E-peer, R16].
- Brilliant reports "learn by doing" interactives as the core of its product [E-co, R45, R47].

**Evidence AGAINST**
- *Decorational* animation d≈−0.05 [R6].
- Transient information effect: animation and speech overload working memory when content disappears [E-peer, R3].
- Segmentation, pauses and temporal cues are needed [E-peer, R5].
- Multiple representations help only if learners can translate between them, and translation is costly [E-peer, R7].
- Khan found the LLM struggles with graphics [E-co, R50]. LLM-generated visuals therefore need deterministic rendering (PIR).

**Alternatives:** static stepwise diagrams (the goldens' ASCII box with index) advanced by the learner, not auto-played.

**Verdict:** supported for representational, learner-controlled, segmented visuals; weak for decorative or auto-playing motion. Confidence: medium.

## H3: LLM tutor chat without answer leaks

**Evidence FOR**
- Harvard physics RCT (N=194): an AI tutor built on research-based pedagogy produced more than double the learning gains of in-class active learning, in less time [E-peer, R12]. Immediate post-test only.
- Tutor CoPilot RCT (about 900 tutors, 1,800 students): +4 percentage points mastery, +9 for weaker tutors [E-peer-preprint, R40].
- LearnLM-Tutor beat prompted Gemini on pedagogy benchmarks [E-co/preprint, R41].
- ChatGPT hints matched human hints in the 2024 follow-up (N=274) [E-peer, R27].
- Kulik & Fletcher ITS median +0.66 SD [R1]; VanLehn [R24].
- Brilliant's Koji and Khanmigo are designed not to hand over answers [E-co, R48, R49].

**Evidence AGAINST / disconfirming**
- PNAS (about 1,000 students): unrestricted GPT access cut unassisted exam performance by about 17%. The guarded "GPT Tutor" *removed the harm but produced no significant gain* [E-peer, R11].
- 2023 pilot: 30% of ChatGPT hints failed quality checks, and human hints produced much larger gains [E-peer-preprint, R39].
- Khanmigo users complained about repetition, and math accuracy needed human-written steps in context [E-co, R49, R50].

**Alternatives:** no free chat, only structured hints plus "explain my answer" (the Duolingo Max pattern [E-co, R51]); tutor chat limited to the current step with the answer withheld by the server; hint ladders.

**Verdict:** supported *only* with server-side answer-withholding, grounding in the step's canonical solution, and evaluation. Unconstrained chat is contradicted by R11. Confidence: medium.

## H4: Adaptive re-explanation in a new representation

**Evidence FOR**
- Multiple representations can deepen understanding when translation is supported [R7, R47].
- Concreteness fading changes representation deliberately [R16].
- Re-explanation after errors is a core ITS behaviour [R24].

**Evidence AGAINST**
- DeFT: each new representation adds a translation cost, heaviest for novices, who are the struggling learners here [R7].
- The project's own goldens keep **one** diagram throughout and, after a wrong answer, give the answer, show why *on the same chart*, then retry a **different example**. The goldens support a new example, not a new representation (repo evidence, `domains/dsa/sliding-window/golden/`).
- Assistance dilemma: when and how much to help is unresolved [E-peer, R26].
- The 2023 LLM hint error rate [R39] makes generating *new* representations the riskiest option.

**Alternatives:** same representation with a new example (golden pattern); a pre-authored second representation per concept (deterministic, reviewed) instead of LLM-invented ones.

**Verdict:** weak for "new representation"; the golden "new example, same chart" is better supported. Confidence: medium.

## H5: Per-screen limits

**Evidence FOR**
- Working memory holds about 4 chunks [E-peer, R13].
- Mayer coherence principle positive in 18 of 19 tests, signalling in 26 of 28 [R2].
- The oracle's "max 1 new concept per step" is consistent with segmenting [R2, R5].

**Evidence AGAINST**
- No source validates *specific* numeric limits (word budget N, K elements).
- Choice-overload meta-analysis mean D≈0.02 [E-peer, R15], so "fewer options" is not automatically better.
- Expertise reversal [R8]: limits tuned for novices may slow experts.

**Alternatives:** limits expressed as element interactivity (new concepts per step) instead of word counts; A/B the word budget.

**Verdict:** supported as a principle; unknown for the exact thresholds. Confidence: medium.

## H6: Motion spec / reduced motion

**Evidence FOR**
- WCAG 2.2 SC 2.3.3 (AAA) asks that motion animation triggered by interaction can be disabled [Std, R35].
- `prefers-reduced-motion` is widely supported [Std, R34].
- Material 3 publishes duration and easing tokens (short 50–200 ms, long up to about 1000 ms) [Std/E-co, R33].
- Duolingo uses Rive state machines for character animation [E-co, R52].

**Evidence AGAINST**
- Decorative motion has no learning benefit [R6].
- Transient motion adds load [R3].

**Verdict:** supported as an accessibility and consistency requirement (high); motion's learning value is weak unless it is representational (medium). Keep a small token set and treat reduce-motion as the default-safe path.

## H7: Grown-up anime/sticker style

**Evidence FOR**
- "Power of Kawaii": viewing cute images improved careful task performance in lab tasks [E-peer, R10]. That is not learning.
- Decorative pictures improved mood and lowered perceived difficulty, with a neutral net effect on learning [E-peer, R28].
- Emotional-design studies report some motivational benefit [E-peer, R29].

**Evidence AGAINST**
- Seductive details can harm retention and transfer (Rey 2012, d≈0.95 / 0.83, as summarised in R14). The same review finds results inconsistent (about 11 of 39 studies support the effect).
- No peer-reviewed evidence specific to anime aesthetics for *adult* learners was found.
- Perceived childishness is a plausible risk but only opinion [O].
- CGM has no reviewed visual asset yet (repo `.content-system/`, adoption_status placeholder).

**Alternatives:** neutral, diagram-first style with a mascot only at transition moments (celebration and reassurance), never on problem screens.

**Verdict:** unknown, leaning weak. Confidence: low. Needs a preference and comprehension test with target users.

## H8: Onboarding in about 60s, signup deferred

**Evidence FOR**
- Duolingo "gradual engagement": lesson first, account later [E-co/O, R53, R54]. The 2013 forced-signup flow was criticised [O, R55].
- NN/g quantitative study (70 users, 4 apps): tutorial decks did not improve task success (91% vs 94%), and readers rated the apps as *more* complex [E-ux, R42]. NN/g recommends contextual help over upfront tutorials [E-ux, R43, R44].
- Headspace RCT: a personalisation quiz doubled course starts (31% → 63%) [E-co field experiment, R56, R57].

**Evidence AGAINST / disconfirming**
- Headspace: active meditation days did **not** increase [R56], so onboarding gains may not carry through to learning.
- Brilliant puts about 12 onboarding steps, then account, then paywall *before* the first lesson, and is commercially successful [O teardown, R58].
- Deferred signup loses contact with users who leave [O, R59].
- No evidence supports "60 seconds" as a threshold.

**Alternatives:** placement probe as the first lesson; account prompt at the first save point.

**Verdict:** supported for "first lesson before signup, no tutorial deck"; unknown for "60s". Confidence: medium.

## H9: Netflix-style catalogue

**Evidence FOR**
- Netflix personalises rows and artwork (contextual bandits) and builds the homepage as a personalised 2D grid [E-co, R60, R61].
- Coursera-style hubs organise large catalogues [O, R62].

**Evidence AGAINST / disconfirming**
- NN/g: carousels are often ignored, auto-forward hurts, and mobile carousels have low discoverability [E-ux, R63–R65].
- Baymard: about half of homepage carousels have issues [E-ux, R66].
- Notre Dame data: about 1% click a carousel, 84% of those on the first slide [O/data, R67].
- Duolingo replaced a branching tree with one path to reduce "what next?" confusion [E-co, R68].
- Netflix's pattern relies on thousands of titles plus behavioural data. Study OS has 4 lanes and no such data.

**Alternatives:** home = one primary "Continue: <lane, step>" card plus a short static list or grid of lanes. Revisit rows once there are 20+ units and usage data.

**Verdict:** weak at the current scale. Confidence: medium.

## H10: Multiple lanes on home

**Evidence FOR**
- Choice-overload effects average about zero [R15], so 4 visible lanes carry little risk.
- Learners with several goals need discoverability [R63].
- "Only HESI shows" is an observed defect (#105), not a hypothesis.

**Evidence AGAINST**
- Duolingo's single path reduced confusion [R68], though it drew backlash about lost choice [E-news, R69].
- Interleaving across unrelated lanes has no evidence of benefit (the interleaving literature covers related problem types). No direct study was found, so **unknown**.

**Verdict:** supported for showing all lanes with one primary continue action. Confidence: medium-low.

## H11: Voice learning agent

**Evidence FOR**
- Modality effect (narration plus graphics beats on-screen text plus graphics), d=0.72 [E-peer, R20].
- Duolingo Video Call and Speak report speaking gains in *language* learning [E-co, R70–R72].
- Cheap open TTS/STT exists: Kokoro-82M (Apache-2.0) [R73] and faster-whisper [R74].

**Evidence AGAINST / disconfirming**
- The modality effect reverses when learners control pacing (d≈−0.14) and shrinks to about 0.20 after publication-bias correction [E-peer, R20 for the pacing moderator; R36 for the bias-corrected estimate].
- Speech is transient [R3].
- ASR error rate is 0.35 for Black speakers vs 0.19 for White speakers [E-peer, R18].
- Humans expect about 200 ms turn gaps [E-peer, R19]. An STT → LLM → TTS chain over InferHub (no STT/TTS routes; only `cx/gpt-5.5` accepts audio) will be well above that.
- No evidence was found for voice tutoring of DSA or maths specifically.

**Verdict:** weak for this product now. Keep #106 as research only. Confidence: medium-low.

## H12: LLM-first, then retrieval/caching

**Evidence FOR (LLM-first as a data-gathering phase)**
- Logging every interaction enables evals and later caching.
- Prompt caching cuts input cost by up to about 90% and latency by up to about 80% for long stable prefixes [E-co docs, R75].

**Evidence AGAINST (ungrounded first)**
- Khan: accuracy improves when human-written steps or hints are in the prompt [E-co, R50].
- RAG improves factuality and specificity over parametric-only generation [E-peer, R38].
- Ungrounded 2023 LLM hints had a 30% error rate [R39].
- The PNAS guarded tutor used teacher-provided solutions in the prompt [R11].

**Alternatives:** "grounded-first". Put the golden, PIR chart and canonical solution into every prompt from day one (this is retrieval, but of *authored* content), then cache validated generations later.

**Verdict:** weak as ordered. Grounding should not wait for phase 2; caching can. Confidence: medium.

## H13: Goldens + oracle as the eval suite

**Evidence FOR**
- Expert-authored references are the kind of human-authored help that outperformed LLM help in R39.
- Rule-based conformance (the oracle's 10 bridges) is deterministic and cheap.
- LearnLM shows the value of pedagogy-specific benchmarks [R41].

**Evidence AGAINST**
- LLM-as-judge shows position bias and verbosity bias. GPT-4 was about 65% consistent when answer order was swapped [E-peer-preprint, R37].
- Conformance to goldens is not learning. The strongest evidence (R11, R12, R40) uses learning outcomes.
- Goldens cover one lane (sliding window), so coverage is thin.

**Alternatives:** a layered eval: (1) deterministic oracle rules, (2) LLM judge with order swap and a rubric, spot-checked by a human, (3) small pre/post learning checks with real or simulated learners, reported separately.

**Verdict:** supported as necessary, not sufficient. Confidence: medium.

## H14: Chibi pet companion (pedagogical agent)

**Claim under test:** a small chibi pet (the learner character) lives on the lesson screen. Tapping it opens the companion panel, where it talks (talking loop + TTS + speech bubble) and reacts to answers (celebrate / encourage loops). The chibi robot helper visits rarely during idle.

**Evidence FOR**
- Pedagogical agents have a small but significant positive effect on learning, g=0.19 across 43 comparisons [E-peer, R78]; a later meta-analysis finds g+=0.20 [E-peer, R79].
- The persona effect: learners rate lifelike agents as helpful and credible [E-peer, R81].
- Interaction with an agent improved transfer and interest [E-peer, R80].

**Evidence AGAINST / disconfirming**
- The effect is smaller for post-secondary learners (g≈0.12 in R78), and our learner is an adult.
- In R80 the agent's *visual presence* had no effect (no "image effect"). The gains came from interactivity and words, so the pet's art adds motivation at best.
- In R78, agents communicating by on-screen text beat narration. Keep the transcript bubble visible even when TTS is on.
- Irrelevant sounds and decorative animation hurt learning (coherence effect) [E-peer, R84; R6, R14].

**Design implications (opinion, derived from the evidence above):**
- Keep the pet small (≤ 96 px mobile / 120 px desktop) and never covering the question or visual.
- Reactions only at feedback moments.
- Idle robot visits rare (≥ 90 s idle, at most once per 10 min), never during assessment or typing.
- Paused under reduced motion; mute/hide toggle remembered per user.
- The talking loop always paired with the text transcript.
- The tutor behind it is the same guarded, grounded, logged tutor (H3).

**Verdict:** weak-to-supported, conditional on the constraints above. Confidence: medium-low. Validate with like/dislike feedback and a hide-rate metric.

## H15: One screen, one state (companion panel beside the question card)

**Evidence FOR**
- The split-attention effect [E-peer, R83] and the spatial/temporal contiguity meta-analysis, d≈0.85 across 50 studies (larger for complex material) [E-peer, R82]: keep help next to the thing it explains, not on another page or in another mode.
- Khanmigo shows the tutor beside the exercise (chat icon / "Tutor Me" next to the question) [E-peer working paper, R85]. The same paper reports that 39.4% of student messages were bare answers, which is a caution for chat-heavy designs.
- Duolingo's "Explain My Answer" appears inline right after the exercise [E-co, R86].

**Evidence AGAINST**
- A side panel shrinks the question area on small screens.
- A half-height sheet on mobile can hide part of the visual. **Mitigation:** the card scrolls above the sheet, and variants update the card itself, not the chat.

**Verdict:** supported as a principle; the specific layout is a hypothesis to validate with Alex's live testing and the like/dislike feedback. Confidence: medium.

---

## Cross-cutting: gamification and celebration (bears on H7 and H8)
- Gamification meta-analysis: cognitive g=0.49, motivation g=0.36, behaviour g=0.25. In rigorous studies only the cognitive effect stays significant [E-peer, R22].
- Early reviews are mostly positive but context-dependent, with a warning about novelty effects [E-peer, R23]. A longitudinal study finds effects fade and then partly recover with familiarisation [E-peer, R32].
- Implication (opinion): stickers and celebrations should not be assumed to sustain engagement. Measure them over weeks, not days.
- Headspace's routine-anchored three-question onboarding [O, R76] and Duolingo's company-reported Video Call results [E-co, R71] are single-company data points.
- Brilliant-style "interactive play" essays [O, R77] are opinion.
- Mobile carousel auto-forwarding is specifically discouraged [E-ux, R64].

## Evidence vs opinion (what is *not* evidence here)
- Teardowns (R55, R58, R59, R62), carousel click data from one university (R67), and Brilliant's design essays (R45–R47) are practitioner opinion or single-site data.
- Company reports (Duolingo, Khan, Headspace/Irrational Labs, Speak) are real data but not peer-reviewed and are subject to selection.
- All "60s", word-budget and animation-duration numbers in our earlier proposals are **our** opinion; no source validates them.

## What would change these verdicts (suggested cheap tests, not builds)
- H7: 5-second preference test plus a comprehension check, comparing 2 style boards.
- H9/H10: first-click test on 2 static home mockups (rows vs continue + grid).
- H3/H4/H12: offline replay of golden situations through grounded vs ungrounded prompts, scored by the oracle, plus a human spot-check of 20 transcripts.
- H11: latency measurement of STT → LLM → TTS on available routes before any design work.

## References

Peer-reviewed / academic (DOIs verified via Crossref on 2026-09-24)
- R1. Kulik & Fletcher (2016). Effectiveness of Intelligent Tutoring Systems. RER. https://doi.org/10.3102/0034654315581420 — ITS median +0.66 SD over 50 evaluations; smaller on standardised tests.
- R2. Mayer, Research-based principles for designing multimedia instruction (APA/UNH PDF). https://www.unh.edu/teaching-learning-resource-hub/sites/default/files/media/2023-06/itow-research-based-principles-for-designing-multimedia-instruction-mayer.pdf — coherence 18/19, signalling 26/28, segmenting 7/7 positive tests. (Timed out from the box; verified via search index.)
- R3. Wong, Leahy, Marcus & Sweller (2012). Cognitive load theory, the transient information effect and e-learning. Learning & Instruction. https://doi.org/10.1016/j.learninstruc.2012.05.004 — transient animation or speech can overload WM; segmentation helps.
- R4. Brod (2021). Predicting as a learning strategy. Psychon Bull Rev. https://doi.org/10.3758/s13423-021-01904-1 — prediction before feedback aids learning.
- R5. Spanjers, van Gog, Wouters & van Merriënboer (2012). Explaining the segmentation effect in learning from animations. Computers & Education. https://doi.org/10.1016/j.compedu.2011.12.024 — pauses and temporal cueing explain segmentation benefits.
- R6. Höffler & Leutner (2007). Instructional animation versus static pictures: a meta-analysis. https://doi.org/10.1016/j.learninstruc.2007.09.013 — d=0.37 overall; representational 0.40; decorational −0.05.
- R7. Ainsworth (2006). DeFT: learning with multiple representations. https://doi.org/10.1016/j.learninstruc.2006.03.001 — benefits depend on translation; translation is costly.
- R8. Kalyuga, Ayres, Chandler & Sweller (2003). The expertise reversal effect. https://doi.org/10.1207/s15326985ep3801_4 — novice-helpful guidance hurts experts.
- R9. Bisra, Liu, Nesbit et al. (2018). Inducing self-explanation: a meta-analysis. https://doi.org/10.1007/s10648-018-9434-x — g≈0.55.
- R10. Nittono, Fukushima, Yano & Moriya (2012). The power of kawaii. PLOS ONE. https://doi.org/10.1371/journal.pone.0046362 — cute images improved careful-task performance (lab tasks, not learning).
- R11. Bastani, Bastani, Sungu et al. (2025). Generative AI without guardrails can harm learning. PNAS. https://doi.org/10.1073/pnas.2422633122 — GPT Base −17% on the unassisted exam; guarded GPT Tutor removed the harm, no significant gain.
- R12. Kestin, Miller, Klales et al. (2025). AI tutoring outperforms in-class active learning: an RCT. Sci Rep. https://doi.org/10.1038/s41598-025-97652-6 — more than double the gains, less time; immediate outcomes.
- R13. Cowan (2001). The magical number 4 in short-term memory. BBS. https://doi.org/10.1017/s0140525x01003922 — WM about 4 chunks.
- R14. Tislar & Steelman (2021). Inconsistent seduction: seductive details review. Brain & Behavior. https://doi.org/10.1002/brb3.2322 — reports Rey 2012 harm sizes but inconsistent findings across studies.
- R15. Scheibehenne, Greifeneder & Todd (2010). Can there ever be too many options? JCR. https://doi.org/10.1086/651235 — mean choice-overload effect ≈0.
- R16. Fyfe, McNeil, Son & Goldstone (2014). Concreteness fading in mathematics and science instruction. EPR. https://doi.org/10.1007/s10648-014-9249-3 — concrete → abstract progression supports transfer.
- R17. Chi & Wylie (2014). The ICAP framework. Educational Psychologist. https://doi.org/10.1080/00461520.2014.965823 — Interactive > Constructive > Active > Passive.
- R18. Koenecke et al. (2020). Racial disparities in automated speech recognition. PNAS. https://doi.org/10.1073/pnas.1915768117 — WER 0.35 vs 0.19.
- R19. Stivers et al. (2009). Universals and cultural variation in turn-taking. PNAS. https://doi.org/10.1073/pnas.0903616106 — response offsets peak within about 200 ms across 10 languages.
- R20. Ginns (2005). Meta-analysis of the modality effect. Learning & Instruction. https://doi.org/10.1016/j.learninstruc.2005.07.001 — d=0.72; system-paced 0.93; learner-paced −0.14.
- R21. Adesope, Trevisan & Sundararajan (2017). Rethinking the use of tests. RER. https://doi.org/10.3102/0034654316689306 — practice testing g≈0.61.
- R22. Sailer & Homner (2020). The gamification of learning: a meta-analysis. EPR. https://doi.org/10.1007/s10648-019-09498-w — cognitive g=0.49, motivation 0.36, behaviour 0.25; only cognitive survives in rigorous studies.
- R23. Hamari, Koivisto & Sarsa (2014). Does gamification work? HICSS. https://doi.org/10.1109/hicss.2014.377 — mostly positive, context-dependent; novelty caveat.
- R24. VanLehn (2011). Relative effectiveness of human tutoring, ITS and other tutoring. Educational Psychologist. https://doi.org/10.1080/00461520.2011.611369 — step-based ITS d≈0.76 vs human 0.79.
- R25. Sinha & Kapur (2021). When problem solving followed by instruction works: productive failure. RER. https://doi.org/10.3102/00346543211019105 — g=0.36 conceptual/transfer; procedural ≈−0.03.
- R26. Koedinger & Aleven (2007). Exploring the assistance dilemma. EPR. https://doi.org/10.1007/s10648-007-9049-0 — how much to help remains unresolved.
- R27. Pardos & Bhandari (2024). ChatGPT-generated help produces learning gains equivalent to human-authored help. PLOS ONE. https://doi.org/10.1371/journal.pone.0304013 — equivalence at N=274.
- R28. Lenzner, Schnotz & Müller (2013). The role of decorative pictures in learning. Instructional Science. https://doi.org/10.1007/s11251-012-9256-z — neutral on learning; better mood and lower perceived difficulty.
- R29. Schneider, Nebel & Rey (2016). Decorative pictures and emotional design in multimedia learning (PDF). https://nschwartz.yourweb.csuchico.edu/Schneider%20et%20al.%20(2016)%20decorative%20pictures.pdf — emotional design effects on motivation and learning.
- R30. Rojo, King, Gersib & Bryant (2022). Rational number interventions for students with mathematics difficulties: a meta-analysis. RASE. https://doi.org/10.1177/07419325221105520 — large intervention effects; visual representations common.
- R31. IES/WWC (2010). Developing effective fractions instruction (practice guide). https://ies.ed.gov/ncee/WWC/Docs/PracticeGuide/fractions_pg_093010.pdf — recommends number lines and visual models.
- R36. Reinwein (2012). Does the modality effect exist? And if so, which modality effect? J Psycholinguist Res. https://doi.org/10.1007/s10936-011-9180-4 — reanalysis: smaller modality effect (≈0.38; ≈0.20 after publication-bias correction, as reported in abstract/search).
- R32. Rodrigues et al. (2022). Gamification suffers from the novelty effect but benefits from familiarization. IJETHE. https://doi.org/10.1186/s41239-021-00314-6 — gamification effects decline then recover over time.

Standards / specs
- R33. Material 3 motion: easing and duration tokens. https://m3.material.io/styles/motion/easing-and-duration/tokens-specs
- R34. MDN, prefers-reduced-motion. https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion
- R35. W3C, Understanding WCAG 2.2 SC 2.3.3 Animation from Interactions. https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html

AI / LLM research (arXiv or peer-reviewed)
- R37. Zheng et al. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. https://arxiv.org/abs/2306.05685 — position, verbosity and self-enhancement biases; mitigations.
- R38. Lewis et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. NeurIPS. https://arxiv.org/abs/2005.11401 — retrieval improves factuality and specificity.
- R39. Pardos & Bhandari (2023). Learning gain differences between ChatGPT and human tutor generated algebra hints. https://arxiv.org/abs/2302.06871 — 30% of ChatGPT hints failed QC; human hints produced larger gains.
- R40. Wang et al. (2024). Tutor CoPilot: a human-AI approach for scaling real-time expertise. https://arxiv.org/abs/2410.03017 — +4 pp mastery in an RCT.
- R41. Google (2024). Towards responsible development of generative AI for education (LearnLM-Tutor). https://arxiv.org/abs/2407.12687 — multi-method pedagogical evals.

UX research
- R42. NN/g, Mobile tutorials: wasted effort or efficiency boost? https://www.nngroup.com/articles/mobile-tutorials/ — 70 users, no task-success gain from tutorials.
- R43. NN/g, Mobile-app onboarding: components and techniques. https://www.nngroup.com/articles/mobile-app-onboarding/ — skip onboarding when possible.
- R44. NN/g, Onboarding tutorials vs contextual help. https://www.nngroup.com/articles/onboarding-tutorials/ — prefer contextual help.
- R63. NN/g, Designing effective carousels. https://www.nngroup.com/articles/designing-effective-carousels/ — carousels often overlooked.
- R64. NN/g, Auto-forwarding carousels annoy users. https://www.nngroup.com/articles/auto-forwarding/
- R65. NN/g, Mobile carousels. https://www.nngroup.com/articles/mobile-carousels/ — low discoverability; prioritise the first items.
- R66. Baymard, Homepage carousel. https://baymard.com/research-articles/homepage-carousel — about half have issues; static alternatives.

Company / engineering / design
- R45. Brilliant, Hand-crafted, machine-made. https://blog.brilliant.org/hand-crafted-machine-made/ — learn by doing; humans design progression.
- R46. Brilliant, Solving equations. https://blog.brilliant.org/solving-equations/ — problem at the edge of understanding, name it afterwards.
- R47. Brilliant, Visual algebra. https://blog.brilliant.org/visual-algebra/ — multiple representations.
- R48. Brilliant, About (Koji tutor). https://brilliant.org/about/ — asks rather than tells (company claim).
- R49. Khan Academy, 7-step prompt engineering for Khanmigo. https://blog.khanacademy.org/khan-academys-7-step-approach-to-prompt-engineering-for-khanmigo/ — repetition complaints led to prompt rewrites.
- R50. Khan Academy, Khanmigo math computation and tutoring updates. https://blog.khanacademy.org/khanmigo-math-computation-and-tutoring-updates/ — human-written steps in context improve accuracy; graphics weakness.
- R51. Duolingo, Duolingo Max. https://blog.duolingo.com/duolingo-max/ — Explain My Answer and Roleplay on GPT-4.
- R52. Duolingo, World character visemes (Rive). https://blog.duolingo.com/world-character-visemes/
- R60. Netflix TechBlog, Artwork personalization. https://netflixtechblog.com/artwork-personalization-at-netflix-c589f074ad76 — contextual bandits for artwork.
- R61. Netflix TechBlog, GenPage: generative homepage construction. https://netflixtechblog.com/genpage-towards-end-to-end-generative-homepage-construction-at-netflix-77146fba8a08 — personalised 2D homepage.
- R68. Duolingo, New home screen design. https://blog.duolingo.com/new-duolingo-home-screen-design/ — tree → path to reduce confusion.
- R70. Duolingo, Video Call. https://blog.duolingo.com/video-call/
- R71. Duolingo, Video Call research report. https://blog.duolingo.com/video-call-research-report/ — company-reported speaking gains.
- R72. OpenAI, Speak customer story. https://openai.com/index/speak-connor-zwick/ — realtime voice for language practice.
- R75. OpenAI, Prompt caching guide. https://developers.openai.com/api/docs/guides/prompt-caching — up to about 90% input-cost and about 80% latency reduction.
- R56. Irrational Labs, Headspace doubled course starts. https://irrationallabs.com/case-studies/headspace-doubled-course-starts/ — 31% → 63% starts; active days unchanged.
- R57. Purchasely, Headspace behavioural-science onboarding experiment. https://www.purchasely.com/blog/headspace-behavioral-science-onboarding-experiment
- R73. Kokoro-82M TTS model card. https://huggingface.co/hexgrad/Kokoro-82M — Apache-2.0, 82M parameters.
- R74. faster-whisper. https://github.com/SYSTRAN/faster-whisper — CTranslate2 Whisper, int8 CPU.

Teardowns / opinion / news / data
- R53. Appcues GoodUX, Duolingo onboarding. https://goodux.appcues.com/blog/duolingo-user-onboarding — gradual engagement.
- R54. Page Flows, Duolingo iOS onboarding recording. https://pageflows.com/post/ios/onboarding/duolingo/ — lesson around 1:27, account around 3:18.
- R55. Krystal Higgins, Duolingo 2013 first-run. https://first-run-ux.kryshiggins.com/duolingo-app-2013/ — critique of forced signup.
- R58. ScreensDesign, Brilliant onboarding showcase. https://screensdesign.com/showcase/brilliant-learn-by-doing — account plus paywall before the first lesson.
- R59. K. Vaidya, Duolingo onboarding case study (Medium). https://kittuvaidyakv.medium.com/duolingo-onboarding-product-feature-case-study-804e597a19f9 — deferred-signup tradeoff (opinion).
- R62. N. Lee, Coursera unified hub system. https://www.nancylee.design/coursera-unified-hub-system — catalogue hubs (designer case study).
- R67. E. Runyon, Carousel interaction stats. https://erikrunyon.com/2013/01/carousel-interaction-stats/ — about 1% click, 84% on slide 1.
- R69. NBC News, Duolingo redesign interview. https://www.nbcnews.com/tech/tech-news/duolingos-update-redesign-luis-von-ahn-interview-rcna44655 — user backlash over the path.
- R76. Appcues GoodUX, Headspace onboarding sequence. https://goodux.appcues.com/blog/headspaces-mindful-onboarding-sequence — three questions, routine anchoring.
- R77. UX Collective, Interactive play for learning math and science online. https://uxdesign.cc/the-key-to-learning-math-and-science-online-is-interactive-play-6ea68ce167fe — opinion.

Added 2026-09-24 (H14/H15; DOIs verified via Crossref, URLs HTTP 200)
- R78. Schroeder, Adesope & Gilbert (2013). How effective are pedagogical agents for learning? A meta-analytic review. JECR. https://doi.org/10.2190/ec.49.1.a — g=0.19 (43 comparisons, N=3,088); text > narration; K-12 > post-secondary.
- R79. Castro-Alonso, Wong, Adesope & Paas (2021). Effectiveness of multimedia pedagogical agents predicted by diverse theories: a meta-analysis. EPR. https://doi.org/10.1007/s10648-020-09587-1 — g+=0.20 (32 effects, 2012–2019).
- R80. Moreno, Mayer, Spires & Lester (2001). The case for social agency in computer-based teaching. Cognition & Instruction. https://doi.org/10.1207/s1532690xci1902_02 — agent group better on transfer and interest; the agent's image alone had no effect; interactivity and voice did.
- R81. Lester et al. (1997). The persona effect: affective impact of animated pedagogical agents. CHI. https://doi.org/10.1145/258549.258797 — learners perceive lifelike agents as helpful and credible (affective).
- R82. Ginns (2006). Integrating information: a meta-analysis of the spatial contiguity and temporal contiguity effects. L&I. https://doi.org/10.1016/j.learninstruc.2006.10.001 — d≈0.85, 50 studies.
- R83. Chandler & Sweller (1992). The split-attention effect as a factor in the design of instruction. BJEP. https://doi.org/10.1111/j.2044-8279.1992.tb01017.x — physically integrating related sources reduces extraneous load.
- R84. Moreno & Mayer (2000). A coherence effect in multimedia learning: minimizing irrelevant sounds. JEP. https://doi.org/10.1037/0022-0663.92.1.117 — irrelevant sounds/music hurt learning.
- R85. "One Click Away: AI tutoring with Khanmigo in a two-year school experiment" (EdWorkingPaper ai26-1551). https://edworkingpapers.com/sites/default/files/ai26-1551.pdf — tutor sits beside the exercise; 39.4% of messages were bare answers.
- R86. Duolingo, Explain My Answer is now free. https://blog.duolingo.com/explain-my-answer-now-free/ — inline, learner-chosen feedback after an exercise.

Repo evidence (not counted as external sources): `domains/dsa/sliding-window/golden/*.md`, `conformance-oracle.v0.1.json`, `src/study_os/pir/sliding_window.py`, `docs/webapp/LLM_ROUTE.md`.
