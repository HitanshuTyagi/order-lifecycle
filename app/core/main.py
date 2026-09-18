from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import (
    connect_to_mongo,
    close_mongo_connection,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""

    await connect_to_mongo()

    print("MongoDB Atlas connected")

    yield

    await close_mongo_connection()

    print("MongoDB connection closed")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "message": "Order Lifecycle API",
        "version": settings.VERSION,
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "database": "connected",
    }