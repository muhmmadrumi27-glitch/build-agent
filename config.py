"""Configuration management for BuildAgent."""
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="BuildAgent", description="Application name")
    app_env: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Log level")

    # API
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="Number of workers")
    api_reload: bool = Field(default=False, description="Auto-reload")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/buildagent",
        description="Database connection string",
    )
    database_pool_size: int = Field(default=20, description="Connection pool size")
    database_max_overflow: int = Field(default=10, description="Max overflow connections")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    redis_password: Optional[str] = Field(default=None, description="Redis password")

    # ChromaDB
    chroma_host: str = Field(default="localhost", description="ChromaDB host")
    chroma_port: int = Field(default=8001, description="ChromaDB port")
    chroma_collection: str = Field(default="buildagent_memory", description="ChromaDB collection")

    # LLM Providers
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model")

    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key")
    gemini_model: str = Field(default="gemini-1.5-pro", description="Gemini model")

    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022", description="Anthropic model"
    )

    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    openrouter_model: str = Field(
        default="anthropic/claude-3.5-sonnet", description="OpenRouter model"
    )

    # Default LLM
    default_llm_provider: str = Field(default="openai", description="Default LLM provider")
    default_llm_model: str = Field(default="gpt-4o", description="Default LLM model")

    # Security
    secret_key: str = Field(default="change-me-in-production", description="JWT secret key")
    access_token_expire_minutes: int = Field(default=30, description="Token expiry in minutes")
    encryption_key: str = Field(default="32-byte-key-for-encryption!!", description="Encryption key")

    # Agent Settings
    max_retries: int = Field(default=3, description="Max retries for failed actions")
    retry_delay: float = Field(default=2.0, description="Delay between retries in seconds")
    screenshot_interval: float = Field(default=1.0, description="Screenshot interval in seconds")
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")
    safe_mode: bool = Field(default=True, description="Safe mode enabled")
    require_approval: bool = Field(default=False, description="Require user approval")

    # Monitoring
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    grafana_port: int = Field(default=3000, description="Grafana port")

    # Paths
    screenshot_dir: str = Field(default="./screenshots", description="Screenshot directory")
    recording_dir: str = Field(default="./recordings", description="Recording directory")
    log_dir: str = Field(default="./logs", description="Log directory")

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure asyncpg driver is used."""
        if v and "postgresql://" in v and "asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://")
        return v

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def screenshot_path(self) -> Path:
        path = Path(self.screenshot_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def recording_path(self) -> Path:
        path = Path(self.recording_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_path(self) -> Path:
        path = Path(self.log_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def available_llm_providers(self) -> List[str]:
        providers = []
        if self.openai_api_key:
            providers.append("openai")
        if self.gemini_api_key:
            providers.append("gemini")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.openrouter_api_key:
            providers.append("openrouter")
        return providers


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
