from datetime import datetime, timezone
from uuid import uuid4

from app.orders.repository import OrderRepository
from app.orders.schemas import CreateOrderRequest


class OrderService:

    def __init__(self):
        self.repository = OrderRepository()

    # @staticmethod
    async def create_order(self,request: CreateOrderRequest):

        now = datetime.now(timezone.utc)

        order = {
            "_id": f"order_{uuid4().hex[:8]}",

            "customer_id": request.customer_id,

            "items": [
                item.model_dump()
                for item in request.items
            ],

            "delivery_location": (
                request.delivery_location.model_dump()
            ),

            "status": "created",

            "packer": None,
            "packed_at": None,

            "rider": None,
            "delivered_at": None,

            "created_at": now,
            "updated_at": now
        }

        return await self.repository.create_order(order)