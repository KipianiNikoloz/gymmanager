from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "FastAPI Gym"
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    jwt_secret: str = Field(default="changeme", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    database_url: str = Field(default="sqlite+aiosqlite:///./app.db", alias="DATABASE_URL")
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    mailer_backend: str = Field(default="console", alias="MAILER_BACKEND")
    mailer_rate_limit_seconds: float = Field(default=0.5, alias="MAILER_RATE_LIMIT_SECONDS")
    mailer_max_retries: int = Field(default=3, alias="MAILER_MAX_RETRIES")
    mailer_retry_delay_seconds: float = Field(default=0.5, alias="MAILER_RETRY_DELAY_SECONDS")

    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: Optional[int] = Field(default=None, alias="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, alias="SMTP_USE_SSL")
    smtp_from_email: Optional[str] = Field(default=None, alias="SMTP_FROM_EMAIL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: List[str] | str) -> List[str]:
        if isinstance(value, str):
            if not value:
                return []
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
