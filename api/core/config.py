"""
ARIA configuration — all settings read from .env via pydantic-settings.
"""

from __future__ import annotations

import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Telegram ──────────────────────────────────────────────────────────
    telegram_bot_token: str = ""
    telegram_user_id: int = 0
    telegram_webhook_secret: str = Field(default_factory=lambda: secrets.token_hex(16))

    # ── Groq ──────────────────────────────────────────────────────────────
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_whisper_model: str = "whisper-large-v3"

    # ── Gmail / Google ────────────────────────────────────────────────────
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""
    gmail_user_email: str = ""
    gmail_pubsub_topic: str = ""

    # ── WhatsApp (Baileys) ────────────────────────────────────────────────
    baileys_host: str = "baileys"
    baileys_port: int = 3001
    baileys_session: str = "aria"

    # ── Discord ───────────────────────────────────────────────────────────
    discord_bot_token: str = ""
    discord_user_id: int = 0

    # ── Slack ─────────────────────────────────────────────────────────────
    slack_webhook_url: str = ""
    slack_bot_token: str = ""
    slack_signing_secret: str = ""

    # ── Notion ────────────────────────────────────────────────────────────
    notion_token: str = ""
    notion_notes_db_id: str = ""
    notion_tasks_db_id: str = ""

    # ── GitHub ────────────────────────────────────────────────────────────
    github_token: str = ""
    github_username: str = ""
    github_repos: str = ""

    # ── Spotify ───────────────────────────────────────────────────────────
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8888/callback"

    # ── SMS Gateway ───────────────────────────────────────────────────────
    sms_gateway_url: str = ""
    sms_gateway_token: str = ""

    # ── Monitoring watchlists ─────────────────────────────────────────────
    stock_watchlist: str = ""
    crypto_watchlist: str = ""
    rss_feeds: str = ""
    keyword_alerts: str = ""

    # ── Database ──────────────────────────────────────────────────────────
    postgres_db: str = "aria"
    postgres_user: str = "aria"
    postgres_password: str = "changeme"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    redis_host: str = "redis"
    redis_port: int = 6379

    minio_root_user: str = "aria"
    minio_root_password: str = "changeme"
    minio_host: str = "minio"
    minio_port: int = 9000
    minio_bucket: str = "aria-storage"

    # ── Behaviour settings ────────────────────────────────────────────────
    briefing_time: str = "08:00"
    timezone: str = "Asia/Kolkata"
    importance_threshold: int = 6
    draft_mode: bool = False
    follow_up_days: int = 3
    language: str = "en"

    # ── Derived properties ────────────────────────────────────────────────
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def github_repo_list(self) -> list[str]:
        return [r.strip() for r in self.github_repos.split(",") if r.strip()]

    @property
    def stock_list(self) -> list[str]:
        return [s.strip() for s in self.stock_watchlist.split(",") if s.strip()]

    @property
    def crypto_list(self) -> list[str]:
        return [c.strip() for c in self.crypto_watchlist.split(",") if c.strip()]

    @property
    def rss_feed_list(self) -> list[str]:
        return [f.strip() for f in self.rss_feeds.split(",") if f.strip()]

    @property
    def keyword_list(self) -> list[str]:
        return [k.strip() for k in self.keyword_alerts.split(",") if k.strip()]

    @property
    def baileys_url(self) -> str:
        return f"http://{self.baileys_host}:{self.baileys_port}"


settings = Settings()
