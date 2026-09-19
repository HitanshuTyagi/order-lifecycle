from datetime import datetime, timezone
from uuid import uuid4

from app.users.repository import UserRepository
from app.users.schemas import CreateUserRequest


class UserService:

    def __init__(self):
        self.repository = UserRepository()

    async def create_user(self, request: CreateUserRequest):

        now = datetime.now(timezone.utc)

        user = {
            "_id": f"user_{uuid4().hex[:8]}",
            "name": request.name,
            "role": request.role.value,

            "is_available": True,
            "current_order_id": None,

            "created_at": now
        }

        return await self.repository.create_user(user)

    async def get_user(self, user_id: str):

        return await self.repository.get_user_by_id(user_id)

    async def get_all_pickers(self):
        return await self.repository.get_all_pickers()

    async def get_picker_status(self, picker_id: str):
        return await self.repository.get_picker_status(picker_id)
    
    async def get_all_users(self):
        return await self.repository.get_all_users()