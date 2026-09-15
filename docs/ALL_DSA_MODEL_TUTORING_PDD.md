# All-DSA generic model tutoring — Product Design Document

Status: focused product/design slice with the generic runner and acceptance
evidence now complete. The real local Luna run produced 14 plans, 210 exchanges,
and 420 learner-visible messages; the aggregate gate passed. Manual semantic
review and live held-out prompt variants remain separate follow-up work.

## Product question

Can one model-generated, schema-constrained, deterministic-guardrail tutoring
path keep fourteen DSA conversations semantically correct and learner-sized,
while preserving evidence and preventing unsupported progression?

The proof target is the corpus in
`datasets/dsa-conversation-replay.v0.1.json`: fourteen scenarios, fifteen
learner/teacher exchanges per scenario, 210 exchanges and 420 nonempty
learner-visible messages. The dataset declares lower validation minimums of ten
problems and 150 learner turns; this product gate uses the stricter handoff
target of all fourteen scenarios.

The scenarios are Two Sum, Contains Duplicate, Best Time to Buy and Sell Stock,
Valid Parentheses, Binary Search, Reverse Linked List, Merge Two Sorted Lists,
Maximum Depth of Binary Tree, BFS Shortest Path, Number of Islands, Kth Largest
Element, Sliding Window Maximum Sum, Merge Intervals, and Valid Palindrome.

## Goals

1. Give the learner one coherent tutoring experience across all fourteen
   problems. The problem-specific teaching content comes from a validated model
   `TeachingPlan`, not from fourteen deterministic lesson implementations.
2. Make each turn small, semantically grounded, and tied to the active concept:
   problem recognition, mental model, state, invariant, procedure, code, or
   terminal behavior as appropriate.
3. Let the model propose a diagnosis, learner outcome, and bounded generation,
   while deterministic code owns concept order, evidence requirements,
   assistance ceilings, representation constraints, and state transitions.
4. Bind a demonstrated outcome to verbatim text from the actual learner message.
   A learner statement of confidence or “I understand” remains self-report, not
   mastery evidence.
5. Preserve enough plan, prompt, model, schema, run, source-problem, and turn
   provenance to reconstruct every generated plan and visible turn.
6. Evaluate semantic behavior across the full corpus and metamorphic variants,
   with a per-problem pass requirement so an aggregate rate cannot hide a failed
   problem.

## Non-goals

- A production UI, hosted deployment, multi-user product, or full DSA course.
- A universal claim about learning, DSA instruction, or learners beyond
  `subject-001` and this bounded research harness.
- A fixed “learning style” classifier or permanent visual/text preference.
- A hand-authored canonical lesson, fourteen stage tables, or a controller branch
  such as `if scenario_id == ...` for any corpus problem.
- Passing hidden benchmark assertions, expected answers, or evaluator rubrics to
  the teacher model.
- Treating scripted corpus turns, generated transcripts, model diagnoses, or
  self-report as human mastery evidence.
- Making FOSSIL a runtime dependency. Study OS remains the canonical owner of
  raw learning evidence; FOSSIL remains an optional export/promotion layer.
- Image, video, or other generative media as authoritative algorithm state.

## Learner-visible behavior

The intended per-turn contract is:

1. The learner sees the problem and a short response about the current concept,
   using the representation required by the active plan. A response may vary in
   wording, examples, and layout, but not in the semantic role of a variable or
   the active concept’s invariant.
2. The response performs one bounded learning operation, such as explain,
   clarify, probe, smaller step, trace, change representation, hint, or assemble.
   It ends with a learner-sized check when the calibrated stage requires one.
3. The tutor responds to the actual learner message. Clarification, a wrong
   answer, or uncertainty does not silently advance the learner. Advancement
   requires a demonstrated outcome with a verbatim evidence quote.
4. Assistance stays at or below the plan’s `A0`/`A1`/`A2` ceiling. The tutor
   does not jump to a full implementation before the plan permits it and does
   not claim mastery.
5. Internal routing and evaluation details never appear in the learner-visible
   response. In particular, `needs_compilation`, reviewed-asset language,
   prompt hashes, trace fields, and controller internals are not product copy.
6. The final concept teaches or checks the declared terminal/base/completion
   behavior. Reaching the final concept is not itself a mastery claim.

The learner-visible contract is semantic rather than prose-exact. The current
generic response validator enforces response size, internal-marker exclusion,
required representation presence, and forbidden-variable exclusion. It does
not yet, by itself, enforce every corpus-specific anchor, question requirement,
or DSA semantic oracle. Those checks belong in the pending calibrated evaluator
and, where a deterministic runtime rule is required, a future versioned code
change.

## Product constraints and trust boundaries

