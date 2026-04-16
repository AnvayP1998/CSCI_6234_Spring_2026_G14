from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "DataInsight AI"
    ENV: str = "dev"

    DATABASE_URL: str
    QDRANT_URL: str
    QDRANT_COLLECTION: str = "datainsight_assets"

    STORAGE_DIR: str = "./storage"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120

    QDRANT_API_KEY: str = ""          # required for Qdrant Cloud, empty for local

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_MOCK: bool = False

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"

    class Config:
        env_file = ".env"

settings = Settings()