from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embeddings import get_embedding
from app.config import settings

async def search_similar_chunks(
    db: AsyncSession,
    query_text: str,
    top_k: int = None,
    threshold: float = None
) -> List[Dict[str, Any]]:
    """
    Search vector chunks in pgvector matching the query embedding.
    Returns list of dicts with source_id, title, episode_url, position, score, content.
    """
    if top_k is None:
        top_k = settings.RETRIEVAL_TOP_K
    if threshold is None:
        threshold = settings.RETRIEVAL_SIMILARITY_THRESHOLD

    query_vec = get_embedding(query_text)
    vec_str = f"[{','.join(str(x) for x in query_vec)}]"

    # Cosine distance: similarity = 1 - (embedding <=> query_vec)
    # Use CAST() instead of ::vector to avoid conflict with SQLAlchemy's :param syntax
    sql = text("""
        SELECT 
            c.id AS chunk_id,
            c.source_id,
            s.title AS source_title,
            s.episode_url,
            c.content,
            c.position,
            1 - (c.embedding <=> CAST(:vec AS vector)) AS similarity_score
        FROM chunks c
        JOIN sources s ON c.source_id = s.id
        WHERE 1 - (c.embedding <=> CAST(:vec AS vector)) >= :threshold
        ORDER BY similarity_score DESC
        LIMIT :top_k;
    """)

    result = await db.execute(
        sql, 
        {"vec": vec_str, "threshold": threshold, "top_k": top_k}
    )
    rows = result.mappings().all()

    # Filter out repetitive sign-off/outro boilerplate chunks if body chunks exist
    retrieved = []
    for r in rows:
        content = r["content"]
        # Skip pure sign-off outro chunks unless no other chunks match
        if "subscribe to the show on Apple Podcasts" in content or "See you in the next episode" in content:
            if len(rows) > 1 and len(retrieved) >= 1:
                continue
                
        retrieved.append({
            "chunk_id": str(r["chunk_id"]),
            "source_id": str(r["source_id"]),
            "title": r["source_title"],
            "episode_url": r["episode_url"] or "",
            "content": content,
            "position": r["position"],
            "score": round(float(r["similarity_score"]), 4)
        })
    return retrieved

