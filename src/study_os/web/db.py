from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import files

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

MIGRATION_LOCK_KEY = 804_217_001


def migration_files() -> list[tuple[str, str]]:
    root = files("study_os.web").joinpath("migrations")
    names = sorted(
        entry.name for entry in root.iterdir() if entry.name.endswith(".sql")
    )
    return [(name, root.joinpath(name).read_text(encoding="utf-8")) for name in names]


def migrate(conn: psycopg.Connection) -> list[str]:
    """Apply pending migrations in order under an advisory lock. Returns applied names."""

    applied: list[str] = []
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (MIGRATION_LOCK_KEY,))
        conn.execute(
            "CREATE TABLE IF NOT EXISTS public.schema_migrations ("
            "name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        done = {
            row[0] for row in conn.execute("SELECT name FROM public.schema_migrations").fetchall()
        }
        for name, sql in migration_files():
            if name in done:
                continue
            conn.execute(sql.encode("utf-8"))
            conn.execute("INSERT INTO public.schema_migrations (name) VALUES (%s)", (name,))
            applied.append(name)
    return applied


class Database:
    def __init__(self, url: str, *, min_size: int = 1, max_size: int = 8) -> None:
        self.url = url
        self.pool = ConnectionPool(
            url,
            min_size=min_size,
            max_size=max_size,
            kwargs={"row_factory": dict_row, "autocommit": False},
            open=True,
        )

    @contextmanager
    def tx(self) -> Iterator[psycopg.Connection]:
        with self.pool.connection() as conn:
            with conn.transaction():
                yield conn

    def migrate(self) -> list[str]:
        with self.pool.connection() as conn:
            return migrate(conn)

    def close(self) -> None:
        self.pool.close()