`TeachingPlan` is the model-to-runtime boundary. Its current v0.1 contract
contains a source problem, ordered concepts and prerequisites, variable roles and
meanings, representation requirements, semantic invariants, completion evidence,
terminal behavior, an assistance ceiling, and immutable provenance. Structural
validation and cross-record validation happen before the plan is used.

`PromptRegistry` owns immutable prompt definitions and SHA-256 content hashes.
Prompt versions cannot be overwritten in place. The decomposition, diagnosis,
and generation roles are registered separately.

`GenericModelTutoringController` is the progression trust boundary. It accepts a
validated plan, derives the active concept and generation contract, checks
evidence and assistance, advances at most one concept, and emits a trace. It
does not write lesson prose. `validate_generated_response` checks generic
learner-visible boundaries; the model remains responsible for proposing text,
not authority.

The model may propose a plan, diagnosis, assessment, or response. It may not
silently change the active concept, variable meanings, representation contract,
assistance ceiling, progression, or mastery state. The evaluator may use hidden
calibration expectations after capture, but those expectations must remain out
of the tutor path.

Raw/private transcripts remain outside the public repository. Public artifacts
must use hashes, manifests, redacted fixtures, schemas, and reviewed derived
records. Observed, self-reported, and derived evidence remain distinct.

## Risks and mitigations

| Risk | Product mitigation |
| --- | --- |
| The model produces a plausible but wrong invariant or algorithm. | Validate plan structure and bindings; use independent calibrated semantic checks and deterministic/reference oracles where available. |
| A variable changes meaning mid-conversation. | Keep plan variables immutable; bind the active concept to allowed variables; check plan/trace continuity and visible output. |
| Helpful text becomes answer leakage or assistance dependency. | Apply plan ceilings, one-operation contracts, stage-aware calibration, fading/transfer checks, and no mastery from model output. |
| Diagnosis is mistaken for observed learner state. | Store diagnosis as derived hypothesis with source turn; require actual learner evidence for demonstrated outcomes. |
| Prompt changes destroy longitudinal comparability or overfit the fixed wording. | Content-address prompts; persist model/prompt/schema provenance; evaluate candidates across all problems and metamorphic variants. |
| An aggregate score hides a catastrophic problem failure. | Require all fourteen per-problem acceptance results, plus a 210-exchange aggregate receipt. |
| The evaluator rewards the tutor’s own style. | Keep teacher and evaluator paths separate; compare semantics, not exact prose; retain evaluator identity/version and hidden assertions outside the teacher input. |
| Benchmark replay is mistaken for human learning evidence. | Label scripted turns and replay outputs as harness evidence; do not promote them to learner outcomes or mastery. |
| Privacy or evidence boundaries drift. | Keep raw evidence private and immutable; persist provenance and hashes; do not commit full private transcripts or hidden answers. |
| A failing problem invites a scenario-specific patch. | Review genericity in code review and acceptance; reject new canonical lessons or controller branches. |

## Acceptance evidence

The following is the product exit evidence, not current repository status:

| Evidence | Acceptance condition | Status in this slice |
| --- | --- | --- |
| Plan contract | Fourteen model-generated plans load through the generic `TeachingPlan` contract and retain immutable, source-matched provenance. | Passed in `artifacts/model-tutoring-all-dsa-acceptance.json`. |
| Per-turn control | Each of 210 turns has a generic authorization, evidence-bound outcome, bounded operation, and versioned trace. | Passed: 210 traces replay through the controller. |
| Visible behavior | Every problem has exactly fifteen exchanges, nonempty learner-visible messages, required representations, no internal leakage, no premature full solution, and correct terminal behavior. | Generic gate passed; calibration agreement is reported diagnostically. |
| Generic path | Every scenario uses the same model/schema/controller path; no learner-visible `needs_compilation`; no new per-problem lesson/controller. | Passed by plan/trace/transcript provenance and leakage checks. |
| Prompt evaluation | Candidate prompt versions are compared across all fourteen problems plus paraphrase/numeric/equivalent variants, with non-regression by problem. | Registry/provenance and structural metamorphic receipt passed; live held-out model variants remain pending. |
| Negative controls | Differential, metamorphic, property/stateful, mutation, and provenance tests fail when authority boundaries are removed. | Generic TDD/mutation/metamorphic tests pass. |
| Real acceptance | A real local Luna student ↔ Study OS Luna teacher run passes all fourteen problems individually: 14×15 = 210 exchanges / 420 visible messages. | Passed; 14 isolated lanes merged into the aggregate artifacts. |
| Manual review | Final transcripts, plans, traces, and acceptance report receive manual review for semantic drift and data-boundary violations. | Pending human review; artifacts are ready. |

Until all rows are complete, PR #77 remains draft and the architecture is not
called proven. A green unit suite or a green Contains Duplicate pilot is useful
regression evidence, but is not the all-DSA product proof.
