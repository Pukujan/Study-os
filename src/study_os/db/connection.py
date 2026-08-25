"""SQLite connection management and ordered migrations."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ..config import RuntimeConfig
from ..errors import unavailable, unsupported


LATEST_SCHEMA_VERSION = 1
MIGRATION_DIR = Path(__file__).with_name("migrations")


def _migration_files() -> list[tuple[int, Path]]:
    files: list[tuple[int, Path]] = []
    for path in MIGRATION_DIR.glob("*.sql"):
        try:
            version = int(path.name.split("_", 1)[0])
        except (ValueError, IndexError):
            continue
        files.append((version, path))
    return sorted(files)


def migrate_database(path: str | Path, *, create_parent: bool = True) -> int:
    db_path = Path(path).expanduser().resolve()
    if create_parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=5.0)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        current = int(connection.execute("PRAGMA user_version").fetchone()[0])
        migrations = _migration_files()
        known_versions = {version for version, _ in migrations}
        if current > LATEST_SCHEMA_VERSION or current not in {0, *known_versions}:
            raise unsupported(
                f"Unsupported database schema version: {current}",
                schema_version=current,
                latest_schema_version=LATEST_SCHEMA_VERSION,
            )
        for version, migration in migrations:
            if version <= current:
                continue
            if version != current + 1:
                raise unsupported(
                    f"Migration ordering gap before version {version}",
                    current_schema_version=current,
                    next_migration=version,
                )
            try:
                connection.executescript(migration.read_text(encoding="utf-8"))
                connection.execute(f"PRAGMA user_version = {version}")
                connection.execute(
                    "INSERT OR REPLACE INTO schema_meta(key, value) VALUES (?, ?)",
                    ("schema_version", str(version)),
                )
                connection.execute(
                    "INSERT OR REPLACE INTO schema_meta(key, value) VALUES (?, ?)",
                    ("contract_version", "0.1.0"),
                )
                connection.commit()
                current = version
            except sqlite3.OperationalError as exc:
                connection.rollback()
                if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                    raise unavailable("Database is temporarily unavailable during migration") from exc
                raise
        if current != LATEST_SCHEMA_VERSION:
            raise unsupported(
                f"Database schema is incomplete: {current}",
                schema_version=current,
                latest_schema_version=LATEST_SCHEMA_VERSION,
            )
        return current
    finally:
        connection.close()


class Database:
    def __init__(self, config: RuntimeConfig, *, migrate: bool = True) -> None:
        self.config = config
        self.config.ensure_directories()
        if migrate:
            migrate_database(config.db_path)
        self.connection = sqlite3.connect(config.db_path, timeout=5.0, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 5000")

    @contextmanager
    def transaction(self, *, immediate: bool = True) -> Iterator[sqlite3.Connection]:
        try:
            self.connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield self.connection
            self.connection.commit()
        except sqlite3.OperationalError as exc:
            self.connection.rollback()
            if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                raise unavailable("Database is temporarily unavailable") from exc
            raise
        except Exception:
            self.connection.rollback()
            raise

    def close(self) -> None:
        self.connection.close()

    def reopen(self) -> None:
        self.close()
        self.connection = sqlite3.connect(self.config.db_path, timeout=5.0, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 5000")
