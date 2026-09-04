from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.config import settings
from app.services.llm_provider import get_provider
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Checks database connectivity and active model provider availability."""
    db_status = "disconnected"
    try:
        res = await db.execute(text("SELECT 1;"))
        if res.scalar() == 1:
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    provider = get_provider(settings.LLM_PROVIDER)
    provider_available = await provider.is_available()

    if db_status != "connected":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "PostgreSQL database connection failed.",
                    "detail": {"db_status": db_status}
                }
            }
        )

    return HealthResponse(
        status="ok",
        database=db_status,
        llm_provider=settings.LLM_PROVIDER,
        provider_available=provider_available
    )
