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

## ChatGPT app setup

OpenAI’s current Developer Mode guidance says ChatGPT cannot connect directly
to a localhost MCP server; a private developer-machine server should use
Secure MCP Tunnel. In a supported Business or Enterprise/Edu workspace:

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
