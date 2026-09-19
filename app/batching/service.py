from uuid import uuid4

from app.batching.schemas import (
    BatchConfig,
    BatchOrder,
    BatchResponse,
)
from app.core.database import get_database
from app.core.distance import calculate_route_distance_km
from app.core.enums import OrderStatus


DEFAULT_MAX_DISTANCE_KM = 5.0
DEFAULT_MAX_BATCH_SIZE = 4

# Replace these with the warehouse coordinates agreed on by the team.
DEFAULT_WAREHOUSE = (
    28.4595,
    77.0266,
)


async def get_batch_config() -> BatchConfig:
    """
    Read operational batching limits from MongoDB.

    Database configuration takes precedence. If the configuration
    document or an individual field is missing, use the application
    fallback.
    """

    db = get_database()

    config = await db.config.find_one(
        {"_id": "batching"}
    )

    if not config:
        return BatchConfig(
            max_distance_km=DEFAULT_MAX_DISTANCE_KM,
            max_batch_size=DEFAULT_MAX_BATCH_SIZE,
        )

    return BatchConfig(
        max_distance_km=config.get(
            "max_distance_km",
            DEFAULT_MAX_DISTANCE_KM,
        ),
        max_batch_size=config.get(
            "max_batch_size",
            DEFAULT_MAX_BATCH_SIZE,
        ),
    )


async def create_batch() -> BatchResponse:
    """
    Build one batch from orders that are ready to hand off.

    Current lifecycle:
        packed → assigned_to_rider

    Therefore PACKED is treated as the ready-to-go state.
    """

    db = get_database()
    config = await get_batch_config()

    # Readiness is determined by status, as required by the task.
    orders = await db.orders.find(
        {
            "status": OrderStatus.PACKED.value,
        }
    ).to_list(None)

    selected_orders: list[BatchOrder] = []
    selected_coordinates: list[tuple[float, float]] = []

    for order in orders:
        if len(selected_orders) >= config.max_batch_size:
            break

        location = order.get("delivery_location") or {}

        latitude = location.get("latitude")
        longitude = location.get("longitude")

        # Ignore malformed orders rather than crashing the entire
        # batching operation.
        if latitude is None or longitude is None:
            continue

        candidate = (
            latitude,
            longitude,
        )

        projected_route = [
            *selected_coordinates,
            candidate,
        ]

        # Check the actual route:
        #
        # warehouse → A → B → C
        #
        # rather than:
        #
        # warehouse → A
        # warehouse → B
        # warehouse → C
        projected_distance = calculate_route_distance_km(
            DEFAULT_WAREHOUSE,
            projected_route,
        )

        if projected_distance > config.max_distance_km:
            continue

        selected_orders.append(
            BatchOrder(
                order_id=str(order.get("_id", "unknown")),
                latitude=latitude,
                longitude=longitude,
            )
        )

        selected_coordinates.append(candidate)

    total_distance = calculate_route_distance_km(
        DEFAULT_WAREHOUSE,
        selected_coordinates,
    )

    return BatchResponse(
        batch_id=str(uuid4()),
        orders=selected_orders,
        total_distance_km=total_distance,
    )