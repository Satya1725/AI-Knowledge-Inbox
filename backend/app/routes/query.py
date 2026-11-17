from fastapi import APIRouter

from app.ai.factory import available_providers, resolve_provider
from app.config import get_settings
from app.schemas import ProvidersInfo, QueryRequest, QueryResponse
from app.services.answering import answer_question

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest) -> QueryResponse:
    return await answer_question(payload.question, payload.top_k, payload.provider)


@router.get("/providers", response_model=ProvidersInfo)
async def providers() -> ProvidersInfo:
    """Reports the providers that will actually be used (after key-based fallback)."""
    settings = get_settings()
    return ProvidersInfo(
        embedding_provider=resolve_provider(settings.embedding_provider),
        default_chat_provider=resolve_provider(settings.chat_provider),
        available_chat_providers=available_providers(),
    )
