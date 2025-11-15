import os
import sys
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils.settings import get_settings
from app.utils.logger import init_logger
from app.middleware.request_logger import RequestLoggingMiddleware
from app.middleware.error_handler import register_error_handlers
from app.services.subscription_service import SqlAlchemySubscriptionService
from app.utils.db import get_session_factory, create_all, get_engine
from app.resources.health import router as health_router
from app.resources.subscriptions import router as subscriptions_router


settings = get_settings()
logger = init_logger(settings)

openapi_tags = [
    {
        "name": "health",
        "description": "Service health and readiness checks.",
    },
    {
        "name": "subscriptions",
        "description": "Operations for managing subscriptions.",
    },
]

app = FastAPI(
    title=settings.app_name,
    description="Whatsub Subscriptions Microservice",
    version="0.1.0",
    contact={
        "name": "Whatsub Team",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware, logger=logger)

register_error_handlers(app, logger)

# Require database configuration - fail if not provided or connection fails
missing_vars = []
if not settings.db_host:
    missing_vars.append("db_host")
if not settings.db_user:
    missing_vars.append("db_user")
if not settings.db_pass:
    missing_vars.append("db_pass")
if not settings.db_name:
    missing_vars.append("db_name")

if missing_vars:
    error_msg = f"Database configuration is required. Missing environment variables: {', '.join(missing_vars)}"
    logger.error("database_configuration_missing", missing_variables=missing_vars)
    raise RuntimeError(error_msg)

# Connect to database - fail fast if connection cannot be established
try:
    engine = get_engine()
    create_all(engine)  # Create tables if they don't exist
    session_factory = get_session_factory()
    app.state.subscription_service = SqlAlchemySubscriptionService(logger, session_factory)
    logger.info("database_connected", host=settings.db_host, database=settings.db_name)
except Exception as e:
    error_msg = f"Failed to connect to database: {str(e)}"
    logger.error("database_connection_failed", error=error_msg)
    raise RuntimeError(error_msg) from e

app.include_router(health_router, prefix="")
app.include_router(subscriptions_router, prefix="/subscriptions", tags=["subscriptions"])


@app.get("/")
async def root():
    return {"service": settings.app_name, "status": "running"}


if __name__ == "__main__":
    import uvicorn
    # Use PORT env var (required for Cloud Run) or fallback to settings
    port = int(os.getenv("PORT", settings.port))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)

