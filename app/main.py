from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, initialize_database

from app.orders.routes import router as orders_router
from app.users.routes import router as users_router
from app.picker.routes import router as packing_router
from app.batching.routes import router as batching_router
from app.test_timezone import timecheck

from app.report.routes import router as report_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    print("MongoDB Atlas connected")

    await initialize_database()
    print("Database initialized")

    yield

    await close_mongo_connection()
    print("MongoDB connection closed")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.include_router(
    users_router,
    prefix=settings.API_V1_STR
)

app.include_router(
    orders_router,
    prefix=settings.API_V1_STR
)

app.include_router(
    packing_router,
    prefix=settings.API_V1_STR
)

app.include_router(
    report_router,
    prefix=settings.API_V1_STR,
)
app.include_router(
    batching_router,
    prefix=settings.API_V1_STR,
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

@app.get('/report')
async def report():
    ans = timecheck()
    return {"message":ans}


