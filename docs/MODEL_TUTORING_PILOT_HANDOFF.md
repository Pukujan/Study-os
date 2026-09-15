# Model/schema-driven tutoring pilot handoff

Status: ACTIVE. The v0.2 evidence-bound pilot reached the full 15 turns and passed its then-current automated gate, but manual review invalidated acceptance because learner-visible semantics drifted.

## Current objective

Keep `contains-duplicate-set` model-generated. Do not add a hand-authored canonical lesson and do not rerun the 210-turn corpus.

The required path remains:

```text
actual learner message
    ↓
Luna diagnosis + learner-outcome assessment
    ↓
verbatim evidence_quote from learner message
    ↓
deterministic controller authorizes stay / advance at most one concept
    ↓
Luna bounded learner-visible generation
    ↓
deterministic structural + semantic validation
    ↓
learner
```

## What v0.2 proved

Commit `51133368bc34673904ae4aa572b6c5e24a9cf440` produced:

- 15 fresh Luna exchanges / 30 visible messages;
- `study-os.model-tutoring-exchange.v0.2` transcript;
- evidence-bound `study-os.model-tutoring-trace.v0.2` trace;
- progression based on actual learner-message evidence rather than scripted corpus signal;
- explicit final no-duplicate `return False` handling;
- automated acceptance v0.2 with zero failures.

Those are real gains, but they are not sufficient acceptance evidence.

## Manual semantic finding

The transcript redefined `box` as a boolean/result in the box-meaning and later stages. The calibrated corpus defines `box` as the collection of earlier values already passed. For example, the v0.2 transcript taught forms such as `box = true` and described box as holding the yes/no result.

That is a semantic teaching failure even though the response contained the expected variable names, visuals, questions, evidence, and stage progression. Therefore v0.2 acceptance is historical only.

## Current semantic contract (v0.3 acceptance)

The deterministic layer still does not author canonical lesson prose. It now protects the meaning of the calibrated concepts:

```text
anchor:
  duplicate = same value occurs at least twice in nums

box-meaning:
  box = collection of earlier/prior nums values already passed
  box != boolean answer

membership:
  check whether current num already has an equal value in box

order:
  check num in box before add

loop:
  for each num:
    if num already in box -> return True
    otherwise -> add num
  after full scan with no match -> return False
```

Luna may choose wording, examples, and visuals freely inside these semantics.

## Current code/gate

- Prompt version: `study-os.model-tutoring-pilot.v3`
- Trace schema: `contracts/model-tutoring-trace.v0.2.schema.json`
- Acceptance schema: `study-os.model-tutoring-acceptance.v0.3`
- Acceptance runner: `tools/check_model_tutoring_acceptance.py`

The generator validator and acceptance runner now reject:

- `box = true/false` or descriptions of box as the boolean/result;
- box-meaning turns that fail to describe prior/earlier values;
- membership turns that do not connect current `num` to an equal value already in `box`;
- add-before-check ordering;
- all previous evidence/progression/visual/variable/provenance/internal-state failures;
- missing final `return False` completion.

## Required validation

TDD, differential, metamorphic, stateful/property, and mutation tests must protect both structural rules and semantic meaning. A mutation that changes `box` from prior-values state into a boolean must fail.

## Fresh proof required

Run only the bounded 15-turn pilot again:

```bash
python tools/run_model_tutoring_contains_duplicate.py --fresh

python tools/check_model_tutoring_acceptance.py \
  --transcript artifacts/model-tutoring-contains-duplicate.jsonl \
  --trace artifacts/model-tutoring-contains-duplicate-trace.jsonl \
  --scenario contains-duplicate-set \
  --report artifacts/model-tutoring-contains-duplicate-acceptance.json
```

Do not call the pilot accepted until:

1. the acceptance runner exits 0 under v0.3;
2. the transcript keeps `box` as prior values throughout;
3. learner evidence still controls progression;
4. the final loop includes both duplicate detection and no-duplicate `return False`;
5. the fresh transcript and trace are manually reviewed.

Only then expand the same model/schema path to the next unsupported problem.
