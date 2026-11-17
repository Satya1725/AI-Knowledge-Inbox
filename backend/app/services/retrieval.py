"""Brute-force cosine search over the chunks stored in SQLite.

Every query loads all vectors for the active embedding model and does one
matrix-vector product. At a few thousand chunks that takes milliseconds; see
README "What breaks at scale" for when to swap this for a real vector index.
"""

import logging
from dataclasses import dataclass

import numpy as np

from app import repository
from app.ai.factory import get_embedding_provider
from app.config import get_settings
from app.services.embeddings import embed_texts

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    item_id: str
    title: str | None
    source_type: str
    url: str | None
    text: str
    score: float


async def retrieve(question: str, top_k: int) -> list[RetrievedChunk]:
    provider = get_embedding_provider()
    rows = repository.load_chunks(provider.embedding_model_id)
    if not rows:
        logger.info("no indexed chunks to search", extra={"embedding_model": provider.embedding_model_id})
        return []

    query_vector = (await embed_texts(provider, [question], purpose="query"))[0]
    matrix = np.stack([np.frombuffer(row["embedding"], dtype=np.float32) for row in rows])

    if matrix.shape[1] != query_vector.shape[0]:
        # Same model id but different dimensions -- should never happen, but fail loudly.
        raise RuntimeError(f"Embedding dimension mismatch: stored {matrix.shape[1]}, query {query_vector.shape[0]}")

    scores = matrix @ query_vector  # cosine similarity, vectors are unit length
    best = np.argsort(-scores)[:top_k]
    min_score = get_settings().min_similarity

    results = [
        RetrievedChunk(
            item_id=rows[i]["item_id"],
            title=rows[i]["title"],
            source_type=rows[i]["source_type"],
            url=rows[i]["url"],
            text=rows[i]["text"],
            score=round(float(scores[i]), 4),
        )
        for i in best
        if scores[i] >= min_score
    ]

    logger.info(
        "retrieval done",
        extra={
            "searched_chunks": len(rows),
            "returned": len(results),
            "top_score": results[0].score if results else None,
        },
    )
    return results
