# P4 Luna–Sol Differential Pedagogical Calibration

Date: 2026-09-07
Status: proposed evaluation design; subordinate to Issue #63, ADR-0016, and the prerequisite/representation reconciliation in PR #73

## Purpose

Use the observed quality gap between Luna and Sol tutoring trajectories as product-development evidence without turning either model into the canonical learning controller.

The calibration target is **pedagogical behavior under the same frozen learner/controller state**, not wording similarity and not imitation of a preferred model's prose style.

The intended loop is:

```text
historical/private learner trajectory or frozen synthetic state
        ↓
exact shared state + authority constraints
        ↓
Luna candidate realization     Sol donor/reference realizations
        ↓                         ↓
normalized pedagogical-behavior extraction
        ↓
deterministic invariant / rubric scoring
        ↓
paired failure analysis
        ↓
smallest controller / representation / prompt-policy delta
        ↓
replay + regression + local/live validation
```

Sol is a **donor/reference candidate**, not the grading authority. Model agreement is not evidence of correctness by itself.

## Why this is preferable to another one-off dogfood run

The failed mutation-testing trajectory already showed the product problem: a learner who could not parse the code representation was not routed cleanly into prerequisite-sensitive, lower-complexity teaching before returning to the parent concept.

A paired differential harness gives stronger evidence than eyeballing one response because it can distinguish:

- controller/routing defects;
- decomposition granularity defects;
- representation-selection defects;
- unnecessary code exposure;
- answer leakage;
- unauthorized progression;
- failure to preserve learner-correct work;
- failure to restore the parent/source representation;
- mere stylistic differences that should **not** become product requirements.

## Evidence sources

Use sources in this order where available.

### A. Original private historical transcript

If the original Luna-vs-Sol mutation-learning transcript still exists in the private Study OS evidence store, local archive, or prior raw session artifact, ingest it as immutable source evidence.

Do not copy private raw transcript text into the public repository.

Record only public-safe derived fixtures and metrics in GitHub.

### B. Historical replay state reconstructed from durable evidence

If the exact transcript is unavailable but the learner/controller state and key turns can be reconstructed from durable private evidence, freeze the reconstructable state and mark any missing material explicitly as unresolved.

Do not fabricate missing turns.

### C. Public-safe synthetic regression

Use `p4.prerequisite-routing.code-confusion.v1` as the minimum public regression family when private evidence is unavailable to repository-side tests.

The synthetic learner event remains:

```text
I don't know how the code works
```

The target semantics must be generic boundary/operator behavior, not one hard-coded theater/ticket narrative.

## Matched-comparison protocol

For every comparison case, freeze the exact same input bundle for all candidate models:

```yaml
case_id: string
course_node_ref: string
problem_or_concept_ref: string
learner_state_snapshot: object
prerequisite_state_snapshot: object
current_representation_intent: object
source_representation: object | null
authorized_operations: [string]
assistance_ceiling: string
forbidden_information: [string]
assessment_contract_ref: string | null
history_window_ref: string
model_prompt_template_version: string
```

The candidate model may realize an authorized teaching action or propose bounded hypotheses. It may not directly mutate canonical progression/mastery/prerequisite state.

For stochastic models, run multiple samples per frozen case. Store model/provider/version, decoding configuration, prompt/template version, and seed where supported.

## Candidate sets

### Luna

Run the configured Luna candidate against the frozen state. Luna is the cost/latency-oriented candidate whose quality must be made acceptable through better deterministic routing, contracts, and bounded prompts rather than by granting it more semantic authority.

### Sol donor/reference

Run Sol on the same frozen state as a donor/reference. Prefer multiple independent Sol realizations where the execution environment supports them.

Do not use majority vote among Sol samples as canonical truth. Instead extract candidate pedagogical behaviors and score those behaviors against deterministic requirements.

### Optional current-production baseline

When useful, include the currently deployed Study OS GPT behavior as a third paired baseline. This identifies whether a defect is model-specific or caused by shared routing/state contracts.

## What to compare

Do **not** score lexical overlap, sentence style, friendliness, length, or whether Luna sounds like Sol.

Extract and compare normalized behavioral features.

### 1. Learner-event classification

For a difficulty utterance before a valid canonical answer:

```text
canonical_response_candidate
learner_difficulty_signal
clarification_or_meta_request
```

Required for the code-confusion case: the turn must not become an `INCORRECT` parent attempt solely because the learner reports inability to parse code.

### 2. Diagnosis proposal quality

Allowed candidate hypotheses include:

- `missing_prerequisite`;
- `representation_interference`;
- `decomposition_too_coarse`;
- uncertain/mixed.

Score whether the model proposes plausible hypotheses without asserting them as truth or marking prerequisite satisfaction.

### 3. Operation choice

Compare whether the realization is compatible with controller-authorized operations such as:

