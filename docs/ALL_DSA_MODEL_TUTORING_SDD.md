# All-DSA generic model tutoring — Software Design Document

Status: implemented generic architecture grounded in the current Python
contracts. Decomposition orchestration, isolated-lane durable execution,
generic trace replay, and the independent all-DSA acceptance evaluator are now
checked in and exercised by the 14×15 local run.

The next qualification layer is implemented as a separate orchestration
boundary in `tools/run_model_tutoring_autonomous_loop.py` and
`study_os.decomposition_qualification`. It records frozen candidate
fingerprints, seeded batch schedules, bounded model/runtime budgets, repair
epoch invalidation, and resumable checkpoints. It does not author teaching
content and it cannot mark a public-only run as qualified.

## Design boundary

The system has four distinct jobs:

```text
raw problem + public learner turn
        ↓
model proposes structured plan/diagnosis/response
        ↓
schema + deterministic validation
        ↓
controller authorizes one bounded operation and one state transition
        ↓
learner-visible response + trace + independent evaluation
```

The model supplies content and hypotheses. The schema makes those claims
inspectable. Deterministic code owns trust-boundary decisions. The acceptance
oracle judges the resulting plan and visible behavior without being supplied to
the teacher as hidden answer material.

## Components

### 1. Corpus/problem adapter

Input is one corpus scenario’s problem identity, statement, public variables, and
one learner message at a time. The adapter also supplies bounded conversation
history to the model. It must not pass `expected` assertions, hidden calibrated
anchors, or evaluator explanations to the teacher.

The existing dataset contains fourteen scenarios with fifteen turns each. The
existing broad replay tool can run or grade visible benchmark conversations, but
it is not the generic model-tutoring acceptance runner described here.

### 2. Decomposition role

The decomposition model receives the raw problem and the registered
decomposition prompt. It returns a JSON-compatible teaching-plan payload. The
payload is loaded with `TeachingPlan.from_payload`, which first calls
`validate_teaching_plan_schema` and then enforces reference integrity,
prerequisite acyclicity, variable bindings, invariant/evidence coverage,
terminal behavior, assistance ceiling, and source/provenance consistency.

The current v0.1 plan surface is:

- `ProblemSpec(id, statement)`;
- ordered `ConceptSpec` values with prerequisites and allowed variables;
- `VariableSpec(role, meaning)` bindings;
- `RepresentationRequirement(id, kind, operation, description, required)`;
- `SemanticInvariant(id, concept_id, statement)`;
- `CompletionEvidence(id, concept_id, evidence_type, description)`;
- nonempty `terminal_behavior`;
- `assistance_ceiling` in `A0`, `A1`, `A2`; and
- `TeachingPlanProvenance`.

The implementation is exercised by the isolated-lane runner in
`tools/run_model_tutoring_all_dsa_parallel.py`; its merged 14-plan/210-turn
receipt is under `artifacts/model-tutoring-all-dsa-*.jsonl` and is checked by
`tools/check_model_tutoring_all_dsa.py`.

Misconception metadata, explicit plan-level progression policies, or any other
new field requires an explicit schema version change. It must not be smuggled
into the current contract as an unvalidated extension.

### 3. Prompt registry and provenance

`PromptDefinition` stores a role, immutable content, and a SHA-256 hash.
`PromptRegistry.register` returns a new registry and rejects version reuse;
`get`, `for_role`, and `verify` resolve or verify a historical definition.
`PromptProvenance` carries:

```text
prompt_version
prompt_hash
model_identifier
teaching_plan_schema_version
turn_trace_schema_version
run_id
source_problem_id
```

The default registry currently defines separate decomposition, diagnosis, and
generation prompt versions. `GenericModelTutoringController` currently resolves
the generation role during construction; a full runner still needs to call and
persist decomposition and diagnosis provenance for the complete lifecycle.

### 4. Diagnosis/assessment parsing

`parse_model_decision` parses one JSON object into `ModelDiagnosis` and
`LearnerAssessment`.

