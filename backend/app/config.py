from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/automa.db"
    secret_key: str = "your-secret-key-change-in-production"
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
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        env_file = ".env"


settings = Settings()