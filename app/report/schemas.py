#Report Schema

# app/report/schemas.py

from datetime import datetime

from pydantic import BaseModel


class DailyReportItem(BaseModel):
    order_id: str
    rider_id: str | None = None
    
    created_at: datetime
    delivered_at: datetime

    duration_minutes: float


class DailyReportResponse(BaseModel):
    date: str
    timezone: str

    total_deliveries: int

    orders: list[DailyReportItem]