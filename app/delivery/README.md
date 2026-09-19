# Delivery Module (Person B: Rider Delivery Workflow)

## Overview

The **Delivery Module** is responsible for managing the post-packing stage of the order lifecycle. It coordinates assigning delivery riders to packed orders, marking orders as delivered with strict idempotency guarantees, and reporting daily delivery metrics while avoiding common production pitfalls (such as the N+1 query problem and duplicate delivery records).

---

## State Machine & Transitions

The delivery module operates on the following state transitions:

```
                  ┌──────────────────────┐
                  │    status: packed    │
                  └──────────┬───────────┘
                             │
                             │ POST /api/v1/orders/{order_id}/assign-rider
                             ▼
                  ┌──────────────────────┐
                  │  assigned_to_rider   │
                  └──────────┬───────────┘
                             │
                             │ POST /api/v1/orders/{order_id}/mark-delivered
                             ▼
                  ┌──────────────────────┐
                  │   status: delivered  │
                  └──────────────────────┘
```

---

## File Structure

```
app/delivery/
├── __init__.py
├── README.md        # This documentation
├── router.py        # FastAPI route definitions and dependency injection
├── schemas.py       # Pydantic request/response schemas
├── service.py       # Core business logic, idempotency, and validations
└── repository.py    # Direct MongoDB queries and atomic operations
```

---

## Endpoints

### 1. Assign Rider to Order
- **Method & Path**: `POST /api/v1/orders/{order_id}/assign-rider`
- **Description**: Assigns an available rider (`role: "delivery_boy"`) to an order in `packed` status.
- **Validations**:
  - Verifies that the order exists (404 if not found).
  - Verifies that the rider exists and possesses the `delivery_boy` role (404 if invalid).
  - Verifies that the order is currently in `packed` status (409 if not).
  - **Idempotency**: If the same rider is already assigned to this order, returns HTTP 200 with the existing assignment timestamp.
- **Request Body**:
  ```json
  {
    "rider_id": "rider_101"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "order_id": "order_abc123",
    "rider_id": "rider_101",
    "status": "assigned_to_rider",
    "assigned_at": "2026-09-19T10:30:00Z"
  }
  ```

---

### 2. Mark Order as Delivered (Idempotent)
- **Method & Path**: `POST /api/v1/orders/{order_id}/mark-delivered`
- **Description**: Marks an assigned order as delivered and writes a single permanent audit record to the `deliveries` collection.
- **Validations**:
  - Verifies that the order exists (404 if not found).
  - Verifies that the order is in `assigned_to_rider` status and has an assigned rider (409 if not).
- **Response** (`200 OK`):
  ```json
  {
    "order_id": "order_abc123",
    "delivery_id": "6507c8f...",
    "rider_id": "rider_101",
    "delivered_at": "2026-09-19T11:15:00Z",
    "already_done": false
  }
  ```
- **Idempotent Retry Response** (`200 OK`):
  If the order was already marked delivered (e.g., retried HTTP request due to mobile network drop):
  ```json
  {
    "order_id": "order_abc123",
    "delivery_id": "6507c8f...",
    "rider_id": "rider_101",
    "delivered_at": "2026-09-19T11:15:00Z",
    "already_done": true
  }
  ```

---

### 3. Get Today's Deliveries
- **Method & Path**: `GET /api/v1/deliveries/today`
- **Description**: Returns all orders delivered during the current day according to the configured timezone (`REPORT_TIMEZONE`, e.g., `Asia/Kolkata`).
- **Response** (`200 OK`):
  ```json
  {
    "deliveries": [
      {
        "order_id": "order_abc123",
        "rider_id": "rider_101",
        "rider_name": "John Doe",
        "delivered_at": "2026-09-19T11:15:00Z"
      }
    ]
  }
  ```

---

## Production Reliability & Architecture Design

### 1. The 7.5% Duplicate Delivery Bug & Rider Payout Inflation

#### The Problem:
In real-world delivery apps, riders face poor mobile connectivity or tap the "Mark Delivered" button repeatedly. Without idempotency protection:
- Client retry storms can result in up to 3–4 delivery records for a single physical drop-off.
- In production, roughly **7.5% of delivery records** became duplicates, inflating rider payouts and corrupting finance reports for months.

#### The Multi-Layer Solution:
1. **Database Hard Constraint**:
   ```python
   # app/core/database.py
   await db.deliveries.create_index("order_id", unique=True)
   ```
   MongoDB guarantees at the storage engine level that **no two delivery documents can ever share the same `order_id`**.

2. **Sequential Fast-Path Idempotency**:
   ```python
   # app/delivery/service.py
   if order.get("status") == "delivered":
       existing = await self.repository.get_delivery_by_order(order_id)
       if existing:
           return DeliveryResponse(..., already_done=True)
   ```
   If the order is already marked delivered, returns the existing record immediately without raising an error.

3. **Concurrency & Race-Condition Handling**:
   If parallel retries pass the initial status check at the exact same millisecond:
   ```python
   try:
       result = await self.repository.create_delivery(order_id, rider_id, now)
   except DuplicateKeyError:
       existing = await self.repository.get_delivery_by_order(order_id)
       return DeliveryResponse(..., already_done=True)
   ```
   The first insert succeeds; the parallel insert trips the unique index, catches `DuplicateKeyError`, and returns the existing delivery with `already_done=True`.

4. **Atomic State Transition**:
   ```python
   # app/delivery/repository.py
   await self.orders.update_one(
       {"_id": order_id, "status": "assigned_to_rider"},
       {"$set": {"status": "delivered", "delivered_at": delivered_at}}
   )
   ```

---

### 2. Eliminating the N+1 Query Problem

When retrieving today's deliveries with rider names:
- **Naive approach**: Query all deliveries (1 query), then iterate through each delivery and query the user document for the rider name ($N$ queries). For 500 deliveries, that requires 501 network roundtrips.
- **Our implementation (2 queries total)**:
  1. **Query 1**: Fetch deliveries in date range:
     ```python
     deliveries = await self.repository.get_today_deliveries(start_utc, end_utc)
     ```
  2. **Query 2**: Extract unique `rider_id` values and batch query using `$in`:
     ```python
     rider_ids = list({d["rider_id"] for d in deliveries})
     riders = await self.repository.get_riders_by_ids(rider_ids)
     ```
  3. Map rider IDs to rider names in-memory.

---

### 3. Timezone Handling

- Daily reporting window starts at `00:00:00.000` and ends at `23:59:59.999` in the business timezone (`settings.REPORT_TIMEZONE`, e.g., `Asia/Kolkata`).
- Dates are converted to UTC before querying MongoDB, ensuring timestamp accuracy regardless of where the server or database is hosted.

---

## MongoDB Collections Used

| Collection | Role in Delivery Module |
| :--- | :--- |
| `orders` | Reads order status; updates order with rider assignment and final delivered state. |
| `users` | Verifies rider existence and `role == "delivery_boy"`; batch-fetches rider names. |
| `deliveries` | Audit log of completed deliveries. Enforces uniqueness on `order_id`. |
