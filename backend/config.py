import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://jobsearch:jobsearch@db:5432/jobsearch"
    redis_url: str = "redis://redis:6379/0"
    cache_ttl_seconds: int = 86400

    # Base and fallback generator configuration
    ollama_base_host: str = "http://host.docker.internal:11434"
    ollama_fallback_host: str = "http://host.docker.internal:11435"

    base_model: str = "qwen3.6:latest"
    fallback_model: str = "gemma4:latest"

    # Judge configuration
    judge_provider: str = "gemini"
    judge_model: str = "gemini-2.0-flash"
    ollama_judge_host: str = "http://host.docker.internal:11435"

    # Gemini-specific config
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    class Config:
        env_file = ".env"


settings = Settings()

# Backward compatibility with older env names
settings.base_model = os.getenv("BASE_MODEL", os.getenv("OLLAMA_GENERATOR_MODEL", settings.base_model))
settings.fallback_model = os.getenv("FALLBACK_MODEL", os.getenv("OLLAMA_JUDGE_MODEL", settings.fallback_model))
settings.judge_model = os.getenv("JUDGE_MODEL", os.getenv("GEMINI_MODEL", settings.judge_model))
settings.ollama_base_host = os.getenv("OLLAMA_BASE_HOST", os.getenv("OLLAMA_GENERATOR_HOST", settings.ollama_base_host))
settings.ollama_fallback_host = os.getenv("OLLAMA_FALLBACK_HOST", os.getenv("OLLAMA_JUDGE_HOST", settings.ollama_fallback_host))
settings.ollama_judge_host = os.getenv("JUDGE_HOST", os.getenv("OLLAMA_JUDGE_HOST", settings.ollama_judge_host))
settings.judge_provider = os.getenv("JUDGE_PROVIDER", settings.judge_provider).lower()
