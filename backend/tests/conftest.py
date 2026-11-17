import hashlib
import re

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.ai import factory
from app.config import get_settings


class FakeProvider:
    """Deterministic stand-in for OpenAI/Gemini.

    Embeddings are a hashed bag-of-words, so texts sharing words are similar --
    good enough to test retrieval ranking without network calls.
    """

    name = "openai"
    embedding_model_id = "fake:bag-of-words"

    def __init__(self):
        self.last_prompt: str | None = None

    async def embed(self, texts, purpose):
        return [self._vector(t) for t in texts]

    async def complete(self, system_prompt, user_prompt):
        self.last_prompt = user_prompt
        return "Fake answer based on [1]."

    @staticmethod
    def _vector(text: str) -> list[float]:
        vec = np.zeros(256, dtype=np.float32)
        for word in re.findall(r"[a-z]+", text.lower()):
            vec[int(hashlib.md5(word.encode()).hexdigest(), 16) % 256] += 1
        return vec.tolist()


@pytest.fixture
def fake_provider():
    return FakeProvider()


@pytest.fixture
def client(tmp_path, monkeypatch, fake_provider):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("CHAT_PROVIDER", "openai")
    monkeypatch.setenv("MIN_SIMILARITY", "0.1")
    # Don't let real keys from backend/.env leak into tests.
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()
    factory._providers.clear()
    factory._providers["openai"] = fake_provider

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

    factory._providers.clear()
    get_settings.cache_clear()
