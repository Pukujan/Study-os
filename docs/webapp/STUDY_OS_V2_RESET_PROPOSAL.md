# Study OS v2 — end-to-end experience reset (proposal)

**Status:** Proposal for owner review; no implementation, migration, or deploy authorization.  
**Tracker:** [#204](https://github.com/Pukujan/Study-os/issues/204)  
**Scope:** Auth/entry, navigation, problem selection, explanation quality, problem decomposition, ontology/linguistic control, algebra/graphs, interaction, feedback and AI use.  
**Based on:** Study OS default-branch source inspection and the owner's October 8 feedback, not a live user-test verdict.

## Decision

**Rebuild the learner journey and teaching core, but do not rewrite the entire repository or erase its evidence.** Ship a small versioned v2 path behind a flag, prove it with a complete learner session, then migrate one feature at a time. The existing Big O sticks-and-boxes game is an approved interaction example, not a ready-made curriculum or a reason to preserve the current surrounding chrome.

Treat this as a *product-system redesign*, not a CSS facelift and not a model upgrade. A fresher agent context may help reasoning, but no model can compensate for undefined concepts, unclear semantics, inconsistent representations or a missing evaluation gate.

## Inspection findings, without overstating certainty

| Area | Inspected evidence | Problem / uncertainty |
| --- | --- | --- |
| Entry | `web/src/pages/Try.tsx`, `web/src/pages/Login.tsx`, `web/src/App.tsx` | Signed-out hero's primary action starts the first hardcoded fractions lesson. There are both legacy `/lesson/:id` and newer `/play/:id` routes. This design needs an end-to-end guest/account/navigation audit, not a login-box restyle. |
| Navigation | `web/src/pages/HomeLanes.tsx`, `web/src/router.ts`, `web/src/pages/Player.tsx` | Lesson-first routes, guest state, resume and backtracking need an explicit user journey with real-device smoke tests. |
| Visual hierarchy | `web/src/styles.css`, `web/src/visuals/TeachRenderBox.module.css`, `web/src/visuals/SticksBoxesComplexity.module.css` | The shell is capped at 720px and interactive cards around 28rem; visual frames are behind a Back/Next carousel-like stepper. The learner-controlled game is too easy to subordinate to static diagram chrome. |
| AI explanation | `src/study_os/web/player/prompts/tutor.v3.md`, `src/study_os/web/player/tutor.py` | Tutor is grounded to the current step and re-render uses pre-existing frame indices. It cannot be assumed to provide new semantically proven algebra, geometry and interactive simulations for arbitrary new problems. |
| Linguistic control | `src/study_os/web/player/human_rewrite.py` | Rewrites style and length (e.g. 42-word teach budget) and removes AI-sounding phrases. It does not validate that terms, symbol bindings, or mathematical claims are correct; truncation risks dropping an essential bridge. |
| Ontology | `schemas/lesson-ir.schema.json`, concepts in lesson packs, `docs/LEARNER_MODEL_CURRICULUM_AUDIT.md` | Stable concept IDs occur, but no separately enforced terminology/ontology contract connecting symbols, learner definitions, prerequisites, misconceptions and representation invariants was identified in the inspected default-branch tree. Another repo or runtime may contain relevant work. |
| Problem decomposition | `docs/research/pedagogical-decomposer.md`, `docs/research/decomposer-review/`, `web/public/review/decomposer/`, issue #118 | Research prototype and mirrored curated/LLM variants are present; the planned `src/study_os/decomposer/` production pipeline and `tools/run_decomposer.py` were not found on main. |
| Valuable core | `web/src/visuals/SticksBoxesComplexity.tsx`, golden lesson/transcript packs, `src/study_os/pir/`, tests and evaluation contracts | Preserve the learner-controlled Big O interaction, curated knowledge, deterministic curriculum authority, provenance, and test/evidence infrastructure. Do not equate old issue status with broken functionality. |

These findings justify a proposed redesign; they do **not** certify that individual live endpoints fail. The first engineering step is a reproducible journey audit.

## Experience contract — one coherent novice journey

The v2 learner must be able to:

1. Land on a fast page that says what will happen, *try without signup*, select a subject/problem, or resume a saved session.
2. Read the **exact original problem** with a plain-language paraphrase and a visible goal. Show *given*, *unknown*, *constraints* and an example. Never replace the question with arbitrary generated marketing text.
3. See **define-before-use** vocabulary. Every token/symbol that matters has a tooltip/glossary explanation in context; synonyms resolve to the same canonical concept when appropriate.
4. Watch a single small example; trace what happens through aligned **table/box → algebra → graph → code** views. Only offer a view when the same underlying verified model supports it.
5. **Act** on the example (move a window, place a stick, adjust n, shade a fraction) and see the computed result update in all applicable views. An interaction is meaningful, not decorative.
6. Answer one explicit question unaided; after an incorrect answer, show exactly which assumption failed on the same representation, try a distinct instance, and only then change representations if needed.
7. Use Back, Resume, Change problem or Ask for help without losing progress or confusing lesson, example and assessment state; create/link an account when saving durable progress is useful.
8. Request 'What does this word mean?', 'Show me a smaller example', 'Show the algebra', 'Show the graph', or 'Let me try it' as explicit controls. AI chat is an optional supplementary channel, never the only way to change the lesson.

The default player surface should expose one main action at a time and a short, meaningful explanation. Avoid both an unbroken text wall and an unexplained game.

## Teaching core: source of truth and invariant

Make teaching semantics explicit with **four versioned objects** (names are proposed):

- **ProblemSpec**: immutable source problem, provenance, normalized givens, outputs, assumptions, constraints, solved/tested examples, expected behavior, domain/source version.
- **ConceptRegistry**: stable concept ID; novice definition and formal definition; names, aliases and forbidden ambiguous shortcuts; symbol meaning/scope; prerequisite edges; examples/nonexamples; common misconceptions; sources.
- **Decomposition**: candidate solution strategy checked by a domain oracle; acyclic dependency graph; learning order; one concept operation per step; preconditions/postconditions; assistance/assessment boundaries; supporting concepts and verification status.
- **RepresentationModel**: typed concrete instance and state transitions, exact quantities and variable bindings, algebraic derivation, graph/table specs and interaction instructions driven by **one** semantic source. Renderer-specific components must not invent numeric facts.

**Critical invariant:** for any concrete learning state, the written definition, algebra, plotted point, table value, game counter and grading oracle must agree. A change of n or of the current example must propagate to all representations or invalidate the ones that cannot be kept in sync.

An LLM may **propose** problem decompositions, analogies and alternative wording; verified solvers, schema validators, curated sources, safety checks and evaluator gates decide what can be shown. Unsupported or ambiguous problems must surface that limitation rather than fabricate a convincing visualization.

Do not use a generic text-shortening pass as the sole linguistic gate. Add checks for undefined terms, inconsistent symbols, omitted prerequisite bridges, changed assumptions, hidden answer leakage and incompatible definitions.

## First proof: Big O, end to end

Use the approved [sticks-and-boxes exemplar](https://github.com/Pukujan/Study-os/issues/185) as the central learner action. The sample is not merely 'O(n²) means fast growth':

- **Words:** `n` = number of input items/boxes; `steps` = elementary operations *in this teaching model*; `O(n²)` describes how work scales, not exact machine time. Distinguish Big O's asymptotic class from the illustrative exact count `n × n`.
- **Try:** choose n=3, O(n), and place one stick per box. Counter shows 0/3 up to 3/3.
- **Algebra:** the illustrative rule gives `W(n)=n` (three placements at n=3); for all-pairs, `W(n)=n × n` (nine placements at n=3). `W(n)` is **toy-model work**, not a benchmark of arbitrary programs.
- **Graph:** at the same n the selected model's point and class label are highlighted; graph and counters use the same n and semantics.
- **Transfer:** ask the learner to predict the next count for a different n and rule without displaying the answer; validate against the model and explain errors on the same visual.

The teacher's screen should explain the symbols *before* evaluating the learner, but not leak the upcoming probe. More prose does not imply more clarity: create bridges through interaction, algebra and consistent labels.

Then validate the same contract on **Two Sum**, **sliding window** and **comparing fractions**. If the pipeline only works on hardcoded Big O, it has not demonstrated general decomposition.

## Rebuild boundaries

**Preserve and reuse:** Postgres/account/session and evidence (subject to privacy audit), canonical exercises and goldens, the deterministic controller, auth correctness/security protections, reproducible evaluation baselines, content provenance and supported interaction engines. ACS/PCM/CGM/OIO are helpers, not lesson authority.

**Replace or simplify where proven necessary:** main route map and user journey, redundant player surfaces, presentation structure, brittle frame-selection-as-'regeneration', unverified decomposer prototype and nonsemantic rewriting of equations/terms. Do not delete the original review prototypes or tests until a replacement proves parity.

**Isolation:** ship as `/v2` or equivalent gated entry point with no production switch, no auto account migration and a rollback. Gather visual evidence at **390×844**, **768×1024**, **1440×900**, with keyboard and screen-reader coverage. Existing UX defect exploration test vocabulary may be reused.

## Gates for acceptance

1. **Journey:** first-time guest can choose a topic, complete a 1-concept example and unaided probe, sign in/link only when desired, resume in the same state, navigate back correctly. No dead ends or silent redirects.
2. **Semantic correctness:** unresolved critical term count = 0 per displayed step; same concept IDs/variable meanings across views; algebra, graph, game, table and assessment agree on sampled model state. Tests deliberately corrupt a synonym, symbol binding and equation to verify detection.
3. **Decomposition:** schema valid, DAG acyclic, concept order respects prerequisites, no unsupported content quietly shown, held-out problem differential meets or exceeds the curated baseline; no answer before probe.
4. **Experience:** no invisible interaction, keyboard usable, narrow/mobile controls readable; screenshots and real-browser interactions reviewed against the learner-approved game, not merely render snapshots.
5. **AI quality:** compare real candidate turns against pinned goldens; count fabricated symbols/facts, bad definitions, missed bridges, misleading graphs, and no-op re-explanations; report failure rates and latency. Do not claim learner efficacy from synthetic tests.
6. **Operations:** branch + PR + CI + authorized review; keep old live app until the new vertical slice is verified; no unrelated main changes or issue mass closure.

## Execution order and explicit stop line

**Phase A — evidence and journey map:** Record current guest/login/resume/navigation and the full teach→probe flow with reproducible defects and baseline screen captures. Find any external ontology/linguistic module before rebuilding it. `#204` tracks this.

**Phase B — frozen contracts:** Define versioned concept and problem/decomposition/representation shapes plus invariants and mutation tests. This must precede new model-powered content generation.

**Phase C — one production-like v2 vertical slice:** Build Big O journey with coherent terms/equations/graph/game and recovery. Keep the old player available.

**Phase D — transfer test:** Run Two Sum, sliding window and fractions through the same contract; fix failures instead of hardcoding more special cases.

**Phase E — measured migration:** Only after acceptance gates, move entry, auth, navigation and more lessons onto v2. Close old issues selectively with test and merged-PR receipts.

**Not authorized by this proposal:** hard-resetting Study OS, replacing its database, disabling validation, deleting raw evidence, merging to main, or claiming live deployment.

## Related records

[#204](https://github.com/Pukujan/Study-os/issues/204) (umbrella); [#118](https://github.com/Pukujan/Study-os/issues/118) (decomposer); [#126](https://github.com/Pukujan/Study-os/issues/126) (player), [#185](https://github.com/Pukujan/Study-os/issues/185) (reference interaction), [#160](https://github.com/Pukujan/Study-os/issues/160) (tutor latency), [#119](https://github.com/Pukujan/Study-os/issues/119) (viewport QA), [#104](https://github.com/Pukujan/Study-os/issues/104) (entry), [#165](https://github.com/Pukujan/Study-os/issues/165) (UI theme), [#203](https://github.com/Pukujan/Study-os/pull/203) (separate ACS install).
