from typing import Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
)

from app.core.config import settings


class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


db_manager = DatabaseManager()


async def connect_to_mongo():
    """Connect to MongoDB Atlas during application startup."""

    db_manager.client = AsyncIOMotorClient(
        settings.MONGODB_URL
    )

    # Verify that Atlas is reachable.
    await db_manager.client.admin.command("ping")

    db_manager.db = db_manager.client[
        settings.DATABASE_NAME
    ]


async def close_mongo_connection():
    """Close MongoDB connection during application shutdown."""

    if db_manager.client:
        db_manager.client.close()

        db_manager.client = None
        db_manager.db = None


def get_database() -> AsyncIOMotorDatabase:
    """Return the shared MongoDB database instance."""

    if db_manager.db is None:
        raise RuntimeError(
            "Database connection has not been initialized."
        )

    return db_manager.db