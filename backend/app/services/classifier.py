import re

TOOL_RETRIEVE_AND_ANSWER = "retrieve_and_answer"
TOOL_WRITE_SHIP30_ESSAY = "write_ship30_essay"
TOOL_GENERATE_ARTIFACT = "generate_artifact"

def classify_intent(user_prompt: str) -> str:
    """
    Lightweight deterministic server-side classifier for tool selection.
    
    Returns:
    - 'write_ship30_essay': Requests for Ship 30/30 essays, atomic essays, or long structured posts.
    - 'generate_artifact': Requests for HTML/CSS visual components, tables, landing pages, or markdown documents.
    - 'retrieve_and_answer': Standard RAG Q&A grounded in transcript knowledge base.
    """
    p = user_prompt.lower().strip()

    # Rule 1: Ship 30/30 Essay request
    ship30_keywords = [
        "ship 30", "ship30", "atomic essay", "1250 word", "write an essay", 
        "growth essay", "write a post", "strategy essay"
    ]
    if any(kw in p for kw in ship30_keywords):
        return TOOL_WRITE_SHIP30_ESSAY

    # Rule 2: Artifact Generation (HTML/CSS visual cards, tables, dashboards, components)
    artifact_keywords = [
        "html", "css", "component", "visual artifact", "dashboard mockup", 
        "table component", "landing page", "ui card", "visual table", "render html"
    ]
    if any(kw in p for kw in artifact_keywords):
        return TOOL_GENERATE_ARTIFACT

    # Rule 3: Default standard RAG Q&A
    return TOOL_RETRIEVE_AND_ANSWER
