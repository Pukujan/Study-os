# P1 ChatGPT ↔ WSL MCP Integration

This document covers only the P1 transport/integration layer. The SQLite,
evidence, service, migration, and 13-tool semantic contract remain unchanged.

## Local endpoint

The runtime now has a loopback-only Streamable HTTP adapter around the existing
`MCPServer`:

```bash
cd ~/Study-os
STUDY_OS_ROOT=~/.study-os PYTHONPATH=src \
  python3 cli/study_os.py mcp-http \
  --host 127.0.0.1 \
  --port 8765 \
  --path /mcp
```

Local MCP endpoint:

```text
http://127.0.0.1:8765/mcp
```

The server binds only to loopback. It rejects non-allowed `Origin` values and
can require a bearer token from `STUDY_OS_HTTP_BEARER_TOKEN`. Do not bind this
server to `0.0.0.0` or expose the local port directly to the public internet.

The expected remote URL is supplied by Secure MCP Tunnel. The tunnel must
forward to the local `/mcp` endpoint and provide the external authentication/
TLS boundary required by the ChatGPT app connection.

## Plus-compatible GPT Actions alternative

If the account does not expose custom MCP app registration, the same endpoint
also exposes authenticated JSON operations under `/actions/<tool_name>`. This
is a GPT Actions wrapper around the existing `MCPServer`; it does not add DB
behavior or a second service implementation.

After starting the tunnel, generate the OpenAPI schema with the exact HTTPS
base URL:

```bash
PYTHONPATH=src python3 tools/generate_gpt_actions_schema.py \
  --server-url https://YOUR-TUNNEL-HOST
```

In the GPT editor, choose Configure -> Actions -> Create new action, paste the
generated JSON, and configure Bearer authentication with the same token used
by `STUDY_OS_HTTP_BEARER_TOKEN`. The generated schema derives its operation
names and required inputs from `contracts/study-os-mcp-tools.v0.1.json`, so the
GPT Action surface remains the same 13 semantic operations.

GPT Actions currently drops unconstrained object inputs from its callable
surface. The generated Plus schema therefore declares required object inputs
(`payload`, `response`, `capability_state`, `assistance_state`, and `resume`)
as JSON-encoded strings. The `/actions` adapter decodes those fields before
dispatch; the MCP `/mcp` surface and the underlying service continue to use
native JSON objects.

This route still needs an HTTPS-reachable endpoint. A temporary public tunnel
is acceptable for a controlled test only when the strong bearer guard is
enabled; never run the action route unauthenticated.

## ChatGPT app setup

OpenAI’s current guidance says ChatGPT cannot connect directly to a localhost
MCP server; a private developer-machine server should use Secure MCP Tunnel.
For a custom MCP app in a supported workspace:

1. Enable Developer Mode for the authorized workspace account.
2. Create a custom MCP app from the workspace/user Apps settings.
3. Enter the Secure MCP Tunnel HTTPS endpoint ending in `/mcp`.
4. Configure the tunnel/app authentication requested by the workspace.
5. Scan Tools and verify the exact 13 Study OS semantic tools appear.
6. Create/enable the app for the test account.

Full MCP write/modify actions are currently documented for Business and
Enterprise/Edu. Pro can use custom MCP with read/fetch permissions, which is
insufficient for the P1 `start_session`, assessment, and checkpoint writes.

After changing the server’s exposed tools or inputs, refresh/rescan the app;
the ChatGPT workspace may retain a frozen approved tool snapshot.

Reference: [Developer mode and MCP apps in ChatGPT](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt-beta).

## P1 acceptance

Use two fresh ChatGPT conversations with the Study OS app enabled:

```text
Chat A
  -> start_session
  -> learning / attempt / assessment
  -> checkpoint
  -> close Chat A

Fresh Chat B
  -> resume
  -> same checkpoint_id and capability/assistance state
  -> same next_action
  -> continue learning
  -> checkpoint again
```

Acceptance evidence must include the tool calls/results, checkpoint IDs, and
confirmation that Chat B did not need Chat A transcript replay or a GitHub
runtime write. ChatGPT confirmation prompts for write actions are expected and
must be approved during this controlled test.

Controlled Plus verification completed on 2026-08-24: the private Study OS
Tutor GPT exposed all 13 actions; Chat A created an accepted checkpoint;
Fresh Chat B recovered the exact checkpoint, capability/assistance state,
current focus, and next action without transcript replay; it then recorded a
new learning event and advanced a second checkpoint using
`expected_current_checkpoint_id`. This proves the integration path; the
account-less Quick Tunnel used for this run is temporary and is not a
production-availability claim.
