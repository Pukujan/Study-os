# Agent Handoff

Last updated: 2026-08-24

## Current phase

**Research Gate R0 — P1 secure ChatGPT-to-WSL MCP continuity.**

P0 is accepted and merged. PR #6 was squash-merged to `main` as `19735a507ccdf9b29451a66bbd65b4dbff7ff84d` after target-WSL validation passed repository validation, **35/35 tests**, schema version `1`, a healthy `doctor`, and the exact 13-tool MCP contract surface.

The active integration branch is `codex/issue-5-p1-secure-mcp`. The active tracker remains Issue #5 because P1/P2 acceptance is still open.

## Immediate objective

Make the accepted local runtime usable from a fresh ChatGPT conversation without relying on ChatGPT memory or transcript replay:

```text
Chat A -> Study OS writes -> checkpoint
close Chat A
fresh Chat B -> resume -> exact checkpoint/next_action -> subsequent write/checkpoint
```

The canonical learner state remains the local Study OS SQLite database plus private evidence store.

## Current P1 implementation

The P1 branch adds transport only; it does not redesign the database or learner semantics.

- `src/study_os/mcp/server.py` — accepted P0 semantic/stdin boundary; remains dependency-free.
- `src/study_os/mcp/network.py` — optional MCP 2.0 Streamable HTTP adapter over the same service boundary.
- `cli/study_os.py mcp-http --port 8765` — stable loopback-only WSL launcher.
- `tools/verify_mcp_endpoint.py` — sanitized bearer/tool-surface verifier.
- `tests/test_p1_mcp_network.py` — network allowlist/auth tests plus fresh-client resume after service restart.
- `docs/P1_SECURE_MCP.md` — operator/integration handoff.
- optional install: `python3 -m pip install -e '.[network]'`.

The network endpoint is intentionally `http://127.0.0.1:8765/mcp`. `STUDY_OS_MCP_BEARER_TOKEN` is required. No token value, `.env`, tunnel credential, private learner data, or raw transcript belongs in this public repository.

## Transport/security reference

The P1 edge design was cross-checked against the sanitized FOSSIL handoff supplied for Cloud Codex:

- `Pukujan/fossil-core`
- branch `codex/public-mcp-cloud-handoff`
- handoff commit `61c3bceb9c2ed33b0453b0c55a7009c08a65e132`
- reviewed PR #236 head `ff1524c67e968019da13b957456ebb8e21b5357a`

That reference verified fail-closed bearer authentication, MCP 2.0 Streamable HTTP, frozen tool discovery, bounded requests, and non-MCP route isolation. Study OS adopts the boundary pattern only. FOSSIL is still **not** required to study, checkpoint, or resume.

## P1 security invariants

1. Run the tunnel client in WSL and keep Study OS bound to loopback.
2. Never bind the Study OS MCP listener to `0.0.0.0` for this architecture.
3. Require bearer authentication before MCP parsing/dispatch.
4. Keep the secret host-local/private and never accept it as a CLI argument.
5. Expose exactly the 13 approved semantic tools; no SQL, shell, filesystem, admin, or arbitrary code-execution tools.
6. Expose only the MCP route at the Study OS HTTP edge; `doctor` is an MCP semantic tool, not a public health endpoint.
7. Preserve the MCP SDK Host/Origin transport-security defaults in production.
8. Keep request bodies bounded (default 1 MiB).
9. Do not use an accountless/public quick tunnel as the production Study OS route.
10. GitHub and FOSSIL remain out of the live learner-state path.

## Canonical contracts

Read `PROJECT_MANIFEST.yaml` first. The important runtime contracts remain:

- `contracts/study-os-mcp-tools.v0.1.json`
- `docs/DATABASE_CONTRACT.md`
- `docs/ERROR_IDEMPOTENCY_CONTRACT.md`
- `docs/VALIDATION_STRATEGY.md`
- `docs/FAILURE_MODES.md`
- `docs/P1_SECURE_MCP.md`

Contract version remains `0.1.0`; SQLite schema version remains `1`.

## Important accepted runtime invariants

