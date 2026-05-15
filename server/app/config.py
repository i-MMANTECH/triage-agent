"""Application settings loaded from environment variables / .env file."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # --- Auth (pick ONE path) ---
    # Path A: Google AI Studio API key — free tier, no billing required.
    # Path B: Vertex AI via GCP project + ADC — needs billing.
    google_api_key: str = Field(default="")
    google_cloud_project: str = Field(default="")
    google_cloud_location: str = Field(default="us-central1")
    # gemini-2.5-flash is on the AI Studio free tier; gemini-2.5-pro is paid.
    # Bump to pro (or 3.0-pro when available) once billing is active.
    gemini_model: str = Field(default="gemini-2.5-flash")

    # --- Dynatrace ---
    dynatrace_tenant_url: str = Field(default="")
    dynatrace_api_token: str = Field(default="")
    dynatrace_mcp_command: str = Field(default="npx")
    dynatrace_mcp_args: str = Field(default="-y,@dynatrace-oss/dynatrace-mcp-server")

    # --- Mock mode ---
    triage_mock_mode: bool = Field(default=True)

    # --- Firestore ---
    firestore_collection_incidents: str = Field(default="triage_incidents")
    firestore_collection_approvals: str = Field(default="triage_approvals")

    # --- Server ---
    web_origin: str = Field(default="http://localhost:3000")
    log_level: str = Field(default="INFO")

    @property
    def dynatrace_mcp_arg_list(self) -> list[str]:
        return [arg.strip() for arg in self.dynatrace_mcp_args.split(",") if arg.strip()]

    @property
    def has_dynatrace_credentials(self) -> bool:
        return bool(self.dynatrace_tenant_url and self.dynatrace_api_token)


@lru_cache
def get_settings() -> Settings:
    return Settings()
