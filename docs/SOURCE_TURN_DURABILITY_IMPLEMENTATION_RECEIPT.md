# Source-turn durability implementation receipt

Date: 2026-09-03  
Issue: #56  
Base: `7799688bbd793d5dfa2a3fc073a756c47ec2d650`

## Architecture

- schema migration: none; schema v1 already represents `raw_artifacts`, `messages`, and `idempotency_records`;
- application operation: `append_conversation_turn`;
- MCP contract: v0.2.0;
- semantic tool count: 14; historical v0.1.0 contract remains preserved;
- reconciliation surface: local `reconcile` CLI/runtime path;
- raw content storage: existing private `EvidenceStore`, immutable UTF-8 bytes and SHA-256 links.

## Verification receipt

The following source-turn acceptance coverage is green in the synthetic test suite:

| Tests | Result | Evidence |
|---|---|---|
| ST1–ST7 | PASS | `tests/test_p3_source_turn_durability.py` |
| ST8–ST10 | PASS | commit-boundary, retry, and response-loss tests in the same file |
| ST11 | PASS | runtime state is reopened by the live service and remains doctor-healthy; restart behavior is covered by the existing runtime durability suite |
| ST12–ST14 | PASS | application/MCP strictness, v0.2 bounded surface, and HTTP transport tests |
| ST15–ST18 | PASS | reviewed reconciliation, rerun idempotency, ambiguity refusal, and two-clock metadata tests |
| ST19 | PASS | message/artifact corruption is detected by `doctor` |
| ST20 | PASS | backup/restore and exact retry preserve the source substrate |
| ST21 | PASS | committed fixtures are synthetic; transport logging omits request bodies and credentials |
| ST22 | BLOCKED | literal ChatGPT UI invocation is outside the local runtime shell; the live authenticated WSL `/actions` two-turn synthetic smoke passed, but it is not claimed as a UI turn |

Parent P3 T1–T14 remain covered by the existing repository suite where applicable.

## Commands

```text
python -m unittest discover -s tests -v
python tools/validate_repo.py
python tools/check_engineering_baseline.py
```

Result: 254 tests passed. The WSL service is active on loopback port 18765, and live `doctor` is healthy.
