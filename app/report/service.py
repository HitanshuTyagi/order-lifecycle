"""
Business logic for daily delivery reports.
"""

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
    DailyReportSummary,
    RiderReport,
)


async def get_daily_report(
    report_date: date,
) -> DailyReportResponse:
    """
    Generate a delivery report for one local calendar day.

    MongoDB stores timestamps in UTC, therefore the requested
    local date is converted to a UTC range before querying.
    """

    db = get_database()

    # Convert the human-facing local date into UTC boundaries.
    start_utc, end_utc = get_utc_day_range(report_date)

    # Filter in MongoDB instead of loading unrelated orders.
    # `$lt` on the end boundary makes the range half-open.
    orders = await db.orders.find(
        {
            "status": OrderStatus.DELIVERED.value,
            "delivered_at": {
                "$gte": start_utc,
                "$lt": end_utc,
            },
        }
    ).to_list(None)

    report_orders: list[DailyReportItem] = []

    # Rider statistics are accumulated while processing orders.
    # This avoids one database query per rider/order.
    rider_stats: dict[str, dict[str, float]] = {}

    for order in orders:
        # Existing production data may predate the current schema.
        # Missing timestamps should not make the entire report fail.
        created_at = order.get("created_at")
        delivered_at = order.get("delivered_at")

        if created_at is None or delivered_at is None:
            continue

        # Normalize everything before doing datetime arithmetic.
        created_at_utc = normalize_to_utc(created_at)
        delivered_at_utc = normalize_to_utc(delivered_at)

        # Calculate elapsed time using UTC timestamps.
        duration = delivered_at_utc - created_at_utc
        duration_minutes = duration.total_seconds() // 60

        # Rider information is embedded in the current order shape.
        # `.get()` keeps this safe for older documents.
        rider = order.get("rider") or {}
        rider_id = rider.get("id")

        report_orders.append(
            DailyReportItem(
                order_id=str(order["_id"]),
                rider_id=rider_id,

                # Convert UTC to local time only at the response edge.
                created_at=created_at_utc.astimezone(
                    get_report_timezone()
                ),
                delivered_at=delivered_at_utc.astimezone(
                    get_report_timezone()
                ),
                duration_minutes=duration_minutes,
            )
        )

        if rider_id:
            rider_data = rider_stats.setdefault(
                rider_id,
                {
                    "deliveries": 0,
                    "total_duration": 0,
                },
            )

            rider_data["deliveries"] += 1
            rider_data["total_duration"] += duration_minutes

    durations = [
        item.duration_minutes
        for item in report_orders
    ]

    if durations:
        average_duration = sum(durations) // len(durations)
        minimum_duration = min(durations)
        maximum_duration = max(durations)
    else:
        average_duration = 0.0
        minimum_duration = None
        maximum_duration = None

    summary = DailyReportSummary(
        total_orders_delivered=len(report_orders),
        average_delivery_time_minutes=average_duration,
        minimum_delivery_time_minutes=minimum_duration,
        maximum_delivery_time_minutes=maximum_duration,
    )

    rider_summary: list[RiderReport] = []

    for rider_id, data in rider_stats.items():
        deliveries = int(data["deliveries"])
        total_duration = data["total_duration"]

        rider_summary.append(
            RiderReport(
                rider_id=rider_id,
                deliveries=deliveries,
                average_delivery_time_minutes=(
                    total_duration / deliveries
                ),
            )
        )

    return DailyReportResponse(
        date=report_date.isoformat(),
        timezone=str(get_report_timezone()),
        summary=summary,
        rider_summary=rider_summary,
        orders=report_orders,
    )