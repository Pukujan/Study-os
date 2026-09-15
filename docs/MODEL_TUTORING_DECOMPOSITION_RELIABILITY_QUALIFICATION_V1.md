# Model tutoring decomposition reliability qualification v1

Status: **durable stopping/promotion contract for the Local Luna autonomous model-tutoring loop.**

This document answers one specific question that earlier orchestration documents left too implicit:

> When may Local Luna stop iterating and say that strong-inference decomposition is now coming out reliably rather than merely passing one convenient batch?

The answer is **not** "after one four-problem batch passes."

A candidate becomes decomposition-reliability-qualified only after the **same frozen candidate identity** survives broad public rotation plus genuinely hidden promotion evidence without being modified between those measurements.

This policy refines, and should be read with:

1. `docs/MODEL_TUTORING_LOCAL_AUTONOMOUS_LOOP_V1.md`
2. `plugins/study-os-dsa-decomposer/skill.md`
3. `plugins/study-os-dsa-decomposer/checklist.md`
4. `docs/MODEL_TUTORING_ROTATING_HOLDOUT_EVAL_V1.md`
5. `contracts/model-tutoring-agent-boundaries.v0.1.json`

## Long-running goal

Local Luna's autonomous engineering objective is:

```text
build candidate
   ↓
run deterministic repo gates
   ↓
freeze candidate
   ↓
public rotating evaluation
   ↓
fail?
  ├─ yes → diagnose → generic fix → NEW candidate identity → repeat
  └─ no
       ↓
accumulate public coverage for SAME frozen candidate
       ↓
full public qualification coverage reached?
  ├─ no → next automatic 4-problem batch, candidate still frozen
  └─ yes
       ↓
hidden promotion batch using SAME frozen candidate
       ↓
fail?
  ├─ yes, no reveal needed → reject candidate → resume engineering
  ├─ yes, raw case needed → burn case → public regression → fix → NEW candidate → reset qualification
  └─ pass
       ↓
DECOMPOSITION_RELIABILITY_QUALIFIED
```

A public batch pass is **progress toward qualification**, not qualification itself.

## Candidate identity is the unit of evidence

Qualification evidence belongs to one immutable candidate identity.

The candidate identity includes at least:

- git commit SHA;
- decomposition prompt version + content hash;
- diagnosis prompt version + content hash;
- generation prompt version + content hash;
- TeachingPlan schema semantic version;
- turn-trace schema version;
- decomposer skill version;
- decomposition checklist version;
- evaluation policy version;
- model identifier(s) used in measured roles.

If any of those materially changes, the next measured run belongs to a **new candidate**.

Do not combine old-candidate passing batches with new-candidate batches and call the new candidate qualified.

Historical evidence remains useful for regression diagnosis, but qualification must describe the exact candidate being promoted.

## Development mode versus qualification mode

The autonomous loop has two public modes.

### Development mode

Purpose: find and fix generic failures cheaply.

- run one automatically selected four-problem public batch;
- inspect deterministic/reviewer failures;
- make generic fixes when needed;
- create new prompt versions rather than overwrite historical prompt semantics;
- new code/prompt/schema/skill behavior creates a new candidate;
- repeat with a different automatically selected four-problem batch.

This is allowed to mutate the candidate between iterations.

### Qualification mode

Purpose: determine whether one candidate is now reliable across the public corpus.

Once a candidate is nominated for qualification:

- freeze it;
- no prompt/code/schema/skill changes during the public qualification epoch;
- continue automatic four-problem batches until every eligible public regression problem has been exercised at least once against that same candidate;
- preserve no-immediate-repeat and structural-family-diversity rules;
- if the 14-problem corpus requires a final fill to keep batches of four, the extra cases may come from the next shuffle epoch, but all 14 unique public cases must have appeared at least once;
- a hard failure rejects the qualification attempt.

If a public qualification failure requires a fix, qualification restarts for the resulting new candidate.

## Required decomposition outputs

For every measured problem, the decomposer must emit a structurally valid, semantically coherent candidate containing equivalent information for:

- algorithm graph;
- primitive objects;
- stable state variables / meanings;
- invariant(s);
- transition / recurrence / pointer or queue-stack state update as appropriate;
- terminal/base conditions;
- integration conditions;
- candidate representation set when alternatives are material;
- selected representation + compact rationale;
- learning dependency graph created by backward prerequisite expansion;
- grounded vocabulary contract;
- grounded learner-facing symbols;
- completion evidence per required node;
- correction/retry/verification policy;
- prompt/model/schema/skill/run provenance.

The decomposition is not reliable merely because all JSON fields exist. The checklist and deterministic semantic validators must establish that the graph can actually derive the algorithm without hidden prerequisite jumps or learner repair of tutor defects.

## Public qualification hard gates

For the same frozen candidate across the public qualification epoch:

1. **100% required-output validity**
   - every selected TeachingPlan satisfies schema and required decomposition/checklist fields.

2. **100% deterministic semantic-gate pass**
   - no variable/concept meaning drift;
   - no undefined learner-facing symbol/term when grounding is required;
   - no illegal prerequisite skip;
   - no broken representation invariant;
   - no fabricated learner evidence;
   - no fixed-turn false completion.

