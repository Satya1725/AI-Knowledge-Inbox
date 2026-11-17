from typing import Literal, Protocol

# Some embedding APIs (Gemini) produce better vectors when told whether the
# text is a stored document or a search query.
EmbedPurpose = Literal["document", "query"]


class AIProvider(Protocol):
    name: str
    # Stored next to every vector. Vectors from different models live in
    # different spaces, so retrieval only compares chunks with the same id.
    embedding_model_id: str

    async def embed(self, texts: list[str], purpose: EmbedPurpose) -> list[list[float]]: ...

    async def complete(self, system_prompt: str, user_prompt: str) -> str: ...
