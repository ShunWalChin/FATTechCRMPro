from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FATTECH_", env_file=".env", extra="ignore",
                                     hide_input_in_errors=True)
    env: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./fattech.db"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"
    webhook_secret: str = ""
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_verify_token: str = ""
    meta_access_token: str = ""
    meta_publish_token: str = ""
    public_tenant_slug: str = "fattech"
    session_hours: int = 12
    # Credential-stuffing limits. Production keeps the defaults; a loopback test harness may raise them.
    login_attempts_per_email: int = 10
    login_attempts_per_ip: int = 30
    max_body_bytes: int = 1_048_576
    external_sends_enabled: bool = False
    capture_creates_deal: bool = True
    blocked_terms: str = ""
    n8n_outbound_url: str = ""
    n8n_outbound_token: str = ""
    worker_max_attempts: int = 8
    worker_poll_seconds: int = 5

    @field_validator("database_url", "allowed_origins", "public_tenant_slug")
    @classmethod
    def require_nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Required configuration must not be blank")
        return value

    @field_validator("webhook_secret", "n8n_outbound_url", "n8n_outbound_token")
    @classmethod
    def reject_whitespace_only(cls, value: str) -> str:
        # Empty optional integration settings intentionally disable the adapter.
        if value and not value.strip():
            raise ValueError("Configuration must not contain only whitespace")
        return value

    @property
    def origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def blocklist(self) -> list[str]:
        return [term.strip() for term in self.blocked_terms.split(",") if term.strip()]

    @property
    def production(self) -> bool:
        return self.env == "production"

    @model_validator(mode="after")
    def validate_production(self):
        if not 1 <= self.login_attempts_per_email <= 1000 or not 1 <= self.login_attempts_per_ip <= 3000:
            raise ValueError('Invalid login attempt limits')
        if self.production and (self.login_attempts_per_email > 20 or self.login_attempts_per_ip > 60):
            raise ValueError('Production login limits must stay restrictive')
        if not 1 <= self.session_hours <= 168 or not 1 <= self.worker_max_attempts <= 20:
            raise ValueError("Invalid session duration or worker attempt limit")
        if self.worker_poll_seconds < 1 or self.max_body_bytes < 1024:
            raise ValueError("Invalid polling interval or body limit")
        if self.n8n_outbound_url:
            url = urlsplit(self.n8n_outbound_url)
            if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
                raise ValueError("Outbound n8n URL must be an HTTP(S) URL without embedded credentials")
            # A literal address is checked here; a hostname is resolved by the worker before each delivery.
            from .outbound import is_public_address
            import ipaddress
            try:
                ipaddress.ip_address(url.hostname)
            except ValueError:
                pass
            else:
                if not is_public_address(url.hostname):
                    raise ValueError("Outbound n8n URL must not target a private or reserved address")
            if self.production and url.scheme != "https":
                raise ValueError("Production outbound n8n requires HTTPS")
            if len(self.webhook_secret) < 32:
                raise ValueError("Outbound events require a 32-character webhook secret")
        if self.production:
            if not self.database_url.startswith("postgresql"):
                raise ValueError("Production requires PostgreSQL")
            if not self.origins or any(not x.startswith("https://") or "*" in x for x in self.origins):
                raise ValueError("Production requires explicit HTTPS origins")
            if len(self.webhook_secret) < 32:
                raise ValueError("Production requires FATTECH_WEBHOOK_SECRET of at least 32 characters")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
