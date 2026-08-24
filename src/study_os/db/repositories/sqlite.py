"""SQLite repository adapter.

The service layer owns semantic validation and transaction composition; this
adapter owns the persistence connection boundary so transports never execute
SQL directly.
"""

from __future__ import annotations

import sqlite3
from contextlib import AbstractContextManager
from typing import Any

from ..connection import Database


class SQLiteRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    @property
    def connection(self) -> sqlite3.Connection:
        return self.database.connection

    def transaction(self, *, immediate: bool = True) -> AbstractContextManager[sqlite3.Connection]:
        return self.database.transaction(immediate=immediate)

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        return self.connection.execute(sql, parameters)

    def close(self) -> None:
        self.database.close()
