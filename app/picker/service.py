import asyncio
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.database import get_database
from app.picker.repository import PackingRepository
from app.picker.schemas import (
    AssignPickerRequest,
    PackingResponse
)
from pymongo.errors import OperationFailure


class PackingService:

    def __init__(self):
        self.repository = PackingRepository()

    async def assign_picker(
        self,
        order_id: str,
        request: AssignPickerRequest
    ):
        db = get_database()

        for attempt in range(3):

            # Fresh read on every attempt
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

            # Same picker already assigned
            if (
                order.get("status") == "assigned_to_packer"
                and order.get("packer", {}).get("user_id") == request.picker_id
            ):
                return PackingResponse(
                    order_id=order_id,
                    status="assigned_to_packer",
                    already_done=True
                )

            # Order is no longer in created state
            if order.get("status") != "created":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Order cannot be assigned in its current state"
                )

            # Picker already busy
            if not picker.get("is_available", False):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Picker is already handling another order"
                )

            now = datetime.now(timezone.utc)

            try:
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

                # Transaction succeeded
                return PackingResponse(
                    order_id=order_id,
                    status="assigned_to_packer",
                    already_done=False
                )

            except HTTPException as e:

                # Our transaction failed because another request
                # changed the order/picker state.
                if e.detail == "Order or picker state changed. Please retry.":

                    # Re-read the database AFTER transaction aborted
                    latest_order = await self.repository.get_order(order_id)

                    if not latest_order:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Order not found"
                        )

                    # Another concurrent request assigned
                    # the SAME picker successfully.
                    if (
                        latest_order.get("status") == "assigned_to_packer"
                        and latest_order.get("packer", {}).get("user_id")
                        == request.picker_id
                    ):
                        return PackingResponse(
                            order_id=order_id,
                            status="assigned_to_packer",
                            already_done=True
                        )

                    # Someone else assigned the order
                    if latest_order.get("status") != "created":
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Order cannot be assigned in its current state"
                        )

                    # Order is still created, so check picker again
                    latest_picker = await self.repository.get_picker(
                        request.picker_id
                    )

                    if not latest_picker:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Picker not found"
                        )

                    if not latest_picker.get("is_available", False):
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Picker is already handling another order"
                        )

                    # State may now be usable again.
                    # Retry the whole operation.
                    if attempt < 2:
                        continue

                # Any other HTTPException should be returned normally
                raise

            except OperationFailure as e:

                # MongoDB says transaction should be retried
                if (
                    "TransientTransactionError"
                    in (e.details or {}).get("errorLabels", [])
                ):
                    if attempt < 2:
                        continue

                raise

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not assign picker due to concurrent update"
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

        try:
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
        except HTTPException as exc:
            if exc.detail == "Order or picker state changed. Please retry.":
                latest_order = await self.repository.get_order(order_id)
                if latest_order and latest_order.get("status") == "packed":
                    return PackingResponse(
                        order_id=order_id,
                        status="packed",
                        already_done=True
                    )
            raise
        except OperationFailure:
            for _ in range(3):
                await asyncio.sleep(0.01)
                latest_order = await self.repository.get_order(order_id)
                if latest_order and latest_order.get("status") == "packed":
                    return PackingResponse(
                        order_id=order_id,
                        status="packed",
                        already_done=True
                    )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order is being packed. Please retry."
            )

        return PackingResponse(
            order_id=order_id,
            status="packed",
            already_done=False
        )