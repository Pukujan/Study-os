#!/usr/bin/env python3
"""Local Study OS CLI.

The CLI is administrative/transport plumbing; semantic writes still route
through ``StudyOSService`` and no generic shell, SQL, or file-write tool is
exposed to MCP clients.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPT_DIR = Path(__file__).resolve().parent
# When this file is executed directly, Python puts ``cli/`` before ``src/``;
# remove that entry so the ``study_os`` package cannot resolve to this script.
sys.path[:] = [entry for entry in sys.path if not entry or Path(entry).resolve() != SCRIPT_DIR]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from study_os.config import RuntimeConfig  # noqa: E402
from study_os.db.connection import migrate_database  # noqa: E402
from study_os.mcp.http_server import serve_http  # noqa: E402
from study_os.mcp.server import MCPServer  # noqa: E402
from study_os.services.runtime import StudyOSService  # noqa: E402


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Study OS local runtime")
    command.add_argument("--root", default=None, help="Private runtime root; defaults to STUDY_OS_ROOT or ~/.study-os")
    sub = command.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate")
    sub.add_parser("doctor")
    status = sub.add_parser("status")
    status.add_argument("subject_id")
    resume = sub.add_parser("resume")
    resume.add_argument("subject_id")
    sub.add_parser("backup").add_argument("--destination", default=None)
    sub.add_parser("restore").add_argument("backup_path")
    sub.add_parser("list-tools")
    sub.add_parser("mcp")
    http = sub.add_parser("mcp-http")
    http.add_argument("--host", default="127.0.0.1")
    http.add_argument("--port", type=int, default=8765)
    http.add_argument("--path", default="/mcp")
    http.add_argument("--actions-path", default="/actions")
    http.add_argument("--allowed-origin", action="append", default=[])
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    config = RuntimeConfig.from_env(args.root)
    if args.command == "migrate":
        print(json.dumps({"schema_version": migrate_database(config.db_path)}, indent=2))
        return 0
    if args.command == "list-tools":
        server = MCPServer(StudyOSService(config))
        print(json.dumps(server.list_tool_names(), indent=2))
        server.service.close()
        return 0
    if args.command == "mcp-http":
        serve_http(
            config,
            host=args.host,
            port=args.port,
            mcp_path=args.path,
            actions_path=args.actions_path,
            allowed_origins=args.allowed_origin,
            bearer_token=os.environ.get("STUDY_OS_HTTP_BEARER_TOKEN"),
        )
        return 0
    service = StudyOSService(config)
    try:
        if args.command == "doctor":
            result = service.doctor()
        elif args.command == "status":
            result = service.status(subject_id=args.subject_id)
        elif args.command == "resume":
            result = service.resume(subject_id=args.subject_id)
        elif args.command == "backup":
            result = service.backup(args.destination)
        elif args.command == "restore":
            result = service.restore(args.backup_path)
        elif args.command == "mcp":
            MCPServer(service).run_stdio()
            return 0
        else:
            raise AssertionError(args.command)
        print(json.dumps(result, indent=2))
        return 0 if result.get("healthy", True) else 1
    except Exception as exc:
        if hasattr(exc, "as_dict"):
            print(json.dumps(exc.as_dict(), indent=2), file=sys.stderr)
        else:
            print(json.dumps({"error": {"category": "internal_error", "message": str(exc), "retryable": False, "details": {}}}, indent=2), file=sys.stderr)
        return 1
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
