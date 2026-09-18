from typing import Any

from app.core.database import get_database


class OrderRepository:

    @staticmethod
    async def create_order(order: dict[str, Any]):
        db = get_database()

        await db.orders.insert_one(order)

        return order

    @staticmethod
    async def get_order_by_id(order_id: str):
        db = get_database()

        return await db.orders.find_one({
            "_id": order_id
        })