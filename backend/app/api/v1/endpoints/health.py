from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.schemas.common import APIResponse, HealthResponse

router = APIRouter()


@router.get("/health", response_model=APIResponse[HealthResponse], summary="System Health Check")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check API operational status and database connectivity."""
    db_connected = False
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_connected = True
    except Exception:
        db_connected = False

    data = HealthResponse(
        status="healthy" if db_connected else "degraded",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database_connected=db_connected,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    return APIResponse(
        success=True,
        message="System status check executed",
        data=data,
    )
