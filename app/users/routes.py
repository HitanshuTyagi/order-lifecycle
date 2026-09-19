from fastapi import APIRouter, status

from app.users.schemas import CreateUserRequest
from app.users.service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

service = UserService()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(request: CreateUserRequest):
    return await service.create_user(request)

@router.get("/pickers")
async def get_all_pickers():
    return await service.get_all_pickers()

@router.get("/pickers/{picker_id}")
async def get_picker(picker_id: str):
    return await service.get_user(picker_id)

@router.get("/pickers/{picker_id}/status")
async def get_picker_status(picker_id: str):
    return await service.get_picker_status(picker_id)

@router.get("/users")
async def get_all_users():
    return await service.get_all_users()