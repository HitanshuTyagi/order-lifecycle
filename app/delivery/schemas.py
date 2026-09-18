from datetime import datetime

from pydantic import BaseModel


class AssignRiderRequest(BaseModel):
    rider_id: str


class DeliveryResponse(BaseModel):
    order_id: str
    delivery_id: str | None = None
    rider_id: str
    delivered_at: datetime | None = None
    already_done: bool = False