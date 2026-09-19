from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.delivery.repository import DeliveryRepository
from app.delivery.schemas import (
    AssignRiderRequest,
    AssignRiderResponse,
    DeliveryListItem,
    DeliveryListResponse,
    DeliveryResponse,
)


class DeliveryService:

    def __init__(self):
        self.repository = DeliveryRepository()

    # ── Task 1: Assign a rider to a packed order ────────────

    async def assign_rider(
        self,
        order_id: str,
        request: AssignRiderRequest,
    ):
        order = await self.repository.get_order(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        rider = await self.repository.get_rider(request.rider_id)

        if not rider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rider not found",
            )

        # Idempotency: same rider already assigned to this order
        if (
            order.get("status") == "assigned_to_rider"
            and order.get("rider", {}).get("id")
            == request.rider_id
        ):
            assigned_at = (order.get("rider") or {}).get("assigned_at")
            if assigned_at is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Order has incomplete rider assignment",
                )
            return AssignRiderResponse(
                order_id=order_id,
                rider_id=request.rider_id,
                status="assigned_to_rider",
                assigned_at=assigned_at,
            )

        # Order must be in PACKED status
        if order.get("status") != "packed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order cannot be assigned to rider "
                "in its current state",
            )

        now = datetime.now(timezone.utc)

        result = await self.repository.assign_rider(
            order_id=order_id,
            rider_id=request.rider_id,
            assigned_at=now,
        )

        if result.modified_count != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order state changed. Please retry.",
            )

        return AssignRiderResponse(
            order_id=order_id,
            rider_id=request.rider_id,
            status="assigned_to_rider",
            assigned_at=now,
        )

    # ── Task 2: Mark an order as delivered (idempotent) ─────

    async def mark_delivered(self, order_id: str):

        order = await self.repository.get_order(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        # Idempotency: already delivered → return existing
        if order.get("status") == "delivered":
            existing = (
                await self.repository.get_delivery_by_order(
                    order_id
                )
            )

            if existing:
                return DeliveryResponse(
                    order_id=order_id,
                    delivery_id=str(existing["_id"]),
                    rider_id=existing["rider_id"],
                    delivered_at=existing["delivered_at"],
                    already_done=True,
                )

        # Order must be ASSIGNED_TO_RIDER
        if order.get("status") != "assigned_to_rider":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order cannot be delivered "
                "in its current state",
            )

        rider_data = order.get("rider")

        if not rider_data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order has no assigned rider",
            )

        rider_id = rider_data.get("id")
        now = datetime.now(timezone.utc)

        # Insert delivery record — unique index prevents dupes
        try:
            result = await self.repository.create_delivery(
                order_id=order_id,
                rider_id=rider_id,
                delivered_at=now,
            )

            delivery_id = str(result.inserted_id)

        except DuplicateKeyError:
            # Another concurrent request already created it.
            # Return the existing record as a success.
            existing = (
                await self.repository.get_delivery_by_order(
                    order_id
                )
            )

            if existing:
                return DeliveryResponse(
                    order_id=order_id,
                    delivery_id=str(existing["_id"]),
                    rider_id=existing["rider_id"],
                    delivered_at=existing["delivered_at"],
                    already_done=True,
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Delivery record conflict",
            )

        # Update order status to DELIVERED
        await self.repository.mark_order_delivered(
            order_id=order_id,
            delivered_at=now,
        )

        return DeliveryResponse(
            order_id=order_id,
            delivery_id=delivery_id,
            rider_id=rider_id,
            delivered_at=now,
            already_done=False,
        )

    # ── Task 4: Today's deliveries with rider names ─────────

    async def get_today_deliveries(self):
        """
        Fetch today's deliveries using exactly 2 DB queries:
          1. deliveries.find  — date-range on delivered_at
          2. users.find       — batch $in on rider_ids
        This avoids the N+1 query problem.
        """

        tz = ZoneInfo(settings.REPORT_TIMEZONE)
        now_local = datetime.now(tz)

        # Midnight today in the reporting timezone
        start_of_day = now_local.replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        end_of_day = start_of_day + timedelta(days=1)

        # Convert to UTC for the MongoDB query
        start_utc = start_of_day.astimezone(timezone.utc)
        end_utc = end_of_day.astimezone(timezone.utc)

        deliveries = await self.repository.get_today_deliveries(
            start_utc, end_utc,
        )

        if not deliveries:
            return DeliveryListResponse(deliveries=[])

        # Batch-fetch all riders in ONE query (N+1 avoidance)
        rider_ids = list({d["rider_id"] for d in deliveries})

        riders = await self.repository.get_riders_by_ids(
            rider_ids,
        )

        rider_map = {
            str(r["_id"]): r["name"] for r in riders
        }

        items = [
            DeliveryListItem(
                order_id=d["order_id"],
                rider_id=d["rider_id"],
                rider_name=rider_map.get(
                    d["rider_id"], "Unknown"
                ),
                delivered_at=d["delivered_at"],
            )
            for d in deliveries
        ]

        return DeliveryListResponse(deliveries=items)
