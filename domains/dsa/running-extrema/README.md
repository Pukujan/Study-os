# Running Extrema Curriculum Slice

This is the first executable P2 atomic curriculum slice.

It intentionally decomposes a broad task such as "find the second-largest value" into separately observable competencies, including value comparison, persistent running state, index-vs-value distinction, state-transition prediction, two-candidate maintenance, invariant explanation, update ordering, and blank implementation.

Files:

- `competencies.v0.1.json` — versioned prerequisite DAG, observable behaviors, misconceptions, task modes, and transfer targets.
- `items.v0.1.json` — versioned diagnostic/practice/public-transfer/public-retention items with complexity vectors, assistance ceilings, representations, learning operations, and grader references.

## Public-fixture boundary

Items marked `transfer_public_fixture` or `retention_public_fixture` are authoring and regression fixtures. They are **not hidden assessment items** and must not be treated as valid unseen-transfer or unseen-retention evidence after exposure through this public repository.

Future private/local hidden pools may use the same schema while remaining outside the public repository.

## Promotion boundary

This content makes selector/replay tests realistic. It does not grant any adaptive selector live authority and does not convert an item result into mastery by itself. Canonical learner evidence and checkpoint promotion remain Study OS runtime responsibilities.
