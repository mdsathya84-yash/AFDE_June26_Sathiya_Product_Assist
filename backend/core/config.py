from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # OpenAI (Primary)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""  # Optional custom endpoint (e.g. key gateway proxy)
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_FALLBACK_MODEL: str = "gpt-3.5-turbo"

    # Groq (Secondary)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FAST_MODEL: str = "llama-3.1-8b-instant"

    # Router
    LLM_PROVIDER: str = "openai"
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: float = 1.0

    # Vector store
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    COLLECTION_NAME: str = "product_strategy"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Chunking
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K_RESULTS: int = 8

    # App
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
