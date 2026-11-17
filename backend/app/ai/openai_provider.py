import logging

from openai import AsyncOpenAI, OpenAIError

from app.ai.base import EmbedPurpose
from app.errors import AIProviderError

logger = logging.getLogger(__name__)


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, chat_model: str, embedding_model: str):
        self._client = AsyncOpenAI(api_key=api_key, timeout=30.0, max_retries=2)
        self._chat_model = chat_model
        self._embedding_model = embedding_model
        self.embedding_model_id = f"openai:{embedding_model}"

    async def embed(self, texts: list[str], purpose: EmbedPurpose) -> list[list[float]]:
        try:
            response = await self._client.embeddings.create(model=self._embedding_model, input=texts)
        except OpenAIError as exc:
            logger.warning("openai embedding failed", extra={"error": str(exc)})
            raise AIProviderError(f"OpenAI embedding request failed: {exc}") from exc
        return [d.embedding for d in response.data]

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._chat_model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except OpenAIError as exc:
            logger.warning("openai completion failed", extra={"error": str(exc)})
            raise AIProviderError(f"OpenAI chat request failed: {exc}") from exc
        return response.choices[0].message.content or ""
