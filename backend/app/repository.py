"""All SQL lives here. Functions take/return plain dicts and numpy arrays."""

import uuid
from datetime import datetime, timezone

import numpy as np

from app.db import connect

PREVIEW_CHARS = 280

_ITEM_COLUMNS = f"""
    i.id, i.source_type, i.title, i.url, i.status, i.error, i.created_at,
    substr(i.raw_content, 1, {PREVIEW_CHARS}) AS preview,
    length(i.raw_content) AS content_length,
    (SELECT count(*) FROM chunks c WHERE c.item_id = i.id) AS chunk_count
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- items ----------

def create_item(source_type: str, title: str | None, url: str | None, raw_content: str | None) -> dict:
    item_id = str(uuid.uuid4())
    now = _now()
    with connect() as conn:
        conn.execute(
            """INSERT INTO items (id, source_type, title, url, raw_content, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'processing', ?, ?)""",
            (item_id, source_type, title, url, raw_content, now, now),
        )
    return get_item(item_id)


def get_item(item_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(f"SELECT {_ITEM_COLUMNS} FROM items i WHERE i.id = ?", (item_id,)).fetchone()
    return dict(row) if row else None


def get_item_content(item_id: str) -> dict | None:
    """Full row including raw_content -- only used by the ingestion worker."""
    with connect() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return dict(row) if row else None


def list_items() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(f"SELECT {_ITEM_COLUMNS} FROM items i ORDER BY i.created_at DESC").fetchall()
    return [dict(r) for r in rows]


def delete_item(item_id: str) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    return cursor.rowcount > 0


def save_fetched_content(item_id: str, title: str | None, raw_content: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE items SET title = COALESCE(title, ?), raw_content = ?, updated_at = ? WHERE id = ?",
            (title, raw_content, _now(), item_id),
        )


def mark_ready(item_id: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE items SET status = 'ready', error = NULL, updated_at = ? WHERE id = ?",
            (_now(), item_id),
        )


def mark_failed(item_id: str, error: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE items SET status = 'failed', error = ?, updated_at = ? WHERE id = ?",
            (error, _now(), item_id),
        )


def fail_interrupted_items() -> int:
    """Items left 'processing' by a crash/restart will never finish -- say so."""
    with connect() as conn:
        cursor = conn.execute(
            "UPDATE items SET status = 'failed', error = 'Interrupted by a server restart. Please re-add it.', "
            "updated_at = ? WHERE status = 'processing'",
            (_now(),),
        )
    return cursor.rowcount


# ---------- chunks ----------

def replace_chunks(item_id: str, texts: list[str], embeddings: np.ndarray, embedding_model: str) -> None:
    rows = [
        (item_id, position, text, vector.astype(np.float32).tobytes(), embedding_model)
        for position, (text, vector) in enumerate(zip(texts, embeddings))
    ]
    with connect() as conn:
        conn.execute("DELETE FROM chunks WHERE item_id = ?", (item_id,))
        conn.executemany(
            "INSERT INTO chunks (item_id, position, text, embedding, embedding_model) VALUES (?, ?, ?, ?, ?)",
            rows,
        )


def load_chunks(embedding_model: str) -> list[dict]:
    """Every chunk embedded with `embedding_model`, joined with its item's metadata."""
    with connect() as conn:
        rows = conn.execute(
            """SELECT c.item_id, c.position, c.text, c.embedding,
                      i.title, i.source_type, i.url
               FROM chunks c JOIN items i ON i.id = c.item_id
               WHERE c.embedding_model = ? AND i.status = 'ready'""",
            (embedding_model,),
        ).fetchall()
    return [dict(r) for r in rows]
