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
    report_date: date = Query(..., alias="date"),
):
    return await get_daily_report(report_date)


@router.get("/health")
def health():
    return {"message":"It works now"}