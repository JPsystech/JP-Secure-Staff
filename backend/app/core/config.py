from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import List
import os

DEFAULT_ORIGINS = [
    "http://localhost:3000", "http://localhost:3001", "http://localhost:3002",
    "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:3002",
]


def get_cors_origins() -> List[str]:
    """Read ALLOWED_ORIGINS from env (comma-separated); else default list."""
    raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    if raw:
        return [x.strip() for x in raw.split(",") if x.strip()]
    return list(DEFAULT_ORIGINS)


class Settings(BaseSettings):
    """DATABASE_URL from env; Railway may provide POSTGRES_URL instead."""
    DATABASE_URL: str = ""
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "jp-secure-staff"
    USE_MINIO: bool = False
    STORAGE_PATH: str = ""
    CORS_ORIGINS: List[str] = []  # Populated from ALLOWED_ORIGINS in main

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @model_validator(mode="after")
    def resolve_database_url(self):
        """Railway provides POSTGRES_URL; app expects DATABASE_URL."""
        if not (self.DATABASE_URL or "").strip():
            self.DATABASE_URL = (os.getenv("POSTGRES_URL") or "").strip()
        return self


settings = Settings()