`ModelDiagnosis` carries `diagnosis_family`, `operation`, `assistance_level`,
and optional decomposition text. Generic parsing normalizes a small set of
legacy aliases but does not make scenario-specific policy decisions.

`LearnerAssessment` carries `learner_outcome` (`demonstrated`, `not_yet`, or
`uncertain`), an optional evidence quote, and rationale. A demonstrated outcome
requires a nonempty quote. `from_payload` and controller authorization require
the quote to be a verbatim substring of the supplied learner message. The
rationale is a model-derived explanation, not observed evidence.

### 5. Generic deterministic controller

`GenericModelTutoringController` is initialized with a validated `TeachingPlan`,
optional `LearnerState`, a `PromptRegistry`, a generation prompt version, and a
model identifier. It rejects plans whose ordered concepts do not already satisfy
their prerequisite edges.

The controller’s public seams are:

| Interface | Responsibility |
| --- | --- |
| `active_concept` | Read the plan concept at the current `LearnerState.concept_index`. |
| `authorize(diagnosis, assessment, learner_message, turn_index)` | Validate evidence/assistance/index, construct a `GenerationContract`, calculate a one-step `advance`, and return `Authorization`. |
| `authorize_model_decision(raw, learner_message, turn_index)` | Parse a model JSON decision, then use `authorize`. |
| `commit(authorization)` | Replace state with the authorization’s `next_state` after the runner accepts the turn. |

`LearnerState` is immutable and currently contains `concept_index` and
`turns_seen`. Advancement is exactly one concept only when the outcome is
`demonstrated`; the final concept remains active because the generic state has no
unproven mastery flag.

### 6. Generation contract and response boundary

`GenerationContract` is derived from the active plan concept. It carries the
problem statement, allowed variables, required representations, semantic
invariants, completion evidence, terminal behavior, assistance ceiling and
requested level, learner outcome/evidence, diagnosis/operation, advance flag,
prompt provenance, plan provenance, and variable bindings.

`build_generation_prompt` resolves the contract’s prompt version and hash in the
registry, includes only the active contract and bounded recent history, and
instructs the model to return JSON with a `response`. It does not author lesson
prose.

`parse_generation_response` extracts the learner-visible response. The current
generic `validate_generated_response` rejects empty/oversized output, internal
routing/provenance markers, missing required representations, and identifiers
outside the active concept’s variable bindings. It is intentionally not a
complete DSA semantic evaluator.

### 7. Trace/provenance emission

`GenerationContract.trace` emits a `model_generated` record with the active
concept, diagnosis, operation, assistance, learner outcome, evidence quote,
advance decision, variable and requirement identifiers, prompt identity, plan
identity, model, schema versions, run ID, and source problem ID. The trace is a
decision record, not a mastery record.

There is an integration gap to resolve before full acceptance: the checked-in
`contracts/model-tutoring-trace.v0.2.schema.json` is a pilot-shaped, closed
schema, while the generic controller emits a richer trace and does not emit all
of the pilot schema’s legacy fields. The generic runner must adopt an explicit
versioned generic trace contract (or an intentional compatible revision), then
validate every emitted trace against that contract. No undocumented schema
coercion is acceptable.

## End-to-end data flow

1. **Capture input.** Select one source problem and one learner message. Keep
   source/private transcript bytes immutable; do not treat a scripted corpus
   message as a real learner observation.
2. **Compile a plan.** Invoke the decomposition role with the raw problem only.
   Record model/prompt identity, parse the payload, validate it into an immutable
   `TeachingPlan`, and persist the plan payload plus provenance.
3. **Load state.** Create a fresh controller for the plan or restore a validated
   state at the next missing turn. Never infer state from teacher prose.
4. **Diagnose/assess.** Invoke the diagnosis role with the active contract
   context and actual learner message. Parse `ModelDiagnosis` and
   `LearnerAssessment`; bind any demonstrated quote to the actual message.
