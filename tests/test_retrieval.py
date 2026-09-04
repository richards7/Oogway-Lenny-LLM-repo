import sys
import os
import pytest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.ingest import chunk_text, parse_transcript_file
from app.services.embeddings import get_embedding

@pytest.mark.unit
def test_chunk_text_ordinal_position():
    text = "Word " * 1000
    chunks = chunk_text(text, chunk_size_words=300, overlap_words=50)
    assert len(chunks) >= 3
    assert all(isinstance(c, str) and len(c) > 0 for c in chunks)

@pytest.mark.unit
def test_parse_transcript_metadata():
    sample_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "transcripts", "ep01_elena_verna_plg.txt")
    if os.path.exists(sample_file):
        parsed = parse_transcript_file(sample_file)
        assert "Elena Verna" in parsed["title"]
        assert len(parsed["content_hash"]) == 32
        assert len(parsed["body_text"]) > 100

@pytest.mark.unit
def test_retrieval_quality_semantic_search():
    """Verify semantic similarity matches known query to specific transcript fact."""
    known_fact_chunk = (
        "In this episode, Elena Verna states that the single most important activation metric "
        "for a two-sided marketplace is when a new seller receives at least 3 buyer bids within 24 hours."
    )
    unrelated_chunk = (
        "PostgreSQL 16 introduced improvements to logical replication and memory allocation for query planners."
    )

    fact_vec = np.array(get_embedding(known_fact_chunk))
    unrelated_vec = np.array(get_embedding(unrelated_chunk))
    
    # Query closely matching the known fact
    query = "What is the key activation metric for a marketplace according to Elena Verna?"
    query_vec = np.array(get_embedding(query))

    # Cosine similarity helper
    def cosine_similarity(v1, v2):
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

    score_fact = cosine_similarity(query_vec, fact_vec)
    score_unrelated = cosine_similarity(query_vec, unrelated_vec)

    # Fact chunk must score significantly higher than unrelated chunk
    assert score_fact > 0.50, f"Expected similarity > 0.50, got {score_fact}"
    assert score_fact > score_unrelated + 0.25, "Target chunk similarity must dominate unrelated content"

@pytest.mark.unit
def test_retrieval_quality_negative_case():
    """Verify out-of-corpus query yields similarity below the grounding threshold."""
    corpus_chunk = "Elena Verna recommends placing paywalls in front of scale, governance, and advanced collaboration features."
    chunk_vec = np.array(get_embedding(corpus_chunk))

    out_of_corpus_query = "What is the thermodynamic formula for enthalpy change in nuclear fusion?"
    query_vec = np.array(get_embedding(out_of_corpus_query))

    def cosine_similarity(v1, v2):
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

    score = cosine_similarity(query_vec, chunk_vec)
    
    # Out of corpus query score must be below threshold 0.30
    assert score < 0.30, f"Expected out-of-corpus score < 0.30, got {score}"
