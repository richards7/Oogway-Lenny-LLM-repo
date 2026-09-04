import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    client_metadata = Column(JSONB, nullable=True, default=dict)

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan")
    artifacts = relationship("ArtifactModel", back_populates="session", cascade="all, delete-orphan")

class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    citations = Column(JSONB, nullable=True, default=list)
    model_provider = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    session = relationship("SessionModel", back_populates="messages")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'tool')", name="check_role_values"),
    )

class SourceModel(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    episode_url = Column(String(500), nullable=True)
    ingested_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    content_hash = Column(String(64), unique=True, nullable=True)

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "ingested_at" not in kwargs or kwargs["ingested_at"] is None:
            kwargs["ingested_at"] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    chunks = relationship("ChunkModel", back_populates="source", cascade="all, delete-orphan")

class ChunkModel(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)
    embedding = Column(Vector(384), nullable=True)

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        super().__init__(**kwargs)

    source = relationship("SourceModel", back_populates="chunks")

class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    # Nullable: artifacts created before this column existed have no owning message.
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    sanitized = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = uuid.uuid4()
        if "created_at" not in kwargs or kwargs["created_at"] is None:
            kwargs["created_at"] = datetime.now(timezone.utc)
        super().__init__(**kwargs)

    session = relationship("SessionModel", back_populates="artifacts")

    __table_args__ = (
        CheckConstraint("type IN ('markdown', 'html')", name="check_artifact_type_values"),
    )
