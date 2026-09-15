# PIR mutation trust-boundary audit

This audit treats mutation testing as evidence about the deterministic PIR
trust boundary, not as a score-optimization exercise.

## Evidence

The pre-audit GitHub run (source revision `41611dc`) reported 1,383 mutants:
1,105 killed and 278 survived. Of those survivors, 83 were unclassified and
all 83 were in the presentation-contract additions to `pir/controller.py`:

| Surface | Survivors | Meaning |
| --- | ---: | --- |
| `_starts_with_visual` | 11 | visual-first detection and blank handling |
| `validate_asset` | 55 | variable, relation, visual, budget, check, and forbidden-term validation |
| bundle/turn propagation | 17 | learner-visible contract and relation metadata propagation |

Targeted contract tests were added to
`tests/test_pir_mutation_semantics.py`. They exercise the real learner-visible
invariants: approved visual prefixes, blank and case-sensitive rejection,
variable-map and forbidden-alias rules, one relation per turn, relation ids,
visual presence/order, strict prose limits, tiny checks, verbatim rendering,
and propagation through nonterminal, expansion, and terminal paths.

The same mutation run was then repeated locally under WSL with the exact CI
selection:

```
total=1383, killed=1169, survived=214
diagnostic=134, equivalent=80, unclassified=0
```

There were no `no_tests`, skipped, suspicious, timeout, interrupted, or
segfault results. `tools/check_pir_mutation_results.py` exited 0, and the
audited production source blob for `src/study_os/pir/controller.py` remained
unchanged.

## Explicit equivalence decisions

The 21 newly classified survivors are equivalent/noise, with reasons recorded
in the gate source:

* omitted `render_mode` and `response_turn_id=None` select model defaults;
* the blank visual sentinel `"XXXX"` still rejects the same input as `""`;
* the automatic-hop counter is redundant because unique-step tracking fails
  cycles and an acyclic graph cannot exceed `len(step_by_id)` hops;
* several mutations change diagnostic text only;
* the terminal status bundle has no response turn or instructional content, so
  its optional presentation metadata does not change learner-visible behavior;
* the assessment fallback is unreachable for a probe because `assessment_id`
  is required and non-empty, and natural ordering of `StrEnum` outcomes matches
  ordering by `.value`.

No production controller behavior was changed to make the mutation report
green. The meaningful presentation invariants are now proven by tests; the
remaining survivors are explicitly justified rather than hidden.