5. **Authorize.** Call `authorize`/`authorize_model_decision`. The controller
   selects the active concept from state, checks the plan ceiling, calculates at
   most one transition, and creates the generation contract and trace.
6. **Generate.** Call `build_generation_prompt`, ask for one JSON response, parse
   it, and run `validate_generated_response`. Do not expose a failed or partial
   response to the learner.
7. **Commit/persist.** Only after the response and trace pass the applicable
   deterministic checks may the runner commit the returned state and append the
   transcript/trace/plan references. The raw learner message and the model’s
   derived fields remain distinguishable.
8. **Evaluate after capture.** A separate evaluator checks calibrated semantics,
   genericity, progression, representations, terminal behavior, provenance, and
   visible output. Its hidden expectations are not sent back to the teacher.

## Retry, restart, and idempotency boundary

The current controller is a pure authorization/commit kernel; `commit` simply
stores `next_state`. It does not itself provide durable writes, matching-prefix
recovery, or duplicate-event detection.

The pending runner must therefore:

- retry a malformed model decision or generated response against the same
  uncommitted state and turn contract;
- avoid advancing or appending evidence on a failed response;
- persist transcript and trace records with a unique `(run_id, source_problem_id,
  turn_index)` identity;
- resume only from a matching, validated prefix;
- reject conflicting duplicates rather than overwrite prior evidence; and
- write a final acceptance report only after all required records exist.

These are runner requirements, not claims about current controller behavior.

## Component boundaries and prohibited dependencies

| Component | Owns | Must not own |
| --- | --- | --- |
| Model roles | Plan/diagnosis/assessment/response proposals | Progression, mastery, hidden answers, or trust decisions |
| `TeachingPlan` | Validated problem semantics and plan bindings | Learner outcome or runtime evidence |
| `PromptRegistry` | Immutable prompt definitions and hashes | Prompt evaluation verdicts or learner state |
| `GenericModelTutoringController` | Active concept, evidence gate, assistance, one-step state transition, decision trace | Lesson prose, scenario branches, or external acceptance scores |
| Response validator | Generic visible-output boundary | A replacement for independent semantic evaluation |
| Corpus/evaluator | Calibrated comparison and failure report | Inputs to the teacher during the measured turn |
| Study OS evidence store | Canonical raw/observed/self-reported/derived records | FOSSIL as a second canonical store |
| FOSSIL | Optional promoted/exported knowledge | Runtime tutoring authority or raw event ownership |

Problem-specific semantics may appear in a model-produced plan and in an
external calibration oracle. They must not become scenario-specific controller
policy or hand-authored learner-visible lessons.

## Planned artifacts and current status

The handoff names durable equivalents for an all-DSA run:

```text
artifacts/model-tutoring-all-dsa-transcript.jsonl
artifacts/model-tutoring-all-dsa-transcript.md
artifacts/model-tutoring-all-dsa-trace.jsonl
artifacts/model-tutoring-all-dsa-plans.jsonl
artifacts/model-tutoring-all-dsa-acceptance.json
artifacts/model-tutoring-prompt-eval.json
```

These are planned outputs only. This documentation task creates none of them.
The existing Contains Duplicate artifacts and pilot runner remain historical
calibration evidence; they are not evidence that the generic all-DSA pipeline
has completed.

## Remaining implementation/evaluation work

- Add the generic decomposition → plan persistence → diagnosis → authorization →
  generation orchestration around the existing interfaces.
- Define and validate the generic versioned trace/exchange contract, resolving
  the current pilot-schema mismatch.
- Add retry/resume/idempotent persistence and no-partial-response behavior.
- Generalize the acceptance checker from one Contains Duplicate scenario to all
  fourteen while keeping hidden expectations outside the teacher input.
- Add calibrated/differential, metamorphic, property/stateful, mutation, and
  prompt-regression runners.
- Execute one real 15-turn run for each problem, then the complete 210-turn
  aggregate, and manually review plans/transcripts/traces.
