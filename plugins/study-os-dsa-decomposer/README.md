# Study OS DSA Decomposer

This directory defines the reusable strong-inference decomposition contract for completion-driven DSA tutoring.

Files:

- `skill.md` — how Local Luna derives an algorithm graph, works backward into a learning graph, selects grounded representation/vocabulary, and emits a TeachingPlan candidate;
- `checklist.md` — post-generation acceptance checklist before learner-visible tutoring.

The intended execution order is:

```text
problem
→ skill.md strong inference
→ structured TeachingPlan candidate
→ checklist.md
→ current TeachingPlan schema + deterministic validation
→ completion-driven tutoring
```

The skill is **not** a static lesson bank and must not contain per-problem answers for the public 14-problem corpus.

This repository file is a behavioral contract for Local Luna. Registration as an external ChatGPT/plugin capability is a separate packaging concern and is not required for the local engineering loop; Local Luna can read/apply the file directly from the checkout.

Current local orchestration authority:

`docs/MODEL_TUTORING_LOCAL_AUTONOMOUS_LOOP_V1.md`

Current role/holdout isolation contract:

`contracts/model-tutoring-agent-boundaries.v0.1.json`
