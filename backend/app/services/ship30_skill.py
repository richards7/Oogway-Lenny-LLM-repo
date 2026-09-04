from typing import List, Dict, Any

SHIP30_SYSTEM_PROMPT = """You are a master growth writer trained in the Ship 30/30 atomic writing methodology.
Your objective is to turn retrieved podcast transcript insights into a high-impact, skimmable growth essay.

Strict Formatting & Structure Rules:
1. **Headline & Hook**: Create a catchy, curiosity-driven headline followed by a 2-sentence hook that pulls busy executives in immediately.
2. **Single Core Takeaway**: State a clear, 1-sentence thesis takeaway in bold.
3. **Skimmable Formatting**:
   - Use clear subheadings (H2/H3).
   - Use bullet points and numbered lists.
   - Apply **selective bolding** on high-impact terms so a reader can skim the essay in 30 seconds.
4. **Length**: Target approximately 1,000 to 1,350 words (comprehensive yet punchy).
5. **Grounded Citations**: Every single factual claim or principle must cite the provided transcript context using explicit tag format: `[Source: Episode Title (chunk: X)]`.

Never invent claims outside the provided transcript chunks.
"""

def build_ship30_prompt(topic: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Build messages array for generating a Ship 30/30 atomic essay."""
    context_str = ""
    for idx, c in enumerate(chunks, 1):
        context_str += f"\n--- CHUNK {idx} | Source: {c['title']} | Chunk Position: {c['position']} ---\n{c['content']}\n"

    user_message = f"""Topic: {topic}

Retrieved Transcript Context:
{context_str}

Please generate a complete Ship 30/30 style atomic essay on this topic grounded strictly in the context above. Enforce the hook, single thesis takeaway, skimmable subheadings, bullet points, selective bolding, ~1,250 words, and explicit chunk citations."""

    return [
        {"role": "system", "content": SHIP30_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
