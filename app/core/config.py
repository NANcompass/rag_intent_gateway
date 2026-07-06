"""
Application configuration management.
"""
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # OpenAI API Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_base_url: Optional[str] = Field(
        None,
        description="OpenAI API base URL (for custom endpoints)"
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use"
    )
    openai_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM responses"
    )
    openai_max_tokens: int = Field(
        default=2000,
        ge=1,
        description="Maximum tokens in LLM response"
    )

    # Application Configuration
    app_name: str = Field(
        default="RAG Intent Gateway",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )

    # API Configuration
    api_prefix: str = Field(
        default="/api/v1",
        description="API route prefix"
    )

    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port"
    )


# Global settings instance
settings = Settings()
