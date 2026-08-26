"""SQLite State Store Connection and Schema Initialization (PRD §11.4)."""

import os
import sqlite3
from pathlib import Path
from typing import Optional


DEFAULT_DB_PATH = ".macao/state.db"

SCHEMA_DDL = """
-- Tasks Table
CREATE TABLE IF NOT EXISTS tasks (
    task_id         TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    source_branch   TEXT,
    target_branch   TEXT,
    state           TEXT NOT NULL,              -- 10 FSM States
    checkpoint_ref  TEXT,
    review_round    INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

-- Artifacts Table (Composite Key for multi-task / multi-round resilience)
CREATE TABLE IF NOT EXISTS artifacts (
    task_id         TEXT NOT NULL,
    kind            TEXT NOT NULL,              -- dev_manifest | review_manifest | vote_result
    checkpoint_ref  TEXT NOT NULL,
    review_round    INTEGER NOT NULL,
    reviewer_id     TEXT DEFAULT '',
    path            TEXT NOT NULL,
    sha256          TEXT,
    consumed        INTEGER NOT NULL DEFAULT 0,
    archived_path   TEXT,
    created_at      TEXT NOT NULL,
    PRIMARY KEY (task_id, kind, checkpoint_ref, review_round, reviewer_id)
);

-- Audit Events Table (Immutable Event Log)
CREATE TABLE IF NOT EXISTS audit_events (
    sequence_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT NOT NULL,
    task_id         TEXT,
    type            TEXT NOT NULL,
    detail          TEXT                        -- JSON detail
);

-- Human Overrides Table
CREATE TABLE IF NOT EXISTS overrides (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_id     INTEGER REFERENCES audit_events(sequence_id),
    task_id         TEXT,
    trigger         TEXT,
    choice          TEXT NOT NULL,
    note            TEXT,
    created_at      TEXT NOT NULL
);

-- Dead Letter Queue (DLQ)
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    message_id      TEXT PRIMARY KEY,
    type            TEXT,
    payload         TEXT,
    retry_count     INTEGER DEFAULT 0,
    reason          TEXT,
    ts              TEXT NOT NULL
);

-- Internal Message Queue (agmsg SQLite backend)
CREATE TABLE IF NOT EXISTS message_queue (
    message_id      TEXT PRIMARY KEY,
    type            TEXT NOT NULL,
    from_agent      TEXT NOT NULL,
    to_agent        TEXT NOT NULL,              -- JSON list or string
    payload         TEXT NOT NULL,              -- JSON payload
    status          TEXT NOT NULL DEFAULT 'PENDING', -- PENDING | ACKED | DEAD
    retry_count     INTEGER NOT NULL DEFAULT 0,
    deadline        TEXT,
    created_at      TEXT NOT NULL,
    acked_at        TEXT
);
"""


class DatabaseManager:
    """Manages SQLite database connections and schema migration."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_DDL)
            conn.commit()


_db_manager: Optional[DatabaseManager] = None

def get_db(db_path: str = DEFAULT_DB_PATH) -> DatabaseManager:
    global _db_manager
    if _db_manager is None or str(_db_manager.db_path) != str(Path(db_path)):
        _db_manager = DatabaseManager(db_path)
    return _db_manager
