from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def render_schema() -> str:
    sys.path.insert(0, str(SRC))
    contracts = importlib.import_module("study_os.application.contracts")
    rendered = contracts.render_application_contract_core_schema()
    parsed = json.loads(rendered)
    if parsed.get("application_contract_version") != contracts.APPLICATION_CONTRACT_VERSION:
        raise RuntimeError("rendered application contract schema version drifted")
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the E11a application contract core JSON Schema bundle")
    parser.add_argument(
        "--check",
        action="store_true",
        help="render twice and fail if output is not deterministic; print only the SHA-256",
    )
    args = parser.parse_args()

    first = render_schema()
    if args.check:
        second = render_schema()
        if first != second:
            raise RuntimeError("application contract schema rendering is not deterministic")
        print(hashlib.sha256(first.encode("utf-8")).hexdigest())
    else:
        print(first, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
