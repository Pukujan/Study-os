# FOSSIL Integration Boundary

## Decision

**Study OS owns a dedicated learning schema. FOSSIL is an optional export/promotion target, not a required runtime dependency.**

Do not send every learner micro-event directly through FOSSIL ingest.

## Why FOSSIL fits well

FOSSIL is well matched to durable knowledge that needs:

- immutable evidence/provenance;
- lifecycle/status handling;
- citations and source lineage;
- promoted research claims;
- durable lesson/research knowledge;
- temporal history and supersession;
- rebuildable search/graph projections.

Examples of good FOSSIL candidates:

- a validated DSA concept definition;
- a lesson-level instructional hypothesis;
- a repeated observation that a representation helps under a specific failure mode;
- a curated Golden Learning Trajectory summary;
- a research conclusion about Study OS methodology;
- external pedagogical research used to justify an intervention.

## Why FOSSIL should not be the primary Study OS event store

Learning sessions produce high-frequency, subject-specific events such as:

- attempts;
- hint requests;
- state predictions;
- timing;
- representation switches;
- learner self-reports;
- assessment scores;
- assistance levels;
- delayed recall;
- hidden transfer outcomes.

These require a domain-specific schema and are often too granular to model cleanly as general knowledge claims/events.

Making FOSSIL mandatory for every interaction would also couple the learning experiment to FOSSIL runtime/indexing availability. Study OS should remain usable if FOSSIL is offline.

## Canonical ownership

### Study OS canonical evidence

- exact raw transcript/export bytes;
- normalized transcript;
- append-only learning event log;
- learning episodes;
- assessment attempts;
- representation versions;
- learner-state derivations.

### FOSSIL-derived/promoted knowledge

- curated claims;
- research summaries;
- lesson knowledge packs;
- selected trajectories;
- provenance-preserving promoted findings.

Therefore:

`raw evidence -> Study OS canonical schema -> derived episodes/state -> optional FOSSIL export`

Do not dual-write Study OS and FOSSIL as two canonical databases.

## Pack boundaries

Study OS should use pack-like boundaries locally even before exporting to FOSSIL:

```text
domains/dsa/_knowledge/
domains/dsa/sliding-window/_knowledge/
domains/dsa/sliding-window/lessons/<lesson>/_knowledge/
sessions/<date>/<session>/knowledge/
```

Their semantics differ:

- **domain knowledge** — durable subject-matter knowledge;
- **concept knowledge** — concept-specific definitions, invariants, relationships, examples;
- **lesson knowledge** — instructional hypotheses and representation design;
- **session knowledge** — observations about one learner at one time.

Session-specific claims must not silently become universal lesson/domain claims.

## Promotion model

Use explicit promotion rather than automatic copying:

`session observation -> repeated observation -> lesson hypothesis -> replicated instructional finding`

Every promotion should preserve source episode/session IDs.

## Proposed FOSSIL adapter

Later add a small adapter:

```text
tools/fossil-export/
  export_session.py
  export_lesson.py
  mappings/
```

The adapter should read Study OS canonical data and emit FOSSIL-compatible events/packs. It must be rebuildable; deleting the FOSSIL export must not destroy learning evidence.

## Transcript ingest decision

The transcript-ingest plugin should **first ingest into Study OS**.

Optional behavior:

1. save immutable/raw transcript;
2. create normalized transcript and manifest;
3. append observed/self-reported events;
4. propose derived learning episodes;
5. validate/confirm important labels;
6. optionally run a `fossil-export` step for promoted knowledge.

Do not call FOSSIL ingest as the first or only persistence path.

## Revisit condition

Consider making FOSSIL more central only if its ingest/query runtime becomes sufficiently reliable and the Study OS learning schema can map without losing domain-specific detail. Even then, keep raw transcript evidence independently recoverable.
