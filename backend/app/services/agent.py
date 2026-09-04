import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import MessageModel, ArtifactModel
from app.services.vector_store import search_similar_chunks
from app.services.classifier import classify_intent, TOOL_WRITE_SHIP30_ESSAY, TOOL_GENERATE_ARTIFACT, TOOL_RETRIEVE_AND_ANSWER
from app.services.llm_provider import get_provider
from app.services.ship30_skill import build_ship30_prompt
from app.services.sanitizer import sanitize_html

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """You are "The Lenny Growth Assistant", an expert AI partner for Product Managers and Growth Leaders.
Your primary role is to answer questions grounded STRICTLY in Lenny's Podcast transcripts.

Rules:
1. Base all factual statements on the provided transcript chunks.
2. For EVERY factual claim, cite your source using the exact format: `[Source: <Episode Title> (chunk: <Position>)]`.
3. If the provided context does NOT contain enough information to answer the question, state clearly: "The ingested podcast transcripts do not cover this question." Do NOT fabricate citations or facts.
4. Be concise, authoritative, and structured.
"""

def _model_context(chunks) -> str:
    """
    Build the context block handed to the model.

    Retrieval stays wide so the UI can cite every match, but a local CPU model
    slows down as the prompt grows, so only the top few chunks - each capped to
    a word budget - are actually sent for generation.
    """
    parts = []
    for c in chunks[:settings.LLM_CONTEXT_MAX_CHUNKS]:
        words = c["content"].split()
        body = " ".join(words[:settings.LLM_CONTEXT_CHUNK_WORDS])
        if len(words) > settings.LLM_CONTEXT_CHUNK_WORDS:
            body += " ..."
        parts.append(f"--- [Source: {c['title']} (chunk: {c['position']})] ---\n{body}")
    return "\n\n".join(parts)


async def process_agent_turn(
    db: AsyncSession,
    session_id: str,
    user_content: str,
    provider_name: Optional[str] = None
) -> Tuple[MessageModel, Optional[ArtifactModel]]:
    """
    Executes a complete agent turn safely without throwing unhandled HTTP 500 errors.
    """
    active_provider_name = provider_name or settings.LLM_PROVIDER
    try:
        # 1. Classify tool
        tool_name = classify_intent(user_content)
        logger.info(f"Session {session_id} | Prompt classified to tool: {tool_name}")

        # 2. Retrieve chunks
        retrieved_chunks = await search_similar_chunks(db, user_content, top_k=settings.RETRIEVAL_TOP_K)

        provider = get_provider(provider_name)

        # 3. Handle low retrieval / out-of-corpus queries
        if not retrieved_chunks:
            answer_content = (
                "I searched Lenny's Podcast transcripts, but could not find relevant content covering your question. "
                "Please try asking about Product-Led Growth, Product Sense, Founder Mode, Empowered Product Teams, the SPADE Framework, or Growth Loops."
            )
            msg = MessageModel(
                session_id=session_id,
                role="assistant",
                content=answer_content,
                citations=[],
                model_provider=active_provider_name
            )
            db.add(msg)
            await db.commit()
            await db.refresh(msg)
            return msg, None

        # Format citations metadata
        citations = []
        for c in retrieved_chunks:
            citations.append({
                "source_id": c["source_id"],
                "title": c["title"],
                "episode_url": c["episode_url"],
                "position": c["position"],
                "score": c["score"],
                "snippet": c["content"][:200] + "..."
            })

        artifact_model = None

        # Helper for safe provider completion with fallback
        async def safe_complete(msgs: List[Dict[str, str]]) -> str:
            try:
                return await provider.complete(msgs)
            except Exception as err:
                logger.warning(f"Provider {active_provider_name} failed: {err}. Using grounded fallback.")
                context_str = "\n\n".join([
                    f"**{c['title']} (chunk {c['position']})**:\n{c['content']}"
                    for c in retrieved_chunks
                ])
                return (
                    f"### Grounded Response (Lenny's Podcast Transcripts)\n\n"
                    f"{context_str}\n\n"
                    f"*(Note: Provider `{active_provider_name}` returned an error or is unconfigured: {err})*"
                )

        # 4. Tool Execution
        if tool_name == TOOL_WRITE_SHIP30_ESSAY:
            messages = build_ship30_prompt(user_content, retrieved_chunks)
            raw_response = await safe_complete(messages)
            
            # Save artifact
            artifact_model = ArtifactModel(
                session_id=session_id,
                type="markdown",
                content=raw_response,
                sanitized=True
            )
            db.add(artifact_model)
            await db.flush()

            response_content = (
                f"I have crafted a Ship 30/30 atomic essay for you based on Lenny's Podcast transcripts.\n\n"
                f"### Preview & Summary\n{raw_response[:400]}...\n\n"
                f"*The complete essay has been opened in the Artifact Viewer panel.*"
            )

        elif tool_name == TOOL_GENERATE_ARTIFACT:
            context_text = _model_context(retrieved_chunks)
            messages = [
                {"role": "system", "content": "You generate clean, responsive HTML/CSS visual card components or tables summarising growth frameworks from the provided transcript context. Output ONLY valid HTML markup inside ```html ... ``` code blocks."},
                {"role": "user", "content": f"Context:\n{context_text}\n\nTask: {user_content}"}
            ]
            raw_response = await safe_complete(messages)
            
            # Extract HTML content
            html_content = raw_response
            if "```html" in raw_response:
                html_content = raw_response.split("```html")[1].split("```")[0].strip()
            elif "```" in raw_response:
                html_content = raw_response.split("```")[1].split("```")[0].strip()

            # Sanitize HTML
            clean_html = sanitize_html(html_content)

            artifact_model = ArtifactModel(
                session_id=session_id,
                type="html",
                content=clean_html,
                sanitized=True
            )
            db.add(artifact_model)
            await db.flush()

            response_content = (
                f"I have generated a visual HTML component based on the transcript insights.\n\n"
                f"*The visual artifact is now rendered in the Artifact Viewer side panel.*"
            )

        else:
            # TOOL_RETRIEVE_AND_ANSWER
            context_str = _model_context(retrieved_chunks)
            
            messages = [
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": f"CONTEXT CHUNKS:\n{context_str}\n\nUSER QUESTION: {user_content}"}
            ]
            response_content = await safe_complete(messages)

        # Save Assistant Message
        assistant_msg = MessageModel(
            session_id=session_id,
            role="assistant",
            content=response_content,
            citations=citations,
            model_provider=active_provider_name
        )
        db.add(assistant_msg)

        # Link the artifact to the message that produced it, so history requests can
        # hand every message its own artifact instead of only the newest one.
        # MessageModel assigns its UUID in __init__, so the id exists pre-flush.
        if artifact_model is not None:
            artifact_model.message_id = assistant_msg.id

        await db.commit()
        await db.refresh(assistant_msg)

        return assistant_msg, artifact_model

    except Exception as exc:
        logger.error(f"Error executing agent turn for session {session_id}: {exc}", exc_info=True)
        fallback_msg = MessageModel(
            session_id=session_id,
            role="assistant",
            content=f"⚠️ **Processing Exception**: Unable to process prompt ({str(exc)}). Please ensure your database and `.env` settings are configured.",
            citations=[],
            model_provider=active_provider_name
        )
        try:
            db.add(fallback_msg)
            await db.commit()
            await db.refresh(fallback_msg)
        except Exception:
            pass
        return fallback_msg, None


