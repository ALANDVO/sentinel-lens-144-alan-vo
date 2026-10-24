"""Application configuration using Pydantic Settings"""

from functools import lru_cache
from typing import Optional
from pydantic import Field
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
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    database_url: str = Field(default="sqlite:///./data/app.db", alias="DATABASE_URL")

    # LLM (optional)
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_base_url: Optional[str] = Field(default=None, alias="LLM_BASE_URL")

    # Keycloak
    keycloak_url: str = Field(default="http://localhost:8080", alias="KEYCLOAK_URL")
    keycloak_realm: str = Field(default="sentinel-lens", alias="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(default="sentinel-lens-backend", alias="KEYCLOAK_CLIENT_ID")
    keycloak_client_secret: Optional[str] = Field(default=None, alias="KEYCLOAK_CLIENT_SECRET")

    @property
    def keycloak_issuer_url(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}"

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.keycloak_issuer_url}/protocol/openid-connect/certs"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def demo_mode(self) -> bool:
        """Demo mode only allowed in development."""
        return self.app_env == "development" and not self.keycloak_client_secret


@lru_cache
def get_settings() -> Settings:
    return Settings()
