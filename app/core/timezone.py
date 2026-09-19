from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings


def normalize_to_utc(dt: datetime) -> datetime:
    """
    Normalize a datetime to a timezone-aware UTC datetime.

    Naive datetimes are interpreted as UTC because project
    timestamps are stored in UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def get_report_timezone() -> ZoneInfo:
    """Return the configured reporting timezone."""
    return ZoneInfo(settings.REPORT_TIMEZONE)


def get_utc_day_range(
    report_date: date,
) -> tuple[datetime, datetime]:
    """
    Convert a local calendar day into a UTC range.

    The returned range is [start_utc, end_utc).
    """
    local_tz = get_report_timezone()

    start_local = datetime.combine(
        report_date,
        time.min,
        tzinfo=local_tz,
    )

    end_local = start_local + timedelta(days=1)

    return (
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
    )