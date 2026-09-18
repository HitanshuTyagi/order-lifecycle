from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import OrderStatus


class OrderItem(BaseModel):
    medicine_id: str
    name: str
    quantity: int = Field(..., gt=0)


class DeliveryLocation(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class Assignment(BaseModel):
    id: str
    assigned_at: datetime


class CreateOrderRequest(BaseModel):
    customer_id: str
    items: list[OrderItem] = Field(..., min_length=1)
    delivery_location: DeliveryLocation


class OrderResponse(BaseModel):
    id: str
    customer_id: str
    items: list[OrderItem]

    delivery_location: DeliveryLocation

    status: OrderStatus

    packer: Assignment | None = None
    packed_at: datetime | None = None

    rider: Assignment | None = None
    delivered_at: datetime | None = None

    created_at: datetime
    updated_at: datetime