# Model tutoring pilot — focused PDD

Status: implementation specification for `contains-duplicate-set` only.

## Problem and bounded outcome

The current PIR runtime fails closed for Contains Duplicate because it has no reviewed
canonical lesson. The pilot tests a different boundary: Luna proposes a diagnosis and
decomposition, deterministic code authorizes one bounded operation, and Luna realizes
that operation as a learner-visible response. The pilot must not install a second
hand-authored lesson graph.

The learner-visible path is:

```text
learner turn
  → model diagnosis/decomposition
  → deterministic authorization
  → bounded model generation
  → deterministic output + trace validation
  → learner-visible response
```

## Product invariants

Code remains authoritative for:

- the five-stage order: duplicate meaning → box meaning → membership → check-before-add → loop assembly;
- one-stage-at-most advancement and no advancement for clarification/wrong turns;
- assistance ceiling A2;
- the allowed variables `nums`, `box`, and `num` (and no alias `seen`);
- required scan-box visual, one relation, short output, and learner-sized check;
- mastery (the pilot records no mastery claim); and
- trace, prompt, model, and controller provenance.

Luna may only select a diagnosis family/operation and write the bounded response. A
malformed or out-of-policy decision is rejected; it cannot change the stage or policy.

## Pilot evidence

The existing calibrated corpus is the behavioral oracle. The pilot must produce a fresh
15-turn local Luna student/teacher transcript and one trace per turn. The checker is the
final learner-visible gate. The transcript and trace are committed only after the gate
passes; no score or mastery is inferred from this pilot.

## Out of scope

No other unsupported DSA problem, no generic compiler, no new canonical teaching asset,
no hosted child task, and no model-generated mastery/progression state.
