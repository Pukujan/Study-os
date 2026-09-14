# All-DSA model tutoring execution handoff

Status: **PRIMARY execution authority for the next model-tutoring phase.**

This supersedes the one-problem-only execution scope in `docs/MODEL_TUTORING_PILOT_HANDOFF.md`. The Contains Duplicate work remains useful calibration evidence, but the next proof is the entire 14-problem DSA corpus in one generic model/schema path.

## Product objective

Do **not** prove one problem at a time anymore.

The next accepted system must handle all 14 DSA scenarios in `datasets/dsa-conversation-replay.v0.1.json` through the same generic model-driven architecture:

```text
14 DSA problems
× 15 learner/teacher exchanges each
= 210 teaching exchanges
= 420 learner-visible messages
```

Every problem must be teachable without adding a hand-authored canonical lesson for that problem and without falling back to learner-visible `needs_compilation` / reviewed-asset language.

The existing semantic correction for Contains Duplicate remains a required regression: `box` means the collection of earlier values, never the boolean answer.

## Local Luna owns the complete engineering loop

Local Luna is authorized to carry this work from design through accepted evidence without stopping for ordinary implementation decisions that can be resolved from the repository, tests, calibration corpus, prior transcripts, and issue history.

Local Luna should:

1. inspect current code and evidence;
2. update a focused PDD/SDD for the generic architecture;
3. generalize the Contains Duplicate-specific kernel into a problem-independent teaching-plan/controller/generation path;
4. define/version schemas and prompts;
5. implement TDD, differential, metamorphic, stateful/property, mutation, and prompt-regression tests;
6. build the 14-problem acceptance runner;
7. run all 14 problems through real local Luna student ↔ Study OS Luna teacher conversations;
8. inspect failures, fix the **general architecture** rather than adding per-problem lesson code, and rerun until accepted;
9. persist all raw transcripts, structured traces, prompt versions, generated teaching plans, acceptance reports, and diagnostics;
10. update durable docs / Issue #63 with evidence and remaining risks.

Do not stop after one problem passes. Do not ask for approval between normal fix/test/rerun cycles.

## Architecture to build

The desired architecture is:

```text
raw DSA problem
    ↓
Luna problem decomposer
    ↓
STRUCTURED TEACHING SPEC
    - concepts and prerequisite graph
    - variable names, roles, and meanings
    - representation contract
    - semantic invariants
    - allowed progression
    - likely misconceptions
    - terminal / base / completion behavior
    - assistance boundaries
    ↓
generic deterministic schema + semantic validation
    ↓
per-learner teaching state
    ↓
actual learner message
    ↓
Luna diagnosis + learner-outcome assessment
    ↓
verbatim evidence binding
    ↓
generic deterministic controller authorizes one operation
    ↓
Luna generates one bounded learner-visible turn
    ↓
generic structural + semantic validation
    ↓
learner
```

### Hard anti-pattern

Do **not** replace static assets with problem-specific Python policy such as:

```python
if scenario_id == "contains-duplicate-set":
    ...
elif scenario_id == "binary-search":
    ...
```

Do not hard-code fourteen stage lists, fourteen semantic rule tables, or fourteen lesson implementations into deterministic code.

The deterministic kernel should understand **generic contracts** such as concept prerequisites, variable-role consistency, representation constraints, legal transitions, evidence requirements, assistance ceilings, completion conditions, and provenance. Problem-specific content should come from the structured teaching spec produced by the model and be evaluated against calibration oracles outside the teacher path.

The teacher must never receive hidden benchmark answer keys / expected assertions from the acceptance corpus.

## Prompt vs schema vs deterministic code

This system is **not prompt-only** and **not schema-only**.

Use the layers for different jobs:

### Prompt

The prompt tells Luna how to perform a role:

- decompose a problem;
- diagnose the learner;
- assess whether the learner demonstrated the current concept;
- generate one bounded teaching turn;
- preserve representations and avoid jumping ahead.

Prompt instructions are probabilistic behavior steering. They are not sufficient authority.

### Schema

Schemas force Luna to externalize structured claims that code can inspect. At minimum the generic teaching spec should expose:

- problem identifier / source;
- concepts;
- prerequisite edges;
- variable bindings and semantic roles;
- representation requirements;
- semantic invariants per concept;
- allowed operations;
- completion / base conditions;
- assistance ceiling;
- misconception / repair metadata where useful;
- model + prompt provenance.

Each runtime turn should continue to expose:

- target concept;
- diagnosis;
- learner outcome;
- verbatim evidence quote when demonstrated;
- authorized operation;
- assistance level;
- variables / representation constraints;
- whether progression is authorized;
- prompt/model/schema provenance.

