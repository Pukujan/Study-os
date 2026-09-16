# All-DSA model tutoring transcript

This artifact records model-generated tutoring harness exchanges and their generic plan references. It is not human learning or mastery evidence.

## Kth Largest Element (`kth-largest-heap`)

**Problem:** Find the kth largest value using a min-heap of size k.

**Plan run:** all-dsa-db1bb0432b5342b3bb212b090255e672

### Exchange 1

**Learner**

When the heap already has k items, do we remove the smallest whenever a bigger number comes in?

**Study OS teacher**

Visual:
Top k values, in descending order:
[largest ... | kth largest]
              ↑ target rank k

Yes. Once there are k candidates, the smallest of those k is the cutoff. If the next value is larger than that cutoff, remove the cutoff and include the new value; otherwise, keep the candidates unchanged. This keeps the requested value at descending rank k.

### Exchange 2

**Learner**

So if the next value is smaller, I should still pop the heap to make room for it?

**Study OS teacher**

Visual:
Descending top-k candidates:
[largest ... | kth largest]
                    ↑ cutoff at rank k

No. If the next value is smaller than the cutoff, keep the k candidates unchanged. Remove the cutoff only when the next value is larger, so the cutoff remains the value at descending rank k.

### Exchange 3

**Learner**

Okay, so I only replace the smallest when the new number is bigger; otherwise I leave the heap alone.

**Study OS teacher**

Visual:
nums ordered from largest to smallest:
[largest ... | value at descending position k]
                         ↑ requested result

Right: replace the smallest candidate only when the new number is bigger. The key idea is that the answer is the value at descending rank k among nums. In one short phrase, what does “kth largest” mean?

### Exchange 4

**Learner**

It means the number that has exactly k−1 numbers larger than it.

**Study OS teacher**

Visual:
nums ordered from largest to smallest:
[1st ... | kth]
             ↑ requested value at descending rank k

Exactly: the kth-largest value is the one with k−1 values in nums larger than it.
