from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import ArtifactModel
from app.schemas import ArtifactResponse

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])

@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve stored artifact by ID."""
    stmt = select(ArtifactModel).where(ArtifactModel.id == artifact_id)
    res = await db.execute(stmt)
    artifact = res.scalar_one_or_none()

    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ARTIFACT_NOT_FOUND", "message": f"Artifact {artifact_id} not found."}}
        )

    return ArtifactResponse(
        id=artifact.id,
        session_id=artifact.session_id,
        message_id=artifact.message_id,
        type=artifact.type,
        content=artifact.content,
        sanitized=artifact.sanitized,
        created_at=artifact.created_at
    )
