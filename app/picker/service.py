from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.database import get_database
from app.picker.repository import PackingRepository
from app.picker.schemas import (
    AssignPickerRequest,
    PackingResponse
)


class PackingService:

    def __init__(self):
        self.repository = PackingRepository()

    async def assign_picker(
        self,
        order_id: str,
        request: AssignPickerRequest
    ):

        db = get_database()

        order = await self.repository.get_order(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        picker = await self.repository.get_picker(request.picker_id)

        if not picker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Picker not found"
            )

        # Same picker already assigned to this order
        if (
            order.get("status") == "assigned_to_packer"
            and order.get("packer", {}).get("user_id")
            == request.picker_id
        ):
            return PackingResponse(
                order_id=order_id,
                status="assigned_to_packer",
                already_done=True
            )

        # Order is already assigned to some other picker
        if order.get("status") != "created":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order cannot be assigned in its current state"
            )

        # Picker is already handling another order
        if not picker.get("is_available", False):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Picker is already handling another order"
            )

        now = datetime.now(timezone.utc)

        async with await db.client.start_session() as session:

            async with session.start_transaction():

                success = await self.repository.assign_picker_to_order(
                    order_id=order_id,
                    picker_id=request.picker_id,
                    assigned_at=now,
                    session=session
                )

                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Order or picker state changed. Please retry."
                    )

        return PackingResponse(
            order_id=order_id,
            status="assigned_to_packer",
            already_done=False
        )

    async def mark_packed(
        self,
        order_id: str
    ):

        db = get_database()

        order = await self.repository.get_order(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        # Already packed
        if order.get("status") == "packed":
            return PackingResponse(
                order_id=order_id,
                status="packed",
                already_done=True
            )

        # Order must currently be assigned to picker
        if order.get("status") != "assigned_to_packer":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order cannot be packed in its current state"
            )

        picker_data = order.get("packer")

        if not picker_data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order has no assigned picker"
            )

        picker_id = picker_data.get("user_id")

        now = datetime.now(timezone.utc)

        async with await db.client.start_session() as session:

            async with session.start_transaction():

                success = await self.repository.mark_order_packed(
                    order_id=order_id,
                    picker_id=picker_id,
                    packed_at=now,
                    session=session
                )

                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Order or picker state changed. Please retry."
                    )

        return PackingResponse(
            order_id=order_id,
            status="packed",
            already_done=False
        )