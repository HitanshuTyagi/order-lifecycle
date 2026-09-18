from fastapi import APIRouter

from app.picker.schemas import (
    AssignPickerRequest,
    PackingResponse
)
from app.picker.service import PackingService


router = APIRouter(
    prefix="/orders",
    tags=["Packing"]
)

service = PackingService()


@router.post(
    "/{order_id}/assign-picker",
    response_model=PackingResponse
)
async def assign_picker(
    order_id: str,
    request: AssignPickerRequest
):
    return await service.assign_picker(
        order_id,
        request
    )


@router.post(
    "/{order_id}/mark-packed",
    response_model=PackingResponse
)
async def mark_packed(order_id: str):
    return await service.mark_packed(order_id)