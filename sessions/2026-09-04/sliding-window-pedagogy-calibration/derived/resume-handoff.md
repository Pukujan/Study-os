# Resume handoff — sliding-window pedagogy calibration

## Current learner-facing state

Active concept: relation between `sum[i]` and `sum[i+1]` for a fixed-size window.

Do **not** advance to a more general recurrence or code yet unless the learner demonstrates this relation is stable.

The last accepted representation was exactly:

```text
index(i):      0   1   2   3   4   5
numbers(a):   [4,  7,  2,  6,  1,  9]
               ↑   ↑   ↑
               └── box ──┘
               sum[i] = 13

                     ↓

index(i):      0   1   2   3   4   5
numbers(a):   [4,  7,  2,  6,  1,  9]
                   ↑   ↑   ↑
                   └── box ──┘
                   sum[i+1] = 15
```

Then only:

`7 + 2 + 6 = 15`

is the same as:

`13 - 4 + 6 = 15`

The learner explicitly marked this form as “perfect”.

## Teaching calibration rules established in this session

- One visual → one relation → one tiny question.
- If the diagram already carries the meaning, do not explain the diagram again.
- Do not introduce the next idea before the current relationship is stable.
- Keep the same representation/layout while teaching a relation; do not switch diagrams unnecessarily.
- Keep the box visible while `sum[i]` is still being learned.
- Explanation/correction diagrams may include arrows/help.
- Exercise diagrams must remove cues that reveal the answer.
- After an incorrect response: show the correct answer visually, retry with a different example, then verify again before advancing.
- Avoid extra prose; the learner reports that over-explanation creates noise even when the underlying concept is understood quickly.

## Important failure immediately before the accepted form

The tutor repeatedly failed by:

- moving to `i = i + 1` before `sum[i]` was stable;
- omitting the box;
- explaining the recurrence before visually establishing equivalence;
- replacing the learner-selected chart with another chart;
- adding prose after the visual already carried the needed meaning.

Treat these as controller/representation failures, not learner failures.

## Suggested first action in a fresh session

Resume by showing the accepted chart above and ask one tiny question that verifies the equivalence without introducing a new concept.

Do not claim mastery from the current transcript alone.
