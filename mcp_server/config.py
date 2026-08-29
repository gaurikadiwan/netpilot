"""Centralised, typed configuration.

Everything the server needs at runtime is read here once, from the
environment, rather than scattered `os.environ` calls through the codebase.
This is the same pattern used in job-fit-tracker's core/config.py.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./netpilot.db"

    # Bearer token(s) NetPilot will accept. In a real deployment this would
    # be replaced by short-lived tokens issued by an identity provider --
    # a single static token is intentional for a local portfolio project,
    # and is called out as a limitation in the README rather than hidden.
    netpilot_api_token: str = "change-me-local-dev-token"
    netpilot_token_scopes: str = "read,plan"

    log_level: str = "INFO"
    audit_log_path: str = "./audit.log"

    @property
    def token_scopes(self) -> set[str]:
        return {s.strip() for s in self.netpilot_token_scopes.split(",") if s.strip()}


settings = Settings()
