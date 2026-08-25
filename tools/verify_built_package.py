#!/usr/bin/env python3
"""Verify the installed Study OS wheel without relying on the repository src tree."""

from __future__ import annotations

from importlib.resources import files

import study_os
from study_os.services.runtime import StudyOSService


def main() -> int:
    if study_os.RUNTIME_VERSION != "0.1.0":
        raise RuntimeError(f"unexpected installed runtime version: {study_os.RUNTIME_VERSION!r}")
    if study_os.CONTRACT_VERSION != "0.1.0":
        raise RuntimeError(f"unexpected installed contract version: {study_os.CONTRACT_VERSION!r}")
    if StudyOSService.__module__ != "study_os.services.runtime":
        raise RuntimeError(f"unexpected StudyOSService module: {StudyOSService.__module__!r}")

    migration = files("study_os").joinpath("db").joinpath("migrations").joinpath("0001_initial.sql")
    if not migration.is_file():
        raise RuntimeError("installed wheel is missing db/migrations/0001_initial.sql")

    print("Installed Study OS wheel import/package-data smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
