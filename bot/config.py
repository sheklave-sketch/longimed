from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Telegram
    telegram_bot_token: str
    admin_chat_ids: List[int] = []
    public_channel_id: int = 0
    discussion_group_id: int = 0
    miniapp_url: str = "https://longimed.vercel.app"

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenRouter (Gemini Flash — Amharic translation)
    openrouter_api_key: str = ""

    # Session config
    free_trial_duration_mins: int = 15
    single_session_duration_mins: int = 30
    doctor_response_timeout_mins: int = 10
    waitlist_accept_timeout_mins: int = 5

    # Platform
    platform_fee_percent: float = 20.0

    # Phase II payments (optional — blank until ready)
    chapa_secret_key: str = ""
    chapa_webhook_secret: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # App
    environment: str = "development"
    log_level: str = "INFO"

    @field_validator("admin_chat_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: object) -> List[int]:
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        if isinstance(v, list):
            return [int(x) for x in v]
        return []

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
