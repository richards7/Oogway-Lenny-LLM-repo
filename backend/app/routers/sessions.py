import uuid
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import SessionModel, MessageModel, ArtifactModel
from app.schemas import (
    SessionCreateRequest, SessionResponse, SessionItemResponse,
    MessageCreateRequest, MessageEditRequest, MessageRegenerateRequest,
    MessageResponse, Citation, ArtifactResponse
)
from app.services.agent import process_agent_turn

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreateRequest = SessionCreateRequest(),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session."""
    session_obj = SessionModel(client_metadata=body.client_metadata or {})
    db.add(session_obj)
    await db.commit()
    await db.refresh(session_obj)
    return SessionResponse(session_id=session_obj.id, created_at=session_obj.created_at)

@router.get("", response_model=List[SessionItemResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """List all sessions ordered by creation time with auto-generated title and message count."""
    stmt = select(SessionModel).order_by(SessionModel.created_at.desc())
    res = await db.execute(stmt)
    sessions = res.scalars().all()

    output = []
    for s in sessions:
        # Get first user prompt for auto-generated title
        stmt_first = (
            select(MessageModel)
            .where(MessageModel.session_id == s.id, MessageModel.role == "user")
            .order_by(MessageModel.created_at.asc())
            .limit(1)
        )
        res_first = await db.execute(stmt_first)
        first_msg = res_first.scalar_one_or_none()
        
        # Get total message count
        stmt_cnt = select(MessageModel).where(MessageModel.session_id == s.id)
        res_cnt = await db.execute(stmt_cnt)
        cnt = len(res_cnt.scalars().all())

        title = "New Chat Session"
        if first_msg and first_msg.content:
            raw = first_msg.content.strip()
            title = raw[:35] + "..." if len(raw) > 35 else raw

        output.append(SessionItemResponse(
            id=s.id,
            created_at=s.created_at,
            title=title,
            message_count=cnt
        ))
    return output

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a chat session."""
    stmt = select(SessionModel).where(SessionModel.id == session_id)
    res = await db.execute(stmt)
    sess = res.scalar_one_or_none()
    if sess:
        await db.delete(sess)
        await db.commit()
    return None


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Fetch message history for a session."""
    stmt = select(SessionModel).where(SessionModel.id == session_id)
    res = await db.execute(stmt)
    sess = res.scalar_one_or_none()
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "SESSION_NOT_FOUND", "message": f"Session {session_id} not found."}}
        )

    stmt_msgs = select(MessageModel).where(MessageModel.session_id == session_id).order_by(MessageModel.created_at.asc())
    res_msgs = await db.execute(stmt_msgs)
    msgs = res_msgs.scalars().all()

    # Load this session's artifacts once and index them by owning message, so every
    # message that produced an artifact keeps its "View Artifact" affordance on reload.
    stmt_arts = select(ArtifactModel).where(ArtifactModel.session_id == session_id)
    res_arts = await db.execute(stmt_arts)
    artifacts_by_message = {
        a.message_id: a for a in res_arts.scalars().all() if a.message_id is not None
    }

    output = []
    for m in msgs:
        art = artifacts_by_message.get(m.id)
        output.append(MessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            citations=m.citations or [],
            artifact=ArtifactResponse(
                id=art.id,
                session_id=art.session_id,
                message_id=art.message_id,
                type=art.type,
                content=art.content,
                sanitized=art.sanitized,
                created_at=art.created_at
            ) if art else None,
            model_provider=m.model_provider,
            created_at=m.created_at
        ))
    return output

@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: UUID,
    body: MessageCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send user message, execute agent turn, return assistant response."""
    stmt = select(SessionModel).where(SessionModel.id == session_id)
    res = await db.execute(stmt)
    sess = res.scalar_one_or_none()
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "SESSION_NOT_FOUND", "message": f"Session {session_id} not found."}}
        )

    # Store User Message
    user_msg = MessageModel(
        session_id=session_id,
        role="user",
        content=body.content,
        citations=[],
        model_provider=body.provider_override or "user"
    )
    db.add(user_msg)
    await db.flush()

    # Run Agent Process
    assistant_msg, artifact = await process_agent_turn(
        db=db,
        session_id=str(session_id),
        user_content=body.content,
        provider_name=body.provider_override
    )

    artifact_resp = None
    if artifact:
        artifact_resp = ArtifactResponse(
            id=artifact.id,
            session_id=artifact.session_id,
            message_id=artifact.message_id,
            type=artifact.type,
            content=artifact.content,
            sanitized=artifact.sanitized,
            created_at=artifact.created_at
        )

    return MessageResponse(
        id=assistant_msg.id,
        session_id=assistant_msg.session_id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        citations=assistant_msg.citations or [],
        artifact=artifact_resp,
        model_provider=assistant_msg.model_provider,
        created_at=assistant_msg.created_at
    )


