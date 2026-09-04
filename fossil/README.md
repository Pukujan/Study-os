# FOSSIL Exports

This directory is reserved for **derived, rebuildable** exports from Study OS into FOSSIL-compatible knowledge packs/events.

It is not canonical Study OS storage.

Expected future structure:

```text
fossil/
  exports/
    sessions/
    lessons/
    research/
  mappings/
```

Good export candidates:

- reviewed Golden Learning Trajectory summaries;
- promoted instructional hypotheses;
- durable DSA concept knowledge;
- Study OS research conclusions;
- source/provenance records needed to reconstruct those claims.

The research export at
[`exports/research/2026-08-29-study-os-methodology.json`](exports/research/2026-08-29-study-os-methodology.json)
links a public-safe Study OS derivative to the separately preserved FOSSIL
pack `pack_study_os_personal_6a90f29fc14c83e`. It remains draft and
`not_promoted`; the full reconstructed source is not copied into this public
repository.

The follow-up export at
[`exports/research/2026-09-03-study-os-continuation.json`](exports/research/2026-09-03-study-os-continuation.json)
links the direct human-in-the-loop correction to FOSSIL pack
`pack_study_os_personal_6a996a5d178483ea`. It is also draft and
`not_promoted`; only the public-safe derivative is committed here.

Do not export every click, hint, prediction, or micro-event by default.

If this folder is deleted, Study OS must still be able to reconstruct it from canonical raw/session data.
