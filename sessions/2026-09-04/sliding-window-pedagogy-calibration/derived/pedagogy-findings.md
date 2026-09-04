# Pedagogy findings — sliding-window calibration

Derived from the raw session transcript. These are hypotheses/operational findings, not learner-trait claims or population-level conclusions.

## Strongest observed teaching pattern

The learner repeatedly converged on a progressive sequence:

```text
problem statement
→ numbers(a)
→ position(p)
→ index(i)
→ box size k
→ i as box start
→ sum[i]
→ later derive sliding-window recurrence
```

The key controller behavior was not simply “use diagrams” or “use algebra.” It was **introduce one relation at a time, preserve the current representation until stable, exercise it, explain with the same representation, retry after error, verify recovery, then advance**.

## Representation findings

1. **Premature recurrence/code was costly.**
   The learner could perform the leaving/entering arithmetic but reported that the code and `S[i+1]` notation were confusing because symbol meanings had not been established individually.

2. **English + symbolic structure worked when symbols were grounded first.**
   The learner explicitly preferred simple algebraic/index structure, but not dense formulas presented before `a`, `p`, `i`, `k`, and `sum[i]` had concrete meanings.

3. **Position before zero-based index reduced one avoidable mismatch.**
   Introducing human position `p = 1..n` first, then defining `index(i) = position(p) - 1`, made the zero-based index relation explicit.

4. **Same-column visual grouping mattered.**
   The learner requested the index, position, and number values in one column to be visually grouped/circled when introducing or explaining the relationship.

5. **Arrows are explanation, not exercise decoration.**
   The learner established a precise rule:
   - use arrows/circles when introducing a concept;
   - use arrows/circles when explaining/correcting an answer;
   - remove answer-revealing arrows/circles for the exercise itself.

6. **`box` should precede moving `i`.**
   `k` first became concrete as “how many numbers go inside the box.” Introducing the moving start index at the same time was rejected as extra load. Only after `k` was stable did `i = where the box starts` become useful.

7. **Keep the box through `sum[i]`.**
   Removing the box when introducing `sum[i]` was judged too little context; adding prose/formulas was too much. The stable representation was the same box plus a compact `sum[i=...]` label.

8. **Avoid accidental index/value collisions when possible.**
   An exercise where `i = 2` and the value at that location was also `2` was identified as unnecessary cognitive load. Example selection should avoid such coincidences when teaching the distinction itself.

## Feedback/progression findings

Observed preferred controller rule:

```text
learner answer
    ↓
correct? ── yes → show why with the same diagram → confirmation exercise when needed
    │
    no
    ↓
give correct answer
→ show why with the same diagram
→ “It’s okay, let’s keep trying.”
→ different retry
→ if retry correct, ask one more to verify
→ only then advance
```

A single correct retry after an error was explicitly considered insufficient evidence to advance.

## Partial-success handling

When asked for `sum[i=2]`, the learner answered with the correct box contents (`2 6`) rather than the arithmetic result. Treating this as partial success worked better than marking the whole response wrong:

```text
Those are the right numbers: 2 and 6.
Now add them:
2 + 6 = ?
```

This preserves the correctly learned sub-operation and isolates the remaining action.

## P4 implications

This trajectory argues for keeping several pedagogical dimensions separate in evidence:

- representation (`box`, row layout, arrows/circles);
- terminology/variable naming (`numbers(a)`, `position(p)`, `index(i)`);
- decomposition/step size;
- exercise answer-reveal policy;
- retry policy;
- confirmation-before-advance policy;
- partial-credit/sub-operation evidence.

The improvement cannot be attributed to one operation such as `rename_terms` or `change_representation` alone. Multiple intervention dimensions changed across the trajectory and should remain separately identifiable in future P4 decision/outcome records.

## Next learning boundary

The learner has shown immediate success with the final representation through `sum[i]`, including changed `i` and `k` examples. Do not call this mastery. The next useful learning step is to use this existing representation to derive the relation between consecutive boxes/sums and only then map that relation to the sliding-window update/code.
