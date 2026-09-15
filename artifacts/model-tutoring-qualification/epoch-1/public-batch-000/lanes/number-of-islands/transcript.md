# All-DSA model tutoring transcript

This artifact records model-generated tutoring harness exchanges and their generic plan references. It is not human learning or mastery evidence.

## Number of Islands (`number-of-islands`)

**Problem:** Count connected groups of 1s in a 2D grid using 4-direction adjacency.

**Plan run:** all-dsa-8fd0557ba8904d0c97a5dce98466cb89

### Exchange 1

**Learner**

How do I know when two 1s belong to the same island?

**Study OS teacher**

```\n1 1 0\n0 1 0\n```\n\nLabel cells by coordinates `(r, c)`. From `(r, c)`, inspect only `(r-1, c)`, `(r+1, c)`, `(r, c-1)`, and `(r, c+1)`. Two 1s belong to the same island when a chain of 1-cells connects them through these four positions. Here, `(0, 0)` connects to `(1, 1)` through `(0, 1)`. Which four positions would you inspect from `(0, 1)`?
