# P1 Secure MCP Integration

Last updated: 2026-08-24

## Goal

Connect ChatGPT to the canonical Study OS runtime in WSL without exposing WSL as a public service and without putting GitHub or FOSSIL in the live study/checkpoint/resume path.

P0 is accepted and merged. The P1 acceptance target is now:

`Chat A -> Study OS writes -> checkpoint -> fresh Chat B -> resume -> subsequent write/checkpoint`

A fresh Chat B must recover the accepted checkpoint and `next_action` from Study OS without replaying the Chat A transcript.

## Network shape

```text
ChatGPT custom MCP app
        |
        v
OpenAI Secure MCP Tunnel
        |
        v
tunnel client running inside WSL
        |
        v
http://127.0.0.1:8765/mcp
        |
        v
Study OS semantic MCP adapter
        |
        v
StudyOSService
        |
        +--> SQLite canonical learner state
        +--> private immutable evidence store
```

The tunnel client should run in the same WSL environment as Study OS. That lets the Study OS HTTP listener remain bound to loopback only; no `0.0.0.0`, LAN listener, router forwarding, or public quick tunnel is required.

## Transport implementation

P1 adds an optional network stack while preserving the accepted P0 stdio path:

- `src/study_os/mcp/server.py` remains the dependency-free semantic MCP boundary used by P0.
- `src/study_os/mcp/network.py` adapts that same boundary to MCP 2.0 Streamable HTTP.
- `cli/study_os.py mcp-http` is the stable local launcher.
- `tools/verify_mcp_endpoint.py` performs a sanitized auth/tool-surface check without printing secrets.
- the frozen semantic contract remains `contracts/study-os-mcp-tools.v0.1.json`.

The network layer must not implement learner semantics independently. Every network tool delegates to the accepted P0 semantic boundary/service.

## Security invariants

1. Bind the Study OS HTTP service only to a loopback address. The provided launcher fixes the host to `127.0.0.1`.
2. Require `STUDY_OS_MCP_BEARER_TOKEN`; there is no CLI token argument, committed default, or public token fixture.
3. Authenticate before MCP request parsing or tool dispatch.
4. Use constant-time bearer comparison and generic HTTP 401 responses. Never reflect the secret.
5. Expose only `/mcp`. Do not add a parallel public health, admin, OpenAPI, SQL, shell, filesystem, or arbitrary code-execution surface.
6. Keep the 13 semantic tool names exactly aligned with contract `0.1.0`.
7. Keep request bodies bounded. The default MCP body limit is 1 MiB.
8. Preserve MCP transport Host/Origin protections; production uses the MCP SDK transport-security defaults.
9. Do not commit `.env`, bearer tokens, tunnel credentials, generated learner data, or raw private transcripts.
10. Do not use an accountless/public quick tunnel as the production Study OS path.

## Reference implementation evidence

The transport/security pattern was cross-checked against the sanitized FOSSIL cloud handoff:

- repository: `Pukujan/fossil-core`
- branch: `codex/public-mcp-cloud-handoff`
- handoff commit: `61c3bceb9c2ed33b0453b0c55a7009c08a65e132`
- reviewed network PR #236 head: `ff1524c67e968019da13b957456ebb8e21b5357a`

That FOSSIL handoff verified bearer failure/success behavior, frozen MCP tool discovery, non-MCP route isolation, and an external verifier. Study OS reuses the boundary pattern only; FOSSIL remains optional and is not a live runtime dependency.

## Install the optional network stack in WSL

From the Study OS repository:

```bash
python3 -m pip install -e '.[network]'
```

Generate or load a strong bearer secret from a local secret store. A shell-only example that does not embed the resulting value in the command itself is:

```bash
export STUDY_OS_MCP_BEARER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

If the token must survive shell restarts, store it in a private local secret mechanism. Do not put the value in this public repository.

## Start and verify the local MCP edge

Terminal A, inside WSL:

```bash
PYTHONPATH=src python3 cli/study_os.py mcp-http --port 8765
```

Terminal B, with the same bearer token loaded:

```bash
python3 tools/verify_mcp_endpoint.py --url http://127.0.0.1:8765/mcp
```

The verifier must report:

- missing bearer -> HTTP 401;
- wrong bearer -> HTTP 401;
- valid bearer -> HTTP 200;
- exact 13-tool Study OS surface;
- no bearer reflection;
- tested non-MCP routes blocked.

## Secure MCP Tunnel and ChatGPT app

Current OpenAI product guidance says ChatGPT does not connect directly to a localhost MCP server. For a developer machine/private network, use Secure MCP Tunnel rather than publishing the server to the internet.

Use the current OpenAI UI/documentation rather than hard-coding tunnel-client commands into this public repository because tunnel setup and entitlements can change.

High-level setup:

1. In the OpenAI Platform organization associated with the ChatGPT workspace, create/authorize a Secure MCP Tunnel.
2. Run the tunnel client inside WSL and point its local target at `http://127.0.0.1:8765/mcp`.
3. In ChatGPT Developer Mode, create a custom MCP app using the tunnel connection.
4. Configure Bearer/API-key authentication using the same locally managed Study OS bearer secret, without committing it.
5. Scan tools and verify the app sees exactly the 13 Study OS operations.
6. Keep the app private/draft until the P1 cross-session acceptance test passes.

Official product reference (verify before setup because availability changes):
`https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt-beta`

As of 2026-08-24, full MCP write/modify actions are documented for Business and Enterprise/Edu; Pro supports custom MCP read/fetch permissions rather than the full write surface. P1 cannot satisfy its live write/checkpoint acceptance criteria on a surface that only permits read/fetch.

## P1 acceptance procedure

### Chat A

Use a synthetic/private-safe first integration subject if desired before real learning.

1. `doctor` returns healthy.
2. `start_session` creates a session.
3. Record baseline/attempt evidence.
4. Record an intervention if one is used.
5. Record a behavioral assessment.
6. Create an evidence-backed checkpoint with a distinctive `next_action`.
7. Record the returned checkpoint ID outside the chat only for test comparison; do not copy the transcript.

### Fresh Chat B

Start a genuinely fresh ChatGPT conversation with no Chat A transcript pasted into it.

1. Select/enable the Study OS custom app.
2. Call `resume(subject_id)` before relying on conversational memory.
3. Verify the returned checkpoint ID exactly matches Chat A.
4. Verify `next_action` exactly matches Chat A's checkpoint.
5. Continue with that next action.
6. Write at least one subsequent learning event/attempt and a new checkpoint.

### Process restart

Stop the Study OS HTTP process, start it again against the same `STUDY_OS_ROOT`, and repeat `resume`. Continuity must survive the restart.

## P1 completion criteria

P1 is complete only when all of the following are demonstrated on the real ChatGPT-to-WSL path:

- secure/private authenticated tunnel path works;
- exact 13-tool contract is discovered;
- Chat A can perform required write actions;
- Chat A creates an evidence-backed checkpoint;
- fresh Chat B resumes the same checkpoint without transcript replay;
- `next_action` matches exactly;
- Chat B can perform a subsequent durable write/checkpoint;
- restart does not break resume;
- no GitHub commit or FOSSIL call is needed in the live path;
- no raw private learner transcript or secret is pushed to the public repository.
