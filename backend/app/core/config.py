import json
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Nexus Studio API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Security & Tokens
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        elif isinstance(v, list):
            return v
        return []

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./studio.db"

    # Storage Backend (local / supabase / s3)
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_DIR: str = "./uploads"

    # Payments (Razorpay)
    RAZORPAY_KEY_ID: str = "rzp_test_placeholder"
    RAZORPAY_KEY_SECRET: str = "rzp_secret_placeholder"
    RAZORPAY_WEBHOOK_SECRET: str = "rzp_webhook_placeholder"

    # AI Website Generation Engine
    AI_GENERATION_ENABLED: bool = False
    ARTIFACT_STORAGE_PATH: str = "builds"

    # AI Provider Keys
    GEMINI_API_KEY: Union[str, None] = None
    CEREBRAS_API_KEY: Union[str, None] = None
    GROQ_API_KEY: Union[str, None] = None
    OPENROUTER_API_KEY: Union[str, None] = None

    # Task Router Configuration (Provider and Model mappings)
    AI_ANALYSIS_PROVIDER: str = "gemini"
    AI_ANALYSIS_MODEL: str = "gemini-2.0-flash-lite"

    AI_PLANNING_PROVIDER: str = "gemini"
    AI_PLANNING_MODEL: str = "gemini-2.0-flash"

    AI_GENERATION_PROVIDER: str = "cerebras"
    AI_GENERATION_MODEL: str = "llama3.3-70b"

    AI_REVIEW_PROVIDER: str = "groq"
    AI_REVIEW_MODEL: str = "llama-3.3-70b-versatile"

    AI_FALLBACK_PROVIDER: str = "openrouter"
    AI_FALLBACK_MODEL: str = "deepseek/deepseek-chat:free"

    # Worker & Execution Settings
    AI_MAX_RETRIES: int = 2
    AI_REQUEST_TIMEOUT_SECONDS: int = 60
    AI_REPAIR_ENABLED: bool = True

    # Deployment Engine Settings
    DEPLOYMENT_ENABLED: bool = False
    DEPLOYMENT_PROVIDER: str = "simulated"  # "simulated", "vercel", "netlify"
    DEPLOYMENT_BASE_DOMAIN: Union[str, None] = "nexusstudio.app"
    VERCEL_TOKEN: Union[str, None] = None
    VERCEL_TEAM_ID: Union[str, None] = None
    NETLIFY_AUTH_TOKEN: Union[str, None] = None
    NETLIFY_SITE_ID: Union[str, None] = None

    # Admin Bootstrap Settings
    ADMIN_EMAIL: str = "chiragparmar5768@gmail.com"
    ADMIN_INITIAL_PASSWORD: Union[str, None] = None
    ADMIN_BOOTSTRAP_ENABLED: bool = True

    # Studio Contact Information & Notifications
    STUDIO_PHONE: str = "7877794272"
    STUDIO_WHATSAPP: str = "7877794272"
    CONTACT_NOTIFICATION_EMAIL: str = "chiragparmar5768@gmail.com"

    # Email & SMTP Settings
    SMTP_HOST: Union[str, None] = None
    SMTP_PORT: int = 587
    SMTP_USER: Union[str, None] = None
    SMTP_PASSWORD: Union[str, None] = None
    SMTP_FROM_EMAIL: Union[str, None] = None
    SMTP_USE_TLS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
