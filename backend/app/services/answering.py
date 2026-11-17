"""The "G" in RAG: build a prompt from retrieved chunks and ask the LLM."""

import logging
import re
import time

from app.ai.factory import get_chat_provider
from app.config import ProviderName, get_settings
from app.schemas import QueryResponse, Source
from app.services.retrieval import RetrievedChunk, retrieve

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant answering questions about the user's personal knowledge inbox \
(their saved notes and web pages).

Rules:
- Answer ONLY from the numbered sources provided. Do not use outside knowledge.
- Cite every claim with the source number in square brackets, e.g. [1] or [2][3].
- If the sources do not contain the answer, say so plainly: \
"I couldn't find that in your saved content." Do not guess.
- Be concise. Use short paragraphs or bullet points when it helps."""

NO_CONTENT_ANSWER = (
    "I couldn't find anything relevant in your saved content. "
    "Try rephrasing the question, or add a note or URL that covers it."
)

_CITATION = re.compile(r"\[(\d+)\]")


def build_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    sources = "\n\n".join(
        f"[{i}] {chunk.title or 'Untitled'} ({chunk.source_type})\n{chunk.text}"
        for i, chunk in enumerate(chunks, start=1)
    )
    return f"Sources:\n\n{sources}\n\n---\n\nQuestion: {question}"


def cited_indices(answer: str) -> set[int]:
    return {int(n) for n in _CITATION.findall(answer)}


async def answer_question(question: str, top_k: int | None, provider_name: ProviderName | None) -> QueryResponse:
    chunks = await retrieve(question, top_k or get_settings().top_k)

    # Nothing relevant -> don't spend an LLM call just to hear "I don't know".
    if not chunks:
        return QueryResponse(answer=NO_CONTENT_ANSWER, sources=[], provider=None)

    chat = get_chat_provider(provider_name)
    started = time.perf_counter()
    answer = (await chat.complete(SYSTEM_PROMPT, build_user_prompt(question, chunks))).strip()

    cited = cited_indices(answer)
    logger.info(
        "answer generated",
        extra={
            "provider": chat.name,
            "context_chunks": len(chunks),
            "cited": sorted(cited),
            "duration_ms": round((time.perf_counter() - started) * 1000),
        },
    )

    sources = [
        Source(
            index=i,
            item_id=chunk.item_id,
            title=chunk.title,
            source_type=chunk.source_type,
            url=chunk.url,
            snippet=chunk.text,
            score=chunk.score,
            cited=i in cited,
        )
        for i, chunk in enumerate(chunks, start=1)
    ]
    return QueryResponse(answer=answer, sources=sources, provider=chat.name)
