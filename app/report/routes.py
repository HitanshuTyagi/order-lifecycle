from datetime import date

from fastapi import APIRouter, Query

from app.report.schemas import DailyReportResponse
from app.report.service import get_daily_report


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get(
    "/daily",
    response_model=DailyReportResponse,
)
async def daily_report(
    report_date: date = Query(
        ...,
        alias="date",
        description="Local calendar date, e.g. 2026-09-18",
    ),
) -> DailyReportResponse:
    """
    Return delivery statistics for the requested local date.
    """
    return await get_daily_report(report_date)