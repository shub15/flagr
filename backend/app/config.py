"""
Configuration management for Legal Advisor backend.
Loads environment variables and provides application settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM API Keys
    openai_api_key: str
    google_api_key: str  # For Gemini (Referee)
    groq_api_key: Optional[str] = None  # Groq (fast inference)
    mistral_api_key: Optional[str] = None  # Mistral AI
    
    # Vector Database (Pinecone)
    pinecone_api_key: str
    pinecone_environment: str
    pinecone_index_name: str = "indian-labour-law"
    
    # Database
    database_url: str = "sqlite:///./legal_advisor.db"
    
    # LLM Model Configuration
    openai_model: str = "gpt-4-turbo-preview"
    mistral_model: str = "mistral-large-latest"  # For council
    groq_model: str = "llama-3.1-70b-versatile"  # For council
    gemini_model: str = "gemini-1.5-flash"  # For Referee only
    
    # Council Settings
    council_consensus_threshold: float = 0.6
    llm_timeout_seconds: int = 30
    max_retries: int = 3
    
    # Rate Limiting (to avoid 429 errors)
    enable_openai: bool = True
    enable_mistral: bool = True  # Mistral AI for council
    enable_groq: bool = False  # Groq (fast inference) - disable by default
    max_concurrent_llm_calls: int = 3  # Limit concurrent calls
    retry_delay_seconds: int = 2  # Delay between retries
    exponential_backoff: bool = True  # Use exponential backoff on retries
    
    # Application
    debug: bool = False
    log_level: str = "INFO"
    
    # RAG Settings
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    rag_top_k: int = 3
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