- `smaller_step`;
- `change_representation`;
- `show_trace`;
- `explain`;
- `restore_original`.

A good response should not silently create an unauthorized pedagogical operation.

### 4. Prerequisite sensitivity

For the mutation/code-confusion case, score whether the teaching move addresses the likely missing lower-level semantics before demanding another parent-level code interpretation.

The critical failure pattern is:

```text
code confusion
→ repeat/rephrase code
→ another parent-level probe
```

The desired behavior family is:

```text
code confusion
→ difficulty evidence
→ plausible prerequisite/representation diagnosis
→ parent progression blocked
→ simpler semantic representation / micro-probe
→ prerequisite evidence
→ deterministic return to parent
```

### 5. Representation quality

Normalize the candidate response into a `RepresentationIntentSpec`-like structure and score:

- representation family;
- semantic roles preserved;
- required relationships preserved;
- required boundary states preserved;
- code visibility appropriate to learner state;
- unrelated implementation complexity avoided;
- mapping back to source representation remains possible.

Do not reward a concrete story merely because it is vivid. Reward preservation of the target semantics with lower extraneous difficulty.

### 6. Step size / decomposition

Score whether the candidate introduces one learner-sized semantic delta rather than collapsing several new concepts into one response.

Relevant failures:

- `UNDER_DECOMPOSITION`;
- `OVER_DECOMPOSITION`;
- `SKIPPED_BRIDGE`;
- `WRONG_ABSTRACTION_LEVEL`;
- `LANGUAGE_REGISTER_JUMP`.

### 7. Progression safety

Hard failures include:

- unauthorized canonical advance;
- treating self-report as assessment failure/mastery;
- prerequisite success directly becoming parent mastery;
- future-concept introduction when forbidden;
- failure to preserve the canonical return target.

These are deterministic gate failures, not model-preference scores.

### 8. Assessment / answer exposure

Hard-fail any realization that exposes controller-only expected-answer material, converts a clarification into a graded attempt without contract authority, or gives away the active micro-probe answer.

### 9. Preservation of correct learner work

Where the learner has already established valid substructure, a correction/adaptation should preserve it. Score unnecessary rewriting as a failure even if the final explanation is technically correct.

### 10. Restoration / transfer readiness

A simplified representation is successful only if the system can later map back toward the authentic/source representation. Prefer candidates that make the semantic mapping explicit enough for deterministic restoration policy.

## Scoring model

Use two layers.

### Layer 1 — deterministic hard gates

A candidate fails the case if it violates any applicable invariant:

```text
unauthorized advancement
answer leakage
canonical attempt fabricated from difficulty signal
mastery fabricated
prerequisite satisfaction fabricated
required semantic relationship dropped
forbidden future concept introduced
parent return target lost
```

No weighted score can compensate for a hard-gate failure.

### Layer 2 — bounded pedagogical quality rubric

For hard-gate-safe candidates, score structured dimensions on a small ordinal scale, for example 0–2:

```yaml
prerequisite_sensitivity: 0..2
representation_fit: 0..2
step_size_fit: 0..2
semantic_preservation: 0..2
learner_work_preservation: 0..2
restoration_readiness: 0..2
uncertainty_handling: 0..2
```

Every score must have a machine-readable reason code and evidence reference. Free-form model judgment may assist annotation but cannot be the sole oracle.

## Differential interpretation

The purpose is not `make Luna equal Sol`.

Classify paired differences into one of these product buckets:

```text
CONTROLLER_GAP
PREREQUISITE_GRAPH_GAP
REPRESENTATION_CONTRACT_GAP
PROMPT_TEMPLATE_GAP
MODEL_CAPABILITY_GAP
ASSESSMENT_CONTRACT_GAP
EVIDENCE_INGESTION_GAP
STYLE_ONLY_DIFFERENCE
UNRESOLVED
```

Examples:

- If Sol chooses an effective non-code prerequisite representation while Luna repeats code, but the backend gave both an unconstrained generic `explain` operation, classify primarily as a controller/representation-contract gap rather than merely `Luna is worse`.
- If both models fail under the same constrained state, the defect is probably shared product/state design.
- If Luna repeatedly fails while Sol succeeds **after** the controller has already fixed the correct operation and representation intent, that is evidence for a model-capability or prompt-template gap.
- Style-only differences must not create new controller complexity.

## Calibration policy

Prefer improvements in this order:

1. fix deterministic state/routing defects;
2. make prerequisite/representation intent explicit;
3. reduce the model's degrees of freedom;
4. improve/version the bounded realization prompt/template;
5. only then consider model-tier escalation for states that remain capability-sensitive.

This ordering keeps Luna useful where the task can be made cheap and reliable, while reserving Sol-class inference for genuinely ambiguous/generative states rather than compensating for missing product structure.

## Model routing implication — later evidence-based optimization

Repeated differential evidence may justify a versioned routing policy such as:

