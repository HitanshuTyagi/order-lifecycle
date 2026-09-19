from datetime import datetime

from pydantic import BaseModel


class DailyReportItem(BaseModel):
    """Information about one successfully processed delivery."""

    order_id: str
    rider_id: str | None = None

    created_at: datetime
    delivered_at: datetime

    duration_minutes: float


class DailyReportSummary(BaseModel):
    """Overall delivery statistics for the selected day."""

    total_orders_delivered: int
    average_delivery_time_minutes: float

    minimum_delivery_time_minutes: float | None = None
    maximum_delivery_time_minutes: float | None = None


class RiderReport(BaseModel):
    """Aggregated delivery statistics for one rider."""

    rider_id: str
    deliveries: int
    average_delivery_time_minutes: float


class DailyReportResponse(BaseModel):
    """Complete daily delivery report."""

    date: str
    timezone: str

    summary: DailyReportSummary
    rider_summary: list[RiderReport]

    orders: list[DailyReportItem]