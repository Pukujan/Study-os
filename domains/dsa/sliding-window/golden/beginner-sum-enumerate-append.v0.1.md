# Golden teaching sequence — sum → enumerate → append v0.1

Status: learner-calibrated golden fixture from live Study OS use on 2026-09-04.

Scope: continue the beginner fixed-size Sliding Window sequence after `sum[i]` is stable enough to compare consecutive windows. This fixture covers only:

```text
sum[i] → sum[i+1] → sum[i+2] → sum[i+3]
↓
enumerate(a)
↓
append conversion
```

Do not infer mastery from this fixture. Do not jump to the full Python loop until these transitions are stable.

## Controller rules added/refined in this calibration

1. Keep the same problem/representation while teaching a relation.
2. Introduce only one new relation at a time.
3. Immediately follow a concept explanation with a tiny exercise.
4. Exercise diagrams must not reveal the answer.
5. After a correct answer, **show why it is correct in the same chart/diagram** before moving on.
6. After a wrong answer, show the correct answer in the same chart/diagram, then retry with a different example and verify again before advancing.
7. Do not ask detached symbol questions that are not visibly connected to the current problem.
8. Do not skip the loop bridge: first show the same algebraic action repeating as `i` changes.
9. For `enumerate(a)`, show index and number as vertically paired columns, then show the resulting `(i, num)` pairs.
10. Two successful `enumerate` checks were sufficient in this session before moving on.
11. For `append`, show that only the **storage form** changes: `S[i] = ...` becomes `S.append(...)`; the value-producing expression stays the same.
12. Short phone responses such as `S.append(...)` may be accepted when the intended structure is unambiguous, but the canonical stored answer must contain the complete correct expression.
13. Keep prose short. Prefer visual equivalence over paragraphs.

---

## Step 1 — consecutive window sums

Use the same box representation.

```text
index(i):      0   1   2   3   4   5
numbers(a):   [3,  8,  1,  5,  2,  7]
               ↑   ↑   ↑
               └── box ──┘
               sum[i] = 12

                   ↑   ↑   ↑
                   └── box ──┘
                   sum[i+1] = ?
```

Ask: **What is `sum[i+1]`?**

If learner answers `14`, show why with the same representation:

```text
index(i):      0   1   2   3   4   5
numbers(a):   [3,  8,  1,  5,  2,  7]
               ↑   ↑   ↑
               └── box ──┘
               sum[i] = 12

                   ↑   ↑   ↑
                   └── box ──┘
                   sum[i+1] = 14
```

Then only:

```text
12 - 3 + 5 = 14
```

Advance one window at a time:

```text
sum[i+1] = 14
sum[i+2] = ?
```

Then:

```text
sum[i+2] = 8
sum[i+3] = ?
```

Expected sequence for this example:

```text
sum[i]   = 12
sum[i+1] = 14
sum[i+2] = 8
sum[i+3] = 14
```

Do not replace this with a generic formula before the learner has traversed the sequence.

---

## Step 2 — show the algebraic repetition

Define:

```text
k = 3
j = k - 1 = 2
```

Formula:

```text
S[i] = S[i-1] - a[i-1] + a[i+j]
```

Show the same formula instantiated over successive `i` values:

```text
i = 1
S[1] = S[0] - a[0] + a[1+2]

i = 2
S[2] = S[1] - a[1] + a[2+2]

i = 3
S[3] = S[2] - a[2] + a[3+2]
```

The learning target here is simply:

```text
same formula
↓
new i each turn
↓
repeat
```

That repetition is the bridge to a loop.

Do not jump from the recurrence directly to a full Python loop.

---

## Step 3 — `enumerate(a)`

Introduce `enumerate(a)` visually:

```text
numbers(a):      [4,  7,  2,  6,  1,  9]

enumerate(a)
      ↓

index(i):         0      1      2      3      4      5
                  │      │      │      │      │      │
number(num):      4      7      2      6      1      9
                  │      │      │      │      │      │
pair:            (0,4)  (1,7)  (2,2)  (3,6)  (4,1)  (5,9)
```

Say:

`enumerate(a)` goes through `a` and gives the **index and number together**.

Then:

```python
for i, num in enumerate(a):
```

means each turn takes one `(index, number)` pair.

### Exercise 1

Keep the chart visible. Ask:

**When the loop reaches `a = 6`, what pair does `enumerate(a)` give us?**

Expected: `(3, 6)`.

After the answer, show why in the chart by visually marking the `3`, `6`, and `(3,6)` column.

### Exercise 2

Use a different array:

```text
numbers(a):      [5,  2,  8,  4,  7,  1]

enumerate(a)
      ↓

index(i):         0      1      2      3      4      5
                  │      │      │      │      │      │
number(num):      5      2      8      4      7      1
```

Ask:

**When the loop reaches `a = 8`, what pair does `enumerate(a)` give us?**

Expected: `(2, 8)`.

After the answer, show why in the same chart, including the pair row:

```text
pair:            (0,5)  (1,2) [(2,8)] (3,4)  (4,7)  (5,1)
```

Two successful checks were enough for this session.

---

## Step 4 — convert indexed assignment to `append`

Start from the learner's recurrence:

```text
S[i] = S[i-1] - a[i-1] + a[i+j]
```

Show the mapping visually:

```text
Algebra:

S[i] = S[i-1] - a[i-1] + a[i+j]
        └────────────────────────┘
              value to store
```

```text
Append:

S.append( S[i-1] - a[i-1] + a[i+j] )
          └────────────────────────┘
                same value
```

The teaching point is only:

```text
S[i] = ...
   ↓
S.append(...)
```

The expression on the right does not change.

### Exercise 1

```text
S[i] = S[i-1] + a[i]
```

Ask the learner to convert it to append form.

Canonical answer:

```python
S.append(S[i-1] + a[i])
```

If the learner gives a shortened phone answer such as `S.append(...)`, accept it only if the intended transformation is clear, then show the full canonical answer and why it is correct.

### Exercise 2

```text
S[i] = S[i-1] + num
```

Canonical answer:

```python
S.append(S[i-1] + num)
```

Again, show why:

```text
Algebra:
S[i] = S[i-1] + num
        └────────────┘
          value to store

Append:
S.append( S[i-1] + num )
          └────────────┘
            same value
```

---

## Current next boundary

The learner has successfully traversed:

```text
consecutive sum updates
↓
algebraic recurrence repetition
↓
enumerate(a)
↓
append conversion
```

The next concept is to combine these pieces into the actual Python loop **one piece at a time**, while preserving the same controller rules. Do not dump the complete solution at once.
