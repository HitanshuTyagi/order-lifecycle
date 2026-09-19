import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.config import settings


URL = os.getenv("PICKER_TEST_URL", "http://127.0.0.1:8000")
ORDER_ID = "order_legacy_missing_created_at"


async def main():
    mongo = AsyncIOMotorClient(settings.MONGODB_URL)
    db = mongo[settings.DATABASE_NAME]
    delivered_at = datetime.now(timezone.utc)
    report_date = delivered_at.astimezone(
        ZoneInfo(settings.REPORT_TIMEZONE)
    ).date().isoformat()
    legacy_order = {
        "_id": ORDER_ID,
        "status": "delivered",
        "delivered_at": delivered_at,
    }

    try:
        try:
            await db.orders.insert_one(legacy_order)
        except OperationFailure as exc:
            assert exc.code == 121
        else:
            raise AssertionError("Order validator accepted a missing field")

        await db.orders.insert_one(
            legacy_order,
            bypass_document_validation=True,
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{URL}/api/v1/reports/daily",
                params={"date": report_date},
            )

        assert response.status_code == 200, response.text
        body = response.json()
        assert ORDER_ID not in {
            item["order_id"] for item in body["orders"]
        }
        print("PASS: validator blocked new bad data and report skipped legacy data")
    finally:
        await db.orders.delete_one({"_id": ORDER_ID})
        mongo.close()


asyncio.run(main())
