import logging

from fastapi import APIRouter, BackgroundTasks, Response, status

from app import repository
from app.ai.factory import get_embedding_provider
from app.errors import ConflictError, NotFoundError
from app.schemas import Item, ItemList
from app.services.ingestion import process_item

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_or_404(item_id: str) -> dict:
    item = repository.get_item(item_id)
    if item is None:
        raise NotFoundError(f"Item '{item_id}' does not exist.")
    return item


@router.get("/items", response_model=ItemList)
async def list_items() -> ItemList:
    return ItemList(items=[Item(**row) for row in repository.list_items()])


@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str) -> Item:
    return Item(**_get_or_404(item_id))


@router.post("/items/{item_id}/reindex", response_model=Item, status_code=status.HTTP_202_ACCEPTED)
async def reindex_item(item_id: str, background_tasks: BackgroundTasks) -> Item:
    """Re-fetch (for URLs), re-chunk and re-embed an item. Also how a failed item is retried."""
    item = _get_or_404(item_id)
    if item["status"] == "processing":
        raise ConflictError("This item is already being indexed.")

    get_embedding_provider()  # fail fast with 503 if no provider is configured

    repository.mark_processing(item_id)
    background_tasks.add_task(process_item, item_id)
    logger.info("item reindex requested", extra={"item_id": item_id, "source_type": item["source_type"]})
    return Item(**_get_or_404(item_id))


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str) -> Response:
    if not repository.delete_item(item_id):
        raise NotFoundError(f"Item '{item_id}' does not exist.")
    logger.info("item deleted", extra={"item_id": item_id})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
