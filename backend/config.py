from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://jobsearch:jobsearch@db:5432/jobsearch"
    redis_url: str = "redis://redis:6379/0"
    cache_ttl_seconds: int = 86400

    # Generator: qwen3.6 on Ollama :11434
    ollama_generator_host: str = "http://host.docker.internal:11434"
    ollama_generator_model: str = "qwen3.6:latest"

    # Judge fallback: gemma4 on Ollama :11435
    ollama_judge_host: str = "http://host.docker.internal:11435"
    ollama_judge_model: str = "gemma4:latest"

    # Judge primary: Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    class Config:
        env_file = ".env"


settings = Settings()
