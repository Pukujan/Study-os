"""Runtime configuration for the private local Study OS store."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeConfig:
    """Filesystem locations for one local Study OS installation.

    The default is intentionally outside any repository. Tests and local
    tooling can provide an explicit temporary root.
    """

    root: Path

    @classmethod
    def from_env(cls, root: str | Path | None = None) -> "RuntimeConfig":
        configured = root if root is not None else os.environ.get("STUDY_OS_ROOT")
        selected = Path(configured).expanduser() if configured else Path.home() / ".study-os"
        return cls(selected.resolve())

    @property
    def db_dir(self) -> Path:
        return self.root / "db"

    @property
    def db_path(self) -> Path:
        return self.db_dir / "study-os.sqlite3"

    @property
    def evidence_root(self) -> Path:
        return self.root / "evidence"

    @property
    def backups_root(self) -> Path:
        return self.root / "backups"

    @property
    def exports_root(self) -> Path:
        return self.root / "exports"

    def ensure_directories(self) -> None:
        for path in (self.db_dir, self.evidence_root, self.backups_root, self.exports_root):
            path.mkdir(parents=True, exist_ok=True)
