import asyncio
import os
import sys
from pathlib import Path

import httpx
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.config import settings


URL = os.getenv("PICKER_TEST_URL", "http://127.0.0.1:8000")

ORDER_ID = "order_145ab422"
PICKER_ID = "user_611e6ddd"


async def mark_packed(client, request_no):
    response = await client.post(
        f"{URL}/api/v1/orders/{ORDER_ID}/mark-packed"
    )
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return request_no, response.status_code, body


async def main():
    mongo = AsyncIOMotorClient(settings.MONGODB_URL)
    db = mongo[settings.DATABASE_NAME]
    await db.orders.update_one(
        {"_id": ORDER_ID},
        {"$set": {
            "status": "assigned_to_packer",
            "packer": {"user_id": PICKER_ID},
            "packed_at": None,
        }},
        upsert=True,
    )
    await db.users.update_one(
        {"_id": PICKER_ID},
        {"$set": {
            "role": "picker",
            "is_available": False,
            "current_order_id": ORDER_ID,
        }},
        upsert=True,
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            results = await asyncio.gather(
                *(mark_packed(client, request_no) for request_no in range(1, 21))
            )

            successful = [
                body for _, code, body in results
                if code == 200 and not body["already_done"]
            ]
            already_done = [
                body for _, code, body in results
                if code == 200 and body["already_done"]
            ]

            for request_no, code, body in results:
                label = (
                    "PACKED_BY_THIS_REQUEST"
                    if body.get("already_done") is False
                    else "ALREADY_DONE"
                )
                print(
                    f"request={request_no} code={code} "
                    f"status={body.get('status')} result={label}"
                )

            assert len(successful) == 1
            assert len(already_done) == 19
            assert all(code == 200 for _, code, _ in results)

        order = await db.orders.find_one({"_id": ORDER_ID})
        assert order["status"] == "packed"
        assert order["packed_at"] is not None
        print("PASS: one pack and 19 idempotent responses")
    finally:
        await db.orders.delete_one({"_id": ORDER_ID})
        await db.users.delete_one({"_id": PICKER_ID})
        mongo.close()


asyncio.run(main())