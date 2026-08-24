# Data Policy

The repository is public. Raw learning transcripts may contain private conversation content, personal details, credentials, links, or other data that should not be published accidentally.

## Default rule

**Full raw transcripts are canonical evidence, but they are private by default.**

Store raw artifacts in one of:

- a local `.study-os-private/` evidence root;
- a private repository;
- a private object/artifact store.

The public repository may contain:

- content hashes;
- session manifests with non-sensitive metadata;
- normalized/redacted transcript derivatives;
- reviewed learning events;
- reviewed learning episodes;
- learner-state derivations that do not expose unnecessary personal content;
- Golden Learning Trajectories after review/redaction.

## Public session manifest

A public manifest can reference a private artifact by content hash and logical URI without embedding its contents.

Example:

```json
{
  "path": "private://sessions/2026-08-23/220000-dsa/transcript.original.json",
  "sha256": "..."
}
```

## Ingest behavior

For a public Study OS repository, the ingest plugin must not upload raw transcript content automatically.

Default flow:

`current conversation/export -> private raw evidence -> hash -> normalized/redacted derivative -> reviewed public events/episodes`

Uploading full raw content to a public repository requires explicit user intent for that specific artifact.

## Redaction

Redaction is a derived transform; never overwrite the raw artifact. Preserve a mapping/version describing the redaction procedure when reproducibility matters.

## Subject identity

Use pseudonymous IDs (`subject-001`) in learning datasets. Do not require real names or account identifiers for the learning model.