### Deterministic code

Deterministic code is the trust boundary. It validates generic invariants and owns state transitions. It should reject:

- unsupported schema shapes;
- fabricated evidence;
- concept skips/backtracks;
- changes in variable meaning;
- representation drift;
- assistance above policy;
- premature mastery claims;
- missing completion/base cases;
- learner-visible internal routing failures;
- responses that violate the active semantic contract.

It should **not author the lesson prose**.

### Acceptance / calibration

The calibration corpus and trusted teaching evidence are external oracles used to judge the generated teaching plan and learner-visible transcript. They must not be passed to the teacher as hidden answers.

## Prompt versioning — required

Prompt versioning is part of the product contract, not a comment in code.

Current Contains Duplicate work records `prompt_version` in traces. Generalize this into an explicit prompt registry/versioned configuration.

Every generated teaching plan and every learner-visible turn must persist at least:

- `prompt_version`;
- `prompt_hash` or equivalent immutable content fingerprint;
- `model_identifier`;
- `teaching_plan_schema_version`;
- `turn_trace_schema_version`;
- source problem identity;
- run identifier.

Never overwrite a prompt version in place after evidence has been recorded. A material prompt change gets a new version.

## Prompt evaluation — required

Yes: prompt evaluation is required, and it must be separate from ordinary unit tests.

Build a reproducible prompt-evaluation runner that can compare candidate prompt versions across the full corpus. Do not evaluate a prompt only on Contains Duplicate.

For each candidate prompt version record:

- teaching-plan schema validity;
- semantic-plan agreement with calibrated problem expectations;
- progression correctness;
- variable/representation consistency;
- learner-evidence correctness;
- assistance-level behavior;
- premature answer leakage;
- completion/base-case coverage;
- transcript acceptance result;
- failure categories by problem and stage.

Use the current 14 scenarios as the regression/calibration suite and add metamorphic/held-out variants (paraphrases, numeric substitutions, equivalent problem statements, altered examples) so a prompt cannot pass merely by memorizing the fixed corpus wording.

A prompt version is promotable only when it is better or non-regressive on the aggregate suite and does not introduce severe per-problem regressions.

## Terra role — independent diagnostician, not authority

No Terra-specific integration currently exists in the repository. If Terra is available in the local environment, Local Luna may use Terra as a **separate critic/diagnostic agent**.

Recommended flow:

```text
failed transcript / trace / generated teaching plan
        ↓
Terra independent diagnosis
        ↓
structured failure hypotheses
        ↓
Local Luna decides what to change
        ↓
tests + prompt eval + full acceptance decide whether the change is valid
```

Terra may diagnose:

- semantic drift;
- skipped prerequisite concepts;
- representation changes;
- over-help / under-help;
- poor decompositions;
- prompt ambiguities;
- repeated failure patterns across problems.

Terra must **not**:

- interact with the learner during the measured tutoring run;
- authorize progression;
- change learner outcomes;
- act as the acceptance oracle;
- make a failing run pass by rewriting the report;
- see hidden calibration answers and then feed them into the teacher.

If Terra is unavailable locally, Local Luna should perform the same diagnostic step itself and persist the diagnostic artifact. Terra is useful for independent perspective, not required for correctness.

Suggested artifacts when Terra is used:

```text
artifacts/model-tutoring-terra-diagnostics.jsonl
artifacts/model-tutoring-terra-diagnostics.md
```

Each diagnostic should identify run ID, problem, turn/stage, observed failure, hypothesized cause, and proposed generic fix. Keep diagnosis separate from acceptance outcome.

## Required generic schemas

Local Luna should create/generalize schemas rather than keeping the current single-scenario constants as the architecture.

At minimum define a versioned teaching-plan schema capable of expressing all 14 problems, and a generic turn trace schema that references that plan.

A reasonable conceptual teaching-plan shape is:

```json
{
  "problem": {"id": "...", "statement": "..."},
  "concepts": [
    {
      "id": "...",
      "prerequisites": ["..."],
      "semantic_invariants": ["..."],
      "allowed_variables": ["..."],
      "representation": {"kind": "..."},
      "completion_evidence": ["..."]
    }
  ],
  "variables": {
    "name": {
      "role": "collection|index|value|accumulator|boundary|...",
      "meaning": "..."
    }
  },
  "terminal_behavior": ["..."],
  "assistance_ceiling": "A2"
}
```

Do not treat this example as a fixed final schema if a better generic contract emerges during implementation.

## Full-corpus acceptance target

A successful architecture run must produce:

