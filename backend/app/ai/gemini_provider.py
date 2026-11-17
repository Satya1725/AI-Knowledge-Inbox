import logging

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.ai.base import EmbedPurpose
from app.errors import AIProviderError

logger = logging.getLogger(__name__)

_TASK_TYPES = {"document": "RETRIEVAL_DOCUMENT", "query": "RETRIEVAL_QUERY"}


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, chat_model: str, embedding_model: str):
        self._client = genai.Client(api_key=api_key)
        self._chat_model = chat_model
        self._embedding_model = embedding_model
        self.embedding_model_id = f"gemini:{embedding_model}"

    async def embed(self, texts: list[str], purpose: EmbedPurpose) -> list[list[float]]:
        try:
            response = await self._client.aio.models.embed_content(
                model=self._embedding_model,
                contents=texts,
                config=types.EmbedContentConfig(task_type=_TASK_TYPES[purpose]),
            )
        except genai_errors.APIError as exc:
            logger.warning("gemini embedding failed", extra={"error": str(exc)})
            raise AIProviderError(f"Gemini embedding request failed: {exc}") from exc
        return [e.values for e in response.embeddings]

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = await self._client.aio.models.generate_content(
                model=self._chat_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.2),
            )
        except genai_errors.APIError as exc:
            logger.warning("gemini completion failed", extra={"error": str(exc)})
            raise AIProviderError(f"Gemini chat request failed: {exc}") from exc
        return response.text or ""
