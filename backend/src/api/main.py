"""
FastAPI application entry point with API versioning.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter

from database import engine
from models import Base
from api.routers.auth import router as auth_router
from api.routers.users import router as users_router
from api.routers.subscriptions import router as subscriptions_router
from api.middleware import setup_cors, RateLimitMiddleware, setup_error_handlers
from logging_config import setup_logging


logger = setup_logging("first.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API server...")
    # using Alembic
    yield
    logger.info("Shutting down API server...")


app = FastAPI(
    title="First API",
    description="Job notification service API",
    version="1.0.0",
    lifespan=lifespan
)

# setup middleware
setup_cors(app)
app.add_middleware(RateLimitMiddleware, requests_per_minute=30)
setup_error_handlers(app)

# API v1 router
v1_router = APIRouter(prefix="/v1")

v1_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

v1_router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"]
)

v1_router.include_router(
    subscriptions_router,
    prefix="/subscriptions",
    tags=["Subscriptions"]
)

# mount v1 API
app.include_router(v1_router)


# health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}