3. **100% per-problem completion or explicit qualification failure**
   - every public problem must reach required terminal/base/integration evidence through the completion-driven controller;
   - one failed public problem prevents qualification.

4. **No severe tutor-contract failure**
   - no semantic misinformation accepted as valid;
   - no learner required to repair the tutor;
   - no answer/oracle leakage;
   - no progression authorized from hidden/scripted learner signals.

5. **Correction behavior remains legal**
   - meaningful errors use correction → changed retry → verification when required;
   - semantically correct tentative statements are not indefinitely blocked merely because of question phrasing.

6. **Vocabulary/representation quality remains stable**
   - simple vocabulary does not destroy semantics;
   - meaning is grounded before technical terminology/symbols when required;
   - unnecessary synonym drift/term overload is rejected;
   - compact algebraic/state-transition representations remain preferred when they genuinely reduce learner friction, without forcing equation-first teaching on structures where another native relation is clearer.

7. **Learner-visible review has no blocking pathology**
   - a separate reviewer may identify non-blocking polish issues;
   - any semantic, progression, representation, or learner-repair pathology is blocking;
   - repeatable reviewer findings should become deterministic tests before final promotion when practical.

8. **Live prompt-evaluation evidence exists**
   - prompt evaluation must execute actual live held-out/metamorphic variants;
   - a structural/provenance-only report cannot satisfy qualification.

## Hidden promotion gate

After the same candidate passes the full public qualification epoch, evaluate that exact frozen candidate against a genuinely unburned hidden batch.

Hidden evaluator rules remain:

- engineering/prompt-fixing Luna cannot read the holdout directory;
- measured decomposer/teacher/student receive only the current problem statement required for the run;
- hidden oracle remains evaluator-only;
- candidate is read-only during evaluation;
- engineering receives only sanitized verdict/metrics/failure codes before burn.

The hidden batch must include enough structural diversity to test transfer beyond exact public examples when the holdout bank permits.

A hidden severe tutor-contract failure prevents qualification.

If raw hidden content is revealed to drive a fix, that case is burned, moved to public regression, and the fix creates a new candidate. Public qualification for the new candidate starts again before relying on another hidden promotion result.

## Reliability-qualified state

Only after both:

```text
SAME FROZEN CANDIDATE
        ↓
full public qualification epoch passes
        ↓
genuinely hidden promotion batch passes
```

may the ledger record:

`candidate_outcome = decomposition_reliability_qualified`

This does **not** mean mathematically proven correct for all future algorithms. It means the candidate has met the current operational evidence standard for broad public + hidden generalization.

Future newly discovered failures can demote confidence and enter the next improvement cycle.

## Autonomous continuation semantics

The default long-running objective should be conceptually:

```text
--goal decomposition-reliability-qualified
```

The orchestrator should continue development/measurement cycles toward that goal without requesting routine human approval between ordinary iterations.

However, do **not** implement one literally infinite uncontrolled self-edit process.

Each invocation should have configurable safety/resource bounds such as:

- maximum candidate generations;
- maximum model calls or token budget if locally measurable;
- maximum wall-clock/runtime budget if desired by the operator;
- existing per-problem anti-loop exchange ceiling;
- hard stop on environment/integrity/permission failures.

When an invocation-level bound is reached before qualification:

- persist all state;
- mark the goal `not_yet_qualified` rather than failed/successful by fiat;
- emit the next resumable state/action;
- a later `--resume --goal decomposition-reliability-qualified` continues from durable evidence rather than restarting or silently changing seeds.

This creates a long-running autonomous goal **without** an unsafe infinite agent loop.

## Suggested orchestrator modes

Support behavior equivalent to:

```bash
python tools/run_model_tutoring_autonomous_loop.py \
  --goal decomposition-reliability-qualified \
  --batch-size 4 \
  --max-exchanges-per-problem 250 \
  --resume
```

Useful bounded controls may include:

```text
--max-candidate-generations N
--max-public-iterations N
--until-public-qualification-complete
--promotion-holdout
--resume
```

Do not silently weaken the reliability gate because an invocation budget was exhausted.

## Ledger additions

The append-only evaluation ledger should make qualification auditable. Add or preserve fields equivalent to:

- candidate ID;
- qualification attempt ID;
- qualification state (`development`, `public_qualifying`, `hidden_qualifying`, `qualified`, `rejected`, `not_yet_qualified`);
- public unique-problem coverage for this exact candidate;
- public required-output pass count;
- public deterministic semantic-gate result;
- public per-problem completion result;
- reviewer blocking findings;
- live prompt-eval result;
- hidden promotion report reference;
- reason qualification reset, if any;
- next resumable action.

## Important anti-overfitting rule

The rotating four-problem development lane helps avoid repeatedly tuning against one static subset, but reliability evidence is stronger than rotation alone.

Therefore:

- development may learn from public failures;
- qualification must measure one unchanged candidate across the full public corpus;
- hidden promotion tests transfer/generalization after that public qualification;
- hidden failures that influence fixes are burned and become public regression;
- the replacement holdout restores future unseen evidence.

This is the operational definition of "keep running until decomposition starts coming out reliably" for Study OS vNext.