- Durable mutating tools require idempotency keys.
- Evidence used for derived learner state is subject-scoped.
- Representation outcomes require behavioral assessment evidence.
- Passing checkpoint capability claims require same-subject passing assessment evidence.
- `pass_unaided` requires assessment evidence with `assistance_level="none"`.
- Checkpoint creation and current-pointer advancement are atomic.
- Resume survives process restart.
- `doctor` checks schema, FKs, pointer integrity, checkpoint evidence/source sessions, raw evidence hashes, and version compatibility.
- Restore rolls back to the prior DB/evidence pair if replacement fails.
- Failed FOSSIL exports do not leave orphan artifacts.
- The live MCP surface has no generic SQL/shell/file-write/code-execution operations.

## What to do next

### Cloud/repo

1. Let GitHub CI run on `codex/issue-5-p1-secure-mcp`.
2. Review any dependency/API failures against `mcp==2.0.0`; do not weaken the semantic contract to fix transport issues.
3. Keep contract `0.1.0` and schema version `1` unless an explicit contract decision is required.
4. When CI is green, open/review the P1 transport PR against Issue #5.

### Local WSL

1. Pull `codex/issue-5-p1-secure-mcp`.
2. Install the optional network dependencies:
   `python3 -m pip install -e '.[network]'`
3. Run compile/repository/full tests again.
4. Load a private `STUDY_OS_MCP_BEARER_TOKEN`.
5. Start:
   `PYTHONPATH=src python3 cli/study_os.py mcp-http --port 8765`
6. In another WSL shell with the same token, run:
   `python3 tools/verify_mcp_endpoint.py --url http://127.0.0.1:8765/mcp`
7. The verifier must show 401/401/200 for missing/wrong/valid bearer, exact 13 tools, and blocked non-MCP routes.

### Secure MCP Tunnel / ChatGPT

Current OpenAI guidance says ChatGPT cannot connect directly to localhost; use Secure MCP Tunnel for a private/developer-machine MCP server. Run the tunnel client in WSL and target `http://127.0.0.1:8765/mcp`.

Create a private/draft ChatGPT custom MCP app, select the tunnel connection, configure the bearer credential through the supported private auth UI, scan tools, and verify the 13-tool surface before real learner data is used.

As of 2026-08-24, OpenAI documents full MCP write/modify actions for Business and Enterprise/Edu. If the active plan/workspace only permits read/fetch, P1 cannot pass its write/checkpoint acceptance criteria on that workspace.

## P1 acceptance test

### Chat A

- `doctor` healthy.
- `start_session`.
- record baseline/attempt evidence.
- record intervention if used.
- record assessment.
- create evidence-backed checkpoint with a distinctive `next_action`.

### Fresh Chat B

- do **not** paste the Chat A transcript.
- enable/select Study OS.
- call `resume(subject_id)` first.
- checkpoint ID must equal Chat A's accepted checkpoint.
- `next_action` must match exactly.
- continue from that action.
- record a subsequent event/attempt and new checkpoint.

Then restart the Study OS HTTP process against the same runtime root and verify `resume` again.

P1 is accepted only when that real ChatGPT-to-WSL path passes.

## Current learner experiment

- Subject: `subject-001`
- Domain: DSA
- Language: Python
- Concept family: Sliding Window
- Learner experiment status: not yet started against the live P1 app path.

Do not start the first real instrumented trajectory until the P1 connectivity test is proven with synthetic/private-safe data.

## Hazards

- Do not commit full personal transcripts, tokens, `.env`, or tunnel credentials.
- Do not use GitHub as the operational learner database.
- Do not make GitHub Actions or FOSSIL a prerequisite for study/resume.
- Do not publicly expose an unauthenticated or unrestricted WSL service.
- Do not add generic machine-control MCP tools.
- Do not resume from ChatGPT conversational memory when a Study OS checkpoint exists.
- Do not promote learner capability without cited behavioral assessment evidence.
- Do not widen the curriculum/research scope until the end-to-end evidence loop works.

## Completion definition for the next agent

A task is complete only when relevant repository/local checks pass and `PROJECT_MANIFEST.yaml` plus this handoff remain synchronized with any changed gate, path, contract, runtime ownership, or acceptance state.
