from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.config import settings
from app.schemas import ConfigResponse, ProviderInfo
from app.services.llm_provider import get_provider

router = APIRouter(prefix="/config", tags=["Config"])

@router.get("", response_model=ConfigResponse)
async def get_system_config(db: AsyncSession = Depends(get_db)):
    """Returns active model provider info, corpus last indexed timestamp, and sources count."""
    provider = get_provider(settings.LLM_PROVIDER)
    model_name = getattr(provider, "model", settings.OLLAMA_MODEL)

    last_indexed_at = None
    sources_count = 0
    try:
        res = await db.execute(text("SELECT MAX(ingested_at) FROM sources;"))
        ts = res.scalar()
        if ts:
            last_indexed_at = ts.isoformat()
            
        res_cnt = await db.execute(text("SELECT COUNT(*) FROM sources;"))
        sources_count = res_cnt.scalar() or 0
    except Exception:
        pass

    # Report real readiness per provider: Ollama is probed live (it can be
    # installed but not running), cloud providers just need a key present.
    ollama_up = False
    try:
        from app.services.llm_provider import OllamaProvider
        ollama_up = await OllamaProvider().is_available()
    except Exception:
        ollama_up = False

    providers = [
        ProviderInfo(
            id="ollama", label="Ollama", model=settings.OLLAMA_MODEL, kind="local",
            configured=ollama_up,
            detail=None if ollama_up else "Not running - start Ollama to use local mode"
        ),
        ProviderInfo(
            id="anthropic", label="Anthropic", model=settings.ANTHROPIC_MODEL, kind="cloud",
            configured=bool(settings.ANTHROPIC_API_KEY),
            detail=None if settings.ANTHROPIC_API_KEY else "Set ANTHROPIC_API_KEY in .env"
        ),
        ProviderInfo(
            id="openai", label="OpenAI", model=settings.OPENAI_MODEL, kind="cloud",
            configured=bool(settings.OPENAI_API_KEY),
            detail=None if settings.OPENAI_API_KEY else "Set OPENAI_API_KEY in .env"
        ),
    ]

    return ConfigResponse(
        active_provider=settings.LLM_PROVIDER,
        providers=providers,
        model_name=model_name,
        embedding_model=settings.EMBEDDING_MODEL,
        last_indexed_at=last_indexed_at,
        sources_count=sources_count
    )

