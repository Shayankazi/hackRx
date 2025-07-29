import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_TITLE: str = "LLM Query-Retrieval System"
    API_VERSION: str = "1.0.0"
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./data/llm_query_db.sqlite"
    
    # LLM Configuration
    LLM_MODEL_NAME: str = "microsoft/DialoGPT-medium"  # Using smaller model for testing
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.1
    
    # Embedding Configuration
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Cross-encoder Configuration
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # FAISS Configuration
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    MAX_RETRIEVAL_RESULTS: int = 20
    TOP_K_RERANK: int = 5
    
    # Document Processing
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    MAX_FILE_SIZE_MB: int = 50
    
    # API Keys (if using external services)
    LLAMAPARSE_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
