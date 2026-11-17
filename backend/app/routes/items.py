import logging

from fastapi import APIRouter, Response, status

from app import repository
from app.errors import NotFoundError
from app.schemas import Item, ItemList

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/items", response_model=ItemList)
async def list_items() -> ItemList:
    return ItemList(items=[Item(**row) for row in repository.list_items()])


@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str) -> Item:
    item = repository.get_item(item_id)
    if item is None:
        raise NotFoundError(f"Item '{item_id}' does not exist.")
    return Item(**item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str) -> Response:
    if not repository.delete_item(item_id):
        raise NotFoundError(f"Item '{item_id}' does not exist.")
    logger.info("item deleted", extra={"item_id": item_id})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
