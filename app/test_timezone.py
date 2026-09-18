from datetime import date

from app.core.timezone import get_utc_day_range

def timecheck():
    start_utc,end_utc = get_utc_day_range(date(2026,9,18))
    return [start_utc,end_utc]
    