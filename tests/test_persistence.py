import sys
import os
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from app.models import SessionModel, MessageModel, SourceModel, ChunkModel, ArtifactModel, Base
from app.config import settings

TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", settings.DATABASE_URL)

@pytest.mark.unit
def test_model_instantiation():
    sess_id = uuid4()
    sess = SessionModel(id=sess_id, client_metadata={"test": True})
    assert sess.id == sess_id
    assert sess.client_metadata == {"test": True}

    msg = MessageModel(
        session_id=sess_id,
        role="user",
        content="Hello Lenny",
        citations=[],
        model_provider="ollama"
    )
    assert msg.role == "user"
    assert msg.content == "Hello Lenny"

    art = ArtifactModel(
        session_id=sess_id,
        type="html",
        content="<div>Test</div>",
        sanitized=True
    )
    assert art.type == "html"
    assert art.sanitized is True


async def get_test_db_session():
    """Helper to acquire DB session or skip if DB unavailable."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1;"))
    except Exception:
        pytest.skip(f"PostgreSQL test database not reachable at {TEST_DB_URL}")
    
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session, engine


@pytest.mark.db
@pytest.mark.asyncio
async def test_db_session_and_message_roundtrip():
    async_session, engine = await get_test_db_session()
    async with async_session() as session:
        sess = SessionModel(client_metadata={"environment": "test"})
        session.add(sess)
        await session.commit()
        
        msg = MessageModel(
            session_id=sess.id,
            role="user",
            content="What is PLG?",
            citations=[{"source": "ep01"}],
            model_provider="ollama"
        )
        session.add(msg)
        await session.commit()

        res_msg = await session.execute(select(MessageModel).where(MessageModel.id == msg.id))
        fetched_msg = res_msg.scalar_one()
        
        assert fetched_msg.session_id == sess.id
        assert fetched_msg.content == "What is PLG?"
        assert fetched_msg.role == "user"
        assert fetched_msg.model_provider == "ollama"
        assert fetched_msg.citations == [{"source": "ep01"}]
    await engine.dispose()


@pytest.mark.db
@pytest.mark.asyncio
async def test_db_source_and_chunk_embedding_roundtrip():
    async_session, engine = await get_test_db_session()
    async with async_session() as session:
        source = SourceModel(
            title="Test Episode",
            episode_url="https://example.com/ep1",
            content_hash=f"hash-{uuid4()}"
        )
        session.add(source)
        await session.commit()

        dummy_embedding = [0.01] * 384
        chunk = ChunkModel(
            source_id=source.id,
            content="Product led growth drives customer acquisition.",
            position=0,
            embedding=dummy_embedding
        )
        session.add(chunk)
        await session.commit()

        res_chunk = await session.execute(select(ChunkModel).where(ChunkModel.id == chunk.id))
        fetched_chunk = res_chunk.scalar_one()

        assert fetched_chunk.source_id == source.id
        assert fetched_chunk.position == 0
        assert "Product led growth" in fetched_chunk.content
        assert len(fetched_chunk.embedding) == 384

        # Tests run against the configured DATABASE_URL, which in local dev is the
        # same database the real corpus lives in. Clean up so test fixtures never
        # show up in the ingested episode count. (Chunks cascade with the source.)
        await session.delete(source)
        await session.commit()
    await engine.dispose()


@pytest.mark.db
@pytest.mark.asyncio
async def test_db_on_delete_cascade():
    async_session, engine = await get_test_db_session()
    async with async_session() as session:
        sess = SessionModel(client_metadata={"cascade": True})
        session.add(sess)
        await session.commit()

        msg = MessageModel(session_id=sess.id, role="user", content="Cascade test", model_provider="ollama")
        art = ArtifactModel(session_id=sess.id, type="markdown", content="# Cascade", sanitized=True)
        session.add_all([msg, art])
        await session.commit()

        await session.delete(sess)
        await session.commit()

        res_msg = await session.execute(select(MessageModel).where(MessageModel.session_id == sess.id))
        res_art = await session.execute(select(ArtifactModel).where(ArtifactModel.session_id == sess.id))
        
        assert len(res_msg.scalars().all()) == 0
        assert len(res_art.scalars().all()) == 0
    await engine.dispose()
