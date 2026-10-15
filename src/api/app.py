"""FastAPI Application Configuration and Lifespan."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import analytics, dashboard, database, health, pipeline, quality
from src.config import setup_logging
from src.load import get_db_engine, init_database

logger = logging.getLogger("sales_pipeline.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle handler."""
    setup_logging()
    logger.info("Initializing database schema on API startup...")
    engine = get_db_engine()
    init_database(engine)
    engine.dispose()
    logger.info("Sales Data Platform API successfully initialized.")
    yield
    logger.info("Sales Data Platform API shutting down.")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="Sales Data Engineering Analytics Platform",
        description="RESTful API for ETL execution, data quality auditing, and SQL analytics.",
        version="2.0.0",
        lifespan=lifespan,
    )

    # Configure CORS for local and cloud deployments
    cors_env = os.getenv("CORS_ORIGINS", "*")
    if cors_env == "*":
        allow_origins = ["*"]
    else:
        allow_origins = [o.strip() for o in cors_env.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register Route Handlers
    app.include_router(health.router)
    app.include_router(dashboard.router)
    app.include_router(analytics.router)
    app.include_router(pipeline.router)
    app.include_router(quality.router)
    app.include_router(database.router)

    return app


app = create_app()
