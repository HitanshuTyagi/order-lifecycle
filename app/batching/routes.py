from fastapi import APIRouter

from app.batching.schemas import BatchResponse
from app.batching.service import create_batch


router = APIRouter(
    prefix="/batches",
    tags=["Batches"],
)


@router.post(
    "/create",
    response_model=BatchResponse,
)
async def create_order_batch() -> BatchResponse:
    """
    Create one batch from currently ready-to-go orders.
    """
    return await create_batch()