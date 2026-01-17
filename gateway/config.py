from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LLM Service Configuration
    llm_endpoint: str = "http://127.0.0.1:8000/v1/chat/completions"
    llm_model: str = "/workspace/kl/kl_league_qlora_out/merged"
    llm_temperature: float = 0.8
    llm_max_tokens: int = 128
    llm_frequency_penalty: float = 0.5
    llm_timeout: float = 30.0  # seconds
    llm_username: str = "user"
    llm_password: str = "jjibooteam"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS Configuration
    cors_origins: list[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
