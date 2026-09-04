from typing import List
from app.config import settings

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
    return _embedding_model


def get_embedding(text: str) -> List[float]:
    """Generate 384-dimensional embedding for input text."""
    model = get_embedding_model()
    vec = model.encode(text, convert_to_numpy=True)
    return vec.tolist()
