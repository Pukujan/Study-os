"""Admin CLI: ``python -m study_os.web.cli migrate | create-account | grant-admin | stats``."""

from __future__ import annotations

import argparse
import getpass
import json
import sys

from . import auth
from .config import load_settings
from .db import Database


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="study-os-web")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate")
    create = sub.add_parser("create-account", help="create a local email/passphrase account (passphrase read from stdin/TTY)")
    create.add_argument("--email", required=True)
    create.add_argument("--handle")
    create.add_argument("--admin", action="store_true")
    grant = sub.add_parser("grant-admin")
    grant.add_argument("--handle", required=True)
    sub.add_parser("stats")
    args = parser.parse_args(argv)
    db = Database(load_settings().database_url, min_size=1, max_size=2)
    try:
        if args.cmd == "migrate":
            print(json.dumps({"applied": db.migrate()}))
        elif args.cmd == "create-account":
            db.migrate()
            passphrase = getpass.getpass("passphrase: ") if sys.stdin.isatty() else sys.stdin.readline().rstrip("\n")
            with db.tx() as conn:
                p = auth.signup_local(conn, email=args.email, passphrase=passphrase, handle=args.handle,
                                      role="admin" if args.admin else "learner")
            print(json.dumps({"handle": p.handle, "role": p.role}))
        elif args.cmd == "grant-admin":
            with db.tx() as conn:
                n = conn.execute("UPDATE auth.account SET role = 'admin' WHERE handle = %s", (args.handle,)).rowcount
            print(json.dumps({"updated": n}))
        elif args.cmd == "stats":
            with db.tx() as conn:
                row = conn.execute(
                    "SELECT (SELECT count(*) FROM auth.account) AS accounts, (SELECT count(*) FROM learn.session) AS sessions, "
                    "(SELECT count(*) FROM learn.attempt) AS attempts, (SELECT count(*) FROM learn.decision) AS decisions, "
                    "(SELECT count(*) FROM ux.event) AS ux_events"
                ).fetchone()
            print(json.dumps(dict(row or {})))
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
