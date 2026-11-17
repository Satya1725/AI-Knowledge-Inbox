"""Request / response shapes for the HTTP API."""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.config import ProviderName

# ---------- ingest ----------


class _IngestBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str | None = Field(default=None, max_length=200)


class NoteIngest(_IngestBase):
    type: Literal["note"]
    text: str = Field(min_length=1, max_length=50_000)


class UrlIngest(_IngestBase):
    type: Literal["url"]
    url: HttpUrl


IngestRequest = Annotated[Union[NoteIngest, UrlIngest], Field(discriminator="type")]


# ---------- items ----------

ItemStatus = Literal["processing", "ready", "failed"]


class Item(BaseModel):
    id: str
    source_type: Literal["note", "url"]
    title: str | None
    url: str | None
    preview: str | None
    content_length: int | None
    chunk_count: int
    status: ItemStatus
    error: str | None
    created_at: str


class ItemList(BaseModel):
    items: list[Item]


# ---------- query ----------


class QueryRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    question: str = Field(min_length=3, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=10)
    provider: ProviderName | None = None


class Source(BaseModel):
    index: int  # the [n] used in the answer
    item_id: str
    title: str | None
    source_type: Literal["note", "url"]
    url: str | None
    snippet: str
    score: float
    cited: bool  # did the answer actually reference [index]?


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    provider: ProviderName | None  # None when no LLM call was needed


# ---------- providers ----------


class ProvidersInfo(BaseModel):
    embedding_provider: ProviderName
    default_chat_provider: ProviderName
    available_chat_providers: list[ProviderName]
