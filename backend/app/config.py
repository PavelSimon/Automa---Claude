import secrets
from typing import Literal
from pydantic import field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    environment: Literal["development", "staging", "production"] = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/automa.db"

    # Security
    secret_key: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Sandbox settings
    sandbox_image: str = "automa-sandbox:latest"
    sandbox_memory_limit: str = "256m"
    sandbox_cpu_limit: str = "0.5"
    sandbox_timeout: int = 300

    # File paths
    scripts_directory: str = "./scripts"
    data_directory: str = "./data"

    # CORS settings
    cors_origins: list[str] = ["http://localhost:8002", "http://localhost:8080"]

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v, info):
        """Ensure secret key is secure for production"""
        if hasattr(info, 'data') and info.data.get('environment') == 'production':
            if len(v) < 32:
                raise ValueError('Secret key must be at least 32 characters for production')
            if v in ['your-secret-key-change-in-production', 'dev-secret-key']:
                raise ValueError('Must use a secure secret key for production')
        return v

    @field_validator('cors_origins')
    @classmethod
    def validate_cors_origins(cls, v, info):
        """Restrict CORS origins in production"""
        if hasattr(info, 'data') and info.data.get('environment') == 'production':
            # Remove localhost origins in production
            return [origin for origin in v if not origin.startswith('http://localhost')]
        return v

    model_config = ConfigDict(env_file=".env")


settings = Settings()