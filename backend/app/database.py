"""Thin SQLite layer.

SQLite is intentionally chosen over a JSON file: it is still a single local
file (zero external services, perfect for a small always-on Render/Railway
instance) but gives us safe concurrent access, ordering, and simple queries.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    text        TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    expires_at  TEXT    NOT NULL
);

-- single-row table tracking the last time the TRMNL device polled us
CREATE TABLE IF NOT EXISTS device_state (
    id           INTEGER PRIMARY KEY CHECK (id = 1),
    last_seen    TEXT
);
INSERT OR IGNORE INTO device_state (id, last_seen) VALUES (1, NULL);
"""


def _db_path() -> Path:
    path = Path(get_settings().database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def init_db() -> None:
    """Create tables on startup."""
    with connect() as conn:
        conn.executescript(_SCHEMA)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Yield a connection with Row access and foreign keys enabled."""
    conn = sqlite3.connect(_db_path(), detect_types=0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
