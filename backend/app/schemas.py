from uuid import UUID
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

# --- Error Envelope ---
class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: Optional[Any] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

# --- Session Schemas ---
class SessionCreateRequest(BaseModel):
    client_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SessionResponse(BaseModel):
    session_id: UUID
    created_at: datetime

class SessionItemResponse(BaseModel):
    id: UUID
    created_at: datetime
    title: str
    message_count: int = 0

# --- Citation Schema ---
class Citation(BaseModel):
    source_id: UUID
    title: str
    episode_url: Optional[str] = ""
    position: int
    score: float
    snippet: str

# --- Artifact Schema ---
class ArtifactResponse(BaseModel):
    id: UUID
    session_id: UUID
    message_id: Optional[UUID] = None
    type: str  # 'markdown' | 'html'
    content: str
    sanitized: bool
    created_at: datetime

# --- Message Schemas ---
class MessageCreateRequest(BaseModel):
    content: str
    provider_override: Optional[str] = None

class MessageEditRequest(BaseModel):
    content: str
    provider_override: Optional[str] = None

class MessageRegenerateRequest(BaseModel):
    """Regeneration replays an existing prompt, so it carries no content."""
    provider_override: Optional[str] = None

class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    citations: List[Citation] = Field(default_factory=list)
    artifact: Optional[ArtifactResponse] = None
    model_provider: str
    created_at: datetime

class MessageListResponse(BaseModel):
    session_id: UUID
    messages: List[MessageResponse]

# --- Config & Health Schemas ---
class HealthResponse(BaseModel):
    status: str
    database: str
    llm_provider: str
    provider_available: bool

class ProviderInfo(BaseModel):
    """One selectable model provider and whether it can actually serve a turn."""
    id: str
    label: str
    model: str
    kind: str            # 'local' | 'cloud'
    configured: bool     # local: reachable now; cloud: API key present
    detail: Optional[str] = None

class ConfigResponse(BaseModel):
    active_provider: str
    providers: List[ProviderInfo] = Field(default_factory=list)
    model_name: str
    embedding_model: str
    last_indexed_at: Optional[str] = None
    sources_count: int = 0

