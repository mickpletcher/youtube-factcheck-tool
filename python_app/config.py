"""Application settings loaded from environment variables / .env file."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: int = 60

    # Transcript fallback
    whisper_model: str = "base"
    yt_dlp_timeout_seconds: int = 60

    # Claim extraction
    max_claims: int = 10

    # Research
    research_max_results: int = 5
    duckduckgo_timeout_seconds: int = 20

    @field_validator("max_claims")
    @classmethod
    def clamp_max_claims(cls, value: int) -> int:
        if value < 1:
            return 1
        if value > 25:
            return 25
        return value


settings = Settings()
