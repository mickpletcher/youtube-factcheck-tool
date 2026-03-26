"""Application settings loaded from environment variables / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Transcript fallback
    whisper_model: str = "base"

    # Claim extraction
    max_claims: int = 10

    # Research
    research_max_results: int = 5


settings = Settings()
