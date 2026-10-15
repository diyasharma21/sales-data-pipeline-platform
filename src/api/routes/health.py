"""Health check endpoint."""

from datetime import datetime
from fastapi import APIRouter
from sqlalchemy import text

from src.api.schemas import HealthResponse
from src.config import get_database_url
from src.load import get_db_engine

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Verify backend system and database connectivity."""
    engine = get_db_engine()
    db_connected = False
    dialect_name = engine.dialect.name

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_connected = True
    except Exception:
        db_connected = False
    finally:
        engine.dispose()

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.now(),
        database_connected=db_connected,
        database_dialect=dialect_name,
        version="2.0.0",
    )