```text
14 scenarios
15 exchanges per scenario
210 exchanges
420 nonempty learner-visible messages
```

All fourteen must use the generic model-generated path.

Acceptance must fail if any scenario:

- falls back to `needs_compilation` or reviewed-asset language;
- requires a newly hand-authored canonical lesson;
- relies on scenario-specific controller code to teach correctly;
- changes a variable's semantic role mid-conversation;
- violates its generated teaching-plan invariants;
- skips prerequisites or advances without learner evidence;
- exceeds assistance policy;
- leaks future concepts / full solutions prematurely;
- drops required representations;
- fails to teach a required terminal/base/completion condition;
- gets stuck after assembly when clarification or verification is still needed;
- produces malformed or unversioned provenance;
- fails corpus-level calibrated behavioral checks.

Do not allow aggregate pass rate to hide a failed problem. For this proof, **all 14 scenarios must pass**.

## Required validation stack

### PDD

Define learner-visible product behavior, genericity requirement, no-static-lesson requirement, trust boundaries, and acceptance criteria.

### SDD

Specify model calls, schemas, prompt registry/versioning, deterministic controller, semantic validation, persistence, diagnostic flow, retries, and acceptance artifacts.

### TDD

Test schema parsing, decomposition validation, semantic invariants, progression, evidence binding, variable-role consistency, representation continuity, retry/idempotency, prompt provenance, and terminal behavior.

### Differential

Compare generated plans and visible behavior against calibrated/trusted examples semantically, not by exact prose. Existing production assets are not automatically ground truth.

### Metamorphic

At minimum cover:

- learner paraphrases;
- numeric substitutions;
- equivalent problem-statement paraphrases;
- harmless variable-value changes;
- wrong-answer paraphrases;
- uncertainty expressed in different language;
- equivalent representations where allowed.

These changes must not arbitrarily change concept order, semantic roles, or progression policy.

### Property/stateful

Randomized valid/invalid learner sequences must not cause skips, backtracks, mastery without evidence, variable-role mutation, representation loss, or assistance overflow.

### Mutation

Mutants must be killed for:

- advancement without demonstrated evidence;
- two-stage advancement;
- evidence fabrication;
- assistance-ceiling removal;
- semantic-role mutation;
- representation requirement removal;
- completion/base-case removal;
- prompt/schema provenance removal;
- bypassing model-generated-path identity;
- allowing `needs_compilation` into learner-visible output.

### Prompt regression / prompt differential

Compare prompt versions over the full corpus and metamorphic variants. Store per-version reports so prompt changes are reviewable and reversible.

## Full run / artifacts

Local Luna should generalize the runner so the canonical proof is one command or one clearly documented command sequence that runs all 14 scenarios through the generic path.

Expected durable artifacts should include equivalents of:

```text
artifacts/model-tutoring-all-dsa-transcript.jsonl
artifacts/model-tutoring-all-dsa-transcript.md
artifacts/model-tutoring-all-dsa-trace.jsonl
artifacts/model-tutoring-all-dsa-plans.jsonl
artifacts/model-tutoring-all-dsa-acceptance.json
artifacts/model-tutoring-prompt-eval.json
```

If Terra is used, also persist its diagnostics separately.

## Self-directed failure loop

Local Luna should use this loop until acceptance is real:

```text
implement generic architecture
    ↓
unit/property/mutation/prompt tests
    ↓
run 14×15 dual-Luna corpus
    ↓
acceptance
    ↓
manual + optional Terra diagnosis of failures
    ↓
identify GENERAL cause
    ↓
fix prompt/schema/controller/validator
    ↓
rerun tests
    ↓
rerun full 14×15 corpus
```

A fix is invalid if it merely special-cases the failing scenario.

Do not stop because a run is expensive or because one problem passes. The evidence target is the complete corpus.

## Completion criteria

This phase is complete only when all of the following are true:

1. all 14 problems are taught through the generic model/schema path;
2. no new per-problem canonical teaching assets were added;
3. no problem exposes `needs_compilation` to the learner;
4. all 210 exchanges have structured versioned traces;
5. generated teaching plans are persisted and schema-valid;
6. prompt version and immutable prompt fingerprint are persisted;
7. full prompt-evaluation report exists;
8. TDD + differential + metamorphic + property/stateful + mutation gates pass;
9. full-corpus acceptance exits 0 with all 14 passing individually;
10. transcript and traces receive manual review;
11. any Terra diagnostics are advisory and separately persisted;
12. Issue #63 and handoff docs are updated with the final evidence and known residual risks.

Until then, keep PR #77 draft and do not claim the generic model-tutoring architecture is proven.
