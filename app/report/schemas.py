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


class DailyReportSummary(BaseModel):
    total_orders_delivered: int
    average_delivery_time_minutes: float
    minimum_delivery_time_minutes: float | None = None
    maximum_delivery_time_minutes: float | None = None


class RiderReport(BaseModel):
    rider_id: str
    deliveries: int
    average_delivery_time_minutes: float


class DailyReportResponse(BaseModel):
    date: str
    timezone: str

    summary: DailyReportSummary
    rider_summary: list[RiderReport]

    orders: list[DailyReportItem]