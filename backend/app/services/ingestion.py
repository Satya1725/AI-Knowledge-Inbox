"""Turns a saved item into searchable chunks.

`process_item` runs as a background task after POST /ingest has already
returned, so it never raises -- it records the outcome on the item instead
(status 'ready' or 'failed' + a human-readable error).
"""

import logging
import time

from app import repository
from app.ai.factory import get_embedding_provider
from app.config import get_settings
from app.errors import AppError, EmptyContentError
from app.services.chunking import chunk_text
from app.services.embeddings import embed_texts
from app.services.fetcher import fetch_page

logger = logging.getLogger(__name__)


def title_from_note(text: str, max_len: int = 60) -> str:
    first_line = text.strip().splitlines()[0]
    return first_line if len(first_line) <= max_len else first_line[: max_len - 1].rstrip() + "…"


async def process_item(item_id: str) -> None:
    started = time.perf_counter()
    log_ctx = {"item_id": item_id}

    try:
        item = repository.get_item_content(item_id)
        if item is None:
            logger.warning("item vanished before processing", extra=log_ctx)
            return

        text = await _load_text(item)
        settings = get_settings()
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise EmptyContentError("There is no text to index.")

        provider = get_embedding_provider()
        vectors = await embed_texts(provider, chunks, purpose="document")

        repository.replace_chunks(item_id, chunks, vectors, provider.embedding_model_id)
        repository.mark_ready(item_id)

        logger.info(
            "item indexed",
            extra={
                **log_ctx,
                "source_type": item["source_type"],
                "chunks": len(chunks),
                "chars": len(text),
                "duration_ms": round((time.perf_counter() - started) * 1000),
            },
        )
    except AppError as exc:
        logger.warning("item processing failed", extra={**log_ctx, "error_code": exc.code, "error": exc.message})
        repository.mark_failed(item_id, exc.message)
    except Exception:
        logger.exception("unexpected error while processing item", extra=log_ctx)
        repository.mark_failed(item_id, "Unexpected server error while processing this item. Check the server logs.")


async def _load_text(item: dict) -> str:
    if item["source_type"] == "note":
        return item["raw_content"]

    page = await fetch_page(item["url"])
    repository.save_fetched_content(item["id"], page.title, page.text)
    return page.text