async def _require_session(session_id: UUID, db: AsyncSession) -> SessionModel:
    """Load a session or raise the standard structured 404."""
    res = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    sess = res.scalar_one_or_none()
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "SESSION_NOT_FOUND", "message": f"Session {session_id} not found."}}
        )
    return sess


async def _truncate_from(session_id: UUID, pivot: MessageModel, db: AsyncSession, inclusive: bool) -> None:
    """
    Drop every message at/after `pivot` so the turn can be replayed.

    Editing or regenerating rewinds the conversation rather than branching it:
    anything downstream was derived from the old text and would be orphaned.
    Artifacts follow via the message_id FK's ON DELETE CASCADE. The id guard
    keeps ties on created_at from deleting the pivot itself when exclusive.
    """
    stmt = delete(MessageModel).where(
        MessageModel.session_id == session_id,
        MessageModel.created_at >= pivot.created_at
    )
    if not inclusive:
        stmt = stmt.where(MessageModel.id != pivot.id)
    await db.execute(stmt)
    await db.commit()


def _to_message_response(msg: MessageModel, artifact) -> MessageResponse:
    return MessageResponse(
        id=msg.id,
        session_id=msg.session_id,
        role=msg.role,
        content=msg.content,
        citations=msg.citations or [],
        artifact=ArtifactResponse(
            id=artifact.id,
            session_id=artifact.session_id,
            message_id=artifact.message_id,
            type=artifact.type,
            content=artifact.content,
            sanitized=artifact.sanitized,
            created_at=artifact.created_at
        ) if artifact else None,
        model_provider=msg.model_provider,
        created_at=msg.created_at
    )


@router.post("/{session_id}/messages/{message_id}/edit", response_model=MessageResponse)
async def edit_message(
    session_id: UUID,
    message_id: UUID,
    body: MessageEditRequest,
    db: AsyncSession = Depends(get_db)
):
    """Rewrite a user message, discard everything after it, and replay the turn."""
    await _require_session(session_id, db)

    res = await db.execute(
        select(MessageModel).where(
            MessageModel.id == message_id,
            MessageModel.session_id == session_id
        )
    )
    target = res.scalar_one_or_none()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "MESSAGE_NOT_FOUND", "message": f"Message {message_id} not found in session."}}
        )
    if target.role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "MESSAGE_NOT_EDITABLE", "message": "Only user messages can be edited."}}
        )
    if not body.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "EMPTY_CONTENT", "message": "Edited message content cannot be empty."}}
        )

    target.content = body.content.strip()
    await db.commit()

    await _truncate_from(session_id, target, db, inclusive=False)

    assistant_msg, artifact = await process_agent_turn(
        db=db,
        session_id=str(session_id),
        user_content=target.content,
        provider_name=body.provider_override
    )
    return _to_message_response(assistant_msg, artifact)


@router.post("/{session_id}/messages/{message_id}/regenerate", response_model=MessageResponse)
async def regenerate_message(
    session_id: UUID,
    message_id: UUID,
    body: MessageRegenerateRequest | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Replay the turn that produced an assistant message, discarding the old answer."""
    await _require_session(session_id, db)

    res = await db.execute(
        select(MessageModel).where(
            MessageModel.id == message_id,
            MessageModel.session_id == session_id
        )
    )
    target = res.scalar_one_or_none()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "MESSAGE_NOT_FOUND", "message": f"Message {message_id} not found in session."}}
        )
    if target.role != "assistant":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "MESSAGE_NOT_REGENERABLE", "message": "Only assistant messages can be regenerated."}}
        )

    res_prev = await db.execute(
        select(MessageModel)
        .where(
            MessageModel.session_id == session_id,
            MessageModel.role == "user",
            MessageModel.created_at < target.created_at
        )
        .order_by(MessageModel.created_at.desc())
        .limit(1)
    )
    prompt_msg = res_prev.scalar_one_or_none()
    if not prompt_msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "NO_SOURCE_PROMPT", "message": "No preceding user message to regenerate from."}}
        )

    await _truncate_from(session_id, target, db, inclusive=True)

    assistant_msg, artifact = await process_agent_turn(
        db=db,
        session_id=str(session_id),
        user_content=prompt_msg.content,
        provider_name=(body.provider_override if body else None)
    )
    return _to_message_response(assistant_msg, artifact)
