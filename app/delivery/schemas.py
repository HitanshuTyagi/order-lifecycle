from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from app.core.enums import OrderStatus

class AssignRiderRequest(BaseModel):
    rider_id: str


class DeliveryResponse(BaseModel):
    order_id: str
    delivery_id: str | None = None
    rider_id: str
    delivered_at: datetime | None = None
    already_done: bool = False

class AssignRiderResponse(BaseModel):
    order_id: str
    rider_id: str
    status: OrderStatus
    assigned_at: datetime

class DeliveryListItem(BaseModel):
    order_id: str
    rider_id: str
    rider_name: str
    delivered_at: datetime


class DeliveryListResponse(BaseModel):
    deliveries: list[DeliveryListItem]