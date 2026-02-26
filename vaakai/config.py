"""VaakAI — Multilingual AI Voice Chatbot Configuration."""

from __future__ import annotations

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ────────────────────────────────
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], alias="CORS_ORIGINS")

    # ── Telephony ──────────────────────────────────
    twilio_account_sid: str = Field(default="", alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(default="", alias="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(default="", alias="TWILIO_PHONE_NUMBER")

    # ── STT ────────────────────────────────────────
    bhashini_api_key: str = Field(default="", alias="BHASHINI_API_KEY")
    bhashini_user_id: str = Field(default="", alias="BHASHINI_USER_ID")
    deepgram_api_key: str = Field(default="", alias="DEEPGRAM_API_KEY")

    # ── LLM ────────────────────────────────────────
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    llama_api_url: str = Field(default="http://localhost:11434", alias="LLAMA_API_URL")

    # ── TTS ────────────────────────────────────────
    elevenlabs_api_key: str = Field(default="", alias="ELEVENLABS_API_KEY")

    # ── Orchestration ──────────────────────────────
    livekit_url: str = Field(default="wss://localhost:7880", alias="LIVEKIT_URL")
    livekit_api_key: str = Field(default="", alias="LIVEKIT_API_KEY")
    livekit_api_secret: str = Field(default="", alias="LIVEKIT_API_SECRET")

    # ── Storage ────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    database_url: str = Field(
        default="postgresql+asyncpg://vaakai:vaakai_secure_pass@localhost:5432/vaakai",
        alias="DATABASE_URL",
    )

    # ── WhatsApp ───────────────────────────────────
    whatsapp_token: str = Field(default="", alias="WHATSAPP_TOKEN")
    whatsapp_phone_number_id: str = Field(default="", alias="WHATSAPP_PHONE_NUMBER_ID")

    # ── CRM ────────────────────────────────────────
    crm_provider: str = Field(default="salesforce", alias="CRM_PROVIDER")
    crm_api_url: str = Field(default="", alias="CRM_API_URL")
    crm_api_key: str = Field(default="", alias="CRM_API_KEY")

    # ── ERP ────────────────────────────────────────
    erp_provider: str = Field(default="odoo", alias="ERP_PROVIDER")
    erp_api_url: str = Field(default="", alias="ERP_API_URL")
    erp_api_key: str = Field(default="", alias="ERP_API_KEY")

    # ── Detection Thresholds ───────────────────────
    fraud_score_threshold: float = Field(default=0.75, alias="FRAUD_SCORE_THRESHOLD")
    urgency_score_threshold: int = Field(default=7, alias="URGENCY_SCORE_THRESHOLD")

    # ── AWS ────────────────────────────────────────
    aws_region: str = Field(default="ap-south-1", alias="AWS_REGION")
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()
