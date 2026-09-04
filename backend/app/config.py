from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "The Lenny Growth Assistant"
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lenny_growth"
    SYNC_DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/lenny_growth"
    
    # Active LLM Provider: ollama | anthropic | openai | openrouter | gemini | auto
    LLM_PROVIDER: str = "ollama"
    
    # Ollama Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_FALLBACK_MODEL: str = "llama3.2:1b"
    # A 3B model on CPU needs minutes, not seconds, for a RAG-sized prompt.
    OLLAMA_TIMEOUT: float = 180.0
    OLLAMA_NUM_PREDICT: int = 512
    
    # Cloud Models
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemini-2.0-flash-lite:free"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # Embeddings & RAG
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RETRIEVAL_TOP_K: int = 6
    RETRIEVAL_SIMILARITY_THRESHOLD: float = 0.30

    # Retrieval stays wide so citations stay rich; only the slice handed to the
    # model is trimmed, since local generation time scales with prompt length.
    LLM_CONTEXT_MAX_CHUNKS: int = 4
    LLM_CONTEXT_CHUNK_WORDS: int = 180

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()

