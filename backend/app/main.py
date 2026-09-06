import time
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.routers import health, sessions, artifacts, config

# Setup structured logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("lenny_backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Automatic DB schema creation and transcript ingestion on startup."""
    logger.info("Initializing database schema & pgvector extensions...")
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            await conn.run_sync(Base.metadata.create_all)

            # create_all() never ALTERs an existing table, so add the artifact->message
            # link explicitly. Idempotent: safe to run on every boot.
            await conn.execute(text("""
                ALTER TABLE artifacts
                ADD COLUMN IF NOT EXISTS message_id UUID
                REFERENCES messages(id) ON DELETE CASCADE;
            """))

            # Backfill artifacts stored before the column existed: attach each to the
            # nearest assistant message in its session (the agent flushes the artifact
            # immediately before committing that message).
            await conn.execute(text("""
                UPDATE artifacts a
                SET message_id = (
                    SELECT m.id FROM messages m
                    WHERE m.session_id = a.session_id
                      AND m.role = 'assistant'
                    ORDER BY ABS(EXTRACT(EPOCH FROM (m.created_at - a.created_at)))
                    LIMIT 1
                )
                WHERE a.message_id IS NULL;
            """))
            
            await conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes WHERE indexname = 'idx_chunks_embedding'
                    ) THEN
                        CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                    END IF;
                END $$;
            """))

        async with AsyncSessionLocal() as session:
            res = await session.execute(text("SELECT COUNT(*) FROM sources;"))
            count = res.scalar()
            if count == 0:
                logger.info("Corpus empty. Executing auto-ingestion of transcript seed data...")
                try:
                    from scripts.ingest import ingest_transcripts
                    ingest_transcripts()
                except Exception as ingest_err:
                    logger.error(f"Auto-ingestion error: {ingest_err}")
    except Exception as db_err:
        logger.error(f"Database initialization warning: {db_err}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structured JSON Logging Middleware
@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = None
    error_code = None

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        status_code = 500
        error_code = "INTERNAL_SERVER_ERROR"
        raise exc
    finally:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        log_data = {
            "path": request.url.path,
            "method": request.method,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "provider": settings.LLM_PROVIDER,
            "error_code": error_code
        }
        logger.info(json.dumps(log_data))

    return response

# Standard Error Envelope Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    
    code = "VALIDATION_ERROR" if exc.status_code == 400 else "HTTP_ERROR"
    if exc.status_code == 404:
        code = "NOT_FOUND"
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": str(exc.detail),
                "detail": None
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred.",
                "detail": str(exc)
            }
        }
    )

# Include Routers
app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(artifacts.router)
app.include_router(config.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True)

