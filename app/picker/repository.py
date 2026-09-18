from app.core.database import get_database


class PackingRepository:

    async def get_order(self, order_id: str, session=None):
        db = get_database()

        return await db.orders.find_one(
            {"_id": order_id},
            session=session
        )

    async def get_picker(self, picker_id: str, session=None):
        db = get_database()

        return await db.users.find_one(
            {
                "_id": picker_id,
                "role": "picker"
            },
            session=session
        )

    async def assign_picker_to_order(
        self,
        order_id: str,
        picker_id: str,
        assigned_at,
        session
    ):
        db = get_database()

        order_result = await db.orders.update_one(
            {
                "_id": order_id,
                "status": "created"
            },
            {
                "$set": {
                    "status": "assigned_to_packer",
                    "packer": {
                        "user_id": picker_id,
                        "assigned_at": assigned_at
                    },
                    "updated_at": assigned_at
                }
            },
            session=session
        )

        if order_result.modified_count != 1:
            return False

        picker_result = await db.users.update_one(
            {
                "_id": picker_id,
                "role": "picker",
                "is_available": True,
                "current_order_id": None
            },
            {
                "$set": {
                    "is_available": False,
                    "current_order_id": order_id
                }
            },
            session=session
        )

        if picker_result.modified_count != 1:
            return False

        return True

    async def mark_order_packed(
        self,
        order_id: str,
        picker_id: str,
        packed_at,
        session
    ):
        db = get_database()

        order_result = await db.orders.update_one(
            {
                "_id": order_id,
                "status": "assigned_to_packer",
                "packer.user_id": picker_id
            },
            {
                "$set": {
                    "status": "packed",
                    "packed_at": packed_at,
                    "updated_at": packed_at
                }
            },
            session=session
        )

        if order_result.modified_count != 1:
            return False

        picker_result = await db.users.update_one(
            {
                "_id": picker_id,
                "role": "picker",
                "current_order_id": order_id,
                "is_available": False
            },
            {
                "$set": {
                    "is_available": True,
                    "current_order_id": None
                }
            },
            session=session
        )

        if picker_result.modified_count != 1:
            return False

        return True