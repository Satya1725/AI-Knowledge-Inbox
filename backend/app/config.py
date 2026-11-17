from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderName = Literal["openai", "gemini"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    embedding_provider: ProviderName = "openai"
    chat_provider: ProviderName = "openai"

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"

    database_path: str = "data/inbox.db"

    # Chunking: ~800 chars is roughly 150-200 tokens -- small enough that a
    # retrieved chunk is about one idea, big enough to keep a paragraph intact.
    chunk_size: int = 800
    chunk_overlap: int = 150

    top_k: int = 5
    min_similarity: float = 0.25

    fetch_timeout_seconds: float = 10.0
    max_fetch_bytes: int = 3_000_000

    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
