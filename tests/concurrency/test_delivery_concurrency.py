import asyncio
from datetime import datetime, timezone
import os
import sys
from pathlib import Path

import httpx
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.config import settings


URL = os.getenv("DELIVERY_TEST_URL", "http://127.0.0.1:8000")

ORDER_ID = "order_test_delivery_101"
RIDER_ID = "user_test_rider_202"


async def mark_delivered(client: httpx.AsyncClient, request_no: int):
    response = await client.post(
        f"{URL}/api/v1/orders/{ORDER_ID}/mark-delivered"
    )
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return request_no, response.status_code, body


async def main():
    mongo = AsyncIOMotorClient(settings.MONGODB_URL)
    db = mongo[settings.DATABASE_NAME]

    now = datetime.now(timezone.utc)

    # 1. Seed test rider
    await db.users.update_one(
        {"_id": RIDER_ID},
        {"$set": {
            "name": "Flash Rider",
            "role": "delivery_boy",
        }},
        upsert=True,
    )

    # 2. Seed test order satisfying strict MongoDB schema validator
    test_order_doc = {
        "_id": ORDER_ID,
        "customer_id": "cust_101",
        "items": [
            {
                "medicine_id": "med_1",
                "name": "Paracetamol",
                "quantity": 2,
            }
        ],
        "delivery_location": {
            "latitude": 28.7041,
            "longitude": 77.1025,
        },
        "status": "assigned_to_rider",
        "packer": {
            "id": "packer_1",
            "name": "John Packer",
        },
        "packed_at": now,
        "rider": {
            "id": RIDER_ID,
            "assigned_at": now,
        },
        "delivered_at": None,
        "created_at": now,
        "updated_at": now,
    }

    await db.orders.replace_one(
        {"_id": ORDER_ID},
        test_order_doc,
        upsert=True,
    )

    # Ensure clean deliveries collection for test order
    await db.deliveries.delete_many({"order_id": ORDER_ID})

    try:
        print(f"--- Starting Concurrency Test for {ORDER_ID} (20 parallel requests) ---")
        async with httpx.AsyncClient(timeout=30.0) as client:
            results = await asyncio.gather(
                *(mark_delivered(client, req_no) for req_no in range(1, 21))
            )

            successful = [
                body for _, code, body in results
                if code == 200 and not body.get("already_done")
            ]
            already_done = [
                body for _, code, body in results
                if code == 200 and body.get("already_done")
            ]

            for request_no, code, body in results:
                label = (
                    "DELIVERED_BY_THIS_REQUEST"
                    if body.get("already_done") is False
                    else "ALREADY_DONE (IDEMPOTENT)"
                )
                print(
                    f"request={request_no:02d} | code={code} | "
                    f"order_id={body.get('order_id')} | result={label}"
                )

            # Assertions on API responses
            assert len(successful) == 1, f"Expected exactly 1 fresh delivery, got {len(successful)}"
            assert len(already_done) == 19, f"Expected 19 idempotent responses, got {len(already_done)}"
            assert all(code == 200 for _, code, _ in results), "Not all status codes were 200"

            # 3. Test Today's Deliveries endpoint
            today_resp = await client.get(f"{URL}/api/v1/deliveries/today")
            assert today_resp.status_code == 200, f"Expected 200 from /deliveries/today, got {today_resp.status_code}"
            today_data = today_resp.json()
            matching = [d for d in today_data.get("deliveries", []) if d.get("order_id") == ORDER_ID]
            assert len(matching) == 1, f"Expected exactly 1 delivery in /today list, got {len(matching)}"
            assert matching[0]["rider_name"] == "Flash Rider"

        # 4. Assertions on Database State
        order_doc = await db.orders.find_one({"_id": ORDER_ID})
        assert order_doc["status"] == "delivered", f"Expected order status 'delivered', got {order_doc.get('status')}"
        assert order_doc["delivered_at"] is not None

        delivery_count = await db.deliveries.count_documents({"order_id": ORDER_ID})
        assert delivery_count == 1, f"Expected exactly 1 delivery record in MongoDB, got {delivery_count}"

        print("----------------------------------------------------------------------")
        print("✅ PASS: Exactly 1 delivery recorded, 19 idempotent responses handled.")
        print(f"✅ PASS: MongoDB unique constraint verified (deliveries count = {delivery_count}).")
        print("✅ PASS: /api/v1/deliveries/today verified with rider name resolution.")
        print("----------------------------------------------------------------------")

    finally:
        # Cleanup test data
        await db.orders.delete_one({"_id": ORDER_ID})
        await db.users.delete_one({"_id": RIDER_ID})
        await db.deliveries.delete_many({"order_id": ORDER_ID})
        mongo.close()


if __name__ == "__main__":
    asyncio.run(main())
