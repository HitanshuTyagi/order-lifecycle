from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import UserRole


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1)
    role: UserRole


class UserResponse(BaseModel):
    id: str
    name: str
    role: UserRole
    created_at: datetime