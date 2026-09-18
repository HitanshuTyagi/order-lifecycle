from __future__ import annotations

from datetime import datetime
from typing import Any

# from pymongo.errors import DuplicateKeyError

from app.core.database import get_database


class DeliveryRepository:

    def __init__(self):
        self.db = get_database()
        self.orders = self.db.orders
        self.deliveries = self.db.deliveries
        self.users = self.db.users

    async def get_order(self, order_id: str) -> dict[str, Any] | None:
        return await self.orders.find_one(
            {"_id": order_id}
        )

    async def get_rider(self, rider_id: str) -> dict[str, Any] | None:
        return await self.users.find_one(
            {
                "_id": rider_id,
                "role": "delivery_boy",
            }
        )

    async def assign_rider(
        self,
        order_id: str,
        rider_id: str,
        assigned_at: datetime,
    ):
        """
        Atomically assign a rider only when the order is PACKED.
        """

        return await self.orders.update_one(
            {
                "_id": order_id,
                "status": "packed",
            },
            {
                "$set": {
                    "status": "assigned_to_rider",
                    "rider": {
                        "id": rider_id,
                        "assigned_at": assigned_at,
                    },
                    "updated_at": assigned_at,
                }
            },
        )

    async def create_delivery(
        self,
        order_id: str,
        rider_id: str,
        delivered_at: datetime,
    ):
        """
        Create exactly one delivery record.

        MongoDB's unique index on order_id prevents duplicates.
        """

        return await self.deliveries.insert_one(
            {
                "order_id": order_id,
                "rider_id": rider_id,
                "delivered_at": delivered_at,
            }
        )

    async def get_delivery_by_order(
        self,
        order_id: str,
    ) -> dict[str, Any] | None:

        return await self.deliveries.find_one(
            {"order_id": order_id}
        )

    async def mark_order_delivered(
        self,
        order_id: str,
        delivered_at: datetime,
    ):
        """
        Atomically change ASSIGNED_TO_RIDER -> DELIVERED.
        """

        return await self.orders.update_one(
            {
                "_id": order_id,
                "status": "assigned_to_rider",
            },
            {
                "$set": {
                    "status": "delivered",
                    "delivered_at": delivered_at,
                    "updated_at": delivered_at,
                }
            },
        )

    async def get_today_deliveries(
        self,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[dict[str, Any]]:

        cursor = self.deliveries.find(
            {
                "delivered_at": {
                    "$gte": start_utc,
                    "$lt": end_utc,
                }
            }
        )

        return await cursor.to_list(length=None)

    async def get_riders_by_ids(
        self,
        rider_ids: list[str],
    ) -> list[dict[str, Any]]:

        if not rider_ids:
            return []

        cursor = self.users.find(
            {
                "_id": {
                    "$in": rider_ids
                },
                "role": "delivery_boy",
            }
        )

        return await cursor.to_list(length=None)