from datetime import date

from app.core.database import get_database
from app.core.enums import OrderStatus
from app.core.timezone import (
    get_report_timezone,
    get_utc_day_range,
    normalize_to_utc,
)
from app.report.schemas import (
    DailyReportItem,
    DailyReportResponse,
)


async def get_daily_report(
    report_date: date,
) -> DailyReportResponse:

    db = get_database()

    start_utc, end_utc = get_utc_day_range(report_date)

    orders = await db.orders.find(
        {
            "status": OrderStatus.DELIVERED.value,
            "delivered_at": {
                "$gte": start_utc,
                "$lt": end_utc,
            },
        }
    ).to_list(None)

    report_orders = []

    for order in orders:
        created_at = order.get("created_at")
        delivered_at = order.get("delivered_at")

        # Defensive read: skip malformed documents
        # instead of causing the whole API to fail.
        if created_at is None or delivered_at is None:
            continue

        created_at = normalize_to_utc(created_at)
        delivered_at = normalize_to_utc(delivered_at)

        duration = delivered_at - created_at
        duration_minutes = duration.total_seconds() / 60

        rider = order.get("rider") or {}
        rider_id = rider.get("id")

        report_orders.append(
            DailyReportItem(
                order_id=str(order["_id"]),
                rider_id=rider_id,
                created_at=created_at.astimezone(
                    get_report_timezone()
                ),
                delivered_at=delivered_at.astimezone(
                    get_report_timezone()
                ),
                duration_minutes=duration_minutes,
            )
        )

    return DailyReportResponse(
        date=report_date.isoformat(),
        timezone=str(get_report_timezone()),
        total_deliveries=len(report_orders),
        orders=report_orders,
    )