from fastapi import APIRouter, Depends

from app.delivery.schemas import (
    AssignRiderRequest,
    AssignRiderResponse,
    DeliveryListResponse,
    DeliveryResponse,
)
from app.delivery.service import DeliveryService


def get_delivery_service():
    """
    Lazy factory — DeliveryRepository calls get_database()
    in __init__, so the service must be created after startup.
    """
    return DeliveryService()


# ── Order-scoped delivery actions ───────────────────────

order_router = APIRouter(
    prefix="/orders",
    tags=["Delivery"],
)


@order_router.post(
    "/{order_id}/assign-rider",
    response_model=AssignRiderResponse,
)
async def assign_rider(
    order_id: str,
    request: AssignRiderRequest,
    service: DeliveryService = Depends(get_delivery_service),
):
    return await service.assign_rider(order_id, request)


@order_router.post(
    "/{order_id}/mark-delivered",
    response_model=DeliveryResponse,
)
async def mark_delivered(
    order_id: str,
    service: DeliveryService = Depends(get_delivery_service),
):
    return await service.mark_delivered(order_id)


# ── Delivery-scoped queries ────────────────────────────

delivery_router = APIRouter(
    prefix="/deliveries",
    tags=["Delivery"],
)


@delivery_router.get(
    "/today",
    response_model=DeliveryListResponse,
)
async def get_today_deliveries(
    service: DeliveryService = Depends(get_delivery_service),
):
    return await service.get_today_deliveries()
