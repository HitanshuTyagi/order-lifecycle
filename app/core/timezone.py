"""
Timezone helpers used by the reporting module.

Project rule:
- Store timestamps in UTC.
- Convert to the configured local timezone only at the reporting boundary.
"""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings


def get_report_timezone() -> ZoneInfo:
    """Return the timezone configured for human-readable reports."""
    return ZoneInfo(settings.REPORT_TIMEZONE)


def normalize_to_utc(dt: datetime) -> datetime:
    """
    Return a timezone-aware UTC datetime.

    MongoDB drivers can sometimes return naive datetimes.
    Since this project stores timestamps in UTC, a naive value
    from the database is interpreted as UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def get_utc_day_range(
    report_date: date,
) -> tuple[datetime, datetime]:
    """
    Convert one local calendar day into a UTC range.

    The range is half-open:

        [start_utc, end_utc)

    This prevents an order delivered exactly at midnight from
    appearing in two different daily reports.
    """
    report_timezone = get_report_timezone()

    start_local = datetime.combine(
        report_date,
        time.min,
        tzinfo=report_timezone,
    )

    end_local = start_local + timedelta(days=1)

    return (
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
    )