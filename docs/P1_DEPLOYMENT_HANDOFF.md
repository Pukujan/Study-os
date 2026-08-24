# P1 Deployment Handoff

Status: **sanitized deployment topology only**

Last updated: 2026-08-24

This document records enough of the working P1 deployment topology for cloud/repository agents to maintain the public code without placing local credentials, host secrets, or machine-specific service definitions in the public repository.

## Verified public code lineage

- Repository: `Pukujan/Study-os`
- P1 branch: `codex/p1-http-mcp-transport`
- P1 pull request: #7 — `[P1] Connect Study OS MCP through loopback HTTP`
- Locally deployed P1 code was reported at commit `79db090ea72c7be6c900a2a7113c90b95b2da0fe` before this documentation-only handoff commit.
- The P1 transport wraps the existing Study OS semantic service; it does not replace SQLite, evidence storage, checkpoint semantics, or the 13-tool contract.

## Stable external endpoint

The current stable external hostname is:

```text
study-os.design-bakery.com
```

The public hostname is an authenticated transport boundary to the local Study OS runtime. It is **not** the canonical learner store. Canonical live learner state remains in the local Study OS SQLite runtime and private evidence store.

Do not assume the public repository contains enough information to recreate the external endpoint account configuration automatically.

## Local runtime topology

The intended deployed path is conceptually:

```text
ChatGPT / Study OS Tutor
        |
        | authenticated HTTPS
        v
study-os.design-bakery.com
        |
        | Cloudflare tunnel / account configuration
        v
WSL loopback Study OS HTTP adapter
        |
        v
existing Study OS semantic service
        |
        +--> SQLite canonical learner state
        +--> private evidence store
```

The HTTP adapter must remain bound to loopback on the WSL host. Do not change the public repository to bind the Study OS runtime directly to `0.0.0.0` merely to simplify tunneling.

## Intentionally local/private deployment state

The following are **not stored in the public repository** and must stay out of Git history:

- Cloudflare tunnel credentials;
- Cloudflare API tokens;
- `.env` secrets;
- bearer/authentication secrets used by the Study OS HTTP/GPT Action boundary;
- WSL systemd service files stored under ignored `.study-os-private/`;
- Windows startup trigger/configuration;
- GPT Action authentication/configuration inside ChatGPT;
- Cloudflare DNS/tunnel account configuration.

Cloud/repository agents should never fabricate these values from placeholders or replace them with public defaults.

## What cloud/repository agents can maintain

Cloud agents can safely maintain and review:

- `src/study_os/mcp/http_server.py`;
- the loopback-only HTTP/MCP/Actions behavior;
- semantic dispatch to the existing 13 Study OS operations;
- `tools/generate_gpt_actions_schema.py`;
- repository tests for the HTTP adapter and GPT Actions schema;
- public integration documentation;
- contract compatibility and regression tests;
- sanitized deployment verification procedures that do not print secrets.

Cloud agents cannot prove the local service manager, Windows startup task, Cloudflare account state, DNS state, tunnel credentials, or ChatGPT-side secret configuration merely by inspecting GitHub.

## ChatGPT integration modes

PR #7 documents two compatible transport surfaces around the same semantic runtime:

1. MCP HTTP at the configured `/mcp` path for a supported custom MCP app/tunnel path.
2. GPT Actions JSON endpoints under `/actions/<tool_name>` for the working GPT Actions integration path.

The semantic source of truth remains the existing Study OS service and `contracts/study-os-mcp-tools.v0.1.json`; transport wrappers must not introduce a second learner-state implementation.

## Reported P1 continuity result

The PR #7 integration documentation records a controlled verification in which:

1. Chat A created durable Study OS state and an accepted checkpoint.
2. A fresh Chat B recovered the exact checkpoint and learner state without transcript replay.
3. Chat B wrote a subsequent learning event and advanced the checkpoint.

This validates the continuity mechanism. It does not, by itself, validate the richness or correctness of the learner model, curriculum, automatic instrumentation policy, or pedagogical decisions.

## Operational safety invariants

- Keep canonical learner data local/private.
- Keep secrets out of Git.
- Keep the WSL Study OS service loopback-only.
- Require authentication at the external/action boundary.
- Preserve the exact semantic-tool allowlist unless a versioned contract change is intentionally approved.
- Do not expose generic SQL, shell, filesystem mutation, or code-execution tools.
- Do not make GitHub, Cloudflare, or FOSSIL the canonical live learner database.
- Do not infer local deployment health solely from GitHub CI.

## When public transport code changes

Before accepting a transport change:

1. run repository/contract/unit tests;
2. validate the loopback HTTP adapter locally;
3. confirm authentication still fails closed;
4. verify the generated GPT Actions schema still maps to the intended semantic contract;
5. perform a sanitized external smoke test through `study-os.design-bakery.com` from an authorized client;
6. if learner writes are affected, repeat fresh-chat checkpoint/resume continuity.

Do not place tokens, tunnel credentials, `.env` contents, GPT Action secrets, Cloudflare account IDs, or machine-specific private service definitions into test logs or issue comments.

## Local-only recovery information

If the deployment fails after a reboot or local machine change, cloud agents should ask the local operator/Luna to inspect the private deployment layer rather than guessing. Relevant state may exist in:

- ignored `.study-os-private/` service definitions;
- WSL service manager state;
- Windows startup configuration;
- Cloudflare tunnel/DNS account state;
- ChatGPT GPT Action authentication/configuration.

Those locations are intentionally outside the public maintenance boundary.
