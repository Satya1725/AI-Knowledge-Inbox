import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id           TEXT PRIMARY KEY,
    source_type  TEXT NOT NULL CHECK (source_type IN ('note', 'url')),
    title        TEXT,
    url          TEXT,
    raw_content  TEXT,
    status       TEXT NOT NULL CHECK (status IN ('processing', 'ready', 'failed')),
    error        TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id          TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    position         INTEGER NOT NULL,
    text             TEXT NOT NULL,
    embedding        BLOB NOT NULL,      -- float32 vector, L2-normalised
    embedding_model  TEXT NOT NULL       -- e.g. "openai:text-embedding-3-small"
);

CREATE INDEX IF NOT EXISTS idx_chunks_item_id ON chunks(item_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_model ON chunks(embedding_model);
"""


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """One short-lived connection per unit of work. Commits on success."""
    conn = sqlite3.connect(get_settings().database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    db_path = Path(get_settings().database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)
