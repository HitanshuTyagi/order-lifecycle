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
    Build the delivery report for one local calendar day.

    The important part here is that `report_date` represents a date
    in the configured reporting timezone, while MongoDB stores
    timestamps in UTC.
    """

    db = get_database()

    # Convert the requested local calendar day into a UTC range.
    #
    # Example for Asia/Kolkata:
    # 2026-09-18 00:00 IST
    #       becomes
    # 2026-09-17 18:30 UTC
    #
    # We use [start, end) so the next midnight belongs only to
    # the following day's report.
    start_utc, end_utc = get_utc_day_range(report_date)

    # We only need orders whose delivery happened during this
    # particular local day. Filtering in MongoDB avoids loading
    # unrelated orders into Python.
    print("Hi Hello")
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

    # Keep rider statistics in memory while processing the orders.
    # This avoids another database query for every delivery.
    rider_stats: dict[str, dict[str, float]] = {}

    for order in orders:
        # Use .get() for fields that may be missing in older or
        # malformed documents. One bad document should not make
        # the entire reporting endpoint return HTTP 500.
        created_at = order.get("created_at")
        delivered_at = order.get("delivered_at")

        if created_at is None or delivered_at is None:
            continue

        # MongoDB/driver configuration can sometimes expose a
        # datetime without timezone information. Normalize both
        # values before doing comparisons or subtraction.
        created_at_utc = normalize_to_utc(created_at)
        delivered_at_utc = normalize_to_utc(delivered_at)

        # Delivery duration is an elapsed-time calculation, so
        # calculate it using normalized UTC timestamps.
        duration = delivered_at_utc - created_at_utc
        duration_minutes = duration.total_seconds() // 60

        # `rider` is embedded inside the order according to the
        # current project schema. Using .get() keeps this read
        # safe if an old document has no rider information.
        rider = order.get("rider") or {}
        rider_id = rider.get("id")

        report_orders.append(
            DailyReportItem(
                order_id=str(order["_id"]),
                rider_id=rider_id,

                # The database representation remains UTC.
                # We convert to the configured reporting timezone
                # only when preparing the API response.
                created_at=created_at_utc.astimezone(
                    get_report_timezone()
                ),
                delivered_at=delivered_at_utc.astimezone(
                    get_report_timezone()
                ),
                duration_minutes=duration_minutes,
            )
        )

        # Build rider-level statistics without querying MongoDB
        # again for each rider/order.
        if rider_id:
            if rider_id not in rider_stats:
                rider_stats[rider_id] = {
                    "deliveries": 0,
                    "total_duration": 0,
                }

            rider_stats[rider_id]["deliveries"] += 1
            rider_stats[rider_id]["total_duration"] += duration_minutes

    # Calculate overall delivery statistics from the successfully
    # processed report records.
    durations = [
        order.duration_minutes
        for order in report_orders
    ]

    if durations:
        average_duration = sum(durations) / len(durations)
        minimum_duration = min(durations)
        maximum_duration = max(durations)
    else:
        # A day with no valid deliveries is still a valid report.
        average_duration = 0.0
        minimum_duration = None
        maximum_duration = None

    summary = DailyReportSummary(
        total_orders_delivered=len(report_orders),
        average_delivery_time_minutes=average_duration,
        minimum_delivery_time_minutes=minimum_duration,
        maximum_delivery_time_minutes=maximum_duration,
    )

    # Convert the accumulated rider statistics into the response
    # schema. No additional database calls are necessary.
    rider_summary: list[RiderReport] = []

    for rider_id, stats in rider_stats.items():
        deliveries = int(stats["deliveries"])
        total_duration = stats["total_duration"]

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