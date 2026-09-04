#!/usr/bin/env python3
"""
Ingestion script for Lenny's Podcast transcripts.
Reads transcripts from data/transcripts/, chunks text, generates embeddings,
and stores sources and vector chunks in PostgreSQL + pgvector.
"""
import os
import re
import glob
import uuid
import hashlib
from typing import List, Tuple, Dict, Any
from datetime import datetime, timezone
import psycopg
from psycopg.rows import dict_row

# Configuration from env or defaults
DATABASE_URL = os.environ.get(
    "SYNC_DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/lenny_growth"
)
TRANSCRIPTS_DIR = os.environ.get(
    "TRANSCRIPTS_DIR", 
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "transcripts")
)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Lazy-loaded embedder
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        print(f"Loading embedding model '{EMBEDDING_MODEL_NAME}' on CPU...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")
    return _model


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate 384-dimensional embeddings for a list of text strings."""
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()

def chunk_text(text: str, chunk_size_words: int = 400, overlap_words: int = 50) -> List[str]:
    """Split text into overlapping word chunks."""
    words = text.split()
    if not words:
        return []
    
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size_words]
        chunk_str = " ".join(chunk_words)
        if chunk_str.strip():
            chunks.append(chunk_str)
        i += (chunk_size_words - overlap_words)
        if i >= len(words):
            break
    return chunks

def parse_transcript_file(file_path: str) -> Dict[str, Any]:
    """Extract metadata and content from transcript file."""
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    content_hash = hashlib.md5(raw_text.encode("utf-8")).hexdigest()
    
    title = os.path.basename(file_path).replace(".txt", "").replace("_", " ").title()
    episode_url = ""
    
    lines = raw_text.splitlines()
    body_lines = []
    for line in lines:
        if line.startswith("# Episode Title:"):
            title = line.replace("# Episode Title:", "").strip()
        elif line.startswith("# URL:"):
            episode_url = line.replace("# URL:", "").strip()
        elif line.startswith("#"):
            continue
        else:
            body_lines.append(line)
            
    body_text = "\n".join(body_lines).strip()
    return {
        "title": title,
        "episode_url": episode_url,
        "content_hash": content_hash,
        "body_text": body_text,
        "file_path": file_path
    }

def init_db(conn):
    """Ensure vector extension and schema exist."""
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                client_metadata JSONB DEFAULT '{}'::jsonb
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
                content TEXT NOT NULL,
                citations JSONB DEFAULT '[]'::jsonb,
                model_provider VARCHAR(50) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                title VARCHAR(255) NOT NULL,
                episode_url VARCHAR(500),
                ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                content_hash VARCHAR(64) UNIQUE
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                position INT NOT NULL,
                embedding VECTOR(384)
            );
        """)
        
        # Create ivfflat index if not existing
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes WHERE indexname = 'idx_chunks_embedding'
                ) THEN
                    CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                END IF;
            END $$;
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                type VARCHAR(20) NOT NULL CHECK (type IN ('markdown', 'html')),
                content TEXT NOT NULL,
                sanitized BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        conn.commit()

def ingest_transcripts():
    """Main ingestion execution function."""
    print(f"Connecting to database: {DATABASE_URL}")
    try:
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Note: Ensure PostgreSQL is running (e.g. via Docker Compose or local service).")
        return False

    print("Initializing database tables and vector extensions...")
    init_db(conn)

    pattern = os.path.join(TRANSCRIPTS_DIR, "*.txt")
    files = glob.glob(pattern)
    print(f"Found {len(files)} transcript files in '{TRANSCRIPTS_DIR}'.")

    for file_path in files:
        parsed = parse_transcript_file(file_path)
        content_hash = parsed["content_hash"]
        
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM sources WHERE content_hash = %s", (content_hash,))
            existing = cur.fetchone()
            if existing:
                print(f"[NO-OP] Source '{parsed['title']}' is unchanged (hash match). Skipping.")
                continue

            # Insert source
            # Tables may have been created by SQLAlchemy's create_all(), which sets
            # the UUID default Python-side only - the columns carry no server default.
            # Supply ids explicitly so ingestion works under either creation path.
            cur.execute(
                """
                INSERT INTO sources (id, title, episode_url, content_hash, ingested_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (uuid.uuid4(), parsed["title"], parsed["episode_url"], content_hash,
                 datetime.now(timezone.utc))
            )
            source_id = cur.fetchone()["id"]
            
            # Chunk and embed
            chunks = chunk_text(parsed["body_text"], chunk_size_words=350, overlap_words=40)
            if not chunks:
                continue

            print(f"Ingesting '{parsed['title']}': {len(chunks)} chunks...")
            embeddings = generate_embeddings(chunks)

            for pos, (chunk_content, emb) in enumerate(zip(chunks, embeddings)):
                emb_str = f"[{','.join(str(x) for x in emb)}]"
                cur.execute(
                    """
                    INSERT INTO chunks (id, source_id, content, position, embedding)
                    VALUES (%s, %s, %s, %s, %s::vector);
                    """,
                    (uuid.uuid4(), source_id, chunk_content, pos, emb_str)
                )
            conn.commit()
            print(f"[SUCCESS] Ingested '{parsed['title']}' ({len(chunks)} chunks).")

    conn.close()
    print("Ingestion pipeline completed successfully.")
    return True

if __name__ == "__main__":
    ingest_transcripts()
