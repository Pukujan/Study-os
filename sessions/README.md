# Sessions

Sessions are time-bounded captures of real learning interactions.

Use:

```text
sessions/YYYY-MM-DD/<session-id>/
  manifest.json
  raw/
  normalized/
  events/
  episodes/
  derived/
  knowledge/
```

## Rules

- `raw/` is immutable evidence.
- `normalized/` is rebuildable.
- `events/learning-events.jsonl` is append-only.
- `episodes/` groups event IDs into reviewed learning episodes.
- `derived/` contains learner-state snapshots and summaries that can be recomputed.
- `knowledge/` contains only session-scoped claims/notes; promotion to lesson/concept/domain scope must be explicit.

A session is not a lesson. One session may contain several concepts/episodes; one lesson may span several sessions.
