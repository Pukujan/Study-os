# Model/schema-driven tutoring pilot handoff

Status: ACTIVE execution authority after the dual-Luna raw transcript review.

## Immediate product goal

Do **not** hand-author another canonical teaching lesson for the pilot.

Make `contains-duplicate-set` teachable through a bounded Luna/model path:

```text
learner message
    ↓
Luna diagnosis / decomposition
    ↓ structured decision trace
controller validates allowed concept / assistance / variables / representation
    ↓
Luna generates one learner-visible teaching turn
    ↓ deterministic validation
learner sees the response
```

The deterministic system remains authority for progression, assistance ceiling, mastery claims, evidence, and hard invariants. It must stop being the author of every learner-visible lesson.

## Why this is the next step

The 14-problem / 210-exchange dual-Luna transcript proved:

- only Two Sum and Sliding Window reached real teaching;
- the other 12 problems repeatedly returned `needs_compilation` / reviewed-asset language;
- the static-asset approach therefore does not scale to normal DSA coverage;
- existing reviewed assets can still encode pedagogical drift;
- assembled state currently blocks useful follow-up clarification.

The first architecture proof should therefore convert one unsupported problem to model/schema-driven tutoring without adding a hand-authored canonical lesson.

## Pilot scope

Only `contains-duplicate-set` is required initially.

Do not generalize to all DSA problems until this pilot passes the acceptance gate and produces a reviewed transcript.

The calibrated concept progression for the pilot is:

```text
duplicate meaning
    ↓
box meaning
    ↓
membership
    ↓
check before add
    ↓
loop assembly
```

The learner-facing variable names remain `nums`, `box`, and `num`; `seen` remains forbidden for this calibrated path.

## Required design work from local Luna

Write/update a small PDD and SDD before implementation. Keep them executable and focused on this pilot rather than expanding architecture broadly.

The implementation must define:

1. how Luna produces a structured diagnosis/decomposition;
2. how the controller authorizes one pedagogical operation;
3. how the generation prompt receives only bounded state/constraints;
4. how generated learner-visible output is validated;
5. how exact prompt/model/version provenance is recorded;
6. how clarification/wrong answers remain on the current concept;
7. how a successful verification advances at most one calibrated concept;
8. how the path avoids a new hand-authored canonical teaching asset.

## Required structured trace

Every accepted teacher turn must emit one trace record matching:

`contracts/model-tutoring-trace.v0.1.schema.json`

Important fields include:

- `path_kind = model_generated`;
- `target_concept`;
- `diagnosis_family`;
- `operation`;
- `assistance_level`;
- `advance`;
- allowed / forbidden variables;
- `visual_required`;
- prompt version;
- model identifier.

For the pilot the target concept IDs are:

```text
anchor       -> duplicate_meaning
box-meaning  -> box_meaning
membership   -> membership
order        -> check_before_add
loop         -> loop_assembly
```

## Acceptance runner

The canonical gate is:

`tools/check_model_tutoring_acceptance.py`

Final acceptance command:

```bash
python tools/check_model_tutoring_acceptance.py \
  --transcript artifacts/model-tutoring-contains-duplicate.jsonl \
  --trace artifacts/model-tutoring-contains-duplicate-trace.jsonl \
  --scenario contains-duplicate-set \
  --report artifacts/model-tutoring-contains-duplicate-acceptance.json
```

Development-only transcript check:

```bash
python tools/check_model_tutoring_acceptance.py \
  --transcript artifacts/model-tutoring-contains-duplicate.jsonl \
  --scenario contains-duplicate-set \
  --transcript-only
```

The final gate rejects, among other things:

- `needs_compilation` and learner-visible asset/alias jargon;
- missing calibrated anchors;
- future-concept leakage;
- forbidden variable aliases;
- dropped visuals;
- failure to ask a learner-sized question;
- output-budget violations;
- full implementation leakage before loop assembly;
- missing model decision trace;
- turns not marked model-generated;
- target-concept drift;
- assistance above A2;
- advancement on clarification or wrong/uncertain turns;
- missing variable/visual constraints;
- missing prompt/model provenance.

## Test strategy required before scaling

### TDD

Implement the new path test-first. Unit tests should cover schema parsing, controller authorization, generation-envelope construction, validator rejection paths, trace persistence, retry/idempotency behavior, and assembled/follow-up behavior where touched.

### Differential tests

Use the calibrated corpus / trusted golden behavior as the primary oracle. Do not treat current production assets as stronger ground truth than the calibration data.

For the pilot, compare stage intent, variables, visual requirement, assistance, and progression semantics rather than exact prose.

### Metamorphic tests

At minimum, demonstrate equivalent behavior for paraphrases such as:

- “what does duplicate mean?”
- “same number twice?”
- “if 4 shows up two times?”
- “duplicate??”

and value substitutions such as `[4,7,4]` → `[8,3,8]` without changing the pedagogical structure.

Wrong-answer paraphrases must not cause accidental advancement.

### Property/stateful tests

Generate valid/invalid learner sequences and prove the controller cannot:

- skip concepts;
- advance more than one concept;
- exceed assistance ceiling;
- claim mastery without evidence;
- use forbidden aliases;
- lose the required representation contract.

### Mutation testing

The critical deterministic kernel must kill mutants that:

- advance two stages instead of one;
- advance after a wrong answer;
- remove the A2 assistance ceiling;
- remove the forbidden `seen` rule;
- make required visuals optional;
- allow mastery from transcript/self-report;
- bypass the model trace/provenance requirement;
- turn assembled state into a clarification dead end if that code is touched.

Prompt/behavior mutations should also be exercised where practical: removing one-concept-at-a-time, variable preservation, visual requirement, or retry behavior should cause transcript acceptance to degrade.

## End-to-end proof

After unit/differential/metamorphic/mutation work is green, run the real local Luna student against the real Study OS Luna teacher for Contains Duplicate and save the 15-turn transcript + trace.

Do not call the architecture validated until:

1. the acceptance runner exits 0;
2. the transcript is manually reviewed against the calibrated teaching behavior;
3. Contains Duplicate is taught without a hand-authored canonical lesson;
4. no product-internal compilation/asset jargon reaches the learner.

Only after that should the same path expand to problem #2.
