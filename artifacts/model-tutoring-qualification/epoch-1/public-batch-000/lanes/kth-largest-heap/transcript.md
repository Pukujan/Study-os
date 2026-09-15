# All-DSA model tutoring transcript

This artifact records model-generated tutoring harness exchanges and their generic plan references. It is not human learning or mastery evidence.

## Kth Largest Element (`kth-largest-heap`)

**Problem:** Find the kth largest value using a min-heap of size k.

**Plan run:** all-dsa-09552fa9f3f0463d9c52455e95420a89

### Exchange 1

**Learner**

Why do we use a min-heap if we’re looking for the largest values?

**Study OS teacher**

```text
nums = [3, 1, 5, 2, 4], k = 2

value  heap (minimum at root)
3       [3]
1       [1, 3]
5       [1, 3, 5] → [3, 5]
2       [2, 3, 5] → [3, 5]
4       [3, 4, 5] → [4, 5]

final heap root: 4
```

We keep only the largest `k` values. Among those retained values, the smallest one is the kth largest overall. A min-heap keeps that smallest retained value at the root, so whenever `heap` grows beyond `k`, we can remove the root. Here, the final retained values are `[4, 5]`, and the root `4` is the 2nd-largest value.

### Exchange 2

**Learner**

So should I use a max-heap and remove the biggest value when the heap gets too large?

**Study OS teacher**

```text
nums = [3, 1, 5, 2, 4], k = 2

value  heap after insert  heap after trimming
3      [3]               [3]
1      [1, 3]             [1, 3]
5      [1, 3, 5]          [3, 5]
2      [2, 3, 5]          [3, 5]
4      [3, 4, 5]          [4, 5]

answer = heap[0] = 4
```

Use a min-heap of size `k`. Insert each value into `heap`; whenever its size exceeds `k`, remove the root, which is the smallest retained value. This keeps the largest `k` values, so the root is the kth largest.