```text
controller state
→ deterministic/template transform sufficient? use it
→ Luna meets hard gates + quality threshold? use Luna
→ otherwise escalate realization/diagnosis proposal to Sol-class model
→ validate output against the same semantic contract
```

This is a future routing decision. Do not introduce automatic tier escalation until enough paired cases exist to define thresholds without overfitting one learner trajectory.

## Minimum mutation-learning calibration suite

Start with these frozen cases:

### CAL-MUT-001 — code representation rejected before assessment

Learner: `I don't know how the code works.`

Require:

- difficulty evidence, not canonical incorrect;
- parent blocked if prerequisite resolution is entered;
- code can be hidden/secondary;
- next move addresses prerequisite semantics or runs a cheap diagnostic probe.

### CAL-MUT-002 — learner requests a visual/structured explanation

Require:

- semantic representation intent chosen explicitly;
- required relationships/boundary states preserved;
- no arbitrary visual complexity;
- no answer leakage.

### CAL-MUT-003 — prerequisite micro-probe succeeds

Require:

- evidence scoped to prerequisite;
- parent mastery remains unchanged;
- deterministic return/bridge becomes eligible according to policy.

### CAL-MUT-004 — return to source/code representation

Require:

- source mapping restored;
- learner is asked to apply the now-established semantics at the parent level;
- assistance is not silently increased;
- no future-node jump.

### CAL-MUT-005 — ambiguous difficulty

Learner gives a vague signal such as `I'm lost.`

Require:

- uncertainty remains explicit;
- choose a cheap diagnostic probe or bounded operation;
- do not assert a specific prerequisite without evidence.

## Regression promotion rule

A Sol-vs-Luna difference becomes a repository requirement only when it can be expressed as one of:

- a deterministic safety/progression invariant;
- a representation semantic requirement;
- a prerequisite/diagnosis contract;
- a bounded pedagogical-operation rule;
- a replayable scored fixture with explicit evidence.

Do not encode `Sol said X, therefore Luna must say X`.

The preferred artifact is:

```text
paired observed behavior
→ normalized failure class
→ semantic requirement
→ executable regression
→ smallest implementation delta
```

## Privacy and evidence boundary

Private learner transcripts remain private/local.

Public GitHub may contain:

- redacted/synthetic fixture inputs;
- hashes/identities of private evidence where safe;
- derived failure classes;
- aggregate paired metrics;
- deterministic invariants;
- public-safe regression examples.

It must not contain private raw learner transcript text unless explicitly approved for publication.

## Execution sequence from current state

1. Keep PAM A and PAM B accepted; do not reopen either without invalidating evidence.
2. Preserve the exact currently deployed known-PIR baseline for PAM C.
3. Locate the original private mutation-learning Luna/Sol transcript if still present in the local evidence/archive; otherwise use durable reconstruction plus `p4.prerequisite-routing.code-confusion.v1`.
4. Freeze matched comparison cases and exact authority context.
5. Collect Luna and Sol candidate realizations for the same states.
6. Normalize and score behavior using hard gates + bounded rubric.
7. Convert stable differences into #63-native prerequisite/representation regressions.
8. Implement the smallest reviewed product delta after the regression contract is accepted.
9. Re-run paired replay, repo assurance, local restart validation, and live dogfood.
10. Only after multiple cases justify it, consider model-tier routing/calibration beyond the initial prerequisite/representation fix.

## Luna-local delegation boundary

Persistent local Luna may perform mechanical work needed to collect the calibration corpus:

- locate private session/evidence artifacts;
- export a sanitized case manifest;
- replay frozen states against the configured Luna endpoint;
- replay the same frozen states against an available Sol-class endpoint when authorized/configured;
- capture model/version/prompt/config metadata;
- normalize receipts;
- run repository-provided scoring/tests;
- return public-safe aggregate results.

Luna may not:

- define the grading oracle from its own outputs;
- edit historical learner evidence;
- promote its preferred response to canonical behavior;
- change prerequisite satisfaction/progression/mastery rules;
- weaken hard gates to improve its score;
- expose private raw transcript contents in GitHub;
- enable arbitrary raw-problem compilation.

## Acceptance criteria for this calibration design

The design is useful when the same frozen mutation-learning states can be given to Luna and Sol and the resulting difference can be explained primarily in **semantic product terms**, not aesthetic preference.

A successful calibration iteration should produce:

```text
frozen case identity
+ exact controller/representation context
+ Luna behavior features
+ Sol behavior features
+ deterministic gate results
+ bounded rubric scores
+ failure classification
+ evidence-backed product delta or explicit no-change decision
```

The end goal is not to make a cheaper model imitate a more capable model. The end goal is to make Study OS constrain and route the teaching problem so that cheaper models succeed whenever the task is structurally solvable, while escalating only the cases that genuinely require stronger inference.