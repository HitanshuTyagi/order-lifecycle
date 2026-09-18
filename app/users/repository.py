from app.core.database import get_database


class UserRepository:

    async def get_user_by_id(self, user_id: str):
        db = get_database()

        user = await db.users.find_one({
            "_id": user_id
        })

        if user:
            user["_id"] = str(user["_id"])

        return user

    async def create_user(self, user):
        db = get_database()

        await db.users.insert_one(user)

        return user
    
    async def get_all_pickers(self):
        db = get_database()

        pickers = await db.users.find({
            "role": "picker"
        }).to_list(length=None)

        for picker in pickers:
            picker["_id"] = str(picker["_id"])

        return pickers 


    async def get_picker_status(self, picker_id: str):
        db = get_database()

        picker = await db.users.find_one({
            "_id": picker_id,
            "role": "picker"
        })

        if not picker:
            return None

        picker["_id"] = str(picker["_id"])

        order_status = None

        if picker.get("current_order_id"):
            order = await db.orders.find_one({
                "_id": picker["current_order_id"]
            })

            if order:
                order_status = order.get("status")

        picker["current_order_status"] = order_status

        return picker