from pydantic import BaseModel


class AssignPickerRequest(BaseModel):
    picker_id: str


class PackingResponse(BaseModel):
    order_id: str
    status: str
    already_done: bool = False