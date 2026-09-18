from fastapi import APIRouter, status

from app.orders.schemas import (
    CreateOrderRequest,
    OrderResponse
)

from app.orders.service import OrderService


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

service = OrderService()


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_order(request: CreateOrderRequest):

    order = await service.create_order(request)

    return OrderResponse(
        id=order["_id"],
        customer_id=order["customer_id"],
        items=order["items"],
        delivery_location=order["delivery_location"],
        status=order["status"],

        packer=order["packer"],
        packed_at=order["packed_at"],

        rider=order["rider"],
        delivered_at=order["delivered_at"],

        created_at=order["created_at"],
        updated_at=order["updated_at"]
    )