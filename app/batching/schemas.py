from pydantic import BaseModel, Field


class BatchConfig(BaseModel):
    """Operational parameters controlling batch creation."""

    max_distance_km: float = Field(gt=0)
    max_batch_size: int = Field(gt=0)


class BatchOrder(BaseModel):
    """Minimal order information required by the batching API."""

    order_id: str
    latitude: float
    longitude: float


class BatchResponse(BaseModel):
    """One generated rider batch."""

    batch_id: str
    orders: list[BatchOrder]

    total_distance_km: float