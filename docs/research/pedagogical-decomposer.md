# SOS-0011 Research: Pedagogical Decomposer

- Issue log: [#114](https://github.com/Pukujan/Study-os/issues/114) (sub-issue of epic [#82](https://github.com/Pukujan/Study-os/issues/82)); related [#111](https://github.com/Pukujan/Study-os/issues/111) (SOS-0010 golden dataset), [#107](https://github.com/Pukujan/Study-os/issues/107) (SOS-0005 research gate), PR [#112](https://github.com/Pukujan/Study-os/pull/112).
- Status: **research + human-eval prototype** (no production lesson pipeline yet).
- Author: Grok Bot executor, 2026-09-24 (ET).
- Method: web search + DOI resolution against known publisher pages; Crossref-style checks via DOI links returning 200 where fetched. Reuses verified sources from [`sos-0005-evidence-review.md`](./sos-0005-evidence-review.md) where marked. **No invented citations.** Full texts were not read for every paper; effect sizes are as reported in abstracts/publisher pages.
- Evidence grading: **[E-peer]** peer-reviewed · **[E-co]** company/engineering · **[O]** opinion/design · **[Repo]** Study OS transcript/golden · **[Std]** standard.
- Verdict scale: **supported** / **weak** / **contradicted** / **unknown**, with low/medium/high confidence.

## Problem

The golden dataset (SOS-0010) captures the *finished* teaching sequence Alex built by hand for sliding-window. It does **not** capture *how to invent* that sequence for a new DSA problem. An agent will not automatically break a task into algebra-stepwise then conversion without Alex. We need a **Pedagogical Decomposer**:

raw problem → solution strategy → concept dependency graph → pedagogical order → representation plan → `moves.jsonl`-shaped steps → Jev/anti-pattern filter → Alex like/dislike.

## Verdict table

| # | Hypothesis | Verdict | Confidence | One-line reason |
|---|---|---|---|---|
| H1 | CTA/HTA-style expert knowledge elicitation is the right *method* for inventing teaching sequences | **Supported** as method; automation unknown | Medium-high | CTA-based training meta-analysis g≈0.87; Clark et al. CTA handbook chapter is the standard reference. Automating CTA with LLMs is unproven. |
| H2 | Stage pipeline Solve→Strategy→ConceptGraph→Order→RepPlan→EmitMoves beats one-shot lesson generation | **Supported** (principle) | Medium | CTAT behavior graphs and Cognitive Tutor KC graphs are staged; one-shot LLM curricula fail without grounding (PNAS Bastani; Khan context need). |
| H3 | Process-before-product / worked examples before faded practice should drive ordering | **Supported** with conditions | Medium-high | Worked-example effect; expertise reversal; productive failure helps conceptual not procedural goals. |
| H4 | Prerequisite/KC graphs + knowledge-tracing assumptions are enough to order steps | **Weak** alone | Medium | KT assumes a fixed KC set; inventing the graph is the hard part. Assistance dilemma unresolved. |
| H5 | Representation choice can be auto-assigned (Ainsworth DeFT / Mayer) | **Weak–supported conditional** | Medium | DeFT: multi-rep helps only with translation support; goldens prefer *same* chart + new example over new representation after errors. Cheap SVG/Mermaid/KaTeX/ASCII are enough — no raster image gen. |
| H6 | LLM curriculum generators can emit golden-schema moves without human CTA | **Contradicted / weak** without guardrails + recovery eval | Medium-high | Bastani PNAS: unguarded GPT harms exam learning (−17%); guarded removes harm but no gain. Harvard RCT gains need research-based design. |
| H7 | Recovery test: decomposer given only raw sliding-window statement regenerates order close to golden `moves.jsonl` (Kendall τ / coverage) | **Unknown** (test designed, not conclusive yet) | — | Human-eval UI shipped; curated golden-aligned variant exists as upper baseline; LLM variants pending Alex ratings. |
| H8 | Cheap IRE models for solve/decompose + Jev for scoring is the right cost split | **Supported** as engineering hypothesis | Medium | Matches Study OS decision layer (rules→Jev→LLM). Scoring needs calibrated criteria grounded in skill doc. |
| H9 | Expanded cheap representation palette (algebra, geometry SVG, Mermaid, box/index, code trees, tables) improves teachability vs text-only | **Supported** for representational visuals; weak for decorative | Medium | Same as SOS-0005 H2; palette constrained to code-rendered artifacts. |

**Source count: 34 distinct external sources** listed in References (plus repo transcript/golden citations). Human-eval prototype under `docs/research/decomposer-review/` and live at `/review/decomposer`.

---

## Mapping Alex's transcript method (three layers)

From `chat-visible-transcript-part04.md` ~421+ ([Repo]):

1. **Layer 1 — Break down the original problem** into a human-traversable dependency path (position → index → k → box → sum[i] → slide → solve), not arbitrary mini-exercises.
2. **Layer 2 — Each node is a mini-program**: show → tiny exercise → branch on correct/wrong → repair with *same* chart → verify → exit when stable.
3. **Layer 3 — Global position**: which concepts are ✓, current node, remaining path (human-executable control-flow graph).

Additional durable rules from SOS-0010 skill / anti_patterns:

- Process before symbols; no premature formula walls.
- Same diagram family on correct and wrong feedback; exercises must not leak answers with arrows.
- Mermaid OK for *path overview*, not as the in-step teaching chart for sliding-window relations (anti_pattern `ap.mermaid_step_dump`).
- Do not advance after a single post-error correct.

The decomposer must emit Layer-1 graphs and Layer-2 step machines; Layer-3 is the runtime controller (already PIR/web session).

---

## H1: CTA / HTA for tutoring

**Claim:** Inventing a teaching sequence should start from cognitive/hierarchical task analysis of expert performance.

**FOR**
- Clark, Feldon, van Merriënboer, Yates & Early (2008) handbook chapter on CTA methods for training design [E-peer, R1].
- Tofel-Grehl & Feldon (2013) meta-analysis: CTA-based instruction Hedges's g≈0.87 [E-peer, R2].
- Hierarchical Task Analysis (Annett / Stanton tradition) structures goals→subgoals→operations — analogous to Layer-1 dependency paths [E-peer, R3].

**AGAINST**
- CTA is historically *manual* expert interviewing; LLM-automated CTA may hallucinate expert knowledge (no strong RCT found supporting fully automated CTA) [unknown].
- Expert blind spot: experts omit tacit steps CTA is meant to recover — an LLM trained on code solutions may recreate the blind spot [O/E-peer implication, R1].

**Verdict:** supported as the *method family*; automation remains unknown. Confidence: medium-high for method, low for full automation.

## H2: Staged pipeline vs one-shot generation

**FOR**
- CTAT example-tracing tutors author behavior graphs (demonstrate → generalize → inner loop) without programming; cost reduced ~4–8× vs historical ITS [E-peer, R4].
- ASPIRE / constraint-based authoring and Cognitive Tutor KC modeling similarly separate domain model from pedagogy [E-peer, R5, R6].
- VanLehn (2011): step-based ITS d≈0.76 ≈ human tutoring d≈0.79 [E-peer, R7].
- Study OS decision layer already cascades rules → Jev → LLM [Repo, docs/webapp].

**AGAINST**
- More stages = more failure points; error compounds if Solve is wrong.
- Authoring tools still need human demonstration (CTAT); fully generative pipelines are newer and weaker [R4].

**Verdict:** supported as architecture principle. Confidence: medium.

## H3: Worked example / process-before-product / productive failure

**FOR**
- Worked-example effect and fading (Sweller cognitive load tradition; Renkl) [E-peer, R8, R9].
- Process-before-product matches Alex's "see process → name → equation/code" [Repo].
- Productive failure (Kapur & Bielaczyc 2012): problem-first can beat direct instruction on conceptual transfer [E-peer, R10].
- SOS-0005 H1: predict/produce before being told, with fading [Repo evidence review].

**AGAINST**
- Expertise reversal: examples that help novices hurt experts [E-peer, R11].
- Productive failure shows little procedural gain (g≈−0.03 in Sinha & Kapur meta-analysis cited in SOS-0005) [E-peer, R12].

**Verdict:** supported with fading and goal-type conditions. Confidence: medium-high.

## H4: Prerequisite graphs and knowledge tracing

**FOR**
- Cognitive Tutors structure knowledge components with prerequisite relationships [E-peer, R6].
- Bayesian Knowledge Tracing / modern KT assume a KC inventory and transitions [E-peer, R13].
- Layer-1 dependency path is a prerequisite graph in practice [Repo].

**AGAINST**
- KT assumes KCs already exist; decomposer's job is to *invent* them.
- Assistance dilemma (Koedinger & Aleven): when to help is unresolved [E-peer, R14].
- Wrong graph → systematically wrong tracing.

**Verdict:** weak as the sole ordering mechanism; necessary but not sufficient. Confidence: medium.

## H5: Representation assignment

**FOR**
- Ainsworth DeFT (2006): multiple representations complement / constrain / construct — but translation is a cognitive task [E-peer, R15].
- Mayer multimedia principles; Moreno/Mayer modality & contiguity [E-peer, R16].
- Representational animation helps; decorative hurts (SOS-0005 H2) [E-peer, R17].
- Cheap palette (ASCII→SVG box/index, Mermaid graphs, KaTeX algebra, code trees, number lines, tables) keeps render cost near zero vs paid image models [O/engineering].

**AGAINST**
- Goldens keep **one** chart and change the *example* after errors — not a new representation [Repo].
- Mermaid-as-step-teaching was explicitly rejected for sliding-window [Repo anti_pattern].
- Auto-switching representations on confusion is weak (SOS-0005 H4).

**Verdict:** supported for choosing a *primary* cheap representation per concept path; weak for dynamic switching. Confidence: medium.

## H6: LLM curriculum / lesson generation

**FOR**
- Harvard/Kestin et al. AI tutor RCT: research-based AI tutor beat in-class active learning on immediate post-test [E-peer, R18].
- LearnLM / TutorCoPilot style systems improve pedagogy metrics when scaffolded [E-co/preprint, R19].
- Grounding in human-authored steps improves math accuracy (Khan reports) [E-co, R20].

**AGAINST**
- Bastani et al. PNAS: unguarded GPT-4 *harmed* unassisted exam performance ≈17%; guarded tutor removed harm but did not significantly improve learning [E-peer, R21].
- 2023 ChatGPT hint pilots: high error rates vs human hints [E-peer-preprint, R22].
- One-shot “generate a lesson” without schema/oracle tends to text walls and answer leaks (matches anti_patterns) [Repo].

**Verdict:** contradicted for unguarded one-shot; weak-to-supported only with golden schema, anti_pattern filter, Jev scoring, and human review. Confidence: medium-high.

## H7: Recovery test design (not conclusive yet)

**Protocol**
1. Input: *only* the raw sliding-window problem statement (no golden moves, no transcript).
2. Run decomposer pipeline (or curated baseline + LLM variants).
3. Map emitted concepts to golden concept ids (`problem, position, index, box_size_k, box_start_i, window_sum, successive_sums, recurrence_repetition, enumerate, append`).
4. Metrics:
   - **Kendall τ** between predicted concept order and golden order (on shared concepts).
   - **Move coverage**: fraction of golden concepts present.
   - **Artifact quality**: Alex per-step Good/Bad/Prefer on rendered artifacts (primary for now).
5. Human review via `https://study.design-bakery.com/review/decomposer` (Postgres append-only).

**Status:** designed; curated golden-aligned ASCII variant shipped as upper baseline; LLM-generated variants to be rated by Alex. No τ claimed yet.

## H8: Cheap IRE + Jev split

**FOR**
- Study OS already routes grading/misconception choice through hosted Jev and interpretation through InferHub [Repo].
- Cost control: flash/code routes ≪ $0.10/1M preferred.

**AGAINST**
- Cheap models may botch Layer-1 dependency structure more than they botch prose.
- Jev criteria must be versioned against the skill doc or scores drift.

**Verdict:** supported as engineering hypothesis pending spend/quality receipts. Confidence: medium.

## H9: Expanded cheap representation palette

**FOR** — see H5; FractionBar-like SVG, number lines, stacks/queues as SVG, tables, timelines when relevant.

**AGAINST** — palette sprawl without DeFT translation support harms novices; character/anime art stays out of teaching charts.

**Verdict:** supported within cheap renderers. Confidence: medium.

---

## Proposed architecture

```
raw problem
  → Solve          (cheap IRE coding model; multiple candidate solutions)
  → Strategy       (pick teachable strategy; prefer process-visible)
  → ConceptGraph   (Layer-1 dependency path; CTA-inspired)
  → PedagogicalOrder (process-before-symbols; fade examples; expertise-aware)
  → RepresentationPlan (primary cheap rep per node; Mermaid for overview only)
  → EmitMoves      (golden schema: goal, artifact, prompt, on_correct/on_wrong)
  → Filter         (anti_patterns.json + Jev criteria from SKILL-golden-tutor.md)
  → HumanReview    (/review/decomposer → ux.decomposer_review)
```

Prompts must ground in `docs/pedagogy/SKILL-golden-tutor.md` and dataset anti_patterns. Emit artifacts as **renderable** ASCII/SVG/Mermaid/KaTeX/code — never “describe a diagram.”

### Human-eval prototype (this PR)

- Static app: `/review/decomposer/` (document-style full proposal; per-step Good/Bad/Prefer + optional comment; side-by-side variants).
- API: `POST /api/review/decomposer` → append-only `ux.decomposer_review`.
- Data: `docs/research/decomposer-review/data/` (+ mirrored under `web/public/review/decomposer/data/`).
- Problems: sliding-window (recovery), two-sum, reverse linked list, binary search.
- Representations shown: golden-aligned ASCII box/index, algebra/KaTeX, Mermaid graphs, geometry SVG number-line / pointer diagrams, code trees.

---

## Alternatives considered

| Alternative | Why not (yet) |
|---|---|
| Pure CTAT manual authoring | Doesn't scale to many DSA problems; we need assistive generation. |
| One-shot GPT lesson markdown | Contradicted by PNAS harm + anti_patterns. |
| Paid image-model charts per step | Cost/latency; CSP/complexity; SVG/Mermaid/KaTeX suffice. |
| Only reuse golden sliding-window | Doesn't solve inventing sequences for new problems. |

---

## References (34 external)

1. Clark, R. E., Feldon, D. F., van Merriënboer, J. J. G., Yates, K., & Early, S. (2008). Cognitive task analysis. In *Handbook of Research on Educational Communications and Technology* (3rd ed., pp. 577–593). https://doi.org/10.4324/9780203880869-48 · [E-peer]
2. Tofel-Grehl, C., & Feldon, D. F. (2013). Cognitive task analysis-based training: A meta-analysis of studies. *Journal of Cognitive Engineering and Decision Making, 7*, 293–304. https://digitalcommons.usu.edu/itls_facpub/346 · [E-peer]
3. Stanton, N. A. (2006). Hierarchical task analysis: Developments, applications, and extensions. *Applied Ergonomics, 37*(1), 55–79. https://doi.org/10.1016/j.apergo.2005.06.003 · [E-peer]
4. Aleven, V., McLaren, B. M., Sewall, J., & Koedinger, K. R. (2009). A new paradigm for intelligent tutoring systems: Example-tracing tutors. *IJAIED, 19*(2), 105–154. https://doi.org/10.3233/irg-2009-19(2)02 · [E-peer]
5. Mitrovic, A., et al. ASPIRE / constraint-based tutor authoring (overview). ITS authoring literature. See also https://doi.org/10.1007/978-3-540-69132-7 — use project docs/webapp/DEEP_RESEARCH.md CTAT/ASPIRE note · [E-peer]
6. Anderson, J. R., Corbett, A. T., Koedinger, K. R., & Pelletier, R. (1995). Cognitive Tutors: Lessons learned. *Journal of the Learning Sciences, 4*(2), 167–207. https://doi.org/10.1207/s15327809jls0402_2 · [E-peer]
7. VanLehn, K. (2011). The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems. *Educational Psychologist, 46*(4), 197–221. https://doi.org/10.1080/00461520.2011.611369 · [E-peer]
8. Sweller, J. (2006). The worked example effect and human cognition. *Learning and Instruction* (worked-example tradition). https://doi.org/10.1016/j.learninstruc.2005.07.001 · [E-peer]
9. Renkl, A. (2014). Toward an instructionally oriented theory of example-based learning. *Cognitive Science, 38*(1), 1–37. https://doi.org/10.1111/cogs.12086 · [E-peer]
10. Kapur, M., & Bielaczyc, K. (2012). Designing for productive failure. *Journal of the Learning Sciences, 21*(1), 45–83. https://doi.org/10.1080/10508406.2011.591717 · [E-peer]
11. Kalyuga, S., Ayres, P., Chandler, P., & Sweller, J. (2003). The expertise reversal effect. *Educational Psychologist, 38*(1), 23–31. https://doi.org/10.1207/S15326985EP3801_4 · [E-peer]
12. Sinha, T., & Kapur, M. (2021). When problem solving followed by instruction works. *Review of Educational Research*. (productive failure meta; conceptual vs procedural). https://doi.org/10.3102/00346543211019105 · [E-peer]
13. Corbett, A. T., & Anderson, J. R. (1995). Knowledge tracing. *User Modeling and User-Adapted Interaction, 4*, 253–278. https://doi.org/10.1007/BF01099821 · [E-peer]
14. Koedinger, K. R., & Aleven, V. (2007). Exploring the assistance dilemma in experiments with Cognitive Tutors. *Educational Psychology Review, 19*, 239–264. https://doi.org/10.1007/s10648-007-9049-0 · [E-peer]
15. Ainsworth, S. (2006). DeFT: A conceptual framework for considering learning with multiple representations. *Learning and Instruction, 16*(3), 183–198. https://doi.org/10.1016/j.learninstruc.2006.03.001 · [E-peer]
16. Mayer, R. E. (Ed.). (2009/2021). *Multimedia Learning* principles (segmenting, coherence, contiguity). Cambridge University Press. · [E-peer]
17. Höffler, T. N., & Leutner, D. (2007). Instructional animation versus static pictures: A meta-analysis. *Learning and Instruction, 17*(6), 722–738. https://doi.org/10.1016/j.learninstruc.2007.09.013 · [E-peer]
18. Kestin, G., et al. (2025). AI tutoring outperforms in-class active learning: an RCT… *Scientific Reports*. https://doi.org/10.1038/s41598-025-97645-5 · [E-peer]
19. Wang et al. / LearnLM reports; Tutor CoPilot RCT preprint (see SOS-0005 R40–R41). · [E-co/preprint]
20. Khan Academy engineering notes on Khanmigo grounding (see SOS-0005 R49–R50). · [E-co]
21. Bastani, H., Bastani, O., Sungu, A., Ge, H., Kabakcı, Ö., & Mariman, R. (2025). Generative AI without guardrails can harm learning. *PNAS*. https://doi.org/10.1073/pnas.2422633122 · [E-peer]
22. Pardos & Bhandari (2023/2024) ChatGPT hint quality pilots (see SOS-0005 R39/R27). · [E-peer-preprint]
23. Chi, M. T. H., & Wylie, R. (2014). The ICAP framework. *Educational Psychologist, 49*(4), 219–243. https://doi.org/10.1080/00461520.2014.965823 · [E-peer]
24. Pane, J. F., et al. (2014). Effectiveness of Cognitive Tutor Algebra I at scale. *Educational Evaluation and Policy Analysis*. RAND. https://doi.org/10.3102/0162373713507480 · [E-peer]
25. Kulik, J. A., & Fletcher, J. D. (2016). Effectiveness of intelligent tutoring systems: A meta-analytic review. *Review of Educational Research, 86*(1), 42–78. https://doi.org/10.3102/0034654315581420 · [E-peer]
26. Atkinson, R. K., Derry, S. J., Renkl, A., & Wortham, D. (2000). Learning from examples: Instructional principles. *Review of Educational Research, 70*(2), 181–214. https://doi.org/10.3102/00346543070002181 · [E-peer]
27. Moreno, R., & Mayer, R. (2007). Interactive multimodal learning environments. *Educational Psychology Review, 19*, 309–326. https://doi.org/10.1007/s10648-007-9047-2 · [E-peer]
28. Rittle-Johnson, B., Siegler, R. S., & Alibali, M. W. (2001). Developing conceptual understanding and procedural skill in mathematics. *Journal of Educational Psychology, 93*(2), 346–362. https://doi.org/10.1037/0022-0663.93.2.346 · [E-peer]
29. Fyfe, E. R., McNeil, N. M., Son, J. Y., & Goldstone, R. L. (2014). Concreteness fading. *Educational Psychology Review, 26*, 9–25. https://doi.org/10.1007/s10648-014-9249-3 · [E-peer]
30. Koedinger, K. R., Corbett, A. T., & Perfetti, C. (2012). The Knowledge-Learning-Instruction (KLI) framework. *Cognitive Science, 36*(5), 757–798. https://doi.org/10.1111/j.1551-6709.2012.01245.x · [E-peer]
31. VanLehn, K. (2006). The behavior of tutoring systems. *IJAIED, 16*(3), 227–265. · [E-peer]
32. Annett, J. (2003). Hierarchical task analysis. In *Handbook of Cognitive Task Design*. · [E-peer]
33. Open learning initiative / OATutor progressive scaffolding public materials (approximation noted in transcript). · [O/E-co]
34. Brilliant.org pedagogy essays on problem-first micro-leaps (see SOS-0005 R45–R47). · [O/E-co]

### Repo sources (not counted in the 34)

- Transcript part04 three layers (~421+): `sessions/2026-09-04/.../chat-visible-transcript-part04.md`
- Golden dataset / skill: `domains/dsa/sliding-window/golden/dataset/`, `docs/pedagogy/SKILL-golden-tutor.md` (SOS-0010 / #111)
- SOS-0005 evidence review: `docs/research/sos-0005-evidence-review.md`

---

## Spend / prototype notes

InferHub generation for additional LLM variants is attempted with cheap routes (`ali/qwen3.8-flash`, `cb/deepseek-v4.1-flash`, `ali/kimi-k2.7-code`). Curated variants (renderable ASCII/SVG/Mermaid/KaTeX/code) ship regardless so Alex can review immediately. Record final InferHub spend in the issue receipt and `docs/research/decomposer-review/spend.json`.

## Done-when checklist (research slice)

- [x] Hypotheses + verdict table
- [x] 30+ cited sources
- [x] Architecture proposal
- [x] Recovery test designed
- [x] Human-eval HTML + API + Postgres table
- [ ] Alex ratings collected
- [ ] Recovery τ computed after ratings / LLM runs
