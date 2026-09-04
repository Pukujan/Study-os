# Golden teaching sequence — beginner sliding-window foundations v0.1

Status: learner-calibrated golden fixture from live Study OS use on 2026-09-04.

Scope: teach only the representation needed to understand a fixed-size sliding window before introducing the recurrence/code. Do not infer mastery from this fixture.

## Controller rules

1. Teach one concept at a time.
2. Keep wording short and concrete.
3. Use the same small ASCII diagram throughout.
4. Arrows/circles are for **introducing** a concept or **explaining/correcting** an answer.
5. Do **not** put arrows/circles that reveal the answer in an exercise diagram.
6. If the learner is wrong: give the right answer, show why with the diagram, say it is okay, and retry with a different example.
7. If the learner gets the retry right after an error: ask one more different example before advancing.
8. If the learner is right: show why with the diagram, then use another exercise when confirmation is useful.
9. Keep the `box` representation until `sum[i]` is understood; do not remove it prematurely.
10. Introduce `k` before using `i` to move the box.
11. Introduce `sum[i]` only after the learner can reliably identify box contents from `i` and `k`.
12. Avoid examples where an array value and its index are the same when that coincidence creates unnecessary cognitive load.

---

## Step 0 — state the problem and introduce `a`

We’re learning how to solve this question:

**Find the largest sum of any 3 numbers next to each other in the array.**

I’ll help you learn this step by step.

```text
numbers(a): [4, 7, 2, 6, 1, 9]
```

`a = numbers`

Ask: **Are you ready?**

---

## Step 1 — position `p`

Introduce with arrows:

```text
                  p = 3
                    ↓
positions(p):  1  2  3  4  5  6
numbers(a):   [4, 7, 2, 6, 1, 9]
                    ↑
                  a = 2
```

Say:

`number(a)` is `2` and its `position(p)` is `3`.

Then exercise **without answer arrows**:

```text
positions(p):  1  2  3  4  5  6
numbers(a):   [4, 7, 2, 6, 1, 9]
```

Ask:

**What is `position(p)` of `number(a) 6`?**

### Correct-feedback example

If learner says `4`:

Correct — **4**.

```text
                  p = 4
                        ↓
positions(p):  1  2  3  4  5  6
numbers(a):   [4, 7, 2, 6, 1, 9]
                        ↑
                      a = 6
```

`number(a)` is `6` and its `position(p)` is `4`.

Then ask another position without arrows.

### Wrong-feedback example

If learner gives a wrong answer for `9`:

The right answer is **6**.

```text
                  p = 6
                              ↓
positions(p):  1  2  3  4  5  6
numbers(a):   [4, 7, 2, 6, 1, 9]
                              ↑
                            a = 9
```

`number(a)` is `9` and its `position(p)` is `6`.

It’s okay, let’s keep trying.

Then ask a different number without arrows. After the learner gets that retry right, ask one more to make sure before advancing.

---

## Step 2 — index `i`

Introduce index after position is stable.

Use index as the isolated top row and visually group the same array column:

```text
                  i = 2
                    ↓
index(i):      0  1  (2)  3  4  5
positions(p):  1  2  (3)  4  5  6
numbers(a):    4  7  (2)  6  1  9
                    ↑
                  p = 3
                  a = 2
```

Say only:

`index(i) = position(p) - 1`

`i = p - 1`

Exercise without arrows/circles:

```text
index(i):      0  1  2  3  4  5
positions(p):  1  2  3  4  5  6
numbers(a):    4  7  2  6  1  9
```

Ask:

**What is the `index(i)` of `number(a) 6`?**

If correct, show the matching column with arrows/circles:

```text
                  i = 3
                       ↓
index(i):      0  1  2  (3)  4  5
positions(p):  1  2  3  (4)  5  6
numbers(a):    4  7  2  (6)  1  9
                       ↑
                     p = 4
                     a = 6
```

Repeat with another number before advancing.

---

## Step 3 — box size `k`

Do not move the box with `i` yet.

Say:

`k` = how many numbers go inside the box.

Here:

`k = 3`

```text
index(i):      0   1   2   3   4   5
numbers(a):   [4,  7,  2,  6,  1,  9]
               ↑   ↑   ↑
               └─ box ─┘
                 k = 3
```

Ask:

**What numbers are inside the box?**

After a correct answer, show why with the same box diagram.

Then remove the box help and vary `k`:

```text
index(i):      0   1   2   3   4   5
numbers(a):   [4,  7,  2,  6,  1,  9]

k = 5
```

Ask:

**What numbers go inside the box?**

If wrong, show the correct box:

```text
index(i):      0   1   2   3   4   5
numbers(a):   [4,  7,  2,  6,  1,  9]
               ↑   ↑   ↑   ↑   ↑
               └──── box ─────┘
                    k = 5
```

Say: `k = 5` means the box holds **5 numbers**.

Retry with another `k`, then verify once more after recovery.

---

## Step 4 — `i` moves the box

Only after `k` is understood, say:

`i` = where the box starts.

Introduce at `i = 0`:

```text
index(i):      0   1   2   3   4   5
numbers(a):   [4,  7,  2,  6,  1,  9]
               ↑   ↑
               i = 0
               └─ k = 2 ─┘
```

Here, the box starts at `i = 0`.

Then show a moved box and make the second diagram an exercise:

```text
index(i):      0   1   2   3   4   5
numbers(a):   [4,  7,  2,  6,  1,  9]
                   ↑   ↑
                   i = 1
                   └─ k = 2 ─┘
```

Ask:

**What numbers are inside the box now?**

After learner succeeds, remove arrow/box answer help for the next exercise:

```text
index(i):      0   1   2   3   4   5
numbers(a):   [4,  7,  2,  6,  1,  9]

i = 3
k = 2
```

Ask:

**What numbers go inside the box?**

If wrong, show the exact start and box with arrows, then retry a different `i`/`k`. If the retry is correct after an error, verify once more before advancing.

---

## Step 5 — `sum[i]`

Keep the box visible.

Say:

Now we introduce `sum[i]`.

```text
index(i):      0   1   2   3   4   5
numbers(a):   [4,  7,  2,  6,  1,  9]
                       ↑   ↑   ↑
                       └── box ──┘
                         k = 3
                       sum[i=2]
```

`sum[i=2]` = add the numbers inside this box.

Ask:

**What is `sum[i=2]`?**

If learner answers `2 + 6 + 1`, confirm the arithmetic result and show the same diagram:

`sum[i=2] = 2 + 6 + 1 = 9`

Then test a changed `i`/`k` without box-answer arrows:

```text
index(i):      0   1   2   3   4   5
numbers(a):   [4,  7,  2,  6,  1,  9]

i = 2
k = 2
```

Ask:

**What is `sum[i=2]`?**

If learner gives only the box contents (`2 6`) rather than the sum, treat that as partial success:

Those are the right numbers: **2 and 6**.

Then show the box and ask only:

`2 + 6 = ?`

After the learner gets `8`, confirm:

`sum[i=2] = 2 + 6 = 8`

Then verify with another example such as `i = 3`, `k = 3`.

---

## What this fixture intentionally does not do yet

- It does not introduce the sliding-window recurrence.
- It does not introduce Python loop syntax.
- It does not claim mastery.
- It does not remove the box representation before the learner can use `sum[i]` correctly.
- It does not advance after a single corrected response when a previous error showed uncertainty.

The next concept should be introduced only after this foundation is stable: relate consecutive `sum[i]` values and derive the update rule from the learner’s existing `i`, `k`, box, and `sum[i]` representation.
