# Model/schema-driven tutoring pilot handoff

Status: ACTIVE execution authority after manual review of the first 15-turn pilot.

## Immediate product goal

Do **not** hand-author another canonical teaching lesson for the pilot.

Make `contains-duplicate-set` teachable through a bounded Luna/model path where progression depends on the learner's actual response:

```text
learner message
    ↓
Luna diagnosis + learner-outcome assessment
    ↓
verbatim evidence_quote from the learner message
    ↓
deterministic controller authorizes stay / advance + bounded operation
    ↓
Luna generates one learner-visible teaching turn
    ↓
deterministic presentation validation
    ↓
learner sees the response
```

The deterministic system remains authority for progression mechanics, assistance ceiling, mastery claims, evidence binding, and hard invariants. Luna supplies adaptive diagnosis/decomposition, proposes the learner outcome, and writes the bounded teaching turn.

## Why v0.2 exists

The 14-problem / 210-exchange dual-Luna transcript proved that static hand-authored assets do not scale: only Two Sum and Sliding Window reached real teaching, while 12 problems returned `needs_compilation` / reviewed-asset language.

The first model-tutoring pilot then proved dynamic learner-visible teaching was possible, but manual review found two acceptance holes:

1. progression was still driven by the corpus's scripted `learner_signal` (`recovery_or_check`) rather than evidence in the actual learner reply;
2. the 15-turn conversation never established the final no-duplicate case, `return False`, even though the old gate passed.

Those v0.1 artifacts are therefore historical evidence, not current acceptance evidence.

## Pilot scope

Only `contains-duplicate-set` is required initially. Do not generalize until a **fresh v0.2 15-turn run** passes the acceptance gate and manual review.

Calibrated concept order:

```text
duplicate meaning
    ↓
box meaning
    ↓
membership
    ↓
check before add
    ↓
loop assembly / finish-without-duplicate case
```

Learner-facing variable names remain `nums`, `box`, and `num`; `seen` remains forbidden for this calibrated path.

## Progression authority

The corpus `learner_signal` is allowed only as simulation guidance for Student Luna. It is **not evidence** and must not authorize progression.

Teacher Luna must produce a structured assessment of the actual learner message:

```json
{
  "learner_outcome": "demonstrated | not_yet | uncertain",
  "evidence_quote": "exact substring from the learner message when demonstrated",
  "rationale": "short explanation"
}
```

Rules:

- `demonstrated` requires a non-empty `evidence_quote`;
- the quote must occur verbatim in the learner message;
- `not_yet` and `uncertain` never advance;
- `demonstrated` may advance at most one concept;
- the final `loop_assembly` concept cannot advance beyond the pilot;
- transcript/self-report never establishes mastery.

## Required structured trace

Every accepted teacher turn must emit one trace record matching:

`contracts/model-tutoring-trace.v0.2.schema.json`

Required fields include:

- `path_kind = model_generated`;
- `target_concept`;
- `diagnosis_family`;
- `operation`;
- `assistance_level`;
- `learner_outcome`;
- `evidence_quote`;
- `advance`;
- allowed / forbidden variables;
- `visual_required`;
- prompt version;
- model identifier.

Target concept IDs:

```text
anchor       -> duplicate_meaning
box-meaning  -> box_meaning
membership   -> membership
order        -> check_before_add
loop         -> loop_assembly
```

## Acceptance runner

Canonical gate:

`tools/check_model_tutoring_acceptance.py`

Final acceptance command:

```bash
python tools/check_model_tutoring_acceptance.py \
  --transcript artifacts/model-tutoring-contains-duplicate.jsonl \
  --trace artifacts/model-tutoring-contains-duplicate-trace.jsonl \
  --scenario contains-duplicate-set \
  --report artifacts/model-tutoring-contains-duplicate-acceptance.json
```

The v0.2 gate rejects, among other things:

- `needs_compilation` and learner-visible asset/alias jargon;
- missing calibrated anchors, visuals, tiny questions, or variable constraints;
- future-concept/full-solution leakage;
- assistance above A2;
- non-model-generated turns or missing provenance;
- advancement without `learner_outcome = demonstrated`;
- demonstrated outcomes without a verbatim evidence quote;
- evidence quotes not found in the real learner message;
- concept skips, backwards movement, or progression inconsistent with the previous turn's `advance` decision;
- failure to reach `loop_assembly`;
- failure for the final learner-visible turn to explicitly establish `return False` after a full scan with no duplicate.

## Test strategy required before scaling

### TDD

Cover assessment parsing, evidence binding, controller authorization, generation envelopes, validator rejection paths, trace persistence, resume behavior, and final loop completion.

### Differential

Use the calibrated corpus / trusted golden behavior as the primary oracle for concept order, variables, visual requirements, assistance, and representation constraints. Do not treat current production assets as stronger ground truth.

### Metamorphic

Paraphrases and numeric substitutions must preserve policy. A corpus signal change by itself must never change progression; progression changes only when the actual learner assessment changes.

### Property/stateful

Generate learner-outcome sequences and prove the controller cannot skip concepts, advance more than one concept, exceed assistance ceiling, claim mastery, lose evidence binding, or use forbidden aliases.

### Mutation

Kill mutants that:

- restore `recovery_or_check -> advance`;
- allow `demonstrated` without learner evidence;
- accept fabricated evidence quotes;
- advance two stages;
- exceed A2;
- remove `seen` prohibition;
- make visuals optional;
- bypass trace/provenance;
- omit the final `return False` completion requirement.

## End-to-end proof

Run a **fresh** local 15-turn pilot after these changes. Old v0.1 transcript/trace files must not be resumed; the runner deliberately rejects them as resumable prefixes.

Do not call the architecture validated until:

1. the new transcript uses `study-os.model-tutoring-exchange.v0.2`;
2. every trace row uses `study-os.model-tutoring-trace.v0.2`;
3. stage progression is justified by actual learner-message evidence, not corpus signals;
4. the final loop teaches/checks the no-duplicate `return False` case;
5. the acceptance runner exits 0;
6. the fresh transcript and trace are manually reviewed;
7. Contains Duplicate remains model-generated without a hand-authored canonical lesson.

Only then expand the same path to problem #2.
