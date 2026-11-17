import logging

from fastapi import APIRouter, BackgroundTasks, status

from app import repository
from app.ai.factory import get_embedding_provider
from app.schemas import IngestRequest, Item, NoteIngest
from app.services.ingestion import process_item, title_from_note

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=Item, status_code=status.HTTP_202_ACCEPTED)
async def ingest(payload: IngestRequest, background_tasks: BackgroundTasks) -> Item:
    """Save a note or URL. Returns immediately with status 'processing';
    fetching + chunking + embedding happen in the background."""

    # Fail fast with a 503 instead of accepting an item that can never be indexed.
    get_embedding_provider()

    if isinstance(payload, NoteIngest):
        item = repository.create_item(
            source_type="note",
            title=payload.title or title_from_note(payload.text),
            url=None,
            raw_content=payload.text,
        )
    else:
        item = repository.create_item(source_type="url", title=payload.title, url=str(payload.url), raw_content=None)

    logger.info("item accepted", extra={"item_id": item["id"], "source_type": item["source_type"]})
    background_tasks.add_task(process_item, item["id"])
    return Item(**item)
